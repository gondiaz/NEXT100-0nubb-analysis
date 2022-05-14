"""
Assumes tasks are created at /path/tasks/ with filenames tasks_
"""

import os
import re
import glob
from math import ceil

job_basename  = "214Bi"
tasks_per_job = 10
tasks_dir     = os.path.expandvars("$LUSTRE/NEXT100/214Bi/tasks/")
logs_dir      = os.path.expandvars("$LUSTRE/logs/")

job_header = os.linesep.join(( "#!/bin/bash"
                             , "#SBATCH --job-name {jobname}"
                             , "#SBATCH --output   {output}"
                             , "#SBATCH --error    {error}"
                             , "#SBATCH --ntasks   {tasks_per_job}"
                             , "#SBATCH --time      06:00:00"    # short partition
                             , "#SBATCH --cpus-per-task 1"
                             , "#SBATCH --mem-per-cpu 3G"
                             , os.linesep))

job_task = "srun --ntasks 1 --exclusive --cpus-per-task 1 {task} &" + os.linesep
job_end  = "wait"                                                   + os.linesep

if __name__ == "__main__":

    jobs_dir = tasks_dir.replace("tasks", "jobs")
    os.makedirs(jobs_dir, exist_ok=True)

    get_file_number = lambda name: int(re.findall("[0-9]+", name.split("/")[-1])[0])
    get_volume_name = lambda name: "_".join(name.split("/")[-1].split("_")[2:]).split(".sh")[0]

    filenames = sorted( glob.glob(os.path.join(tasks_dir, "task_*.sh"))
                      , key=get_volume_name)

    # split task in volumes
    splited_in_volumes = []
    i = 0
    while (i<len(filenames)-1):
        chunk = []
        for j, filename in enumerate(filenames[i:]):
            vol  = get_volume_name(filename)
            chunk.append(filename)
            n = i+j+1
            if n == len(filenames): break
            nvol = get_volume_name(filenames[n])
            if vol != nvol: break
        i += len(chunk)
        splited_in_volumes.append(chunk)

    print(f"Creating {job_basename} jobs..")

    for task_filenames in splited_in_volumes:
        task_filenames = sorted(task_filenames, key=get_file_number)
        volume = get_volume_name(task_filenames[0])

        ntasks   = len(task_filenames)
        nbatches = ceil(ntasks/tasks_per_job)

        # write jobs
        for batch in range(0, nbatches):
            tasks_in_batch = task_filenames[batch*tasks_per_job:(batch+1)*tasks_per_job]

            # write job-header
            job = job_header.format( jobname= volume + "_" + str(batch+1) + job_basename
                                   , output = os.path.join(logs_dir, volume + "." + str(batch+1)+".out")
                                   , error  = os.path.join(logs_dir, volume + "." + str(batch+1)+".err")
                                   , tasks_per_job = len(tasks_in_batch))
            # write tasks
            for task in tasks_in_batch:
                job += job_task.format(task=task)

            # write end
            job += job_end

            # write to file
            filename = os.path.join(jobs_dir, f"job_{volume}_{batch+1}.sh")
            with open(filename, "x") as outfile:
                outfile.write(job)

        print(f"{nbatches} jobs created for volume {volume}")
