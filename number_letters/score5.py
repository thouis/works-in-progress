from itertools import permutations
import numpy as np

points = {'LTN' : 1,
          'RDS' : 2,
          'GBM' : 3,
          'CHP' : 4,
          'FWV' : 5,
          'YKJ' : 6,
          'QXZ' : 7}

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
    wlist = np.hstack([tonum(w) for w in wlist])

    best = 0
    ct = 0
    bestwords = ()
    for c1 in ['LTN']:
        for c2 in permutations('RDS'):
            for c3 in permutations('GBM'):
                for c4 in permutations('CHP'):
                    for c5 in permutations('FWV'):
                        for c6 in permutations('YJK'):
                            for c7 in permutations('QZX'):
                                vals = [to_score_array(''.join(s)) for s in zip(c1, c2, c3, c4, c5, c6, c7)]
                                ct += 1
                                print ct, 6**6
                                scores1 = (vals[0] * wlist).A.flatten()
                                scores2 = (vals[1] * wlist).A.flatten()
                                scores3 = (vals[2] * wlist).A.flatten()
                                m1 = max(scores1)
                                m2 = max(scores2)
                                m3 = max(scores3)
                                if m1 + m2 + m3 > best:
                                    print orig[scores1.argmax()], orig[scores2.argmax()], orig[scores3.argmax()], m1 + m2 + m3
                                    best = m1 + m2 + m3
                                    bestwords = (orig[scores1.argmax()], orig[scores2.argmax()], orig[scores3.argmax()])
    return bestwords, best


if __name__ == '__main__':
    import timeit
    print timeit.timeit('print find_best_words()', 'from __main__ import find_best_words', number=1)
