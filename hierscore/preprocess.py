import csv
import numpy as np
import pymc

### SETUP
# plate, well, treatment, ct1, ct2, ct3, frac1, frac2, frac3
rows = [tuple(row) for row in csv.reader(open('NephrineMedianThresh.csv', 'rU'), delimiter=';')]
plate_ids, wells, treatments, ct1, ct2, ct3, fr1, fr2, fr3 = [np.array(v) for v in zip(*rows)]
ct1 = np.array([float(s.replace(',', '')) for s in ct1])
ct2 = np.array([float(s.replace(',', '')) for s in ct2])
ct3 = np.array([float(s.replace(',', '')) for s in ct3])
fr1 = fr1.astype(float)
fr2 = fr2.astype(float)
fr3 = fr3.astype(float)
pos1 = ct1 * fr1
pos2 = ct2 * fr2
pos3 = ct3 * fr3
test13 = ct1 * fr3
print max(abs(pos1 - np.round(pos1))), max(abs(pos2 - np.round(pos2))), max(abs(pos3 - np.round(pos3)))
print max(abs(test13 - np.round(test13)))

writer = csv.writer(open('nephrine_fracs.csv', 'w'))
for batch, pos, ct in zip(range(3), [pos1, pos2, pos3], [ct1, ct2, ct3]):
    for p, ct, pl, w, t in zip(pos, ct, plate_ids, wells, treatments):
        writer.writerow((int(p), int(ct), batch + 1, pl, w[0], w[1:], t))
