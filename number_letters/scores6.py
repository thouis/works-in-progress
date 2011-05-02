from itertools import permutations
import numpy as np

points = {'LTN' : 1,
          'RDS' : 2,
          'GBM' : 3,
          'CHP' : 4,
          'FWV' : 5,
          'YKJ' : 6,
          'QXZ' : 7}

# from Keith Randall
S ={'L':1,'T':1,'N':1,
    'R':2,'D':2,'S':2,
    'G':3,'B':3,'M':3,
    'C':4,'H':4,'P':4,
    'F':5,'W':5,'V':5,
    'Y':6,'K':6,'J':6,
    'Q':7,'X':7,'Z':7,
    }

def best_possible_score(w):
    # ordered list of (per-letter-score, count, letter) for all non-AEIOU
    letter_info = np.array(list(reversed(sorted([(S[c], w.count(c)) for c in S]))))
    return (letter_info.prod(axis=1)[::3].sum() - 2 * letter_info[1::3, 1].sum() - 2 * letter_info[2::3, 1].sum())

def tonum(word):
    word_array = np.zeros(26, dtype=np.int)
    for l in word:
        word_array[ord(l) - ord('A')] += 1
    return word_array.reshape((26, 1))

def to_score_array(letters):
    score_array = np.zeros(26, dtype=np.int) - 2
    for v in 'AEIOU':
        score_array[ord(v) - ord('A')] = 0
    for idx, l in enumerate(letters):
        score_array[ord(l) - ord('A')] = idx + 1
    return np.matrix(score_array.reshape(1, 26))

def find_best_words():
    wlist = [l.strip().upper() for l in open('/usr/share/dict/words') if l[0].lower() == l[0]]
    wlist = [l for l in wlist if len(l) > 4]
    orig = [l for l in wlist]
    for rep in 'AEIOU':
        wlist = [l.replace(rep, '') for l in wlist]
    best_possible_scores = [best_possible_score(w) for w in wlist]
    best_possible_scores, wlist, orig = zip(*reversed(sorted(zip(best_possible_scores, wlist, orig))))
    wlist = np.hstack([tonum(w) for w in wlist])

    best_possible_scores = np.array(best_possible_scores)
    neg_best_possible_scores = - best_possible_scores
    score_at_least = np.zeros(best_possible_scores[0] + 1, np.int)
    score_at_least[0] = -1
    for minscore in range(best_possible_scores[0]):
        score_at_least[minscore] = np.searchsorted(neg_best_possible_scores, -minscore, 'right')


    # test
    testpt = score_at_least[10]
    print orig[testpt-3:testpt+2]
    print best_possible_scores[testpt-3:testpt+2]
    print orig[testpt]

    best = 0
    ct = 0
    bestwords = ()
    # we perform all iterations so that scores1 is guaranteed at some point to be the highest scoring word
    for c1 in permutations('LTN'):
        for c2 in permutations('RDS'):
            for c3 in permutations('GBM'):
                for c4 in permutations('CHP'):
                    min_score_w1 = (best) / 3
                    print ct, 6**7, score_at_least[min_score_w1], wlist.shape[1]
                    for c5 in permutations('FWV'):
                        for c6 in permutations('YJK'):
                            for c7 in permutations('QZX'):
                                vals = [to_score_array(''.join(s)) for s in zip(c1, c2, c3, c4, c5, c6, c7)]
                                ct += 1
                                min_score_w1 = (best + 2) / 3
                                scores1 = (vals[0] * wlist[:, :score_at_least[min_score_w1]]).A.flatten()
                                m1 = max(scores1)
                                if m1 < min_score_w1:
                                    continue
                                min_score_w2 = max((best - m1 + 1) / 2, 0)
                                if min_score_w2 > best_possible_scores[0]:
                                    continue
                                scores2 = (vals[1] * wlist[:, :score_at_least[min_score_w2]]).A.flatten()
                                m2 = max(scores2)
                                if m2 < min_score_w2:
                                    continue
                                min_score_w3 = max((best - m1 - m2 + 1), 0)
                                if min_score_w3 > best_possible_scores[0]:
                                    continue
                                scores3 = (vals[2] * wlist[:, :score_at_least[min_score_w3]]).A.flatten()
                                m3 = max(scores3)
                                if m1 + m2 + m3 > best:
                                    print orig[scores1.argmax()], orig[scores2.argmax()], orig[scores3.argmax()], m1 + m2 + m3
                                    best = m1 + m2 + m3
                                    bestwords = (orig[scores1.argmax()], orig[scores2.argmax()], orig[scores3.argmax()])
    return bestwords, best


if __name__ == '__main__':
    import timeit
    print timeit.timeit('print find_best_words()', 'from __main__ import find_best_words', number=1)
