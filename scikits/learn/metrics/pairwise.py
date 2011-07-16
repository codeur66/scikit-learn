"""Utilities to evaluate pairwise distances or affinity of sets of samples"""

# Authors: Alexandre Gramfort <alexandre.gramfort@inria.fr>
#          Mathieu Blondel <mathieu@mblondel.org>
# License: BSD Style.

import numpy as np
from scipy.sparse import csr_matrix, issparse
from ..utils import safe_asanyarray, atleast2d_or_csr
from ..utils.extmath import safe_sparse_dot

################################################################################
# Distances 

from ..utils.extmath import safe_sparse_dot
from ..utils import inplace_row_normalize


def euclidean_distances(X, Y, Y_norm_squared=None, squared=False):
    """
    Considering the rows of X (and Y=X) as vectors, compute the
    distance matrix between each pair of vectors.

    Parameters
    ----------
    X: array-like, shape = [n_samples_1, n_features]

    Y: array-like, shape = [n_samples_2, n_features]

    Y_norm_squared: array-like, shape = [n_samples_2], optional
        Pre-computed (Y**2).sum(axis=1)

    squared: boolean, optional
        Return squared Euclidean distances.

    Returns
    -------
    distances: {array, sparse matrix}, shape = [n_samples_1, n_samples_2]

    Examples
    --------
    >>> from scikits.learn.metrics.pairwise import euclidean_distances
    >>> X = [[0, 1], [1, 1]]
    >>> # distance between rows of X
    >>> euclidean_distances(X, X)
    array([[ 0.,  1.],
           [ 1.,  0.]])
    >>> # get distance to origin
    >>> euclidean_distances(X, [[0, 0]])
    array([[ 1.        ],
           [ 1.41421356]])
    """
    # should not need X_norm_squared because if you could precompute that as
    # well as Y, then you should just pre-compute the output and not even
    # call this function.
    if X is Y:
        X = Y = safe_asanyarray(X)
    else:
        X = safe_asanyarray(X)
        Y = safe_asanyarray(Y)

    if X.shape[1] != Y.shape[1]:
        raise ValueError("Incompatible dimension for X and Y matrices")

    if issparse(X):
        XX = X.multiply(X).sum(axis=1)
    else:
        XX = np.sum(X * X, axis=1)[:, np.newaxis]

    if X is Y:  # shortcut in the common case euclidean_distances(X, X)
        YY = XX.T
    elif Y_norm_squared is None:
        if issparse(Y):
            # scipy.sparse matrices don't have element-wise scalar
            # exponentiation, and tocsr has a copy kwarg only on CSR matrices.
            YY = Y.copy() if isinstance(Y, csr_matrix) else Y.tocsr()
            YY.data **= 2
            YY = np.asarray(YY.sum(axis=1)).T
        else:
            YY = np.sum(Y ** 2, axis=1)[np.newaxis, :]
    else:
        YY = atleast2d_or_csr(Y_norm_squared)
        if YY.shape != (1, Y.shape[0]):
            raise ValueError(
                        "Incompatible dimensions for Y and Y_norm_squared")

    # TODO:
    # a faster cython implementation would do the dot product first,
    # and then add XX, add YY, and do the clipping of negative values in
    # a single pass over the output matrix.
    distances = XX + YY  # Using broadcasting
    distances -= 2 * safe_sparse_dot(X, Y.T)
    distances = np.maximum(distances, 0)
    return distances if squared else np.sqrt(distances)

euclidian_distances = euclidean_distances  # both spelling for backward compat

def l1_distances(X, Y):
    """
    Computes the componentwise L1 pairwise-distances between the vectors
    in X and Y.

    Parameters
    ----------

    X: array_like
        An array with shape (n_samples_X, n_features)

    Y: array_like, optional
        An array with shape (n_samples_Y, n_features).

    Returns
    -------

    D: array with shape (n_samples_X * n_samples_Y, n_features)
        The array of componentwise L1 pairwise-distances.

    Examples
    --------

    >>> l1_distances(3, 3)
    array([[0]])
    >>> l1_distances(3, 2)
    array([[1]])
    >>> l1_distances(2, 3)
    array([[1]])
    >>> import numpy as np
    >>> X = np.ones((1, 2))
    >>> y = 2*np.ones((2, 2))
    >>> l1_distances(X, y)
    array([[ 1.,  1.],
           [ 1.,  1.]])
    """
    X, Y = np.atleast_2d(X), np.atleast_2d(Y)
    n_samples_X, n_features_X = X.shape
    n_samples_Y, n_features_Y = Y.shape
    if n_features_X != n_features_Y:
        raise Exception("X and Y should have the same number of features!")
    else:
        n_features = n_features_X
    D = np.abs(X[:, np.newaxis, :] - Y[np.newaxis, :, :])
    D = D.reshape((n_samples_X * n_samples_Y, n_features))

    return D



################################################################################
# Kernels

def linear_kernel(X, Y):
    """
    Compute the linear kernel between X and Y.

    Parameters
    ----------
    X: array of shape (n_samples_1, n_features)

    Y: array of shape (n_samples_2, n_features)

    Returns
    -------
    Gram matrix: array of shape (n_samples_1, n_samples_2)
    """
    return np.dot(X, Y.T)


def polynomial_kernel(X, Y, degree=3, gamma=0, coef0=1):
    """
    Compute the polynomial kernel between X and Y.

    K(X, Y) = (gamma <X, Y> + coef0)^degree

    Parameters
    ----------
    X: array of shape (n_samples_1, n_features)

    Y: array of shape (n_samples_2, n_features)

    degree: int

    Returns
    -------
    Gram matrix: array of shape (n_samples_1, n_samples_2)
    """
    if gamma == 0:
        gamma = 1.0 / X.shape[1]

    K = linear_kernel(X, Y)
    K *= gamma
    K += coef0
    K **= degree
    return K


def sigmoid_kernel(X, Y, gamma=0, coef0=1):
    """
    Compute the sigmoid kernel between X and Y.

    K(X, Y) = tanh(gamma <X, Y> + coef0)

    Parameters
    ----------
    X: array of shape (n_samples_1, n_features)

    Y: array of shape (n_samples_2, n_features)

    degree: int

    Returns
    -------
    Gram matrix: array of shape (n_samples_1, n_samples_2)
    """
    if gamma == 0:
        gamma = 1.0 / X.shape[1]

    K = linear_kernel(X, Y)
    K *= gamma
    K += coef0
    np.tanh(K, K)   # compute tanh in-place
    return K


def rbf_kernel(X, Y, gamma=0):
    """
    Compute the rbf (gaussian) kernel between X and Y.

    K(X, Y) = exp(-gamma ||X-Y||^2)

    Parameters
    ----------
    X: array of shape (n_samples_1, n_features)

    Y: array of shape (n_samples_2, n_features)

    gamma: float

    Returns
    -------
    Gram matrix: array of shape (n_samples_1, n_samples_2)
    """
    if gamma == 0:
        gamma = 1.0 / X.shape[1]

    K = euclidean_distances(X, Y, squared=True)
    K *= -gamma
    np.exp(K, K)    # exponentiate K in-place
    return K


def cosine_similarity(X, Y, copy=True):
    """Compute pairwise cosine similarities between rows in X and Y

    Cosine similarity is a normalized linear kernel with value ranging
      - -1: similar vectors with opposite signs
      - 0: completely dissimilar (orthogonal) vectors
      - 1: similar vectors (same sign)

    In practice, cosine similarity is often used to measure the
    relatedness of text documents represented by sparse vectors of word
    counts, frequencies or TF-IDF weights. In this cases all features
    are non negative and the similarities range from 0 to 1 instead.

    Cosine similarity can be used as an affinity matrix for spectral
    and power iteration clustering algorithms.

    Parameters
    ----------

    X: array or sparse matrix of shape (n_samples_1, n_features)

    Y: array or sparse matrix of shape (n_samples_2, n_features)

    copy: boolean, optional, True by default
        For memory efficiency, set to False to avoid copies of X and Y and
        accept them to be modified (inplace row normalization).

    Returns
    -------

    array or sparse matrix of shape (n_samples_1, n_samples_2)

    Examples
    --------

    >>> from scikits.learn.metrics.pairwise import cosine_similarity
    >>> X = np.asarray([[0, 1], [1, 1], [0, -1], [0, 0]], dtype=np.float64)
    >>> cosine_similarity(X, X).round(decimals=2)
    array([[ 1.  ,  0.71, -1.  ,  0.  ],
           [ 0.71,  1.  , -0.71,  0.  ],
           [-1.  , -0.71,  1.  ,  0.  ],
           [ 0.  ,  0.  ,  0.  ,  0.  ]])

    >>> from scipy.sparse import csr_matrix
    >>> X_sparse = csr_matrix(X)
    >>> cosine_similarity(X_sparse, X_sparse).toarray().round(decimals=2)
    array([[ 1.  ,  0.71, -1.  ,  0.  ],
           [ 0.71,  1.  , -0.71,  0.  ],
           [-1.  , -0.71,  1.  ,  0.  ],
           [ 0.  ,  0.  ,  0.  ,  0.  ]])

    It is possible to use the cosine similarity to perform similarity
    queries:

    >>> query = [[0.5, 0.9]]
    >>> cosine_similarity(X, query)
    array([[ 0.87415728],
           [ 0.96152395],
           [-0.87415728],
           [ 0.        ]])
    """
    if not hasattr(X, 'todense'):
        X = np.asanyarray(X)
    if not hasattr(Y, 'todense'):
        Y = np.asanyarray(Y)

    if copy:
        X, Y = X.copy(), Y.copy()

    inplace_row_normalize(X, norm=2)
    inplace_row_normalize(Y, norm=2)
    return safe_sparse_dot(X, Y.T)
