import os
import re
import glob
import numpy as np

job_basename  = "fits"
nexperiments  = 30 # experiments per job
njobs         = 60
tasks_per_job = 10
T12_0nubb     = np.arange(1, 6.1, 0.05)*1e+25
fit_type      = "typeII"
sel_filename  = os.path.expandvars("../create_pdfs/pdfs.h5")
out_filename  = os.path.expandvars("$LUSTRE/fits/{fit_type}/{t12}/outs/result_{file_number}.csv")
jobs_dir      = os.path.expandvars("$LUSTRE/fits/{fit_type}/{t12}/jobs/")
logs_dir      = os.path.expandvars("$LUSTRE/logs/{fit_type}/{t12}/")

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


    for t12 in T12_0nubb:
        t12 = np.format_float_scientific(t12, 2, unique=False)

        os.makedirs(os.path.dirname(out_filename).format(fit_type=fit_type, t12=t12), exist_ok=True)
        os.makedirs(                     jobs_dir.format(fit_type=fit_type, t12=t12), exist_ok=True)
        os.makedirs(                     logs_dir.format(fit_type=fit_type, t12=t12), exist_ok=True)

        print(f"Creating {job_basename} jobs for T12={t12} years..")

        # write jobs
        for j in range(0, njobs):

            # write job-header
            job = job_header.format( jobname= str(j) + "_" + job_basename
                                   , output = os.path.join(logs_dir.format(fit_type=fit_type, t12=t12), str(j)+".out")
                                   , error  = os.path.join(logs_dir.format(fit_type=fit_type, t12=t12), str(j)+".err")
                                   , tasks_per_job = tasks_per_job)
            # write tasks
            for task in range(j*tasks_per_job, (j+1)*tasks_per_job):
                outfile = out_filename.format(fit_type=fit_type, t12=t12, file_number=task)
                task = f"python experiment_and_fit.py -n {nexperiments} -s {sel_filename} -o {outfile} -T12 {t12} -t {fit_type}"
                job += job_task.format(task=task)

            # write end
            job += job_end

            # write to file
            filename = os.path.join(jobs_dir.format(fit_type=fit_type, t12=t12), f"job_{j}.sh")
            with open(filename, "x") as outfile:
                outfile.write(job)

        print(f"{njobs} jobs created")
