"Create OpenBabel fingerprints"

# Copyright (c) 2010 Andrew Dalke Scientific, AB (Gothenburg, Sweden)
# See the contents of "__init__.py" for full license details.

from __future__ import absolute_import

import sys
import os
import struct
import warnings

import openbabel as ob

from . import io
from . import types


# OpenBabel really wants these two variables. I get a segfault if
# BABEL_LIBDIR isn't defined, and from the mailing list, some of the
# code doesn't work correctly without BABEL_DATADIR. I've had problems
# where I forget to set these variables, so check for them now and
# warn about possible problems.

#if "BABEL_LIBDIR" not in os.environ:
#    warnings.warn("BABEL_LIBDIR is not set")

#else:
#  ... check that SMILES and a few other things are on the path ...
#  but note that BABEL_LIBDIR is a colon (or newline or control-return?)
#  separated field whose behaviour isn't well defined in the docs.
#  I'm not going to do additional checking without a stronger need.


# This is the only thing which I consider to be public
__all__ = ["read_structures"]

# This is a "standard" size according to the struct module
# documentation, so the following is an excess of caution
if struct.calcsize("<I") != 4:
    raise AssertionError("The chemfp.ob module assumes 32 bit integers")


# OpenBabel 2.2 doesn't expose "obErrorLog" to Python
HAS_ERROR_LOG = hasattr(ob, "obErrorLog")

# OpenBabel before 2.3 didn't have a function to return the version.
# I've brought this up on the list, and it's in 2.3. I can fake
# support for older lists by reading the PDB output text.

def _emulated_GetReleaseVersion():
    "GetReleaseVersion() -> the version string for the OpenBabel toolkit"
    obconversion = ob.OBConversion()
    obconversion.SetInFormat("smi")
    obconversion.SetOutFormat("pdb")
    obmol = ob.OBMol()
    
    obconversion.ReadString(obmol, "C")
    for line in obconversion.WriteString(obmol).splitlines():
        if "GENERATED BY OPEN BABEL" in line:
            return line.split()[-1]
    return "<unknown>"

try:
    from openbabel import GetReleaseVersion
except ImportError:
    GetReleaseVersion = _emulated_GetReleaseVersion
_ob_version = GetReleaseVersion()

SOFTWARE = "OpenBabel/" + _ob_version


# OpenBabel fingerprints are stored as vector<unsigned int>.  On all
# the machines I use, ints have 32 bits.

# OpenBabel bit lengths must be at least sizeof(int)*8 bits long and
# must be a factor of two. I have no idea why this is required.

# OpenBabel supports new fingerprints through a plugin system.  I got
# it working thanks to Noel O'Boyle's excellent work with Cinfony. I
# then found out that the OB API doesn't have any way to get the
# number of bits in the fingerprint. The size is rounded up to the
# next power of two, so FP4 (307 bits) needs 512 bits (16 ints)
# instead of 320 bits (10 ints). That means I can't even get close to
# guessing the bitsize.

# In the end, I hard-coded the supported fingerprints into the system.



############

# I could have written a more general function which created these but
# there's only a few fingerprints lengths to worry about.

# This needs 128 bytes, for 1024 bits
# vectorUnsignedInt will contain 32 32-bit words = 1024 bits

_ob_get_fingerprint = {}
def _init():
    for name in ("FP2", "FP3", "FP4", "MACCS"):
        ob_fingerprinter = ob.OBFingerprint.FindFingerprint(name)
        if ob_fingerprinter is None:
            _ob_get_fingerprint[name] = (None, None)
        else:
            _ob_get_fingerprint[name] = (ob_fingerprinter, ob_fingerprinter.GetFingerprint)

    n = _ob_get_fingerprint["FP2"][0].Getbitsperint()
    if n != 32:
        raise AssertionError(
            "The chemfp.ob module assumes OB fingerprints have 32 bits per integer")
            
_init()

def calc_FP2(mol, fp=None,
             get_fingerprint=_ob_get_fingerprint["FP2"][1],
             _pack_1024 = struct.Struct("<" + "I"*32).pack):
    if fp is None:
        fp = ob.vectorUnsignedInt()
    get_fingerprint(mol, fp)
    return _pack_1024(*fp)

# This needs 7 bytes, for 56 bits.
# vectorUnsignedInt will contain 2 32-bit words = 64 bits
def calc_FP3(mol, fp=None,
             get_fingerprint=_ob_get_fingerprint["FP3"][1],
             _pack_64 = struct.Struct("<II").pack):
    if fp is None:
        fp = ob.vectorUnsignedInt()
    get_fingerprint(mol, fp)
    return _pack_64(*fp)[:7]

# This needs 39 bytes, for 312 bits
# vectorUnsignedInt will contain 16 32-bit words = 512 bits
def calc_FP4(mol, fp=None,
             get_fingerprint=_ob_get_fingerprint["FP4"][1],
             _pack_512 = struct.Struct("<" + "I"*16).pack):
    if fp is None:
        fp = ob.vectorUnsignedInt()
    get_fingerprint(mol, fp)
    return _pack_512(*fp)[:39]

# This needs 21 bytes, for 166 bits
# vectorUnsignedInt will contain 8 32-bit words = 256 bits
# (Remember, although 6 words * 32-bits/word = 192, the OpenBabel
# fingerprint size must be a power of 2, and the closest is 8*32.)
def calc_MACCS(mol, fp=None,
               get_fingerprint=_ob_get_fingerprint["MACCS"][1],
               _pack_256 = struct.Struct("<" + "I"*8).pack):
    if fp is None:
        fp = ob.vectorUnsignedInt()
    get_fingerprint(mol, fp)
    return _pack_256(*fp)[:21]


# Pre 2.3 versions of OpenBabel did not have MACCS.
# Version 2.3.0 contained a buggy MACCS implementation.
# That was soon fixed in version control.
# MACCS might also be missing if BABEL_DATADIR doesn't exist.
HAS_MACCS = False
MACCS_VERSION = 0

def _check_for_maccs():
    global HAS_MACCS, MACCS_VERSION
    if _ob_get_fingerprint["MACCS"] == (None, None):
        if _ob_version.startswith("2.2."):
            return
        # MACCS should be here. Report the most likely reason
        if "BABEL_DATADIR" not in os.environ:
            warnings.warn("MACCS fingerprint missing; perhaps due to missing BABEL_DATADIR?")
        else:
            warnings.warn("MACCS fingerprint missing; perhaps due to BABEL_DATADIR?")
        return

    HAS_MACCS = 1

    # OpenBabel 2.3.0 released the MACCS keys but with a bug in the SMARTS.
    # While they are valid substructure keys, they are not really MACCS keys.
    # This is a run-time detection to figure out which version was installed
    obconversion = ob.OBConversion()
    obconversion.SetInFormat("smi")
    obmol = ob.OBMol()
    obconversion.ReadString(obmol, "C1CCC1")
    fp = calc_MACCS(obmol)
    if fp[:6] == "000020":
        MACCS_VERSION = 1
    else:
        MACCS_VERSION = 2

_check_for_maccs()


#########

def _get_ob_error(log):
    msgs = log.GetMessagesOfLevel(ob.obError)
    return "".join(msgs)

def read_structures(filename=None, format=None):
    """read_structures(filename, format) -> (title, OBMol) iterator 
    
    Iterate over structures from filename, returning the structure
    title and OBMol for each reacord. The structure is assumed to be
    in normalized_format(filename, format) format. If filename is None
    then this reads from stdin instead of the named file.
    """
    if not (filename is None or isinstance(filename, basestring)):
        raise TypeError("'filename' must be None or a string")
    
    obconversion = ob.OBConversion()
    format_name, compression = io.normalize_format(filename, format,
                                                   default=("smi", ""))
    if compression not in ("", ".gz"):
        raise TypeError("Unsupported compression type for %r" % (filename,))

    # OpenBabel auto-detects gzip compression.

    if not obconversion.SetInFormat(format_name):
        raise TypeError("Unknown structure format %r" % (format_name,))
    
    obmol = ob.OBMol()

    if not filename:
        # OpenBabel's Python libary has no way to read from std::cin
        # Fake it through /dev/stdin for those OSes which support it.
        if not os.path.exists("/dev/stdin"):
            raise TypeError("Unable to read from stdin on this platform")

        return _stdin_reader(obconversion, obmol)

    # Deal with OpenBabel's logging
    if HAS_ERROR_LOG:
        ob.obErrorLog.ClearLog()
        lvl = ob.obErrorLog.GetOutputLevel()
        ob.obErrorLog.SetOutputLevel(-1) # Suppress messages to stderr

    success = obconversion.ReadFile(obmol, filename)

    errmsg = None
    if HAS_ERROR_LOG:
        ob.obErrorLog.SetOutputLevel(lvl) # Restore message level
        if ob.obErrorLog.GetErrorMessageCount():
            errmsg = _get_ob_error(ob.obErrorLog)

    if not success:
        # Either there was an error or there were no structures.
        open(filename).close() # Make sure the file can be opened for reading

        # If I get here then the file exists and is readable.

        # If there was an error message then use it.
        if errmsg is not None:
            # Okay, don't know what's going on. Report OB's error
            raise IOError(5, errmsg, filename)

    # We've opened the file. Switch to the iterator.
    return _file_reader(obconversion, obmol, success)

def _stdin_reader(obconversion, obmol):
    "This is an internal function"
    # Read structures from stdin.

    # The current release of scripting for OpenBabel doesn't let me
    # use C++'s std::cin as the input stream so I need to fake it
    # using "/dev/stdin". That works on Macs, Linux, and FreeBSD but
    # not Windows.

    # Python says that it's in charge of checking for ^C. When I pass
    # control over to OpenBabel, Python is still in charge of checking
    # for ^C, but it won't do anything until control returns to Python.

    # I found it annoying that if I started the program, which by
    # default expects SMILES from stdin, then I couldn't hit ^C to
    # stop it. My solution was to stay in Python until there's
    # information on stdin, and once that's happened, call OpenBabel.

    import select
    try:
        select.select([sys.stdin], [], [sys.stdin])
    except KeyboardInterrupt:
        raise SystemExit()

    # There's data. Pass parsing control into OpenBabel.
    notatend = obconversion.ReadFile(obmol, "/dev/stdin")
    return _file_reader(obconversion, obmol, notatend)

def _file_reader(obconversion, obmol, notatend):
    i = 1
    while notatend:
        title = obmol.GetTitle()
        if not title:
            title = "Record" + str(i)
        yield title, obmol
        i += 1
        obmol.Clear()
        notatend = obconversion.Read(obmol)
        # How do I detect if the input contains a failure?

########
def read_fp2_fingerprints_v1(source, format, kwargs={}):
    assert not kwargs
    fingerprinter = calc_FP2
    reader = read_structures(source, format)

    def read_openbabel_fp2_structure_fingerprints():
        for (title, mol) in reader:
            yield (fingerprinter(mol), title)

    return read_openbabel_fp2_structure_fingerprints()

def read_fp3_fingerprints_v1(source, format, kwargs={}):
    assert not kwargs
    fingerprinter = calc_FP3
    reader = read_structures(source, format)

    def read_openbabel_fp3_structure_fingerprints():
        for (title, mol) in reader:
            yield (fingerprinter(mol), title)

    return read_openbabel_fp3_structure_fingerprints()

def read_fp4_fingerprints_v1(source, format, kwargs={}):
    assert not kwargs
    fingerprinter = calc_FP4
    reader = read_structures(source, format)

    def read_openbabel_fp4_structure_fingerprints():
        for (title, mol) in reader:
            yield (fingerprinter(mol), title)

    return read_openbabel_fp4_structure_fingerprints()

def read_maccs166_fingerprints_v1(source, format, kwargs={}):
    assert HAS_MACCS
    assert MACCS_VERSION == 1
        
    assert not kwargs
    fingerprinter = calc_MACCS
    reader = read_structures(source, format)

    def read_openbabel_maccs166_structure_fingerprints():
        for (title, mol) in reader:
            yield (fingerprinter(mol), title)

    return read_openbabel_maccs166_structure_fingerprints()

def read_maccs166_fingerprints_v2(source, format, kwargs={}):
    assert HAS_MACCS
    assert MACCS_VERSION == 2
        
    assert not kwargs
    fingerprinter = calc_MACCS
    reader = read_structures(source, format)

    def read_openbabel_maccs166_structure_fingerprints():
        for (title, mol) in reader:
            yield (fingerprinter(mol), title)

    return read_openbabel_maccs166_structure_fingerprints()

#####

class _OpenBabelFingerprinter(types.Fingerprinter):
    software = SOFTWARE

class OpenBabelFP2Fingerprinter_v1(_OpenBabelFingerprinter):
    name = "OpenBabel-FP2/1"
    num_bits = 1021
    _get_reader = staticmethod(read_fp2_fingerprints_v1)

class OpenBabelFP3Fingerprinter_v1(_OpenBabelFingerprinter):
    name = "OpenBabel-FP3/1"
    num_bits = 55
    _get_reader = staticmethod(read_fp3_fingerprints_v1)

class OpenBabelFP4Fingerprinter_v1(_OpenBabelFingerprinter):
    name = "OpenBabel-FP4/1"
    num_bits = 307
    _get_reader = staticmethod(read_fp4_fingerprints_v1)


class OpenBabelMACCSFingerprinter_v1(_OpenBabelFingerprinter):
    name = "OpenBabel-MACCS/1"
    num_bits = 166
    _get_reader = staticmethod(read_maccs166_fingerprints_v1)
    
class OpenBabelMACCSFingerprinter_v2(_OpenBabelFingerprinter):
    name = "OpenBabel-MACCS/2"
    num_bits = 166
    _get_reader = staticmethod(read_maccs166_fingerprints_v2)
