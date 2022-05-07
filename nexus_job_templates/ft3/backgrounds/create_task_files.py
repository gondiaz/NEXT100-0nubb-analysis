import os
import subprocess
import pandas as pd
import numpy  as np
from math import ceil

# assumes activity in mBq
year = (3600. * 24. * 365)/1000.

background = "208Tl"
exposure = 40. * year
min_total_events = 100
min_sim_per_file = 1e6
max_sim_per_file = 1e7
min_events_per_file = 10
max_events_per_file = 100

template_filename = os.path.expandvars(f"$PWD/NEXT100_{background}.sh")
outjob_dir        = os.path.expandvars("$LUSTRE/NEXT100/{background}/tasks/")
outjob_filename   = os.path.join(outjob_dir, "task_{number}_{volume}.sh")
tables_filename   = os.path.expandvars("$PWD/activities_efficiencies.ods")

table = pd.read_excel(tables_filename, sheet_name=background).set_index("G4Volume")
table.loc[:,           "total"] = (table.TotalActivity*table.MCEfficiency*exposure).apply(np.ceil).astype(int)
# correct total
table.loc[:,           "total"] = np.maximum(table.total, min_total_events)
table.loc[:,       "total_sim"] = table.total/table.MCEfficiency
table.loc[:,    "sim_per_file"] = min_sim_per_file
table.loc[:, "events_per_file"] = np.minimum(table.sim_per_file*table.MCEfficiency, max_events_per_file)
table.loc[:, "events_per_file"] = np.maximum(table.events_per_file, min_events_per_file)
if background == "208Tl":
    table.loc["FIELD_RING", "events_per_file"] = 200
    table.loc[       "ICS", "events_per_file"] = 250
table.loc[:, "sim_per_file"]    = (table.events_per_file/table.MCEfficiency).apply(np.ceil).astype(int)
table.loc[:, "sim_per_file"]    = np.minimum(table.sim_per_file, max_sim_per_file)
table.loc[:, "events_per_file"] = (table.sim_per_file*table.MCEfficiency).apply(np.ceil).astype(int)
table.loc[:,       "nfiles"]    = (table.total_sim/table.sim_per_file) .apply(np.ceil).astype(int)

if __name__ == "__main__":

    template = open(template_filename).read()

    print(f"Creating {template_filename.split('/')[-1]} tasks...")

    for volume in table.index:
        os.makedirs( outjob_dir.format(background=background, volume=volume)
                   , exist_ok=True)

        sim_events_per_file = ceil(table.loc[volume].sim_per_file)
        ntasks              = ceil(table.loc[volume].nfiles)

        # # hardcoded to estimate efficiencies
        # sim_events_per_file = 100000
        # ntasks = 100

        for j in range(0, ntasks):
            filename = outjob_filename.format(background=background, volume=volume, number=(j+1))
            with open(filename, "x") as outfile:
                outfile.write(template.format(NEVENTS=sim_events_per_file, RNDSEED=(j+1), VOLUME=volume))
            os.chmod(filename, 0o744)

        print(f"Created {ntasks} tasks for {background}/{volume} with {sim_events_per_file} events")
