import _chemfp
import ctypes


def threshold_tanimoto_search(queries, targets, threshold):
    assert queries.header.num_bits == targets.header.num_bits
    num_bits = queries.header.num_bits

    num_queries = len(queries)

    offsets = (ctypes.c_int * (num_queries+1))()
    offsets[0] = 0

    num_cells = min(100, len(queries)) * len(targets)
    indicies = (ctypes.c_int * num_cells)()
    scores = (ctypes.c_double * num_cells)()
    
    query_start = 0
    query_end = len(queries)


    def add_rows(query_start):
        return _chemfp.threshold_tanimoto_arena(
            threshold, num_bits,
            queries.storage_size, queries.arena, query_start, query_end,
            targets.storage_size, targets.arena, 0, -1,
            targets.popcount_indicies,
            offsets, query_start,
            indicies, scores)

    return _search(query_end, offsets, indicies, scores, add_rows,
                   queries.ids, targets.ids)

def _search(query_end, offsets, indicies, scores, add_rows, query_ids, target_ids):
    num_added = add_rows(0)
    if num_added == query_end:
        return SearchResults(offsets, indicies, scores, query_ids, target_ids)

    query_start = num_added

    last = offsets[num_added]
    all_indicies = indicies[:last]
    all_scores = scores[:last]

    while query_start < query_end:
        num_added = add_rows(query_start)
        assert num_added > 0

        prev_last = offsets[query_start]
        all_indicies[prev_last:] = indicies
        all_scores[prev_last:] = scores

        query_start += num_added

    return SearchResults(offsets, all_indicies, all_scores, query_ids, target_ids)


def knearest_tanimoto_search(queries, targets, k, threshold):
    assert queries.header.num_bits == targets.header.num_bits
    num_bits = queries.header.num_bits

    num_queries = len(queries)

    offsets = (ctypes.c_int * (num_queries+1))()
    offsets[0] = 0

    num_cells = min(100, len(queries))*k

    indicies = (ctypes.c_int * num_cells)()
    scores = (ctypes.c_double * num_cells)()

    query_start = 0
    query_end = len(queries)

    def add_rows(query_start):
        return _chemfp.klargest_tanimoto_arena(
            k, threshold, num_bits,
            queries.storage_size, queries.arena, query_start, query_end,
            targets.storage_size, targets.arena, 0, -1,
            targets.popcount_indicies,
            offsets, query_start,
            indicies, scores)

    return _search(query_end, offsets, indicies, scores, add_rows,
                   queries.ids, targets.ids)


class FingerprintLookup(object):
    def __init__(self, fp_size, storage_size, arena):
        self._fp_size = fp_size
        self._storage_size = storage_size
        self._arena = arena
        self._range_check = xrange(len(self))

    def __len__(self):
        return len(self._arena) / self._storage_size

    def __iter__(self):
        fp_size = self._fp_size
        arena = self.arena
        for id, start_offset in zip(self.ids, xrange(0, len(self.arena), storage_size)):
            yield id, arena[start_offset:start_offset+target_fp_size]
        
        
    def __getitem__(self, i):
        start_offset = self._range_check[i] * self._storage_size
        self.arena[start_offset:start_offset+self._fp_size]

class Library(object):
    def __init__(self, header, storage_size, arena, popcount_indicies, ids):
        self.header = header
        self.num_bits = header.num_bits
        self.storage_size = storage_size
        self.arena = arena
        self.popcount_indicies = popcount_indicies
        self.ids = ids
        self.fingerprints = FingerprintLookup(header.num_bytes_per_fp, storage_size, arena)
        self._range_check = xrange(len(self))

    def __len__(self):
        return len(self.arena) / self.header.num_bytes_per_fp

    def __getitem__(self):
        start_offset = self._range_check[i] * self._storage_size
        self.arena[start_offset:start_offset+self._fp_size]
        return self.ids[i], arena[start_offset:start_offset+self.header.num_bytes_per_fp]
        
    def reset(self):
        pass

    def __iter__(self):
        storage_size = self.storage_size
        target_fp_size = self.header.num_bytes_per_fp
        arena = self.arena
        for id, start_offset in zip(self.ids, xrange(0, len(self.arena), storage_size)):
            yield id, arena[start_offset:start_offset+target_fp_size]

#    _tanimoto_count_fp_ = staticmethod(tanimoto_count_fp)
#    _tanimoto_count_ = staticmethod(tanimoto_count)
#    _tanimoto_count_once_ = staticmethod(tanimoto_count)

#    _threshold_tanimoto_search_fp_ = staticmethod(threshold_tanimoto_search_fp)
    _threshold_tanimoto_search_ = staticmethod(threshold_tanimoto_search)
#    _threshold_tanimoto_search_once_ = staticmethod(threshold_tanimoto_search)

#    _knearest_tanimoto_search_fp = staticmethod(knearest_tanimoto_search_fp)
    _knearest_tanimoto_search_ = staticmethod(knearest_tanimoto_search)
#    _knearest_tanimoto_search_once_ = staticmethod(knearest_tanimoto_search)


class ChemFPOrderedPopcount(ctypes.Structure):
    _fields_ = [("popcount", ctypes.c_int),
                ("index", ctypes.c_int)]

import array
def reorder_fingerprints(fingerprints):
    ordering = (ChemFPOrderedPopcount*len(fingerprints))()
    popcounts = array.array("i", (0,)*(fingerprints.header.num_bits+1))
    #popcounts = (ctypes.c_int*(fingerprints.header.num_bits+1))()
    
    new_arena = _chemfp.reorder_by_popcount(
        fingerprints.header.num_bits, fingerprints.storage_size,
        fingerprints.arena, 0, -1, ordering, popcounts)

    print list(popcounts)
    new_ids = [fingerprints.ids[item.index] for item in ordering]
    return Library(fingerprints.header, fingerprints.storage_size,
                   new_arena, popcounts.tostring(), new_ids)
                                

def knearest_tanimoto_search_fp(query_fp, targets, k, threshold):
    if not isinstance(query_fp, Library):
        raise Spam
    




class SearchResults(object):
    def __init__(self, offsets, indicies, scores, query_ids, target_ids):
        assert len(offsets) > 0
        if offsets:
            assert indicies[offsets[-2]]
            assert scores[offsets[-2]]
        self.offsets = offsets
        self.indicies = indicies
        self.scores = scores
        self.query_ids = query_ids
        self.target_ids = target_ids
        
    def __len__(self):
        return len(self.offsets)-1

    def size(self, i):
        return self.offsets[i+1]-self.offsets[i]
    
    def __getitem__(self, i):
        start, end = self.offsets[i:i+2]
        return zip(self.indicies[start:end], self.scores[start:end])

    def __iter__(self):
        target_ids = self.target_ids
        indicies = self.indicies
        scores = self.scores
        start = self.offsets[0]
        for target_id, end in zip(self.query_ids, self.offsets[1:]):
            yield target_id, zip((target_ids[index] for index in indicies[start:end]),
                                 scores[start:end])
            start = end

    def iterhits():
        indicies = self.indicies
        scores = self.scores
        start = self.offsets[0]
        for end in self.offsets[1:]:
            yield target_id, zip(indicies[start:end], scores[start:end])
            start = end

    