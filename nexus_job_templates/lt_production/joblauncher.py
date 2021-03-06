import os
import glob
import subprocess
from time import sleep


jobsdir   = os.path.expandvars("$LUSTRE/NEXUS/LT_generation/NEXT100/-5.5/jobs/")
filenames = glob.glob(jobsdir + "*.sh")


queue_state_command = "squeue -r |grep usciegdl |wc -l"
joblaunch_command   = "sbatch {filename}"
queue_limit = 99


def check_jobs(cmd, nmin=10, wait=1):
    j = nmin
    while j>nmin-1:
        j = subprocess.run(cmd, shell=True, capture_output=True)
        j = int(j.stdout)
        sleep(wait)

#-------------------
#----- Launch ------
#-------------------
for filename in filenames:

    check_jobs(queue_state_command, nmin=queue_limit)

    cmd = joblaunch_command.format(filename = filename)
    print("Launching job:", filename)
    subprocess.run(cmd, shell=True)
