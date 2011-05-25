import csv
import numpy as np
from pymc import Gamma, Normal, NoncentralT, Binomial, Uniform, invlogit, logit, deterministic, stochastic

### SETUP
# counts_pos, counts_total, batch_id, plate_id, row, col, treatment
rows = [tuple(row) for row in csv.reader(open('nephrine_fracs.csv'))]
pos_counts, total_counts, batch_ids, plate_ids, row_ids, col_ids, treatment_ids = [np.array(v) for v in zip(*rows)]
pos_counts = pos_counts.astype(int)
total_counts = total_counts.astype(int)
num_wells = len(pos_counts)

# batches
batch_names, batch_idxs = np.unique(batch_ids, return_inverse=True)
num_batches = len(batch_names)

# plates
plate_names, plate_idxs = np.unique(plate_ids, return_inverse=True)
num_plates = len(plate_names)

# batchrows, batchcols
batchrow_names, batchrow_idxs = np.unique(['batchrow_%s_%s'%(b, r) for b, r in zip(batch_ids, row_ids)], return_inverse=True)
batchcol_names, batchcol_idxs = np.unique(['batchcol_%s_%s'%(b, c) for b, c in zip(batch_ids, col_ids)], return_inverse=True)
num_batchrows = len(batchrow_names)
num_batchcols = len(batchcol_names)

# treatments
treatment_names, treatment_idxs = np.unique(treatment_ids, return_inverse=True)
num_treatments = len(treatment_names)

### MODEL
# base effect, uninformative prior
base_fx = Normal('base', mu=0, tau=0.001, size=1, value=np.zeros(1))

# batch effect, somewhat informative prior
batch_fx = Normal('batch_fx', mu=0, tau=0.1, size=num_batches, value=np.zeros(num_batches))

# plate effect, two-level prior, somewhat informative
plate_prec = Gamma('plate_prec', alpha=0.1, beta=0.1)
plate_fx = np.array([Normal('plate_fx_%s'%(name), mu=0, tau=plate_prec, value=0) for name in plate_names])

# batch row and column effects, two-level prior
batchrowcol_prec_base = Gamma('batchrowcol_prec_prior', alpha=0.01, beta=0.01)
batchrow_fx = np.array([Normal('batchrow_fx_%s'%(name), mu=0, tau=batchrowcol_prec_base, value=0) for name in batchrow_names])
batchcol_fx = np.array([Normal('batchcol_fx_%s'%(name), mu=0, tau=batchrowcol_prec_base, value=0) for name in batchcol_names])

def initial_guess(treatment):
    return np.median(logit((pos_counts[treatment_ids == treatment] + 1).astype(float) / (total_counts[treatment_ids == treatment] + 2)))

# treatment effect - individual precisions
# NB: these are the values we are interested in capturing.
treatment_prec = [Gamma('treatment_prec_%s'%(name), alpha=0.01, beta=0.01, value=0.5) for name in treatment_names]
treatment_fx = np.array([Normal('treatment_fx_%s'%(name), mu=0, tau=treatment_prec[idx], value=initial_guess(name)) for idx, name in enumerate(treatment_names)])

# # well effects - we want to allow outliers, so use a 3-parameter
# # Student's t distribution (see ARM, pg. 384, Gelman & Hill)
# # nu = degrees of freedom
# well_df_inv = Uniform('well_df_inv', lower=0.0, upper=0.5, value=0.25)
# @deterministic(plot=False)
# def well_df(well_df_inv=well_df_inv):
#     return 1.0 / well_df_inv
# 
# #lam = scale
# @deterministic(plot=False)
# def well_lam(well_df=well_df):
#     return (well_df - 2) / well_df
# 
# well_fx = np.array([NoncentralT('well_fx_%d'%(wellidx), mu=0, lam=well_lam, nu=well_df, value=0) for wellidx in range(num_wells)])

# Unnobserved probabilities per well
@deterministic(plot=False)
def p_wells(base_fx=base_fx,
            batch_fx=batch_fx,
            plate_fx=plate_fx,
            batchrow_fx=batchrow_fx,
            batchcol_fx=batchcol_fx,
            treatment_fx=treatment_fx):
    # use this ordering to make everything turn into an ArrayContainer
    return invlogit(treatment_fx[treatment_idxs] + 
                    base_fx +
                    batch_fx[batch_idxs] +
                    plate_fx[plate_idxs] +
                    batchrow_fx[batchrow_idxs] +
                    batchcol_fx[batchcol_idxs])

# Likelihood
pos_counts_likelihood = Binomial('pos_counts', value=pos_counts, n=total_counts, p=p_wells, observed=True, verbose=0)
