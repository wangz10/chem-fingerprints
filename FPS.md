First and foremost, this format is meant to be easy to use. It is
line-oriented and human-readable. FPS files are easy to generate and
parse using skills that any cheminformatics programmer or Unix user,
should be comfortable with.

The following example is the first 10 lines of an FPS file.

```
#FPS1
#num_bits=256
#software=RDKit/2009Q3_1
#type=RDKit-Fingerprint/1 minPath=1 maxPath=7 fpSize=256 nBitsPerHash=4 useHs=True
#source=/Users/dalke/databases/Compound_00000001_00025000.sdf.gz
#date=2010-01-27T02:22:26
fffeffbfb7fffedff7beefdbddf7ffffabff76cf6df7fcf6f7fffebf7d7ffd6f	1
fffeffbfb7fffedff7beefdbddf7ffffabff76cf6df7fcf6f7fffebf7d7ffd6f 	2
ffffbfdfffffffffbfeffffffffffffffffffffffff77efffffffebfffffffef 	3
00c02010002610000080800041100002084000440d100000c055048801224400 	4
```

The source structure data comes from a compressed PubChem SD file. The
fingerprints were generated by RDKit using the listed parameters to
generate fingerprints of length 256 bits. (The default RDKit
fingerprint is 2048 bits. The short size here is for demonstration purposes.)

The fingerprint records start after the '#' header lines. Each record
contains two columns, separated by a tab. The first field is the
hex-encoded fingerprint, and the second field is the identifier.

In this case the fingerprint has 64 hex characters, since each hex
character represents 4 bits of the original fingerprint and 64\*4=256.

## Newline conventions ##

FPS fingerprint files will be generated with both Unix and Windows
readline conventions. Parsers must understand both conventions.

## Version line ##

The first line of an FPS file is the version string "#FPS1". Programs
which generate FPS output must include that line to make it easier for
other tools to identify the specific file format.

Parsers must be aware that few people read format specifications
before they generate fingerprint output so should accept files which
don't have the version header. They may complain bitterly.

If the version line is not present then parsers may assume the input
is in the latest version of this format.

## Key/value headers ##

After the version header is an optional set of lines of the format

```
'#'  key '=' value
```

The key must be written with no leading and trailing spaces. Since I
doubt everyone will follow these rules, parsers must strip any leading
and trailing spaces from the key. Unless otherwise noted, the same
rules apply  to the value.

Keys will contain one or more of the ASCII characters `[a-zA-z0-9_-]`.
(The range of characters may increase in the future, but will never
allow the '=' nor space character, nor any character with code points
0-31.)

The value field contains UTF-8 encoded text. This must not contain
the code points 0 - 31 and must not contain the Unicode byte order mark.

All key/value headers are optional. For purposes of future version
compatibility, parsers may ignore unknown headers.

Lines starting with "x-" or "X-" may be used for experimental headers or to provide extra metadata which is not part of the FPS specification. (For example, it may store that the fingerprint is a reaction fingerprint instead of a molecule fingerprint.)

### num\_bits header ###

The 'num\_bits' header contains the number of bits in the
fingerprint. It must be a postive integer and should be
present.

Examples:

```
#num_bits=256
#num_bits=166
#num_bits=7
#num_bits=2001
```

There are two relevant lengths involved: the bit length of the
fingerprint and its byte length. Fingerprints are stored in 8-bit
bytes, so the byte length must be 1/8 of the bit length, rounded up.

If the num\_bits header is not present then it can be calculated by
reading the first fingerprint and multiplying its byte length by 8.

If the num\_bits header is present then it must be compared to the byte
length of the first fingerprint to ensure that they are
commensurate. That is, that:

```
 (byte_length-1)*8 <  bit_length <= byte_length*8
```

Question: Is this too strong? Should it just check that bit\_length <= byte\_length\*8 ?

### software header ###

The 'software' header contains information about the software program
which generated the fingerprint, including version information. It is
based on the [User-Agent field of RFC 1945](http://tools.ietf.org/html/rfc1945#section-10.15)
and contains one or more product or comment tokens "identifying the software
and any subproducts which form a significant part of the software" used to
generate the fingerprint. The tokens may only be separated by a space character,
and should only be separated by a single space character.

Examples:

```
 #software=OpenBabel/2.2.3
 #software=RDKit/2009Q3_1 boost/1.41
 #software=OEGraphSim/1.0.0 (20100809)
```

In the above examples, RDKit depends on the Boost RNG libraries and
while there should be no differences between Boost 1.40 and 1.41,
it may be useful to keep track of that information.

OEGraphSim here shows the release number (the "1.0.0"), and
its internal version number which looks to be a release date.

### type header ###

The 'type' header contains information about the specific
fingerprint type and any parameters which were used to generate
it. This header is used to test for compatibility between two
different data sets.

Examples:

```
 #type=OpenEye-MACCS166/1.1
 #type=OpenBabel-FP2/3
 #type=OpenEye-Path/1 min_bonds=0 max_bonds=5 atype=AtomicNumber btype=BondOrder|Chiral
 #type=RDKit-Fingerprint/1.0.2 minPath=1 maxPath=7 fpSize=2048 nBitsPerHash=4 useHs=True
```

The 'type' header value contains fields separated by whitespace. The
first field is the name of the fingerprint type and optional version,
separated by a "/". The version MUST change whenever the underlying
fingerprint algorithm changes.

The other fields in the 'types' value are parameters which affect the
fingerprint algorithm.

The 'type' value must be written in normalized form, using a
single space between fields and with no leading or trailing
whitespace.

The parameters must be listed in a consistent order so they can be
used to compare two fingerprint data sets for compatibility. Two data
sets are compatible if and only if the fingerprints have the same
number of bits and if their normalized 'type' values are the same.

For example, the following two 'type' headers are compatible

```
 #type=Daylight/4 size=2048   minstep=0   maxstep=7
 #type=Daylight/4 size=2048 minstep=0 maxstep=7
```

while the following two are not

```
 #type=Daylight/4 size=2048 minstep=0 maxstep=7
 #type=Daylight/4 size=2048 maxstep=7 minstep=0
```

TODO: have a page with a list of the canonical types for each toolkit/program.

### aromaticity header ###

The 'aromaticity' header describes how the toolkit perceived the chemistry. This field is currently only useful for OEChem since Open Babel and RDKit implement only one aromaticity model. Here are some examples:

```
 #aromaticity: openeye
 #aromaticity: daylight
```

The values are toolkit dependent. In the future this may be extended to support additional parameters, such as the largest supported aromatic ring size used.


### source header ###

The 'source' header describes the source of the structure data. This
will generally be a filename but may be a URL or description of the
data set.

Some examples are

```
 #source=/Users/dalke/databases/nci_09425001_09450000.smi
 #source=PubChem 2010-01-22
 #source=http://example.com/my_stuctures.sdf
```

The information in this file is meant for humans as part of data
provenance and is not meant to be understand by software.

This field may contain Unicode characters. For example, a filename may
contain non-ASCII characters. For that reason, this field must be
UTF-8 encoded. Note that it must fit on a single line and therefore any
newlines must be removed or replaced before use.

Multiple source lines are permitted.

### date header ###

The 'date' header contains the time at which the fingerprints were
created, in UTC.  Some examples are:

```
 #date=2010-01-27T01:38:52
 #date=2010-10-16T23:14:01
```

The date is written as an ISO 8601 timestamp in extended format, which
matches the template:

```
   [YYYY]-[MM]-[DD]T[hh]:[mm]:[ss]
```

or in strftime format,

```
  %Y-%m-%dT%H:%M:%S
```

This field exists for data provenance. Note that the creation time is
not always the same as the time the data was converted into FPS
format.

The date does not include timezone information. Instead, all
dates must be given in UTC.

### other possible headers ###

Question: Would be be useful to define 'title', 'user', 'copyright',
'disclaimer', 'comment' or other headers at this point? I got those
header terms from the PNG specification. If you wish to experiment
with these fields, please use the "x-" prefix.

## Fingerprint records ##

The fingerprint records occur after the version line and headers. Each
record is on a single line and contains a hex-encoded fingerprint
followed by a single tab character, followed by an identifier name.

Examples:

```
 000000082000082159d404eea9e898338ea07a6e3b	CID9425009
 2ac8363d166c704209bef498253a94cb2b687a072f961617f2f50c0fe97344c7	CID137
 0400000070b001	NCI9425402
```

These lines are conceptually identical to a SMILES file, and
deliberately so. Experience with SMILES files tells me that some
people use spaces in an identifier (such as an IUPAC name, and I've
seen it in a corporate database), so these fields **must** be tab separated
and must allow the identifier to include the ASCII space character.

### Bit and byte order ###

Fingerprints are numbered in an abstract space, starting with 0. They
are mapped to a sequence of 8-bit bytes. All fingerprints in an FPS
file must have the same byte length, which must be long enough to
store num\_bits fingerprint bits.

Fingerprint bits 0-7 are stored in the first byte in bit positions
0-7. Fingerprint bits 8-15 are stored in the second byte in bit
positions 0-7, and so on.

Use the following to get from a fingerprint bit position to the byte position and bit
position in the byte:

```
 byte_position(fingerprint_bit) = fingerprint_bit // 8
 bit_position(fingerprint_bit) = fingerprint_bit % 8
```

where '//' and '%' indicate integer division and modulo, respectively.

For example, to tell if bit B in fingerprint fp is on:

```
 bit_is_on(B) = (fp[B//8] >> (B%8)) & 0x01
```

where square brackets indicates a byte offset index, & is bitwise-and, and '>>'
is a right-shift.

Note that the bytes are ordered with the least significant byte first
("little-endian") while the bits in the bytes are ordered with the
most significant bit first ("big-endian"). This will lead to an
apparent transposition of hex digits in the hex encoding.

### Hex encoding ###

The fingerprint bytes are hex-encoded for storage in the fingerprint
record. A hex character encodes only 4 bits of data, so the resulting
hex encoding will be twice a long as the fingerprint byte length. The
hex characters may include uppercase and lowercase forms of the
letters A-F. A parser MUST support both forms.

Hex encoding does lead to an unusual ordering, due to the mix of
little-endian and big-endian values. Consider the 16-bit fingerprint
written with bit 0 on the left:

```
     0           1 
 bit 0123 4567 8901 2345
 =======================
     1000 1010 0011 0010
```

The is translated into the byte string "QL" because:

```
  byte[0]:  0101 0001 = 0x51 = 81 = 'Q'
  byte[1]:  0100 1100 = 0x4C = 76 = 'L'
```

which makes the hex encoding "514C".

Note that the first hex character ("5") corresponds to fingerprint bit
position 4-7, while the second hex character ("1") corresponds to
fingerprint bit positions 0-3. The pattern repeats like this for the
entire string.

To validate your fingerprint bit parser, see BitCheck.

### Identifier ###

The identifier should be a printable ASCII character, that is, it should
only use the code points 32-127. The identifier may include the
space character.

Question: Is there ever a need to allow UTF-8 encoded Unicode,
or any character in the byte range 128-255?

The identifier MUST NOT contain a tab, control-return, or newline
character. The tab is used as the column delimiter and the other
two are part of standard newline conventions.

A parser may ignore additional fields after the identifier.