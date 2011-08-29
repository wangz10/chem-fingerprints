# Library for working with cheminformatics fingerprints

# All chem-fingerprint software is distributed with the following license:

# Copyright (c) 2010-2011 Andrew Dalke Scientific, AB (Gothenburg, Sweden)
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__version__ = "1.0a1"
__version_info = (1, 0, 0)
SOFTWARE = "chemfp/" + __version__

import os
import __builtin__

from .error_handlers import ChemFPError

_K = 3
_THRESHOLD = 0.7

def read_structure_fingerprints(type, source=None, format=None):
    from . import types
    return types.read_structure_fingerprints(type, source, format)
    
# Low-memory, forward-iteration, or better
def open(source, format=None, type=None):
    from . import io
    format_name, compression = io.normalize_format(source, format)

    if format_name == "fps":
        from . import readers
        return readers.open_fps(source, format_name+compression)

    if format_name == "fpb":
        raise NotImplementedError

    # Otherwise it's a structure input.
    if type is None:
        raise TypeError("'type' is required to read structure fingerprints")
    return read_structure_fingerprints(type, source, format_name+compression)

def open_fps(source):
    from . import readers
    return readers.open_fps(source)

def load_fingerprints(reader, header=None, sort=True):
    if isinstance(reader, basestring):
        reader = open(reader)
    # See if it has its own way to generate an in-memory search library
    f = getattr(reader, "_chemfp_load_library_", None)
    if f is not None:
        return f(sort=sort)

    # Nope. Use the basic forward-iteration algorithm
    from chemfp import library
    return library.fps_to_library(reader, header=header, sort=sort)

# High-level interface

def tanimoto_count(queries, targets, threshold=_THRESHOLD, batch_size=100):
    if batch_size == 1:
        for (query_id, query_fp) in queries:
            targets.reset()
            yield query_id, targets.tanimoto_count(query_fp, threshold)
        return
    
    for query_arena in queries.iter_arenas(batch_size):
        targets.reset()
        results = targets.tanimoto_count_arena(query_arena, threshold)
        for item in zip(query_arena.ids, results):
            yield item
    

def threshold_tanimoto_search(queries, targets, threshold=_THRESHOLD, batch_size=100):
    if batch_size == 1:
        for (query_id, query_fp) in queries:
            targets.reset()
            yield query_id, targets.threshold_tanimoto_search_fp(query_fp, threshold)
        return
    
    for query_arena in queries.iter_arenas(batch_size):
        targets.reset()
        results = targets.threshold_tanimoto_search_arena(query_arena, threshold)
        for item in zip(query_arena.ids, results):
            yield item

def knearest_tanimoto_search(queries, targets, k=_K, threshold=_THRESHOLD, batch_size=100):
    if batch_size == 1:
        for (query_id, query_fp) in queries:
            targets.reset()
            yield query_id, targets.threshold_tanimoto_search_fp(query_fp, k, threshold)

    for query_arena in queries.iter_arenas(batch_size):
        targets.reset()
        results = targets.threshold_tanimoto_search_arena(query_arena, k, threshold)
        for item in zip(query_arena.ids, results):
            yield item
