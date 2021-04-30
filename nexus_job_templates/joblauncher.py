import os
import glob
import subprocess
import numpy as np

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


queue_state_command = "squeue |grep usciegdl |wc -l"
joblaunch_command   = "sbatch --array={nl}-{nu} {jobfilename}"
queue_limit = 1

event_type = "214Bi"
jobfilename = os.path.expandvars(f"$HOME/NEXT/NEXT100-0nubb-analysis/nexus_job_templates/NEXT100_{event_type}.sh")

# time factor
f = 3600*24*30*6
if (event_type == "214Bi"):
    REGIONS = {"TP_COPPER_PLATE"  : int(f*1.99e-4),
               "SIPM_BOARD"       : int(f*8.10e-3),
               "EP_COPPER_PLATE"  : int(f*6.45e-4),
               "SAPPHIRE_WINDOW"  : int(f*2.51e-3),
               "OPTICAL_PAD"      : int(f*2.82e-3),
               "INTERNAL_PMT_BASE": int(f*4.20e-2),
               "LIGHT_TUBE"       : int(f*1.09e-2)
               }
elif (event_type == "208Tl"):
    REGIONS = {"TP_COPPER_PLATE"  : int(f*6.81e-5),
               "SIPM_BOARD"       : int(f*1.30e-3),
               "EP_COPPER_PLATE"  : int(f*2.20e-4),
               "SAPPHIRE_WINDOW"  : int(f*3.56e-4),
               "OPTICAL_PAD"      : int(f*8.31e-4),
               "INTERNAL_PMT_BASE": int(f*5.35e-2),
               "LIGHT_TUBE"       : int(f*1.51e-3)
               }
else:
    REGIONS = {"NO_REGION": 300}


njobs = 250
bunch = 200
if __name__ == "__main__":

    # ITERATE IN REGIONS and LAUNCH JOBS
    for REGION in REGIONS:
        with open(jobfilename, "r") as jobfile:
            splited = jobfile.read().splitlines()
            splited = rewrite_config_lines(splited, REGION, REGIONS[REGION])
        with open(jobfilename + ".temp", "w") as temp:
            temp.write("\n".join(splited))

        print(f"Launching region {REGION} with {REGIONS[REGION]/f*1e3} mBq")
        print("-----------------------------------------------------------")
        ns = np.clip(np.arange(0, njobs + bunch, bunch), 0, njobs)
        for i, n in enumerate(ns[:-1]):
            check_jobs(queue_state_command, nmin=queue_limit)
            #### launch job ####
            cmd = joblaunch_command.format(nl=n, nu=ns[i+1]-1, jobfilename=jobfilename + ".temp")
            print(cmd)
            # subprocess.run(cmd, shell=True)

        print("-----------------------------------------------------------")
        os.remove(jobfilename + ".temp")
