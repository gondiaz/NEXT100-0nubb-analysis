"""
Assumes tasks are created at /path/tasks/ with filenames tasks_
"""

import os
import re
import glob
from math import ceil

job_basename  = "kr83m"
tasks_per_job = 5
tasks_dir     = os.path.expandvars("$LUSTRE/NEXT100/kr83m/tasks/")
logs_dir      = os.path.expandvars("$LUSTRE/logs/")

job_header = os.linesep.join(( "#!/bin/bash"
                             , "#SBATCH --job-name {jobname}"
                             , "#SBATCH --output   {output}"
                             , "#SBATCH --error    {error}"
                             , "#SBATCH --ntasks   {tasks_per_job}"
                             , "#SBATCH --time      00:10:00"
                             , "#SBATCH --cpus-per-task 1"
                             , "#SBATCH --mem-per-cpu 3G"
                             , os.linesep))

job_task = "srun --ntasks 1 --exclusive --cpus-per-task 1 {task} &" + os.linesep
job_end  = "wait"                                                   + os.linesep

if __name__ == "__main__":

    jobs_dir = tasks_dir.replace("tasks", "jobs")
    os.makedirs(jobs_dir, exist_ok=True)

    get_file_number = lambda name: int(re.findall("[0-9]+", name.split("/")[-1])[0])

    task_filenames = sorted( glob.glob(os.path.join(tasks_dir, "task_*.sh"))
                           , key=get_file_number)
    ntasks   = len(task_filenames)
    nbatches = ceil(ntasks/tasks_per_job)


    print(f"Creating {job_basename} jobs..")

    # write jobs
    for batch in range(0, nbatches):
        tasks_in_batch = task_filenames[batch*tasks_per_job:(batch+1)*tasks_per_job]

        # write job-header
        job = job_header.format( jobname= str(batch+1) + "_" + job_basename
                               , output = os.path.join(logs_dir, str(batch+1)+".out")
                               , error  = os.path.join(logs_dir, str(batch+1)+".err")
                               , tasks_per_job = len(tasks_in_batch))
        # write tasks
        for task in tasks_in_batch:
            job += job_task.format(task=task)

        # write end
        job += job_end

        # write to file
        filename = os.path.join(jobs_dir, f"job_{batch+1}.sh")
        with open(filename, "x") as outfile:
            outfile.write(job)

    print(f"{nbatches} jobs created")
