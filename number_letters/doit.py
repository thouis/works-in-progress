import numpy as np
import os
os.environ['C_INCLUDE_PATH']=np.get_include()
import pyximport
pyximport.install()
import score2
score2.doit()

