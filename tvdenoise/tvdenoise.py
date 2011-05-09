import numpy as np

def discrete_div(vec):
    # backward differences using Dirichlet boundary conditions.
    # NB: the boundary conditions are assumed, and rely on
    # vec[-1, :, 0] == 0.0 and vec[:, -1, 1] == 0.0, which is the
    # case in the code below (nu initially is all 0, and
    # discrete_grad(u) always fulfills this condition)
    temp = np.sum(vec, axis=2)
    temp[1:, :] -= vec[:-1, :, 0]
    temp[:, 1:] -= vec[:, :-1, 1]
    return temp

def discrete_grad(u):
    temp_i = np.zeros_like(u)
    temp_j = np.zeros_like(u)
    temp_i[:-1, :] = np.diff(u, axis=0)
    temp_j[:, :-1] = np.diff(u, axis=1)
    return np.dstack((temp_i, temp_j))

def proj(vec):
    return vec / np.atleast_3d(np.maximum(1, np.sqrt(np.sum(vec**2, axis=2))))

def tvdenoise(im, lmbda, thresh=1/512.0):
    # http://wwwcremers.in.tum.de/teaching/ss2010/vmcv2010/vmcv_ss2010_08.pdf
    u = im
    xi = np.dstack((np.zeros_like(u), np.zeros_like(u)))
    nu = xi
    t = 1.0
    change = np.inf
    stop_at = np.max(u) * thresh

    iter = 0
    while (iter < 3) or (change > stop_at):
        u_new = im + lmbda * discrete_div(nu)
        change = np.max(np.abs(u - u_new))
        u = u_new

        xi_new = proj(nu + discrete_grad(u) / (8 * lmbda))
        t_new = (1 + np.sqrt(1 + 4 * t**2)) / 2
        nu = xi_new + ((t - 1) / t_new) * (xi_new - xi)
        xi = xi_new
        t = t_new
        iter += 1
    return u

import pylab
import scipy.misc

lena = scipy.misc.lena()
lena = lena.astype(float) / np.amax(lena)
pylab.imshow(lena)
pylab.gray()
pylab.figure()
pylab.imshow(tvdenoise(lena, 0.01))
pylab.gray()
