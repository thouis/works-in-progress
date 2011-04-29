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
    if word == '':
        return tonum('A')
    return np.array([ord(w) for w in word], dtype=np.uint8)


def to_score_array(letters):
    score_array = np.zeros(255, dtype=np.int) - 2
    score_array[0] = 0
    for v in 'AEIOU':
        score_array[ord(v)] = 0
    for idx, l in enumerate(letters):
        score_array[ord(l)] = idx + 1
    return score_array

def score_word(word, values):
    return values[word].sum()

wlist = [l.strip().upper() for l in open('/usr/share/dict/words') if l[0].lower() == l[0]]
wlist = [l for l in wlist if len(l) > 4]
orig = [l for l in wlist]
for rep in 'AEIOU':
    wlist = [l.replace(rep, '') for l in wlist]
wlist = [tonum(w) for w in wlist]
print wlist[:10]
largest = max(len(w) for w in wlist)
print largest, "largest len"
wordarray = np.zeros((len(wlist), largest), dtype=np.uint8)
for idx, w in enumerate(wlist):
    wordarray[idx, :len(w)] = w

best = 0
ct = 0
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
                            scores1 = vals[0][wordarray].sum(axis=1)
                            scores2 = vals[1][wordarray].sum(axis=1)
                            scores3 = vals[2][wordarray].sum(axis=1)
                            m1 = max(scores1)
                            m2 = max(scores2)
                            m3 = max(scores3)
                            if m1 + m2 + m3 > best:
                                print orig[scores1.argmax()], orig[scores2.argmax()], orig[scores3.argmax()], m1 + m2 + m3
                                best = m1 + m2 + m3
