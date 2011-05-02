import MySQLdb
import xlwt
import os
import os.path
import glob
from xml_parse import parse_xml_summary
import cPickle
import numpy as np
import sys
import bfx_images
import Image
import cStringIO
import random

experiment = sys.argv[1]
feature_of_interest = (sys.argv[2], sys.argv[3])

print experiment, feature_of_interest

if os.path.exists('/Volumes/plateformes/incell'):
    basedir = '/Volumes/plateformes/incell'
else:
    basedir = '/import/gemini.curie.fr/incell'

if experiment not in ('Ars', 'SUMO') and 'Low' in feature_of_interest[0]:
    sys.exit(0)

if experiment == 'Ars' and 'Low' in feature_of_interest[0]:
    feature_of_interest = ('Low PML Nucl. Bodies', 'Low NB (%)')

conn = MySQLdb.connect('ptilouis', 'biophenics', 'biophenics', 'biophenics')
cursor = conn.cursor()

# find all plates with 'PML' and 'HCS' in their name
cursor.execute("SELECT PLATE_ID, EXPERIMENT_ID FROM PLATE WHERE PLATE_THEME='HCS_E004' AND NOT ISNULL(EXPERIMENT_ID)")
plate_to_experiment = dict(cursor.fetchall())

book = xlwt.Workbook()

def trace_project(project_id, chase=False):
    if project_id is None:
        return "None"

    cursor.execute('SELECT ITEM_NAME, PARENT_ITEM_ID from PROJECT_ITEM where PROJECT_ITEM_ID=%d'%(project_id))
    name, parent = cursor.fetchall()[0]
    if parent is not None and chase:
        return trace_project(parent) + ' | ' + name
    return name

def read_plate_data(path):
    fnames = glob.glob(os.path.join(basedir, path, '*.xml'))
    fnames = [f[1] for f in sorted([(os.stat(f).st_mtime, f) for f in fnames])]
    orig = [os.path.basename(f) for f in fnames]
    if len(fnames) > 1:
        if experiment == 'SUMO':
            fnames = [f for f in fnames if 'SUMO' in os.path.basename(f)]
        elif experiment == 'Ars':
            fnames = [f for f in fnames if 'PML-arse' in os.path.basename(f)]
        elif experiment in ('noArs', 'Supl'):
            fnames = [f for f in fnames if 'E-004-PML.xml' in os.path.basename(f)]
    if len(fnames) > 1:
        fnames = [f for f in fnames if 'filters' not in os.path.basename(f)]
        if len(fnames) > 1 and experiment == 'SUMO':
            fnames = [fnames[-1]]
    
    assert len(fnames) == 1, (orig, experiment, feature_of_interest)
    
    return parse_xml_summary(fnames[0])


batch_to_plates = {}
data = {}
siRNAmap = {}
plate_dir = {}

for plate_id, experiment_id in sorted(plate_to_experiment.iteritems()):
    # find the experiment and project name
    cursor.execute('SELECT EXP_NAME, PROJECT_ITEM_ID from EXPERIMENT WHERE EXPERIMENT_ID=%d'%(experiment_id))
    exp_name, project_id = cursor.fetchall()[0]

    cursor.execute('SELECT PLATE_THEME, PLATE_CODE, PLATE_NAME FROM PLATE WHERE PLATE_ID=%d'%(plate_id))
    theme, code, name = cursor.fetchall()[0]

    # chase the project name tree
    project_name = trace_project(project_id)
    
    # find an acquisition
    cursor.execute('SELECT IMAGE_PATH FROM ACQUISITION WHERE PLATE_ID=%d'%(plate_id))
    paths = [v[0] for v in cursor.fetchall() if not '20X' in v[0]]
    title = " ".join(['Expt:', exp_name, 'Proj:', project_name, 'Plate:', str(unicode(name, errors='ignore')), 'Barcode:', str(code), str(plate_id)])

    if any([v in title for v in ['Pre-', 'pr-IF', 'PreIF']]):
        continue

    batch = os.path.dirname(paths[0])

    if experiment != 'Supl' and 'Supl' in batch:
        continue

    if experiment in  ('Ars', 'SUMO'):
        if 'Without' in batch:
            continue
    elif experiment == 'noArs':
        if 'Without' not in batch:
            continue
    elif experiment == 'Supl':
        if 'Supl' not in batch:
            continue
    elif experiment == 'SUMO':
        if 'SUMO' not in batch:
            continue

    batch_to_plates[batch] = batch_to_plates.get(batch, []) + [(plate_id, title)]
    assert len(paths)==1

    data[plate_id] = read_plate_data(paths[0])
    plate_dir[plate_id] = paths[0]

    # find siRNA per well
    cursor.execute('SELECT WELL_ROW, WELL_COL, DUPLEX_NAME, DUPLEX_NUMBER FROM WELL NATURAL JOIN SI_RNA_WELL NATURAL JOIN SI_RNA WHERE PLATE_ID=%d'%(plate_id))
    siRNAmap[plate_id] = dict([((r, c), (dname, dnum)) for r,c,dname,dnum in cursor.fetchall()])

# for testing offline
cPickle.dump((data, batch_to_plates, siRNAmap), open('/Users/tjones/PML_withArs.pickle', 'w'))


scores_by_batch = {}
batch_siRNA_to_directory_well = {}
for batch, plates in batch_to_plates.iteritems():

    # find map from siRNA to score(s)
    scores_by_siRNA = scores_by_batch[batch] = {}
    GL2_count = 0
    
    for (plate, title) in plates:
        for well in set([k[0] for k in data[plate].keys()]):
            # compute soluble pml if needed
            if 'Soluble PML' in feature_of_interest:
                try:
                    nucarea = float(data[plate][(well, ('Nuclei', 'Nuc Area'))])
                except:
                    nucarea = float(data[plate][(well, ('Cells', 'Nuc/Cell Area'))]) * float(data[plate][(well, ('Cells', 'Cell Area'))])
                pmlarea = float(data[plate][(well, ('Organelles', 'Total Area'))])
                nucintens = float(data[plate][(well, ('Cells', 'Nuc Intensity'))])
                pmlintens = float(data[plate][(well, ('Organelles', 'Intensity'))])
                data[plate][well, ('Nuclei', 'Soluble PML')] = (nucarea * nucintens - pmlarea * pmlintens) / (nucarea - pmlarea)

            value = float(data[plate][(well, feature_of_interest)])
            siRNA = siRNAmap[plate].get(well, ('empty', ''))
            if siRNA[0] == 'GL2':
                GL2_count += 1
                temp_GL2 = ('GL2-%d'%(GL2_count), siRNA[1])
                print temp_GL2, scores_by_siRNA.get(temp_GL2, [])
                batch_siRNA_to_directory_well[batch, temp_GL2] = batch_siRNA_to_directory_well.get((batch, temp_GL2), []) + [(plate_dir[plate], well)]
                scores_by_siRNA[temp_GL2] = scores_by_siRNA.get(temp_GL2, []) + [value]
            scores_by_siRNA[siRNA] = scores_by_siRNA.get(siRNA, []) + [value]
            batch_siRNA_to_directory_well[batch, siRNA] = batch_siRNA_to_directory_well.get((batch, siRNA), []) + [(plate_dir[plate], well)]

    # normalize each batch separately
    shift = np.median(scores_by_siRNA['GL2', 1])
    scale = 1.48 * np.median(np.abs(np.array(scores_by_siRNA['GL2', 1]) - shift))
    for siRNA in scores_by_siRNA:
        scores_by_siRNA[siRNA] = [(v - shift) / scale for v in scores_by_siRNA[siRNA]]

# check that all batches have the same genes?
for b in scores_by_batch.keys():
    assert set(scores_by_batch[b].keys()) == set(scores_by_siRNA.keys())

# join batches for hit calling
sheet = book.add_sheet('separate siRNAs')
row = 0
for row, siRNA in enumerate(sorted(scores_by_siRNA.keys())):
    sheet.write(row, 0, '%s %s'%siRNA)
    scores = sum((scores_by_batch[b][siRNA] for b in scores_by_batch.keys()), [])
    for idx, v in enumerate(scores[:255]):
        sheet.write(row, idx + 1, v)

sheet = book.add_sheet('median by siRNA')
row = 0
siRNA_gene_scores = {}
for row, siRNA in enumerate(sorted(scores_by_siRNA.keys())):
    sheet.write(row, 0, '%s %s'%siRNA)
    scores = sum((scores_by_batch[b][siRNA] for b in scores_by_batch.keys()), [])
    sheet.write(row, 1, np.median(scores))
    siRNA_gene_scores[siRNA[0]] = siRNA_gene_scores.get(siRNA[0], []) + [np.median(scores)]


sheet = book.add_sheet('hit and score by gene')
row = 0
num_hits = 0
hitgenes = []
for row, (gene, scores) in enumerate(sorted(siRNA_gene_scores.iteritems())):
    sheet.write(row, 0, '%s'%gene)
    scores = np.array(scores)
    is_hit = (sum(scores > 2.0) >= 2) or (sum(scores < -2.0) >= 2)
    if is_hit:
        num_hits += 1
        hitgenes = hitgenes + [gene] + ['GL2-%d'%(int(random.random() * GL2_count))]
        sheet.write(row, 1, 'hit')
    sheet.write(row, 2, np.median(scores))
sheet.write(row, 3, '%s total hits'%num_hits)

print hitgenes

def get_image_path(siRNA, batch):
    return batch_siRNA_to_directory_well[batch, siRNA]



hitgenes = set(hitgenes)
gene_to_images = {}
for siRNA in scores_by_siRNA:
    if siRNA[0] in hitgenes:
        for b in scores_by_batch.keys():
            gene_to_images[siRNA[0]] = gene_to_images.get(siRNA[0], []) + [(siRNA, scores_by_batch[b][siRNA], get_image_path(siRNA, b))]

print gene_to_images

def logify(im):
    im = np.log(np.asarray(im))
    im -= im.min()
    im /= im.max()
    im *= 255.0
    im = im.astype(np.uint8)
    return Image.fromarray(im)

def stretch(im):
    im = np.asarray(im).astype(np.float)
    im -= im.min()
    im /= im.max()
    im *= 255.0
    im = im.astype(np.uint8)
    return Image.fromarray(im)



im_file_map = {}
def get_ims(basedir, path, well):
    if (path, well) not in im_file_map:
        for imf in [f for f in  glob.glob(os.path.join(basedir, path, "*.tif")) if not 'thumb' in f]:
            rc = bfx_images.get_well(imf)
            r = ord(rc[0]) - ord('A') + 1
            c = int(rc[1:])
            im_file_map[path, (r, c)] = im_file_map.get((path, (r, c)), []) + [imf]
    return sorted(im_file_map[path, well])



imidx = 0
hit_dir = "%s %s %s"%(experiment, feature_of_interest[0], feature_of_interest[1])
for gene, imlist in gene_to_images.iteritems():
    try:
        os.mkdir(hit_dir)
    except:
        pass
    hitfile = open(os.path.join(hit_dir, "%s.html"%(gene)), "w")
    hitfile.write("<html><body><center>%s</center>\n"%(gene))
    for siRNA, scores, pathwells in imlist:
        hitfile.write("<center>%s</center>\n"%("%s #%s"%(siRNA)))
        for (path, well), score in zip(pathwells, scores):
            hitfile.write("<center>%s</center>\n"%(score))
            
            imlist = get_ims(basedir, path, well)
            assert len(imlist) in (8, 12), (imlist, well)
            dapi_list = [im for im in imlist if 'D360_40x' in im]
            PML_list = [im for im in imlist if 'HQ535_50x' in im]
            if experiment in ('Ars', 'SUMO'):
                SUMO_list = [im for im in imlist if 'HQ480_40x' in im]
            else:
                SUMO_list = PML_list
            hitfile.write(repr(imlist))
            continue
            for d,p,s in zip(dapi_list, PML_list, SUMO_list):
                dim = stretch(Image.open(d).convert('RGB').split()[0])
                pim = stretch(Image.open(p).convert('RGB').split()[1])
                if experiment in ('Ars', 'SUMO'):
                    sim = stretch(Image.open(s).convert('RGB').split()[2])
                else:
                    sim = Image.fromarray(0 * np.asarray(dim), 'L')
                outpng = cStringIO.StringIO()
                Image.merge('RGB', (pim, sim, dim)).save(outpng, 'PNG')
                try:
                    os.mkdir(os.path.join(hit_dir, siRNA[0]))
                except Exception, e:
                    pass
                imf = open(os.path.join(hit_dir, siRNA[0], str(imidx) + ".png"), "w")
                imf.write(outpng.getvalue())
                imf.close()
                hitfile.write('<img src="%s" width=45%%>\n'%(os.path.join(siRNA[0], str(imidx) + ".png")))
                imidx += 1
    hitfile.close()
    print "	", gene


book.save('hit_calls_%s_%s_%s.xls'%(experiment, feature_of_interest[0], feature_of_interest[1]))


