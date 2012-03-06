"""Build a sentiment analysis / polarity model

Sentiment analysis can be casted as a binary text classification problem,
that is fitting a linear classifier on features extracted from the text
of the user messages so as to guess wether the opinion of the author is
positive or negative.

In this examples we will use a movie review dataset.

"""
# Author: Olivier Grisel <olivier.grisel@ensta.org>
# License: Simplified BSD

import sys
import numpy as np

from sklearn.feature_extraction.text import Vectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.grid_search import GridSearchCV
from sklearn.datasets import load_files
from sklearn.cross_validation import train_test_split
from sklearn import metrics

#
# The real code starts here
#

if __name__ == "__main__":
    # NOTE: we put the following in a 'if __name__ == "__main__"' protected
    # block to be able to use a multi-core grid search that also works under
    # Windows, see: http://docs.python.org/library/multiprocessing.html#windows
    # The multiprocessing module is used as the backend of joblib.Parallel
    # that is used when n_jobs != 1 in GridSearchCV

    # the training data folder must be passed as first argument
    movie_reviews_data_folder = sys.argv[1]
    dataset = load_files(movie_reviews_data_folder, shuffle=False)
    print "n_samples: %d" % len(dataset.data)

    # split the dataset in training and test set:
    docs_train, docs_test, y_train, y_test = train_test_split(
        dataset.data, dataset.target, test_fraction=0.25, random_state=None)

    # TASK: Build a vectorizer / classifier pipeline using the previous
    # analyzer
    pipeline = Pipeline([
        ('vect', Vectorizer(max_features=100000, max_df=0.9)),
        ('clf', LinearSVC()),
    ])

    # TASK: Define a parameters grid for searching whether extracting bi-grams
    # is suited for this task, and which value of C in 1000 or 10000 is the
    # best for LinearSVC on this dataset.
    parameters = {
        'vect__max_n': (1, 2),
        'clf__C': (1000, 10000),
    }

    # TASK: Build a grid search to find out whether unigrams or bigrams are
    # more useful.
    # Fit the pipeline on the training set using grid search for the parameters
    # To make this run faster, fit it only on the top first 200 documents of
    # the training set.
    print "Performing grid search for parameters: ", parameters
    grid_search = GridSearchCV(pipeline, parameters, n_jobs=-1, verbose=2)
    grid_search.fit(docs_train[:200], y_train[:200])

    print
    print "Scores: "
    print
    for params, mean_score, scores in grid_search.grid_scores_:
        print "%0.3f (+/- %0.3f) for %r" % (
            mean_score, scores.std() / 2, params)
    print

    clf = grid_search.best_estimator_

    # TASK: Refit the best estimator on the complete training set
    print
    print "Fitting on the full dataset:"
    print
    clf.fit(docs_train, y_train)

    # TASK: (Optional) Display the most discriminative features
    feature_names = clf.named_steps['vect'].get_feature_names()
    sorted_indices = clf.named_steps['clf'].coef_[0].argsort()
    sorted_features = np.array(feature_names)[sorted_indices]
    print "Most negative words:"
    for word in sorted_features[:10]:
        print ' -', word
    print
    print "Most positive words:"
    for word in sorted_features[:-10:-1]:
        print ' -', word
    print

    # Predict the outcome on the testing set
    y_predicted = clf.predict(docs_test)

    # Print the classification report
    print metrics.classification_report(y_test, y_predicted,
                                        target_names=dataset.target_names)

    # Plot the confusion matrix
    cm = metrics.confusion_matrix(y_test, y_predicted)
    print cm


    #import pylab as pl
    #pl.matshow(cm)
    #pl.show()
