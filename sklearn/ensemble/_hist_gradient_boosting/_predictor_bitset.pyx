# cython: cdivision=True
# cython: boundscheck=False
# cython: wraparound=False
# cython: language_level=3
# cython: nonecheck=False
# distutils: language=c++

from ._bitset cimport in_bitset
from .common cimport BITSET_INNER_DTYPE_C
from libc.limits cimport CHAR_BIT
from libcpp.vector cimport vector


cdef inline unsigned char in_vec_bitset(vector[BITSET_INNER_DTYPE_C]& bitset,
                                        int value) nogil:
    cdef:
        unsigned int i1 = value // 32
        unsigned int i2 = value % 32

    if bitset.size() < i1 + 1:
        return 0
    return (bitset[i1] >> i2) & 1


cdef inline void insert_vec_bitset(vector[BITSET_INNER_DTYPE_C]& bitset,  # OUT
                                   int value) nogil:
    cdef:
        unsigned int i1 = value // 32
        unsigned int i2 = value % 32

    if bitset.size() < i1 + 1:
        bitset.resize(i1 + 1, 0)
    bitset[i1] |= (1 << i2)


cdef class PredictorBitSet:
    def __init__(self, list bin_thresholds,
                 const unsigned char [:] is_categorical):
        """Creates bitset for all known categories"""
        if is_categorical is None or bin_thresholds is None:
            return

        cdef:
            int i
            X_DTYPE_C raw_cat
            unsigned int i1
            unsigned int i2

        for f_idx in range(is_categorical.shape[0]):
            if not is_categorical[f_idx]:
                continue
            for raw_cat in bin_thresholds[f_idx]:
                insert_vec_bitset(self.feature_idx_raw_cats[f_idx],
                                  <int>(raw_cat))

    def insert_categories_bitset(self, unsigned int node_idx,
                                 X_DTYPE_C[:] category_bins,
                                 BITSET_INNER_DTYPE_C[:] cat_bitset):
        """Insert category into bitset for raw categories and binned cateogires
        for node_idx.
        """
        cdef:
            BITSET_INNER_DTYPE_C val
            int k, offset
            int cardinality = category_bins.shape[0]
            int BITSET_SIZE = sizeof(BITSET_INNER_DTYPE_C) * CHAR_BIT
            unsigned int i1, i2

        self.node_to_binned_bitset[node_idx].resize(cat_bitset.shape[0])
        for k, val in enumerate(cat_bitset):
            offset = BITSET_SIZE * k
            self.node_to_binned_bitset[node_idx][k] = val
            while val and offset < cardinality:
                if val & 1:
                    insert_vec_bitset(self.node_to_raw_bitset[node_idx],
                                      <int>(category_bins[offset]))
                val >>= 1
                offset += 1

    cdef unsigned char is_known_category(self, unsigned int feature_idx,
                                         X_DTYPE_C category) nogil:
        """Check if category is known"""
        return in_vec_bitset(self.feature_idx_raw_cats[feature_idx],
                             <int>category)

    cdef unsigned char raw_category_in_bitset(self, unsigned int node_idx,
                                              X_DTYPE_C category) nogil:
        """Check if raw category is in bitset for node_idx"""
        return in_vec_bitset(self.node_to_raw_bitset[node_idx], <int>category)

    cdef unsigned char binned_category_in_bitset(self, unsigned int node_idx,
                                                 X_BINNED_DTYPE_C category) nogil:
        """Check if binned cateogry is in bitset for node_idx"""
        return in_vec_bitset(self.node_to_binned_bitset[node_idx],
                             <int>category)

    def get_binned_categories(self, unsigned int node_idx):
        """Used for testing"""
        return self.node_to_binned_bitset[node_idx]

    def get_raw_categories(self, unsigned int node_idx):
        """Used for testing"""
        return self.node_to_raw_bitset[node_idx]
