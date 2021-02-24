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

queue_state_command = "squeue |grep usciegdl |wc -l"
joblaunch_command   = "sbatch --array={nl}-{nu} {jobfilename}"
queue_limit = 1

jobfilename = os.path.expandvars("$HOME/NEXT100-0nubb-analysis/nexus_job_templates/NEXT100_Kr83m.sh")

####################
##### LAUNCHER #####
####################
ns = np.arange(500, 1000 + 100, 100)
print(ns)

for n in ns:
    check_jobs(queue_state_command, nmin=queue_limit)
    #### launch job ####
    cmd = joblaunch_command.format(nl=n, nu=n+99, jobfilename=jobfilename)
    print(cmd)
    subprocess.run(cmd, shell=True)
