
from numpy import *
import numpy.linalg as la
from scipy import sparse
from scipy.io import loadmat


foo = loadmat('../test_auc_rls.mat')

Y = mat(foo['Y'])
X = mat(foo['X'])

regparam = 1.
fsize = X.shape[0]
tsize = X.shape[1]

P = sparse.lil_matrix((tsize, 2))
Q = sparse.lil_matrix((2, tsize))
D = sparse.lil_matrix((tsize, tsize))

posinds = []
neginds = []

for i in range(tsize):
    if Y[i] == 1.:
        posinds.append(i)
        P[i, 0] = 1.
        Q[1, i] = 1.
    else:
        neginds.append(i)
        P[i, 1] = 1.
        Q[0, i] = 1.

for i in range(tsize):
    if Y[i] == 1.:
        D[i, i] = len(neginds)
    else:
        D[i, i] = len(posinds)


ww, _, _, _ = la.lstsq(X * D * X.T - (X * P) * (Q * X.T) + regparam * mat(eye(fsize)), X * (D * Y - P * (Q * Y)))
print ww

