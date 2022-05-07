#!/bin/bash

#SBATCH --time 24:00:00          # Maximum execution time (HH:MM:SS)
#SBATCH --job-name bi
#SBATCH -o /mnt/lustre/scratch/home/usc/ie/gdl/NEXUS/logs/%A_%a.out        # Standard output
#SBATCH -e /mnt/lustre/scratch/home/usc/ie/gdl/NEXUS/logs/%A_%a.err        # Standard error
#SBATCH --qos shared_short
#SBATCH --partition shared
##SBATCH --qos amd-shared
##SBATCH --partition amd-shared
##SBATCH --qos cl-intel-shared
##SBATCH --partition cl-intel-shared
#SBATCH -n 1
#SBATCH -N 1

## Job options
FULLSIM=false
NEVENTS=100
REGION="TP_COPPER_PLATE"

RNDSEED=$(( SLURM_ARRAY_TASK_ID+1 ))
STARTID=$(( SLURM_ARRAY_TASK_ID*NEVENTS ))
NODEOUTDIR="$LUSTRE_SCRATCH/$SLURM_ARRAY_JOB_ID/$SLURM_ARRAY_TASK_ID/"
OUTFILE="$NODEOUTDIR/nexus_${SLURM_ARRAY_TASK_ID}_214Bi"

OUTDIR="$LUSTRE/NEXT100/214Bi/$REGION/nexus/"
mkdir -p $NODEOUTDIR $OUTDIR

INI_MACRO="$NODEOUTDIR/nexus.init.${SLURM_ARRAY_TASK_ID}.mac"
CFG_MACRO="$NODEOUTDIR/nexus.config.${SLURM_ARRAY_TASK_ID}.mac"
DLY_MACRO="$NODEOUTDIR/nexus.dlyd.${SLURM_ARRAY_TASK_ID}.mac"

#------------------------------------
#--------- Init macro ---------------
#------------------------------------
# physics lists
echo "/PhysicsList/RegisterPhysics G4EmStandardPhysics_option4" >> ${INI_MACRO}
echo "/PhysicsList/RegisterPhysics G4DecayPhysics"              >> ${INI_MACRO}
echo "/PhysicsList/RegisterPhysics G4RadioactiveDecayPhysics"   >> ${INI_MACRO}
echo "/PhysicsList/RegisterPhysics NexusPhysics"                >> ${INI_MACRO}
echo "/PhysicsList/RegisterPhysics G4StepLimiterPhysics"        >> ${INI_MACRO}
echo "/PhysicsList/RegisterPhysics G4OpticalPhysics"            >> ${INI_MACRO}

# geometry and generator
echo "/nexus/RegisterGeometry Next100OpticalGeometry"           >> ${INI_MACRO}
echo "/nexus/RegisterGenerator IonGenerator"                    >> ${INI_MACRO}

# actions
echo "/nexus/RegisterRunAction DefaultRunAction"                >> ${INI_MACRO}
echo "/nexus/RegisterEventAction DefaultEventAction"            >> ${INI_MACRO}
echo "/nexus/RegisterTrackingAction DefaultTrackingAction"      >> ${INI_MACRO}

# persistency
echo "/nexus/RegisterPersistencyManager PersistencyManager"     >> ${INI_MACRO}
echo "/nexus/RegisterMacro ${CFG_MACRO}"                        >> ${INI_MACRO}
echo "/nexus/RegisterDelayedMacro ${DLY_MACRO}"                 >> ${INI_MACRO}

#------------------------------------
#--------- Config macro -------------
#------------------------------------
# verbosity
echo "/run/verbose      0"                                      >> ${CFG_MACRO}
echo "/event/verbose    0"                                      >> ${CFG_MACRO}
echo "/tracking/verbose 0"                                      >> ${CFG_MACRO}

# generator
echo "/Generator/IonGenerator/atomic_number 83"                 >> ${CFG_MACRO}
echo "/Generator/IonGenerator/mass_number 214"                  >> ${CFG_MACRO}
echo "/Generator/IonGenerator/region ${REGION}"                 >> ${CFG_MACRO}

# actions
echo "/Actions/DefaultEventAction/energy_threshold 2.0 MeV"     >> ${CFG_MACRO}
echo "/Actions/DefaultEventAction/max_energy       3.0 MeV"     >> ${CFG_MACRO}

# geometry
echo "/Geometry/PmtR11410/time_binning 25. nanosecond"             >> ${CFG_MACRO}
echo "/Geometry/Next100/sipm_time_binning 1. microsecond"          >> ${CFG_MACRO}

echo "/Geometry/Next100/max_step_size     1. mm"                   >> ${CFG_MACRO}
echo "/Geometry/Next100/pressure          10.0 bar"                >> ${CFG_MACRO}
echo "/Geometry/Next100/sc_yield          25510. 1/MeV"            >> ${CFG_MACRO}
echo "/Geometry/Next100/drift_transv_diff 1.2 mm/sqrt(cm)"         >> ${CFG_MACRO}
echo "/Geometry/Next100/drift_long_diff   0.3 mm/sqrt(cm)"         >> ${CFG_MACRO}
echo "/Geometry/Next100/e_lifetime        12. ms"                  >> ${CFG_MACRO}
echo "/Geometry/Next100/EL_field          14. kilovolt/cm"         >> ${CFG_MACRO}
echo "/Geometry/Next100/elfield                        ${FULLSIM}" >> ${CFG_MACRO}

# physics
echo "/PhysicsList/Nexus/clustering                    ${FULLSIM}" >> ${CFG_MACRO}
echo "/PhysicsList/Nexus/drift                         ${FULLSIM}" >> ${CFG_MACRO}
echo "/PhysicsList/Nexus/electroluminescence           ${FULLSIM}" >> ${CFG_MACRO}
echo "/process/optical/processActivation Cerenkov      ${FULLSIM}" >> ${CFG_MACRO}
echo "/process/optical/processActivation Scintillation ${FULLSIM}" >> ${CFG_MACRO}

# persistency
echo "/nexus/random_seed            ${RNDSEED}" >> ${CFG_MACRO}
echo "/nexus/persistency/start_id   ${STARTID}" >> ${CFG_MACRO}
echo "/nexus/persistency/outputFile ${OUTFILE}" >> ${CFG_MACRO}
echo "/nexus/persistency/eventType  background" >> ${CFG_MACRO}

#-------------------------------------
#--------- Delayed macro -------------
#-------------------------------------
echo "/grdm/nucleusLimits 214 214 83 84" >> ${DLY_MACRO}


#---------------------------------
#--------- Run nexus -------------
#---------------------------------
start=`date +%s`

# load dependencies
source $STORE/NEXUS/loadmodules.sh

$STORE/NEXUS/nexus/bin/nexus -b -n ${NEVENTS} ${INI_MACRO}
cp "${OUTFILE}.h5" ${OUTDIR}

end=`date +%s`
let deltatime=end-start
let hours=deltatime/3600
let minutes=(deltatime/60)%60
let seconds=deltatime%60
printf "Time spent: %d:%02d:%02d\n" $hours $minutes $seconds
