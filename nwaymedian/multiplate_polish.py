import numpy as np

def multiplate_polish(plates, controls, labels):
    '''median polish for multiple plates with shared effects.
    
    Plates is a list of IxJ matrices.  Controls is a boolean matrix
    indicating controls (used to estimate per-plate effect).  Labels
    is a list of label matrices, with independent plate-position
    effects estimated for shared labels across the stack of plates.

    For instance, using a list of two matrices with row and column
    position, respectively, is equivalent to B-scoring.
    '''

    # actual effect
    polished = np.dstack((plates))
    per_plate = np.zeros(len(plates))
    per_labels = [np.zeros(l.max() + 1) for l in labels]
    change = np.inf * (1 + polished)
    
    while abs(change).max() > 0.05:
        start = polished.copy()
        # compute per plate correction
        for pl in range(polished.shape[2]):
            delta = np.median(polished[:, :, pl])
            per_plate[pl] += delta
            polished[:, :, pl] -= delta

        polished += np.median(per_plate)
        per_plate -= np.median(per_plate)

        # compute per label correction
        for label, per_label in zip(labels, per_labels):
            for idx in range(label.max() + 1):
                delta = np.median(polished[idx == label])
                per_label[idx] += delta
                polished[idx == label] -= delta
            polished += np.median(per_label)
            per_label -= np.median(per_label)


        change = polished - start

    return polished, per_plate, per_label

if __name__ == '__main__':
    from pylab import *
    real = [np.random.uniform(0, 1, (8, 13)) for idx in range(25)]
    pl = [np.random.uniform(0, 1) for idx in range(25)]
    roweff = np.random.uniform(0, 1, (8, 1))
    coleff = np.random.uniform(0, 1, (1, 13))
    colidx, roidx = np.meshgrid(np.arange(13), np.arange(8))
    print pl
    fixed, ppest, plest = multiplate_polish([r + p + roweff + coleff for r, p in zip(real, pl)], np.median(real[0]) > 0.5, [roidx, colidx])
