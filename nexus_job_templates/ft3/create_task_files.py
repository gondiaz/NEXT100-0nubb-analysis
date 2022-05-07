import os
import subprocess

njobs = 12
template_filename = os.path.expandvars("$PWD/NEXT100_Kr83m.sh")
outjob_dir        = os.path.expandvars("$LUSTRE/NEXT100/kr83m/tasks/")
outjob_filename   = os.path.join(outjob_dir, "task_{number}.sh")

os.makedirs(outjob_dir, exist_ok=True)

if __name__ == "__main__":

    template = open(template_filename).read()

    print(f"Creating {template_filename.split('/')[-1]} tasks...")

    for j in range(0, njobs):

        filename = outjob_filename.format(number=(j+1))

        with open(filename, "x") as outfile:
            outfile.write(template.format(RNDSEED=(j+1)))
        os.chmod(filename, 0o744)

    print(f"{njobs} tasks created")
