import sys
import xlrd
import xlwt
import numpy as np
import pylab
import os.path

book = xlrd.open_workbook(sys.argv[1])
sheet = book.sheet_by_name(sys.argv[2])

separate_replicates = False
if len(sys.argv) == 5:
    assert sys.argv[4] in ['combined', 'separate']
    separate_replicates = sys.argv[4] == 'separate'
if separate_replicates:
    sys.argv[1] += ' (separated by replicate)'

# parse XLS
features = [c.value for c in sheet.row(0)[3:6]]
plate_genes = {}
plate_values = {}
for rowidx in range(1, sheet.nrows):
    plate, well, gene, r1, r2, r3  = [c.value for c in sheet.row(rowidx)[:6]]
    plate_genes[plate, well] = gene
    plate_values[plate, well] = [float(v) for v in [r1, r2, r3]]

# create plate maps
plate_maps = {}
for plate in set([pl for pl, wl in plate_genes.keys()]):
    for replicate in range(3):
        # 96-well plates
        cur_plate_map = plate_maps[plate, replicate] = np.zeros((8, 12))
        for well in set([wl for pl, wl in plate_genes.keys()]):
            row = int(ord(well[0]) - ord('A'))
            col = int(well[1:]) - 1
            cur_val = cur_plate_map[row, col] = plate_values[plate, well][replicate]/100.0 + 0.001
        

# create control maps
control_maps = {}
for plate in set([pl for pl, wl in plate_genes.keys()]):
    # 96-well plates
    cur_control_map = control_maps[plate] = np.zeros((8, 12), np.bool)
    for well in set([wl for pl, wl in plate_genes.keys()]):
        row = int(ord(well[0]) - ord('A'))
        col = int(well[1:]) - 1
        # cur_control_map[row, col] = plate_genes[plate, well] == 'GL2'
        if plate != 'P8':
            cur_control_map[row, col] = (0 < col < 11) or (plate_genes[plate, well] == 'GL2')
        else:
            cur_control_map[row, col] = col >= 6

num_plates = max([int(pl[1:]) for pl, wl in plate_genes.keys()])

count = 0
def get_count():
    global count
    count = count + 1
    return '%d '%(count)

def robust_cv(vals):
    return 1.48 * np.median(abs(vals - np.median(vals))) / np.median(vals)

def show_plates(plate_maps, title, same_scale=True):
    lo = np.array(plate_maps.values()).min()
    hi = np.array(plate_maps.values()).max()
    pylab.figure(figsize=(8.3,11.7))
    for (pl, rep), vals in plate_maps.iteritems():
        pylab.subplot(num_plates, 3, 1 + (int(pl[1:]) - 1) * 3 + rep)
        if same_scale:
            pylab.imshow(vals, interpolation='nearest', vmin=lo, vmax=hi)
        else:
            pylab.imshow(vals, interpolation='nearest')
        pylab.xlabel('%0.3f'%(robust_cv(vals)))
        pylab.axis('image')
    pylab.suptitle(sys.argv[1] + "\n" + title)
    pylab.subplot(num_plates, 3, 3 * num_plates)
    pylab.colorbar()
    pylab.savefig(os.path.join(sys.argv[3].replace('.xls', ''), get_count() + title + '.png'))
    pylab.close()

def show_plates_median(plate_maps, title, same_scale=True):
    pylab.figure()
    plmed = np.median(np.dstack([v for (pl, r), v in plate_maps.iteritems() if pl != 'P8']), axis=2)
    pylab.imshow(plmed, interpolation='nearest')
    pylab.axis('image')
    pylab.xlabel('%0.3f'%(robust_cv(plmed)))
    pylab.suptitle(title)
    pylab.colorbar()
    pylab.savefig(os.path.join(sys.argv[3].replace('.xls', ''), get_count() + title + '.png'))
    pylab.close()

def show_plates_median_by_replicate(plate_maps, title, same_scale=True):
    meds = []
    for rep in range(3):
        meds += [np.median(np.dstack([v for (pl, r), v in plate_maps.iteritems() if pl != 'P8' and r == rep]), axis=2)]
    lo = np.dstack(meds).min()
    hi = np.dstack(meds).max()
    pylab.figure(figsize=(8.3,11.7))
    for rep in range(3):
        pylab.subplot(3,1,rep+1)
        pylab.imshow(meds[rep], interpolation='nearest', vmin=lo, vmax=hi)
        pylab.axis('image')
        pylab.xlabel('%0.3f'%(robust_cv(meds[rep])))
    pylab.suptitle(title)
    pylab.colorbar()
    pylab.savefig(os.path.join(sys.argv[3].replace('.xls', ''), get_count() + title + '.png'))
    pylab.close()

def show_distributions(plate_maps, title):
    pylab.figure(figsize=(8.3,11.7))
    for rep in range(3):
        pylab.subplot(3, 1, rep+1)
        bins = pylab.hist(np.dstack([v for (pl, r), v in plate_maps.iteritems() if r == rep]).flatten(), 50)[1]
        control_scores = []
        negcontrol_scores = []
        for (pl, cr), vals in plate_maps.iteritems():
            if cr != rep:
                continue
            for well in set([wl for _, wl in plate_genes.keys()]):
                row = int(ord(well[0]) - ord('A'))
                col = int(well[1:]) - 1
                if plate_genes[pl, well] == 'GL2':
                    control_scores += [vals[row, col]]
                elif plate_genes[pl, well] == 'KIF11':
                    negcontrol_scores += [vals[row, col]]
        pylab.hist(negcontrol_scores, bins, color='r')
        pylab.hist(control_scores, bins, color='g')

    pylab.suptitle(title)
    pylab.savefig(os.path.join(sys.argv[3].replace('.xls', ''), get_count() + title + '.png'))
    pylab.close()
    


show_plates(plate_maps, 'original')

def logit(x):
    return np.log(x / (1 - x))

def invlogit(x):
    return np.exp(x) / (1 + np.exp(x))


if 'Count' in sys.argv[2]:
    trans = np.log
    invtrans = np.exp
else:
    trans = logit
    invtrans = invlogit

# transform to log_scale
plate_maps_log = dict(((pl, rep), trans(v)) for (pl, rep), v in plate_maps.iteritems())

# show combined plate map on the log scale
show_plates(plate_maps_log, 'transformed')

def GL2_shift(plate_maps):
    GL2_medians = np.array([np.median(vals[control_maps[pl]]) for (pl, rep), vals in plate_maps.iteritems()])
    # preserve identifiability
    GL2_medians -= np.median(GL2_medians)
    return dict(((pl, rep), vals - gl2med) for ((pl, rep), vals), gl2med in zip(plate_maps.iteritems(), GL2_medians))

def row_shift(plate_maps):
    if separate_replicates == False:
        row_medians = np.median(np.hstack(plate_maps.values()), axis=1).reshape((8,1))
        # preserve identifiability
        row_medians -= np.median(row_medians)
        return dict(((pl, rep), vals - row_medians) for (pl, rep), vals in plate_maps.iteritems())
    else:
        row_medians = dict([(rep, np.median(np.hstack([plate_maps[pl, r] for pl, r in plate_maps if r == rep]), 
                                            axis=1).reshape((8,1)))
                            for rep in range(3)])
        # preserve identifiability
        for rep in range(3):
            row_medians[rep] -= np.median(row_medians[rep])

        return dict(((pl, rep), vals - row_medians[rep]) for (pl, rep), vals in plate_maps.iteritems())
    

def col_shift(plate_maps):
    if separate_replicates == False:
        col_medians = np.median(np.vstack([v for (p, r), v in plate_maps.iteritems() if p != 'P8']), axis=0).reshape((1,12))
        # ignore first and last columns
        col_medians[0, 0] = col_medians[0, 1]
        col_medians[0, -1] = col_medians[0, -2]
        # preserve identifiability
        col_medians -= np.median(col_medians)
        return dict(((pl, rep), vals - col_medians) for (pl, rep), vals in plate_maps.iteritems())
    else:
        def colmed(r):
            col_medians = np.median(np.vstack([v for (p, rep), v in plate_maps.iteritems() if p != 'P8' and rep == r]), axis=0).reshape((1,12))
            # ignore first and last columns
            col_medians[0, 0] = col_medians[0, 1]
            col_medians[0, -1] = col_medians[0, -2]
            # preserve identifiability
            col_medians -= np.median(col_medians)
            return col_medians
        col_medians = dict((r, colmed(r)) for r in range(3))
        return dict(((pl, rep), vals - col_medians[rep]) for (pl, rep), vals in plate_maps.iteritems())
        

plate_maps_current = plate_maps_log


for iter in range(20):
    plate_maps_current = GL2_shift(plate_maps_current)
    if iter == 0:
        show_plates(plate_maps_current, 'median shifted (before polishing)')
        show_plates_median_by_replicate(plate_maps_current, 'median shifted (before polishing, by batch)' )
        show_plates_median(plate_maps_current, 'median shifted (before polishing, combined)')

    plate_maps_current = row_shift(plate_maps_current)
    plate_maps_current = col_shift(plate_maps_current)

show_plates_median(plate_maps_current, 'median shifted (after polishing, combined)')
show_plates_median_by_replicate(plate_maps_current, 'median shifted (after polishing, by batch)')

show_distributions(plate_maps_current, "dist after polishing (transformed %s)"%(sys.argv[2]))

show_plates(plate_maps_current, 'transformed - polished')

plate_maps_cleaned_transformed = plate_maps_current

plate_maps_linear = dict(((pl, rep), invtrans(v)) for (pl, rep), v in plate_maps_current.iteritems())
show_plates(plate_maps_linear, 'polished')
show_distributions(plate_maps_linear, "dist after polishing (raw %s)"%(sys.argv[2]))

# find GL2 scores

control_scores = dict((r, []) for r in range(3))
for (pl, rep), vals in plate_maps_cleaned_transformed.iteritems():
    for well in set([wl for _, wl in plate_genes.keys()]):
        row = int(ord(well[0]) - ord('A'))
        col = int(well[1:]) - 1
        if plate_genes[pl, well] == 'GL2':
            print pl, rep, row, col
            control_scores[rep] += [vals[row, col]]

GL2med = [np.median(control_scores[r]) for r in range(3)]
print "LENGHTS", [len(control_scores[r]) for r in range(3)]
GL2sigmaMAD = [np.median(abs(np.array(control_scores[r]) - GL2med[r])) * 1.48 for r in range(3)]

# report transformed, cleaned values
outputs = []
gene_scores = {}
for pl in set(k[0] for k in plate_maps_linear.keys()):
    print pl
    for well in set([wl for _, wl in plate_genes.keys()]):
        row = int(ord(well[0]) - ord('A'))
        col = int(well[1:]) - 1
        outvals = [plate_maps_cleaned_transformed[pl, r][row, col] for r in range(3)]
        outputs += [(pl, well, plate_genes[pl, well], outvals[0], outvals[1], outvals[2])]
        g = plate_genes[pl, well]
        # if g == 'GL2' and pl != 'P8':
        #     g = 'GL2-%s-col%d'%(pl, col)
        gene_scores[g] = gene_scores.get(g, []) + [(pl, well, np.median([(outvals[rep] - GL2med[rep]) / GL2sigmaMAD[rep] for rep in range(3)]))]

outbook = xlwt.Workbook()
rnaisheet = outbook.add_sheet('%s cleaned, by RNAi'%(sys.argv[2]))
rowidx = 0
outputs = [['Plate', 'Well', 'Gene Name', 
            'Replicate 1 Corrected', 'Replicate 2 Corrected', 'Replicate 3 Corrected']] + sorted(outputs)
for rowidx, line in enumerate(outputs):
    for colidx, val in enumerate(line):
        rnaisheet.write(rowidx, colidx, val)

basecol = colidx + 2
# write out GL2 median and sigmaMad
outputs = [['', 'R1', 'R2', 'R3'], ['GL2 median'] + GL2med, ['GL2 sigmaMAD'] + GL2sigmaMAD]
for rowidx, line in enumerate(outputs):
    for colidx, val in enumerate(line):
        rnaisheet.write(rowidx, basecol + colidx, val)

rnaisheet.write(rowidx + 2, basecol, 'Source: ' + sys.argv[1])
rnaisheet.write(rowidx + 3, basecol, 'Phenotype ' + sys.argv[2])

genesheet = outbook.add_sheet('%s by RNAi'%(sys.argv[2]))

def scores(v):
    # sort by magnitude
    v = np.array(v)
    v = v[np.argsort(-abs(v))]
    return v[0], v[1], np.median(v)

def sort_by_score(vals):
    # score is third
    return [d for (s, d) in sorted([(-np.abs(v[2]), v) for v in vals])]

def rank_genes():
    for g, vals in gene_scores.iteritems():
        for idx, (pl, well, s) in enumerate(sort_by_score(vals)):
            yield [pl, well, g, s, idx + 1]

outputs = [['Plate', 'Well', 'Gene Name', 'RNAi Z-score', 'Rank in magnitude']] + sorted([r for r in rank_genes()])
for rowidx, line in enumerate(outputs):
    for colidx, val in enumerate(line):
        genesheet.write(rowidx, colidx, val)

outbook.save(sys.argv[3])



pylab.show()
