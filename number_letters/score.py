from itertools import permutations

points = {'LTN' : 1,
          'RDS' : 2,
          'GBM' : 3,
          'CHP' : 4,
          'FWV' : 5,
          'YKJ' : 6,
          'QXZ' : 7}

def score_word(word, value):
    score = 0
    for c in word:
        try:
            score += value.index(c) + 1
        except:
            score -= 2
    return score

wlist = [l.strip().upper() for l in open('/usr/share/dict/words')] #  if l[0].lower() == l[0]]
wlist = [l for l in wlist if len(l) > 4]
orig = [l for l in wlist]
for rep in 'AEIOU':
    wlist = [l.replace(rep, '') for l in wlist]
print wlist[:10]

best = 0
ct = 0
for c1 in permutations('LTN'):
    for c2 in permutations('RDS'):
        for c3 in permutations('GBM'):
            for c4 in permutations('CHP'):
                for c5 in permutations('FWV'):
                    for c6 in permutations('YJK'):
                        for c7 in permutations('QZX'):
                            vals = [''.join(s) for s in zip(c1, c2, c3, c4, c5, c6, c7)]
                            ct += 1
                            print ct, 2187
                            scores1 = [score_word(w1, vals[0]) for w1 in wlist]
                            scores2 = [score_word(w2, vals[1]) for w2 in wlist]
                            scores3 = [score_word(w3, vals[2]) for w3 in wlist]
                            m1 = max(scores1)
                            m2 = max(scores2)
                            m3 = max(scores3)
                            if m1 + m2 + m3 > best:
                                print orig[scores1.index(m1)], orig[scores2.index(m2)], orig[scores3.index(m3)], m1 + m2 + m3
                                best = m1 + m2 + m3
