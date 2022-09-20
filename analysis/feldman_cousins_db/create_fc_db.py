import os
import numpy  as np
import pandas as pd

os.sys.path.append(os.path.expandvars("$HOME/NEXT/pybbsens/"))
from pybbsens.conflimits import FeldmanCousins

@np.vectorize
def mean_upper_limit(b, cl=90):
    fc = FeldmanCousins(cl)
    return fc.AverageUpperLimit(b)


background_rates = np.arange(0.5, 4, 0.1) # background rate (1/years)
exposures        = np.arange(1, 6+1, 0.5) # exposure (years)

df = pd.DataFrame(columns=exposures)
for i, c in enumerate(background_rates, 1):

    proc = f"Processing {i} / {len(background_rates)}"
    print(proc.ljust(100))

    Ul = mean_upper_limit(c * exposures)
    df.loc[c] = Ul

df.to_csv("fc_upper_lims.csv")
