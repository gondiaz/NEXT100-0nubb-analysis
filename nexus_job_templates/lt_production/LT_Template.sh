#!/bin/bash

#SBATCH --time 18:00:00          # Maximum execution time (HH:MM:SS)
#SBATCH --job-name LT
#SBATCH -o /mnt/lustre/scratch/home/usc/ie/gdl/NEXUS/logs/%A_%a.out        # Standard output
#SBATCH -e /mnt/lustre/scratch/home/usc/ie/gdl/NEXUS/logs/%A_%a.err        # Standard error
##SBATCH --qos shared_short
##SBATCH --partition shared
##SBATCH --qos amd-shared
##SBATCH --partition amd-shared
#SBATCH --qos cl-intel-shared
#SBATCH --partition cl-intel-shared
#SBATCH -n 1
#SBATCH -N 1


## Job options
NPHOTONS=1000000
NEVENTS=100
RNDSEED="{RNDSEED}"
STARTID=0
X="{X}"
Y="{Y}"
Z="{Z}"
NODEOUTDIR="$LUSTRE_SCRATCH/$SLURM_ARRAY_JOB_ID/$SLURM_ARRAY_TASK_ID/"
OUTFILE="$NODEOUTDIR/nexus_x_{X}_y_{Y}_z_{Z}_next100LT"

OUTDIR="$LUSTRE/NEXUS/LT_generation/NEXT100/$Z/prod/"
mkdir -p $NODEOUTDIR $OUTDIR

INI_MACRO="$NODEOUTDIR/nexus.init.$SLURM_ARRAY_TASK_ID.mac"
CFG_MACRO="$NODEOUTDIR/nexus.config.$SLURM_ARRAY_TASK_ID.mac"


#------------------------------------
#--------- Init macro ---------------
#------------------------------------
# physics lists
echo "/PhysicsList/RegisterPhysics G4EmStandardPhysics_option4" >> $INI_MACRO
echo "/PhysicsList/RegisterPhysics G4DecayPhysics"              >> $INI_MACRO
echo "/PhysicsList/RegisterPhysics G4RadioactiveDecayPhysics"   >> $INI_MACRO
echo "/PhysicsList/RegisterPhysics NexusPhysics"                >> $INI_MACRO
echo "/PhysicsList/RegisterPhysics G4StepLimiterPhysics"        >> $INI_MACRO
echo "/PhysicsList/RegisterPhysics G4OpticalPhysics"            >> $INI_MACRO

# geometry and generator
echo "/Geometry/RegisterGeometry NEXT100_OPT"                   >> $INI_MACRO
echo "/Generator/RegisterGenerator SCINTILLATION"               >> $INI_MACRO

# actions
echo "/Actions/RegisterTrackingAction LIGHT_TABLE"              >> $INI_MACRO

# persistency
echo "/nexus/RegisterMacro $CFG_MACRO"                          >> $INI_MACRO

# # ACTIONS
# echo "/Actions/RegisterRunAction      DEFAULT"                  >> $INI_MACRO
# echo "/Actions/RegisterEventAction    SAVE_ALL"                 >> $INI_MACRO
# echo "/Actions/RegisterTrackingAction DEFAULT"                  >> $INI_MACRO
# echo "/Actions/RegisterSteppingAction ANALYSIS"                 >> $INI_MACRO


#------------------------------------
#--------- Config macro -------------
#------------------------------------
# verbosity
echo "/run/verbose      0"                                      >> $CFG_MACRO
echo "/event/verbose    0"                                      >> $CFG_MACRO
echo "/tracking/verbose 0"                                      >> $CFG_MACRO
echo "/tracking/verbose 0"                                      >> $CFG_MACRO

# generator
echo "/Generator/ScintGenerator/region      AD_HOC"             >> $CFG_MACRO
echo "/Generator/ScintGenerator/nphotons   $NPHOTONS"           >> $CFG_MACRO
echo "/Geometry/Next100/specific_vertex_X  $X mm"               >> $CFG_MACRO
echo "/Geometry/Next100/specific_vertex_Y  $Y mm"               >> $CFG_MACRO
echo "/Geometry/Next100/specific_vertex_Z  $Z mm"               >> $CFG_MACRO

# geometry
# echo "/Geometry/PmtR11410/time_binning 1. nanosecond"           >> $CFG_MACRO
# echo "/Geometry/SiPMSensl/time_binning 1. microsecond"          >> $CFG_MACRO

# persistency
echo "/nexus/random_seed            $RNDSEED" >> $CFG_MACRO
echo "/nexus/persistency/start_id   $STARTID" >> $CFG_MACRO
echo "/nexus/persistency/outputFile $OUTFILE" >> $CFG_MACRO


#---------------------------------
#--------- Run nexus -------------
#---------------------------------
start=`date +%s`

# load dependencies
source $STORE/NEXUS/loadmodules.sh

$STORE/NEXUS/nexus/bin/nexus -b -n $NEVENTS $INI_MACRO
cp "$OUTFILE.h5" $OUTDIR

end=`date +%s`
let deltatime=end-start
let hours=deltatime/3600
let minutes=(deltatime/60)%60
let seconds=deltatime%60
printf "Time spent: %d:%02d:%02d\n" $hours $minutes $seconds
