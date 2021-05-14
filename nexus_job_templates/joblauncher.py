import os
import glob
import subprocess
import numpy  as np
import pandas as pd

from time import sleep

def check_jobs(cmd, nmin=10, wait=1):
    j = nmin
    while j>nmin-1:
        j = subprocess.run(cmd, shell=True, capture_output=True)
        j = int(j.stdout)
        sleep(wait)

def rewrite_config_lines(splited, REGION, NEVENTS):
    for i, line in enumerate(splited):
        if line.startswith("NEVENTS="):
            splited[i] = f'NEVENTS={NEVENTS}'
        if line.startswith("REGION="):
            splited[i] = f'REGION="{REGION}"'
    return splited


bunch = 100
queue_state_command = "squeue -r |grep usciegdl |wc -l"
joblaunch_command   = "sbatch --array={nl}-{nu} {jobfilename}"
queue_limit = 190

event_type = "208Tl"
jobfilename    = os.path.expandvars(f"$PWD/NEXT100_{event_type}.sh")
tablesfilename = os.path.expandvars(f"$PWD/../fitting_utils/Efficiency_table.ods")

if (event_type == "214Bi") or (event_type == "208Tl"):
    table = pd.read_excel(tablesfilename, sheet_name=event_type)
else:
    raise Exception("Unknow event type")

if __name__ == "__main__":

    # ITERATE IN REGIONS and LAUNCH JOBS
    for region, df in table.groupby("Region"):
        nevents = int(df["Simulation events"])
        njobs   = int(df["Jobs"])
        with open(jobfilename, "r") as jobfile:
            splited = jobfile.read().splitlines()
            splited = rewrite_config_lines(splited, region, nevents)
        with open(jobfilename + ".temp", "w") as temp:
            temp.write("\n".join(splited))

        print(f"Launching region {region} with {nevents} events per job")
        print("-----------------------------------------------------------")
        ns = np.clip(np.arange(0, njobs + bunch, bunch), 0, njobs)
        for i, n in enumerate(ns[:-1]):
            check_jobs(queue_state_command, nmin=queue_limit-(ns[i+1]+1-n))
            #### launch job ####
            cmd = joblaunch_command.format(nl=n, nu=ns[i+1]-1, jobfilename=jobfilename + ".temp")
            print(cmd)
            # subprocess.run(cmd, shell=True)

        print("-----------------------------------------------------------")
        os.remove(jobfilename + ".temp")
