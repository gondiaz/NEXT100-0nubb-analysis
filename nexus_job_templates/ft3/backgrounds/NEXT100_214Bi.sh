#!/bin/bash

## Job options
NEVENTS={NEVENTS}
RNDSEED={RNDSEED}
STARTID=$(( (RNDSEED-1)*NEVENTS ))
VOLUME={VOLUME}

NODEOUTDIR="$LUSTRE_SCRATCH/$RNDSEED/$VOLUME/"
OUTDIR="$LUSTRE/NEXT100/214Bi/$VOLUME/nexus/"

OUTFILE="$OUTDIR/nexus_$((RNDSEED))_214Bi"

mkdir -p $NODEOUTDIR $OUTDIR

INI_MACRO="$NODEOUTDIR/nexus.init.$RNDSEED.mac"
CFG_MACRO="$NODEOUTDIR/nexus.config.$RNDSEED.mac"
DLY_MACRO="$NODEOUTDIR/nexus.dlyd.$RNDSEED.mac"

> $INI_MACRO
> $CFG_MACRO
> $DLY_MACRO

#------------------------------------
#--------- Init macro ---------------
#------------------------------------
# physics lists
echo "/PhysicsList/RegisterPhysics G4EmStandardPhysics_option4" >> $INI_MACRO
echo "/PhysicsList/RegisterPhysics G4DecayPhysics"              >> $INI_MACRO
echo "/PhysicsList/RegisterPhysics G4RadioactiveDecayPhysics"   >> $INI_MACRO
echo "/PhysicsList/RegisterPhysics G4StepLimiterPhysics"        >> $INI_MACRO

# geometry and generator
echo "/nexus/RegisterGeometry  Next100"                         >> $INI_MACRO
echo "/nexus/RegisterGenerator IonGenerator"                    >> $INI_MACRO

# actions
echo "/nexus/RegisterRunAction      DefaultRunAction"           >> $INI_MACRO
echo "/nexus/RegisterEventAction    DefaultEventAction"         >> $INI_MACRO
echo "/nexus/RegisterTrackingAction DefaultTrackingAction"      >> $INI_MACRO

# persistency
echo "/nexus/RegisterPersistencyManager PersistencyManager"     >> $INI_MACRO
echo "/nexus/RegisterMacro        $CFG_MACRO"                   >> $INI_MACRO
echo "/nexus/RegisterDelayedMacro $DLY_MACRO"                   >> $INI_MACRO


#------------------------------------
#--------- Config macro -------------
#------------------------------------
# verbosity
echo "/control/verbose  1"                               >> $CFG_MACRO
echo "/run/verbose      1"                               >> $CFG_MACRO
echo "/event/verbose    0"                               >> $CFG_MACRO
echo "/tracking/verbose 0"                               >> $CFG_MACRO

# generator
echo "/Generator/IonGenerator/atomic_number  83"         >> $CFG_MACRO
echo "/Generator/IonGenerator/mass_number   214"         >> $CFG_MACRO
echo "/Generator/IonGenerator/region        $VOLUME"     >> $CFG_MACRO

# actions
echo "/Actions/DefaultEventAction/energy_threshold 2.0 MeV"  >> $CFG_MACRO

# geometry
echo "/Geometry/Next100/max_step_size  1.  mm"        >> $CFG_MACRO
echo "/Geometry/Next100/pressure      13.5 bar"       >> $CFG_MACRO
echo "/Geometry/Next100/elfield       false"          >> $CFG_MACRO

# persistency
echo "/nexus/random_seed            $RNDSEED"   >> $CFG_MACRO
echo "/nexus/persistency/start_id   $STARTID"   >> $CFG_MACRO
echo "/nexus/persistency/outputFile $OUTFILE"   >> $CFG_MACRO
echo "/nexus/persistency/eventType  background" >> $CFG_MACRO


#-------------------------------------
#--------- Delayed macro -------------
#-------------------------------------
echo "/process/had/rdm/nucleusLimits 214 214 83 84" >> $DLY_MACRO


#---------------------------------
#--------- Run nexus -------------
#---------------------------------
start=`date +%s`

# load dependencies
source $STORE/NEXUS/loadmodules.sh

$STORE/NEXUS/nexus/bin/nexus -b -n $NEVENTS $INI_MACRO

end=`date +%s`
let deltatime=end-start
let hours=deltatime/3600
let minutes=(deltatime/60)%60
let seconds=deltatime%60
printf "Time spent: %d:%02d:%02d\n" $hours $minutes $seconds
