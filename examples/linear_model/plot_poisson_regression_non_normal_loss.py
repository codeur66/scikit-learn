"""
======================================
Poisson regression and non-normal loss
======================================

This example illustrates the use of linear Poisson regression
on the French Motor Third-Party Liability Claims dataset [1] and compares
it with models learned with least squared error. The goal is to predict the
number of insurance claims (or frequency) following car accidents for a user
given historical data over a population of users.

We start by defining a few helper functions for loading the data and
visualizing results.


.. [1]  A. Noll, R. Salzmann and M.V. Wuthrich, Case Study: French Motor
    Third-Party Liability Claims (November 8, 2018).
    `doi:10.2139/ssrn.3164764 <http://dx.doi.org/10.2139/ssrn.3164764>`_

"""
print(__doc__)

# Authors: Christian Lorentzen <lorentzen.ch@gmail.com>
#          Roman Yurchak <rth.yurchak@gmail.com>
# License: BSD 3 clause
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from sklearn.datasets import fetch_openml
from sklearn.dummy import DummyRegressor
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import PoissonRegressor, LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder
from sklearn.preprocessing import OrdinalEncoder
from sklearn.preprocessing import StandardScaler, KBinsDiscretizer
from sklearn.ensemble import GradientBoostingRegressor

from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.metrics import mean_poisson_deviance


def load_mtpl2(n_samples=100000):
    """Fetcher for French Motor Third-Party Liability Claims dataset

    Parameters
    ----------
    n_samples: int, default=100000
      number of samples to select (for faster run time).
    """

    # freMTPL2freq dataset from https://www.openml.org/d/41214
    df_freq = fetch_openml(data_id=41214, as_frame=True)['data']
    df_freq['IDpol'] = df_freq['IDpol'].astype(np.int)
    df_freq.set_index('IDpol', inplace=True)

    # freMTPL2sev dataset from https://www.openml.org/d/41215
    df_sev = fetch_openml(data_id=41215, as_frame=True)['data']

    # sum ClaimAmount over identical IDs
    df_sev = df_sev.groupby('IDpol').sum()

    df = df_freq.join(df_sev, how="left")
    df["ClaimAmount"].fillna(0, inplace=True)

    # unquote string fields
    for column_name in df.columns[df.dtypes.values == np.object]:
        df[column_name] = df[column_name].str.strip("'")
    return df.iloc[:n_samples]


##############################################################################
#
# 1. Loading datasets and pre-processing
# --------------------------------------
#
# We construct the freMTPL2 dataset by joining the  freMTPL2freq table,
# containing the number of claims (``ClaimNb``) with the freMTPL2sev table
# containing the claim amount (``ClaimAmount``) for the same user ids.

df = load_mtpl2(n_samples=50000)

# Note: filter out claims with zero amount, as the severity model
# requires a strictly positive target values.
df.loc[(df.ClaimAmount == 0) & (df.ClaimNb >= 1), "ClaimNb"] = 0

# correct for unreasonable observations (that might be data error)
df["ClaimNb"] = df["ClaimNb"].clip(upper=4)
df["Exposure"] = df["Exposure"].clip(upper=1)

column_trans = ColumnTransformer(
    [
        ("Veh_Driv_Age", KBinsDiscretizer(n_bins=10), ["VehAge", "DrivAge"]),
        (
            "Veh_Brand_Gas_Region",
            OneHotEncoder(),
            ["VehBrand", "VehPower", "VehGas", "Region", "Area"],
        ),
        ("BonusMalus", "passthrough", ["BonusMalus"]),
        (
            "Density_log",
            make_pipeline(
                FunctionTransformer(np.log, validate=False), StandardScaler()
            ),
            ["Density"],
        ),
    ],
    remainder="drop",
)
X = column_trans.fit_transform(df)

##############################################################################
#
# The number of claims (``ClaimNb``) is a positive integer that can be modeled
# as a Poisson distribution. It is then assumed to be the number of discrete
# events occurring with a constant rate in a given time interval
# (``Exposure``). Here we model the frequency ``y = ClaimNb / Exposure``,
# which is still a (scaled) Poisson distribution, and use ``Exposure`` as
# `sample_weight`.

df["Frequency"] = df.ClaimNb / df.Exposure

print(
   pd.cut(df.Frequency, [-1e-6, 1e-6, 1, 2, 3, 4, 5]).value_counts()
)

##############################################################################
#
# It worth noting that 96 % of users have 0 claims, and if we were to convert
# this problem into a binary classification task, it would be significantly
# imbalanced.
#
# To evaluate the pertinence of the used metrics, we will consider as a
# baseline an estimator that returns 0 for any input.

df_train, df_test = train_test_split(df, random_state=0)

dummy = make_pipeline(
    column_trans,
    DummyRegressor(strategy='constant', constant=0)
)
dummy.fit(df_train, df_train.Frequency,
          dummyregressor__sample_weight=df_train.Exposure)

##############################################################################
#
# The Poisson deviance cannot be computed on negative values predicted by the
# model, so we set the minimum predicted value to eps,


def score_estimator(estimator, df_test, eps=1e-5):
    """Score an estimatr on the test set"""

    print("MSE: %.3f" % mean_squared_error(
              df_test.Frequency.values, estimator.predict(df_test),
              df_test.Exposure.values))
    print("MAE: %.3f" % mean_absolute_error(
              df_test.Frequency.values, estimator.predict(df_test),
              df_test.Exposure.values))

    print("mean Poisson deviance: %.3f" % mean_poisson_deviance(
            df_test.Frequency.values, np.fmax(estimator.predict(df_test), eps),
            df_test.Exposure.values))


print("DummyRegressor")
score_estimator(dummy, df_test)

##############################################################################
#
# We start by modeling the target variable with the least squares linear
# regression model,

linregr = make_pipeline(column_trans, LinearRegression())
linregr.fit(df_train, df_train.Frequency,
            linearregression__sample_weight=df_train.Exposure)


print('Number Negatives: %s / total: %s' % (
      (linregr.predict(df_train) < 0).sum(),
      df_train.shape[0]))

print("LinearRegression")
score_estimator(linregr, df_test)

##############################################################################
#
# Next we fit the Poisson regressor on the target variable,

glm_freq = make_pipeline(
    column_trans,
    PoissonRegressor(alpha=0, max_iter=1000)
)
glm_freq.fit(df_train, df_train.Frequency,
             poissonregressor__sample_weight=df_train.Exposure)

print("PoissonRegressor")
score_estimator(glm_freq, df_test)

##############################################################################
#
# Finally we will consider a non linear model  with Gradient boosting that
# still minimizes the least square error. Gradient Boostring Decision Trees do
# not require for categorical data to be one hot encoded, therefore here we use
# a simpler pre-processing pipeline without ``KBinsDiscretizer`` and with
# ``OrdinalEncoder`` instead of ``OneHotEncoder``.


gbr = make_pipeline(
    ColumnTransformer(
        [
            (
                "Veh_Brand_Gas_Region",
                OrdinalEncoder(),
                ["VehBrand", "VehPower", "VehGas", "Region", "Area"],
            ),
            ("Continious", "passthrough", ["VehAge", "DrivAge", "BonusMalus"]),
            ("Density_log", make_pipeline(
                FunctionTransformer(np.log, validate=False), StandardScaler()),
                ["Density"]),
        ],
        remainder="drop",
    ),
    GradientBoostingRegressor()
)
gbr.fit(df_train, df_train.Frequency.values,
        gradientboostingregressor__sample_weight=df_train.Exposure.values)


print("GradientBoostingRegressor")
score_estimator(gbr, df_test)

##############################################################################
#
# In this example, although Gradient boosting minimizes the least square error,
# because of a higher predictive power it also results in a smaller Poisson
# deviance than the Poisson regression model.
#
# Evaluating models with a single train / test split is prone to numerical
# errors, we can verify that we would also get equivalent resuts with the
# cross-validation score.
#
# The difference between these models can also be visualized by comparing the
# histogram of observed target values with that of predicted values,


fig, axes = plt.subplots(1, 4, figsize=(16, 3))
fig.subplots_adjust(bottom=0.2)

df_train.Frequency.hist(bins=np.linspace(-1, 10, 50), ax=axes[0])

axes[0].set_title('Experimental data')

for idx, model in enumerate([linregr, glm_freq, gbr]):
    y_pred = model.predict(df_train)

    pd.Series(y_pred).hist(bins=np.linspace(-1, 8, 50), ax=axes[idx+1])
    axes[idx + 1].set_title(model.__class__.__name__)

for axi in axes:
    axi.set(
        yscale='log',
        xlabel="y (Frequency)"
    )

##############################################################################
#
# The experimental data presents a long tail distribution for ``y``. In all
# models we predict the mean expected value, so we will have necessairily fewer
# extreme values. Additionally normal distribution used in ``Ridge`` and
# ``GradientBoostingRegressor`` has a constant variance, while for the Poisson
# distribution used in ``PoissonRegressor``, the variance is proportional to
# the mean predicted value.
#
# Thus, among the considered estimators,
# ``PoissonRegressor`` and ``GradientBoostingRegressor`` are better suited for
# modeling the long tail distribution of the data as compared to the ``Ridge``
# estimator.
