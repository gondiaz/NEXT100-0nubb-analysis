import os
import glob
import pandas as pd


path         = os.path.expandvars("../results/typeI/")
in_filename  = os.path.join(path, "{t12}/outs/result_*.csv")
out_filename = os.path.join(path, "merged_results_{t12}.csv")

t12s  = os.listdir(path)
isdir = lambda name: os.path.isdir(os.path.join(path, name))
t12s  = list(filter(isdir, t12s))

for i, t12 in enumerate(t12s, 1):
    print(f"Processing {i}/{len(t12s)}", end="\r")
    filenames = glob.glob(in_filename.format(t12=t12))
    if len(filenames)<1: continue
    df = pd.concat([pd.read_csv(filename) for filename in filenames])
    df.to_csv(out_filename.format(t12=t12), index=False)
