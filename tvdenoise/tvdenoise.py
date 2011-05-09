import numpy as np

def discrete_div(nu):
    # backward differences using Dirichlet boundary conditions
    temp_i = nu[:, :, 0].copy()
    temp_i[-1, :] = 0
    temp_j = nu[:, :, 1].copy()
    temp_j[:, -1] = 0
    return temp_i - np.roll(temp_i, 1, 0) + temp_j - np.roll(temp_j, 1, 1)

def discrete_grad(u):
    temp_i = np.roll(u, -1, 0) - u
    temp_j = np.roll(u, -1, 1) - u
    temp_i[-1, :] = 0
    temp_j[:, -1] = 0
    return np.dstack((temp_i, temp_j))

def proj(nu):
    return nu / np.atleast_3d(np.maximum(1, np.sqrt(nu[:,:,0]**2 + nu[:,:,1]**2)))

def tvdenoise(f, lmbda, thresh=0.0001):
    # http://wwwcremers.in.tum.de/teaching/ss2010/vmcv2010/vmcv_ss2010_08.pdf
    u = f
    xi = np.dstack((np.zeros_like(u), np.zeros_like(u)))
    nu = xi
    t = 1.0
    change = np.inf
    stop_at = np.max(u) * thresh

    iter = 0
    while (iter < 3) or (change > stop_at):
        u_new = f - lmbda * discrete_div(xi)
        change = np.max(np.abs(u - u_new))
        print "	", change, stop_at, 
        u = u_new
        dg = discrete_grad(u)
        xi = proj(xi + dg * (1.0 / (80 * lmbda)))
        dgl = np.sum(np.sqrt((dg**2).sum(axis=2)))
        print "obj", 1.0 / (2 * lmbda) * np.sum((u-f)**2) + dgl, dgl
        iter += 1
    return u

import pylab
import scipy.misc

lena = scipy.misc.lena()
lena = lena.astype(float) / np.amax(lena)
pylab.imshow(lena)
pylab.gray()
pylab.figure()
pylab.imshow(tvdenoise(lena, 0.05))
pylab.gray()
