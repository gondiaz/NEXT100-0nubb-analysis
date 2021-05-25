#!/bin/bash

#SBATCH --time 02:00:00          # Maximum execution time (HH:MM:SS)
#SBATCH --job-name Th
#SBATCH -o /home/gdiaz/DEMO_Run8/logs/%A_%a.out        # Standard output
#SBATCH -e /home/gdiaz/DEMO_Run8/logs/%A_%a.err        # Standard error
#SBATCH --partition p9short48
#SBATCH -n 1
#SBATCH -N 1

MACROSDIR="$HOME/DEMO_Run8/macros/"
OUTPATH="$HOME/DEMO_Run8/"

## Job options
FULLSIM=false
NEVENTS=10000
RNDSEED=$(( SLURM_ARRAY_TASK_ID+1 ))
STARTID=$(( SLURM_ARRAY_TASK_ID*NEVENTS ))
OUTDIR="$OUTPATH/Tlde/nexus/"

mkdir -p $MACROSDIR $OUTDIR

OUTFILE="$OUTDIR/nexus_${SLURM_ARRAY_TASK_ID}_tlde"

INI_MACRO="$MACROSDIR/nexus.init.${SLURM_ARRAY_TASK_ID}.mac"
CFG_MACRO="$MACROSDIR/nexus.config.${SLURM_ARRAY_TASK_ID}.mac"

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
echo "/nexus/RegisterGeometry NextDemo"                         >> ${INI_MACRO}
echo "/nexus/RegisterGenerator IonGenerator"                    >> ${INI_MACRO}

# actions
echo "/nexus/RegisterRunAction DefaultRunAction"                >> ${INI_MACRO}
echo "/nexus/RegisterEventAction DefaultEventAction"            >> ${INI_MACRO}
echo "/nexus/RegisterTrackingAction DefaultTrackingAction"      >> ${INI_MACRO}

# persistency
echo "/nexus/RegisterPersistencyManager PersistencyManager"     >> ${INI_MACRO}
echo "/nexus/RegisterMacro ${CFG_MACRO}"                        >> ${INI_MACRO}



#------------------------------------
#--------- Config macro -------------
#------------------------------------
# verbosity
echo "/run/verbose      0"                                      >> ${CFG_MACRO}
echo "/event/verbose    0"                                      >> ${CFG_MACRO}
echo "/tracking/verbose 0"                                      >> ${CFG_MACRO}
echo "/tracking/verbose 0"                                      >> ${CFG_MACRO}

# generator
echo "/Generator/IonGenerator/region       AD_HOC"     >> ${CFG_MACRO}
echo "/Geometry/NextDemo/specific_vertex_X 0.0 mm"     >> ${CFG_MACRO}
echo "/Geometry/NextDemo/specific_vertex_Y 152.0 mm"   >> ${CFG_MACRO}
echo "/Geometry/NextDemo/specific_vertex_Z 110.0 mm"   >> ${CFG_MACRO}  #Z=110.0 mm or Z=200.0 mm (Tl)
echo "/Generator/IonGenerator/atomic_number 81"        >> ${CFG_MACRO}
echo "/Generator/IonGenerator/mass_number  208"        >> ${CFG_MACRO}

# geometry
echo "/Geometry/PmtR11410/time_binning 25. nanosecond"            >> ${CFG_MACRO}
echo "/Geometry/NextDemo/sipm_time_binning 1. microsecond"        >> ${CFG_MACRO}

echo "/Geometry/NextDemo/config    run8"                          >> ${CFG_MACRO}
echo "/Geometry/NextDemo/pressure  8.50 bar"                      >> ${CFG_MACRO}
echo "/Geometry/NextDemo/EL_field_intensity 14.0 kilovolt/cm"     >> ${CFG_MACRO}
echo "/Geometry/NextDemo/max_step_size 1. mm"                     >> ${CFG_MACRO}
echo "/Geometry/NextDemo/elfield                      ${FULLSIM}" >> ${CFG_MACRO}
echo "/Geometry/NextDemo/sc_yield             25510 1/MeV"        >> ${CFG_MACRO}
echo "/Geometry/NextDemo/drift_transv_diff    1.0 mm/sqrt(cm)"    >> ${CFG_MACRO}
echo "/Geometry/NextDemo/drift_long_diff      0.3 mm/sqrt(cm)"    >> ${CFG_MACRO}
echo "/Geometry/NextDemo/ELlong_diff          0.0 mm/sqrt(cm)"    >> ${CFG_MACRO}

# actions
echo "/Actions/DefaultEventAction/energy_threshold 1.4 MeV"     >> ${CFG_MACRO}
echo "/Actions/DefaultEventAction/max_energy       1.8 MeV"     >> ${CFG_MACRO}

# physics
echo "/PhysicsList/Nexus/clustering                    ${FULLSIM}" >> ${CFG_MACRO}
echo "/PhysicsList/Nexus/drift                         ${FULLSIM}" >> ${CFG_MACRO}
echo "/PhysicsList/Nexus/electroluminescence           ${FULLSIM}" >> ${CFG_MACRO}
echo "/process/optical/processActivation Cerenkov      ${FULLSIM}" >> ${CFG_MACRO}
echo "/process/optical/processActivation Scintillation ${FULLSIM}" >> ${CFG_MACRO}
echo "/PhysicsList/Nexus/photoelectric                 ${FULLSIM}" >> ${CFG_MACRO}

# persistency
echo "/nexus/random_seed            ${RNDSEED}" >> ${CFG_MACRO}
echo "/nexus/persistency/start_id   ${STARTID}" >> ${CFG_MACRO}
echo "/nexus/persistency/outputFile ${OUTFILE}" >> ${CFG_MACRO}



#---------------------------------
#--------- Run nexus -------------
#---------------------------------
start=`date +%s`

source $HOME/Software/setups/nexus_setup.sh

/software/nexus/bin/nexus -b -n ${NEVENTS} ${INI_MACRO}

rm -rf ${INI_MACRO}
rm -rf ${CFG_MACRO}

end=`date +%s`
let deltatime=end-start
let hours=deltatime/3600
let minutes=(deltatime/60)%60
let seconds=deltatime%60
printf "Time spent: %d:%02d:%02d\n" $hours $minutes $seconds
