#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
=============================================================
Compare the effect of different scalers on data with outliers
=============================================================

The feature 0 and feature 5 of California housing dataset are outside of the
typical range [0, 1] and contain large outliers. These two characteristics lead
to difficulties to visualize the data and, more importantly, they can degrade
the fitting procedure of most of machine learning algorithms.

Indeed many estimators assume that each feature takes values spread around or
close to zero and more importantly that all features vary on comparable
scales. In particular metric-based and gradient-based estimators often assume
approximately standardized data (centered features with unit variances). A
notable exception are decision tree-based estimators that are robust to
arbitrary scaling of the data.

This example uses different scalers, transformers and normalizers to bring the
data within a pre-defined range.

Scalers are linear (or more exactly affine) transformations and differ from
each other in the way to estimate the parameters used to shift and scale each
feature. ``QuantileTransformer`` provides a non-linear transformation in which
distances between marginal outliers and inliers are shrunk. Unlike the
previous transformations, normalization refers to a per sample transformation
instead of a per feature transformation.

"""

# Author:  Raghav RV <rvraghav93@gmail.com>
#          Guillaume Lemaitre <g.lemaitre58@gmail.com>
#          Thomas Unterthiner
# License: BSD 3 clause

from __future__ import print_function

from collections import OrderedDict

import numpy as np

import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib import cm

from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import minmax_scale
from sklearn.preprocessing import MaxAbsScaler
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import RobustScaler
from sklearn.preprocessing import Normalizer
from sklearn.preprocessing.data import QuantileTransformer

from sklearn.datasets import fetch_california_housing

print(__doc__)

dataset = fetch_california_housing()
X_full, y_full = dataset.data, dataset.target

# Take only 2 features to make visualization easier
# Feature of 0 has a long tail distribution.
# Feature 5 has a few but very large outliers.

X = X_full[:, [0, 5]]

distributions = OrderedDict((
    ('Unscaled data', X),
    ('Data after standard scaling',
        StandardScaler().fit_transform(X)),
    ('Data after robust scaling',
        RobustScaler(quantile_range=(25, 75)).fit_transform(X)),
    ('Data after min-max scaling',
        MinMaxScaler().fit_transform(X)),
    ('Data after max-abs scaling',
        MaxAbsScaler().fit_transform(X)),
    ('Data after sample-wise L2 normalizing',
        Normalizer().fit_transform(X)),
    ('Data after quantile transformation (uniform pdf)',
        QuantileTransformer(output_distribution='uniform')
        .fit_transform(X)),
    ('Data after quantile transformation (gaussian pdf)',
        QuantileTransformer(output_distribution='normal')
        .fit_transform(X))))

y = minmax_scale(y_full)  # To make colors corresponding to the target),


def create_axes(figsize=(8, 8)):
    plt.figure(figsize=figsize)

    # define the axis for the first plot
    left, width = 0.1, 0.22
    bottom, height = 0.1, 0.2
    bottom_h = left_h = left + width + 0.02

    rect_scatter = [left, bottom, width, height]
    rect_histx = [left, bottom_h, width, 0.1]
    rect_histy = [left_h, bottom, 0.1, height]

    ax_scatter = plt.axes(rect_scatter)
    ax_histx = plt.axes(rect_histx)
    ax_histy = plt.axes(rect_histy)

    # define the axis for the zoomed-in plot
    left = width + left + 0.2
    left_h = left + width + 0.02

    rect_scatter = [left, bottom, width, height]
    rect_histx = [left, bottom_h, width, 0.1]
    rect_histy = [left_h, bottom, 0.1, height]

    ax_scatter_zoom = plt.axes(rect_scatter)
    ax_histx_zoom = plt.axes(rect_histx)
    ax_histy_zoom = plt.axes(rect_histy)

    # define the axis for the colorbar
    left, width = width + left + 0.13, 0.01

    rect_colorbar = [left, bottom, width, height]
    ax_colorbar = plt.axes(rect_colorbar)

    return ((ax_scatter, ax_histy, ax_histx),
            (ax_scatter_zoom, ax_histy_zoom, ax_histx_zoom),
            ax_colorbar)


def plot_distribution(axes, X, y, hist_nbins=50, title="",
                      X_label="", y_label=""):
    ax, hist_X1, hist_X0 = axes

    ax.set_title(title)
    ax.set_xlabel(X_label)
    ax.set_ylabel(y_label)

    # The scatter plot
    colors = cm.plasma_r(y)
    ax.scatter(X[:, 0], X[:, 1], alpha=0.5, marker='o', s=5, lw=0, c=colors)

    # Removing the top and the right spine for aesthetics
    # make nice axis layout
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    ax.spines['left'].set_position(('outward', 10))
    ax.spines['bottom'].set_position(('outward', 10))

    # Histogram for axis X1 (feature 5)
    hist_X1.set_ylim(ax.get_ylim())
    hist_X1.hist(X[:, 1], bins=hist_nbins, orientation='horizontal',
                 color='grey', ec='grey')
    hist_X1.axis('off')

    # Histogram for axis X0 (feature 0)
    hist_X0.set_xlim(ax.get_xlim())
    hist_X0.hist(X[:, 0], bins=hist_nbins, orientation='vertical',
                 color='grey', ec='grey')
    hist_X0.axis('off')

###############################################################################
# Two plots will be shown for each scaler/normalizer/transformer. The left
# figure will show a scatter plot of the full data set while the right figure
# will exclude the extreme values considering only 99 % of the data set,
# excluding marginal outliers. In addition, the marginal distributions for each
# feature will be shown on the side of the scatter plot.


def make_plot(item_idx):
    title, X = distributions.items()[item_idx]
    ax_zoom_out, ax_zoom_in, ax_colorbar = create_axes()
    axarr = (ax_zoom_out, ax_zoom_in)
    plot_distribution(axarr[0], X, y, hist_nbins=200,
                      title=title + ' including outliers',
                      X_label="Median Income", y_label="Number of households")

    # zoom-in
    zoom_in_percentile_range = (0, 99)
    cutoffs_X0 = np.percentile(X[:, 0], zoom_in_percentile_range)
    cutoffs_X1 = np.percentile(X[:, 1], zoom_in_percentile_range)

    non_outliers_mask = (
        np.all(X > [cutoffs_X0[0], cutoffs_X1[0]], axis=1) &
        np.all(X < [cutoffs_X0[1], cutoffs_X1[1]], axis=1))
    plot_distribution(axarr[1], X[non_outliers_mask], y[non_outliers_mask],
                      hist_nbins=50,
                      title=title + '\nZoomed-in at percentile range (0, 99)',
                      X_label="Median Income", y_label="Number of households")

    norm = mpl.colors.Normalize(y_full.min(), y_full.max())
    mpl.colorbar.ColorbarBase(ax_colorbar, cmap=cm.plasma_r,
                              norm=norm, orientation='vertical',
                              label='Color mapping for values of y')


###############################################################################
# A large majority of the samples in the original data set are compacted to a
# specific range, [0, 6] for the 1st feature and [0, 10] for the second
# feature. However, as shown on the right figure, there is some marginal
# outliers which might alterate the learning procedure of the some machine
# learning algorithms. Therefore, depending of the application, a specific
# pre-processing is beneficial. In the following, we present some insights and
# behaviors of those pre-processing methods, with the presence of marginal
# outliers.

make_plot(0)

###############################################################################
# The ``StandardScaler`` removes the mean and scale the data to a unit
# variance. However, the outliers have an influence when computing the
# empirical mean and standard deviation which shrink the range of the feature
# values as shown in the left figure below.

make_plot(1)

###############################################################################
# Unlike, the ``StandardScaler``, the statistics (i.e. median, 1st and 3rd
# quartiles) computed to scale the data set will not be influenced by marginal
# outliers. Consequently, the range of the feature values is larger than in the
# previous example, as shown in the zoomed-in figure. Note that the outliers
# remain far from the inliers.

make_plot(2)


###############################################################################
# The ``MinMaxScaler`` rescales the data set such that all feature values are
# in the range [0, 1] as shown in the right figure below. However, this scaling
# compress all inliers in the narrow range [0, 0.005].

make_plot(3)

###############################################################################
# The ``MaxAbsScaler`` differs from the previous scaler such that the absolute
# values are mapped in the range [0, 1]. Therefore, in the current example,
# there is no observable difference since the feature values are originally
# positive.

make_plot(4)

###############################################################################
# The ``Normalizer`` rescales each sample will scale to a unit norm. It can be
# seen on both figures below where all samples are mapped to the unit circle.

make_plot(5)

###############################################################################
# The ``QuantileNormalizer`` applies a non-linear transformation such that the
# probability density function of each feature will be mapped to a uniform
# distribution. In this case, all the data will be mapped in the range [0, 1],
# even the outliers which cannot be distinguished anymore from the inliers.

make_plot(6)

###############################################################################
# The ``QuantileNormalizer`` has an additional ``output_distribution``
# parameter allowing to match a Gaussian distribution instead of a normal
# distribution.

make_plot(7)

plt.show()
