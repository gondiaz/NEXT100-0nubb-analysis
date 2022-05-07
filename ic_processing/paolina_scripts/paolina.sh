#!/bin/bash

#SBATCH --time 24:00:00          # Maximum execution time (HH:MM:SS)
#SBATCH --job-name pdata
#SBATCH -o /mnt/lustre/scratch/home/usc/ie/gdl/NEXUS/logs/%A_%a.out        # Standard output
#SBATCH -e /mnt/lustre/scratch/home/usc/ie/gdl/NEXUS/logs/%A_%a.err        # Standard error
#SBATCH --qos shared_short
#SBATCH --partition shared
#SBATCH -n 1
#SBATCH -N 1

start=`date +%s`
source $HOME/Software/ic_setup.sh

python paolina.py {in_filename} {out_filename}

end=`date +%s`
let deltatime=end-start
let hours=deltatime/3600
let minutes=(deltatime/60)%60
let seconds=deltatime%60
printf "Time spent: %d:%02d:%02d\n" $hours $minutes $seconds
