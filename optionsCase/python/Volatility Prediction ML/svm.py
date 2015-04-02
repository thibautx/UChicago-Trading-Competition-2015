from sklearn.svm import SVC
from sklearn.ensemble import AdaBoostClassifier
import numpy as np
import numpy.linalg as npla

'''

'''

WRITE_COEFFS = True

if WRITE_COEFFS:
    coefs_file = open("svm-coeffs", 'w')

line_count = 5000
C = 1.0
kernel = 'linear'
nfolds = 5
gamma = 0.00
filter_gamma = 0.00
gamma_skew = 1
alpha = 2
beta = 10
threshold = 0.4
do_weights = True
class_weights = {}

if WRITE_COEFFS:
    nfolds = 1

print kernel
print C
print threshold
print filter_gamma
print beta
print do_weights

training_file = open("training_file_1.0-2.0-0.9-0.04-0.0-0.9-5-3-3-0.0-100.txt", 'r')
#training_file = open("training_file.txt", 'r')

data = []
scores = []
fpositives = []
fneutrals = []
fnegatives = []
positives = []
neutrals = []
negatives = []
fuck_ups = []

for i, line in enumerate(training_file):
    if i > line_count:
        break
    l = map(float, line.split(","))
    l = l[10-beta:]
    data.append(l)

labels = zip(*data)[-1]

if do_weights:
    pos_count = np.sum(map(lambda x: 1 if x >= 0 else 0, labels))
    neg_count = np.sum(map(lambda x: 1 if x < 0 else 0, labels))
    class_weights[-1] = float(len(labels)) / neg_count
    class_weights[1] = float(len(labels)) / pos_count

print class_weights[-1]
print class_weights[1]

data = filter(lambda d: abs(d[-1]) > filter_gamma, data)

k = line_count / nfolds


def mapY(z):
    if z > alpha*gamma:
        return 1
    elif z > gamma:
        return 1
    elif z < -alpha*gamma:
        return -1
    elif z < -gamma:
        return -1
    else:
        return 0


mapY = lambda z: 1 if z >= 0 else -1 if z < 0 else 0
mapTestY = lambda z: 1 if z > gamma else -1 if z < -gamma else 0

for c in xrange(0, nfolds):
    training_data = data[0:k*c] + data[k*(c+1):]
    test_data = data[k*c:k*(c+1)]

    if WRITE_COEFFS:
        training_data = data
        testing_data = data

    classifier = SVC(kernel=kernel, class_weight=class_weights, probability=True)
    #classifier = AdaBoostClassifier(base_estimator=classifier, n_estimators=5, learning_rate=1)

    X, y = zip(*zip(*training_data)[:-1]), zip(*training_data)[-1]

    #X = map(lambda x: np.concatenate([x, [np.average(x)]]), X)

    Y = map(mapY, y)

    classifier.fit(X, Y)

    if WRITE_COEFFS:
        coefs_file.write(str(map(list, classifier.support_vectors_)) + "\n")
        coefs_file.write(str(map(list, classifier.coef_)) + "\n")
        coefs_file.write(str(classifier.intercept_) + "\n")

    testX, testy = zip(*zip(*test_data)[:-1]), zip(*test_data)[-1]

    #testX = map(lambda x: np.concatenate([x, [np.average(x)]]), testX)

    testY = map(mapTestY, testy)

    #accuracy = classifier.score(testX, testY)

    #print accuracy

    #scores.append(accuracy)

    correct = 0
    false_positives = 0
    false_negatives = 0
    false_neutrals = 0
    _positives = 0
    _negatives = 0
    _neutrals = 0
    _fuck_ups = 0
    #correct_sign = 0

    for i, x in enumerate(testX):
        #y1 = classifier.predict(x)
        v1, = classifier.decision_function(x)
        #print v1
        y2 = testY[i]
        if abs(v1) > threshold and np.sign(v1) == np.sign(y2) and np.sign(y2) != np.sign(x[-1]):
            correct += 1
            if np.sign(v1) == -1:
                _negatives += 1
            elif np.sign(v1) == 1:
                _positives += 1
        elif (np.sign(y2) == np.sign(x[-1]) and y2 == 0) or (abs(v1) <= threshold and y2 == 0):
            _neutrals += 1
        elif (np.sign(y2) == np.sign(x[-1])) or (abs(v1) <= threshold):
            false_neutrals += 1
        elif np.sign(v1) == -1 and np.sign(y2) != np.sign(x[-1]):
            false_negatives += 1
        elif np.sign(v1) == 1 and np.sign(y2) != np.sign(x[-1]):
            false_positives += 1
        if np.sign(v1) == -y2 and abs(v1) > threshold and np.sign(y2) != np.sign(x[-1]):
            _fuck_ups += 1

    N = float(len(testY) - false_neutrals - _neutrals)
    scores.append(correct / N)
    fpositives.append(false_positives / N)
    fneutrals.append(false_neutrals / N)
    fnegatives.append(false_negatives / N)
    positives.append(_positives)
    neutrals.append(_neutrals)
    negatives.append(_negatives)
    fuck_ups.append(_fuck_ups)
    #sign_scores.append(correct_sign / float(len(testY)))
    print scores[-1]

print np.average(scores)
print np.average(fpositives)
print np.average(fneutrals)
print np.average(fnegatives)
print np.average(positives)
print np.average(neutrals)
print np.average(negatives)
print np.average(fuck_ups)
#print np.average(sign_scores)


training_file.close()