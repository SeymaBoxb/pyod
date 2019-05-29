# -*- coding: utf-8 -*-
"""Connectivity-Based Outlier Factor (COF) Algorithm
"""
# Author: Yahya Almardeny <almardeny@gmail.com>
# License: BSD 2 clause

from __future__ import division
from __future__ import print_function

from operator import itemgetter

import numpy as np
from scipy.spatial import distance_matrix
from sklearn.utils import check_array

from .base import BaseDetector
from ..utils.utility import check_parameter


class COF(BaseDetector):
    """Connectivity-Based Outlier Factor (COF) COF uses the ratio of average
    chaining distance of data point and the average of average chaining
    distance of k nearest neighbor of the data point, as the outlier score
    for observations.

    See :cite:`tang2002enhancing` for details.

    Parameters
    ----------
    contamination : float in (0., 0.5), optional (default=0.1)
        The amount of contamination of the data set, i.e.
        the proportion of outliers in the data set. Used when fitting to
        define the threshold on the decision function.

    n_neighbors : int, optional (default=20)
        Number of neighbors to use by default for k neighbors queries.
        Note that n_neighbors should be less than the number of samples.
        If n_neighbors is larger than the number of samples provided,
        all samples will be used.

    Attributes
    ----------
    decision_scores_ : numpy array of shape (n_samples,)
        The outlier scores of the training data.
        The higher, the more abnormal. Outliers tend to have higher
        scores. This value is available once the detector is
        fitted.

    threshold_ : float
        The threshold is based on ``contamination``. It is the
        ``n_samples * contamination`` most abnormal samples in
        ``decision_scores_``. The threshold is calculated for generating
        binary outlier labels.

    labels_ : int, either 0 or 1
        The binary labels of the training data. 0 stands for inliers
        and 1 for outliers/anomalies. It is generated by applying
        ``threshold_`` on ``decision_scores_``.

    n_neighbors_: int
        Number of neighbors to use by default for k neighbors queries.
    """

    def __init__(self, contamination=0.1, n_neighbors=20):
        super(COF, self).__init__(contamination=contamination)
        if isinstance(n_neighbors, int):
            check_parameter(n_neighbors, low=1, param_name='n_neighbors')
        else:
            raise TypeError(
                "n_neighbors should be int. Got %s" % type(n_neighbors))
        self.n_neighbors_ = n_neighbors
        self.decision_scores_ = None

    def fit(self, X, y=None):
        """Fit detector. y is optional for unsupervised methods.

        Parameters
        ----------
        X : numpy array of shape (n_samples, n_features)
            The input samples.

        y : numpy array of shape (n_samples,), optional (default=None)
            The ground truth of the input samples (labels).
        """
        X = check_array(X)
        if self.n_neighbors_ >= X.shape[0]:
            self.n_neighbors_ = X.shape[0] - 1
        self._set_n_classes(y)
        self.decision_scores_ = self.decision_function(X)
        self._process_decision_scores()

        return self

    def decision_function(self, X):
        """Predict raw anomaly score of X using the fitted detector.
        The anomaly score of an input sample is computed based on different
        detector algorithms. For consistency, outliers are assigned with
        larger anomaly scores.

        Parameters
        ----------
        X : numpy array of shape (n_samples, n_features)
            The training input samples. Sparse matrices are accepted only
            if they are supported by the base estimator.

        Returns
        -------
        anomaly_scores : numpy array of shape (n_samples,)
            The anomaly score of the input samples.
        """
        return self._cof(X)

    def _cof(self, X):
        """
        Connectivity-Based Outlier Factor (COF) Algorithm
        This function is called internally to calculate the
        Connectivity-Based Outlier Factor (COF) as an outlier
        score for observations.
        :return: numpy array containing COF scores for observations.
                 The greater the COF, the greater the outlierness.
        """
        dist_matrix = np.array(distance_matrix(X, X))
        sbn_path_index, ac_dist, cof_ = [], [], []
        for i in range(X.shape[0]):
            sbn_path = sorted(range(len(dist_matrix[i])),
                              key=dist_matrix[i].__getitem__)
            sbn_path_index.append(sbn_path[1: self.n_neighbors_ + 1])
            cost_desc = []
            for j in range(self.n_neighbors_):
                cost_desc.append(
                    np.min(dist_matrix[sbn_path[j + 1]][sbn_path][:j + 1]))
            acd = []
            for _h, cost_ in enumerate(cost_desc):
                neighbor_add1 = self.n_neighbors_ + 1
                acd.append(((2. * (neighbor_add1 - (_h + 1))) / (
                        neighbor_add1 * self.n_neighbors_)) * cost_)
            ac_dist.append(np.sum(acd))
        for _g in range(X.shape[0]):
            cof_.append((ac_dist[_g] * self.n_neighbors_) /
                        np.sum(itemgetter(*sbn_path_index[_g])(ac_dist)))
        return np.nan_to_num(cof_)
