import os
import sys
import glob
import subprocess

from time import sleep

def check_jobs(cmd, nmin=10, wait=1):
    j = nmin
    while j>nmin-1:
        j = subprocess.run(cmd, shell=True, capture_output=True)
        j = int(j.stdout)
        sleep(wait)

queue_state_command = "squeue |grep usciegdl |wc -l"
joblaunch_command   = "sbatch {jobfilename}"
queue_limit = 100

in_dir  = os.path.expandvars("")
out_dir = os.path.expandvars("")

os.makedirs(out_dir, exist_ok=True)
get_file_number = lambda filename: int(filename.split("/")[-1].split("_")[1])
filenames = sorted(glob.glob(in_dir + "/*.h5"), key=get_file_number)

if __name__ == "__main__":

    for i, filename in enumerate(filenames, 1):
        check_jobs(queue_state_command, nmin=queue_limit)

        sys.stdout.write(f"Launching {i}/{len(filenames)} \n")
        sys.stdout.flush()

        out_filename = out_dir + f"/pdata_{get_file_number(filename)}.h5"

        #create and run paolina job
        with open("paolina.sh", "r") as jobfile:
            job = jobfile.read().format(in_filename  = filename,
                                        out_filename = out_filename)
        temp_jobname = "paolina.sh.temp"
        with open(temp_jobname, "w") as jobfile:
            jobfile.write(job)

        subprocess.run(joblaunch_command.format(jobfilename=temp_jobname), shell=True)
        os.remove(temp_jobname)
