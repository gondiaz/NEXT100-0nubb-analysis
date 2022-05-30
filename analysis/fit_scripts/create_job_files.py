"""
Assumes tasks are created at /path/tasks/ with filenames tasks_
"""

import os
import re
import glob
from math import ceil

job_basename  = "fits"
nexperiments  = 60 # experiments per job
njobs         = 10
tasks_per_job = 10
T12_0nubb     = 1e+25
out_filename  = os.path.expandvars("$PWD/outs/result_{file_number}.csv")
jobs_dir      = os.path.expandvars("$PWD/jobs")
logs_dir      = os.path.expandvars("$LUSTRE/logs/")
os.makedirs(jobs_dir, exist_ok=True)
os.makedirs(os.path.dirname(out_filename), exist_ok=True)

job_header = os.linesep.join(( "#!/bin/bash"
                             , "#SBATCH --job-name {jobname}"
                             , "#SBATCH --output   {output}"
                             , "#SBATCH --error    {error}"
                             , "#SBATCH --ntasks   {tasks_per_job}"
                             , "#SBATCH --time      01:00:00"
                             , "#SBATCH --cpus-per-task 1"
                             , "#SBATCH --mem-per-cpu 3G"
                             , ""
                             , "source $STORE/ic_setup.sh"
                             , ""
                             , "start=`date +%s`"
                             , os.linesep))

job_task = "srun --ntasks 1 --exclusive --cpus-per-task 1 {task} &" + os.linesep
job_end  = "wait"                                                   + os.linesep
job_end += """
end=`date +%s`
let deltatime=end-start
let hours=deltatime/3600
let minutes=(deltatime/60)%60
let seconds=deltatime%60
printf 'Time spent: %d:%02d:%02d\\n' $hours $minutes $seconds
"""

if __name__ == "__main__":

    print(f"Creating {job_basename} jobs..")

    # write jobs
    for j in range(0, njobs):

        # write job-header
        job = job_header.format( jobname= str(j) + "_" + job_basename
                               , output = os.path.join(logs_dir, str(j)+".out")
                               , error  = os.path.join(logs_dir, str(j)+".err")
                               , tasks_per_job = tasks_per_job)
        # write tasks
        for task in range(j*tasks_per_job, (j+1)*tasks_per_job):
            outfile = out_filename.format(file_number=task)
            task = f"python experiment_and_fit.py -n {nexperiments} -o {outfile} -T12 {T12_0nubb}"
            job += job_task.format(task=task)

        # write end
        job += job_end

        # write to file
        filename = os.path.join(jobs_dir, f"job_{j}.sh")
        with open(filename, "x") as outfile:
            outfile.write(job)

    print(f"{njobs} jobs created")
