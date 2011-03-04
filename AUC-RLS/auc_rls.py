import numpy as np
import debug

def auc_rls(X, Y, llambda):
    '''
    X is size (h, m) - m = # examples, h = # features
    Y is (m, 1) of {-1, +1}
    llambda is the regularization factor
    return value is w of size (m, 1), s.t. X.T * w is approx. Y
    '''

    # reorder X, Y so that all positive examples are first
    reord = np.argsort(Y, axis=0)[::-1]
    Y = np.matrix(Y[reord, 0])
    X = np.matrix(X[:, reord])
    numpos = (Y == 1).sum()
    numneg = (Y == -1).sum()
    assert numpos + numneg == Y.shape[0], "all labels must be in {-1, +1}."

    # parts of equation 12
    p = np.vstack((np.ones((numpos, 1)), np.zeros((numneg, 1))))
    P = np.matrix(np.hstack((p, 1 - p)))
    Q = (1 - P).T

    # D is diagonal matrix in the paper, but we'll use a vector and np.multiply
    D = np.zeros(Y.shape).T
    D[0,:numpos] = numneg
    D[0,numpos:] = numpos
    
    XDXT = np.multiply(X, D) * X.T
    XPQXT = (X * P) * (Q * X.T)
    XDY = X * np.multiply(D.T, Y)
    XPQY = X * (P * (Q * Y))
    lambdaI = np.diag(llambda * np.ones(X.shape[0]))

    print XDXT.shape, XDY.shape
    w, _, _, _ = np.linalg.lstsq(XDXT - XPQXT + lambdaI, XDY - XPQY)

    return w

if __name__ == '__main__':
    num_pos = 300
    num_neg = 100
    num_features = 15
    llambda = 1.0
    X = np.random.randn(num_features, num_pos + num_neg)
    Y = np.ones((num_pos + num_neg, 1))
    X[1, num_pos:] += 0.5
    Y[num_pos:, 0] = -1
    w= auc_rls(X, Y, llambda)
    print w[1] / abs(w[w != w[1]]).max(), w[1]
    from scipy.io import savemat
    savemat('test_auc_rls.mat', {'X':X, 'Y':Y, 'lambda':llambda, 'w':w})
