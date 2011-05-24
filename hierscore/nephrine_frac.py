import csv
import numpy as np
import pymc

### SETUP
# counts_pos, counts_total, batch_id, plate_id, row, col, treatment
rows = [tuple(row) for row in csv.reader(open('nephrine_fracs.csv'))]
pos_counts, total_counts, batch_ids, plate_ids, row_ids, col_ids, treatment_ids = [np.array(v) for v in zip(*rows)]

# batches
batch_names, batch_idxs = np.unique(batch_ids, return_inverse=True)
num_batches = len(batch_names)

# plates
plate_names, plate_idxs = np.unique(plate_ids, return_inverse=True)
num_plates = len(plate_names)

# batchrows, batchcols
batchrow_names, batchrow_idxs = np.unique(['batchrow_%s_%s'%(b, r) for b, r in zip(batch_ids, row_ids)], return_inverse=True)
batchcol_names, batchcol_idxs = np.unique(['batchcol_%s_%s'%(b, c) for b, c in zip(batch_ids, col_ids)], return_inverse=True)

# treatments
treatment_names, treatment_idxs = np.unique(treatment_ids, return_inverse=True)


### MODEL
# base effect, uninformative prior
base_fx = pymc.Normal('base', mu=0, tau=0.001)

# batch effect, somewhat informative prior
batch_fx = np.array([pymc.Normal('batch_%s'%(batch_names[idx]), mu=0, tau=0.1) for idx in range(num_batches)])

# plate effect, two-level prior
plate_prec_base = pymc.Gamma('plate_prec_prior', alpha=0.01, beta=0.01)
plate_fx = np.array([pymc.Normal('plate_%s'%(plate_names[idx]), mu=0, tau=plate_prec_base) for idx in range(num_plates)])

# platerow effect, two-level prior
batchrowcol_prec_base = pymc.Gamma('batchrowcol_prec_prior', alpha=0.01, beta=0.01)
batchrow_fx = np.array([pymc.Normal(name, mu=0, tau=batchrowcol_prec_base) for name in batchrow_names])
batchcol_fx = np.array([pymc.Normal(name, mu=0, tau=batchrowcol_prec_base) for name in batchcol_names])

# treatment effect - individual precisions
# NB: these are the values we are interested in capturing.
treatment_prec_bases = np.array([pymc.Gamma('treatment_prec_prior_%s'%(name), alpha=0.01, beta=0.01, value=0.5) for name in treatment_names])
treatment_fx = np.array([pymc.Normal('treatment_%s'%(name), mu=0, tau=tau) for name, tau in zip(treatment_names, treatment_prec_bases)])

# individual well noise - see pg. 384 of ARM, Gelman & Hill
wellnoise_df_inv = pymc.Uniform('wellnoise_df_inv', lower=0, upper=0.5, value=0.33)

@pymc.deterministic(plot=False)
def wellnoise_df(wellnoise_df_inv=wellnoise_df_inv):
    return 1.0 / wellnoise_df_inv

@pymc.deterministic(plot=False)
def wellnoise_scale(wellnoise_df=wellnoise_df):
    return wellnoise_df / (wellnoise_df - 2)

# well effect, drawn from treatment, robit-type noise
well_fx = pymc.NoncentralT('well_effects', treatment_fx[treatment_idxs], wellnoise_scale, wellnoise_df)

# Unnobserved probabilities per well
@pymc.deterministic(plot=False)
def p_wells(base_fx=base_fx,
            batch_fx=batch_fx,
            plate_fx=plate_fx,
            platerow_fx=platerow_fx,
            platecol_fx=platerow_fx,
            treatement_fx=treatement_fx):
    return pymc.invlogit(base_fx +
                         batch_fx[batch_idxs] +
                         plate_fx[plate_idxs] +
                         batchrow_fx[batchrow_idxs] +
                         batchcol_fx[batchcol_idxs] +
                         well_fx)

# Likelihood
@pymc.stochastic(observed=True)
def pos_counts_i(x=pos_counts, n=total_counts, p=p_wells):
    return pymc.Binomial(x, n, p)
