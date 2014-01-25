"""
Testing for the gradient boosting loss functions and initial estimators.
"""

import numpy as np
from numpy.testing import assert_array_equal
from numpy.testing import assert_almost_equal
from numpy.testing import assert_equal

from nose.tools import assert_raises


from sklearn.ensemble.gradient_boosting import BinomialDeviance
from sklearn.ensemble.gradient_boosting import LogOddsEstimator
from sklearn.ensemble.gradient_boosting import NormalizedDiscountedCumulativeGain


def test_binomial_deviance():
    """Check binomial deviance loss.

    Check against alternative definitions in ESLII.
    """
    bd = BinomialDeviance(2)

    # pred has the same BD for y in {0, 1}
    assert_equal(bd(np.array([0.0]), np.array([0.0])),
                 bd(np.array([1.0]), np.array([0.0])))

    assert_almost_equal(bd(np.array([1.0, 1.0, 1.0]),
                           np.array([100.0, 100.0, 100.0])),
                        0.0)
    assert_almost_equal(bd(np.array([1.0, 0.0, 0.0]),
                           np.array([100.0, -100.0, -100.0])), 0)

    # check if same results as alternative definition of deviance (from ESLII)
    alt_dev = lambda y, pred: np.mean(np.logaddexp(0.0, -2.0 *
                                                   (2.0 * y - 1) * pred))
    test_data = [(np.array([1.0, 1.0, 1.0]), np.array([100.0, 100.0, 100.0])),
                 (np.array([0.0, 0.0, 0.0]), np.array([100.0, 100.0, 100.0])),
                 (np.array([0.0, 0.0, 0.0]),
                  np.array([-100.0, -100.0, -100.0])),
                 (np.array([1.0, 1.0, 1.0]),
                  np.array([-100.0, -100.0, -100.0]))]

    for datum in test_data:
        assert_almost_equal(bd(*datum), alt_dev(*datum))

    # check the gradient against the
    alt_ng = lambda y, pred: (2 * y - 1) / (1 + np.exp(2 * (2 * y - 1) * pred))
    for datum in test_data:
        assert_almost_equal(bd.negative_gradient(*datum), alt_ng(*datum))


def test_log_odds_estimator():
    """Check log odds estimator. """
    est = LogOddsEstimator()
    assert_raises(ValueError, est.fit, None, np.array([1]))

    est.fit(None, np.array([1.0, 0.0]))
    assert_equal(est.prior, 0.0)
    assert_array_equal(est.predict(np.array([[1.0], [1.0]])),
                       np.array([[0.0], [0.0]]))


def test_ndcg():
    ndcg = NormalizedDiscountedCumulativeGain(n_classes=1)

    # test all zeros, 64 bit
    y = np.zeros(5, dtype=np.int64)
    pred = np.ones((5, 1))
    assert(np.isnan(ndcg(y, pred)))

    # test all ones, 64 bit
    y = np.ones(5, dtype=np.int64)
    pred = np.ones((5, 1))
    assert(ndcg(y, pred) == 1)

    # test all zeros, 32 bit
    y = np.zeros(5, dtype=np.int32)
    pred = np.ones((5, 1))
    assert(np.isnan(ndcg(y, pred)))

    # test all ones, 32 bit
    y = np.ones(5, dtype=np.int32)
    pred = np.ones((5, 1))
    assert(ndcg(y, pred) == 1)

    # nontrivial ndcg
    y = np.asarray([3, 4, 5, 0, 1, 2], dtype=np.int32)
    pred = np.asarray(range(6)[::-1])[:, None]
    assert_almost_equal(ndcg(y, pred), 0.88814767)

    # two queries
    y = np.r_[y, y]
    pred = np.asarray(range(12)[::-1])[:, None]
    query = np.r_[np.zeros(6), np.ones(6)]
    assert_almost_equal(ndcg(y, pred, query), 0.88814767)
