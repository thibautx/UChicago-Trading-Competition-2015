from sklearn.svm import SVC
import numpy as np

kernel = 'rbf'
nfolds = 5
gamma = 0.05
gamma_skew = 1
alpha = 2
beta = 5
do_weights = False
class_weights = {
    -1: 1,
    0: 1,
    1: 1
}

print kernel
print gamma
print gamma_skew
print beta
print do_weights

training_file = open("training_file_1.0-2.0-0.9-0.04-0.0-0.9-5-3-3-0.0-100.txt", 'r')

data = []
scores = []
fpositives = []
fneutrals = []
fnegatives = []
positives = []
neutrals = []
negatives = []

for line in training_file:
    l = map(float, line.split(","))
    l = l[10-beta:]
    data.append(l)

labels = zip(*data)[-1]

if do_weights:
    pos_count = np.sum(map(lambda x: 1 if x > gamma else 0, labels))
    neg_count = np.sum(map(lambda x: 1 if x < -gamma else 0, labels))
    neu_count = len(labels) - pos_count - neg_count

    class_weights[-1] = float(len(labels)) / pos_count
    class_weights[0] = float(len(labels)) / neu_count
    class_weights[1] = float(len(labels)) / neg_count

print class_weights[-1]
print class_weights[0]
print class_weights[1]

k = len(data) / nfolds


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


mapY = lambda z: 1 if z > gamma else -1 if z < -gamma_skew*gamma else 0


for c in xrange(0, nfolds):
    training_data = data[0:k*c] + data[k*(c+1):]
    test_data = data[k*c:k*(c+1)]

    classifier = SVC(kernel=kernel, class_weight=class_weights)

    X, y = zip(*zip(*training_data)[:-1]), zip(*training_data)[-1]

    #X = map(lambda x: np.concatenate([x, [np.average(x)]]), X)

    Y = map(mapY, y)

    classifier.fit(X, Y)

    testX, testy = zip(*zip(*test_data)[:-1]), zip(*test_data)[-1]

    #testX = map(lambda x: np.concatenate([x, [np.average(x)]]), testX)

    testY = map(mapY, testy)

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
    #correct_sign = 0

    for i, x in enumerate(testX):
        y1 = classifier.predict(x)
        y2 = testY[i]
        if y1 == y2:
            correct += 1
            if y1 == -1:
                _negatives += 1
            elif y1 == 0:
                _neutrals += 1
            elif y1 == 1:
                _positives += 1
        elif y1 == -1:
            false_negatives += 1
        elif y1 == 0:
            false_neutrals += 1
        elif y1 == 1:
            false_positives += 1

    scores.append(correct / float(len(testY)))
    fpositives.append(false_positives / float(len(testY)))
    fneutrals.append(false_neutrals / float(len(testY)))
    fnegatives.append(false_negatives / float(len(testY)))
    positives.append(_positives)
    neutrals.append(_neutrals)
    negatives.append(_negatives)
    #sign_scores.append(correct_sign / float(len(testY)))
    print scores[-1]

print np.average(scores)
print np.average(fpositives)
print np.average(fneutrals)
print np.average(fnegatives)
print np.average(positives)
print np.average(neutrals)
print np.average(negatives)
#print np.average(sign_scores)


training_file.close()