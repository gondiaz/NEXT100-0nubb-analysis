#!/bin/bash

## Job options
NEVENTS=450000 # efficiency 2.2e-5 for deposited energy between 2.4-2.5 MeV
RNDSEED={RNDSEED}
STARTID=$(( (RNDSEED-1)*NEVENTS ))

NODEOUTDIR="$LUSTRE_SCRATCH/$RNDSEED/"
OUTDIR="$LUSTRE/NEXT100/muons/nexus/"

OUTFILE="$NODEOUTDIR/nexus_$((RNDSEED))_muon"

mkdir -p $NODEOUTDIR $OUTDIR

INI_MACRO="$NODEOUTDIR/nexus.init.$RNDSEED.mac"
CFG_MACRO="$NODEOUTDIR/nexus.config.$RNDSEED.mac"
DLY_MACRO="$NODEOUTDIR/nexus.delayed.$RNDSEED.mac"

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
echo "/PhysicsList/RegisterPhysics G4EmExtraPhysics"            >> $INI_MACRO
echo "/PhysicsList/RegisterPhysics G4HadronElasticPhysicsHP"    >> $INI_MACRO
echo "/PhysicsList/RegisterPhysics G4HadronPhysicsQGSP_BERT_HP" >> $INI_MACRO
echo "/PhysicsList/RegisterPhysics G4StoppingPhysics"           >> $INI_MACRO
echo "/PhysicsList/RegisterPhysics G4IonPhysics"                >> $INI_MACRO
echo "/PhysicsList/RegisterPhysics G4StepLimiterPhysics"        >> $INI_MACRO

echo "/physics_lists/em/MuonNuclear true"                       >> $INI_MACRO

# geometry and generator
echo "/nexus/RegisterGeometry  Next100"                         >> $INI_MACRO
echo "/nexus/RegisterGenerator MuonAngleGenerator"              >> $INI_MACRO

# actions
echo "/nexus/RegisterRunAction      DefaultRunAction"           >> $INI_MACRO
echo "/nexus/RegisterEventAction    DefaultEventAction"         >> $INI_MACRO
echo "/nexus/RegisterTrackingAction DefaultTrackingAction"      >> $INI_MACRO

# persistency
echo "/nexus/RegisterPersistencyManager PersistencyManager"     >> $INI_MACRO
echo "/nexus/RegisterDelayedMacro $DLY_MACRO"                   >> $INI_MACRO
echo "/nexus/RegisterMacro $CFG_MACRO"                          >> $INI_MACRO


#------------------------------------
#--------- Config macro -------------
#------------------------------------
# verbosity
echo "/control/verbose  1"                               >> $CFG_MACRO
echo "/run/verbose      1"                               >> $CFG_MACRO
echo "/event/verbose    0"                               >> $CFG_MACRO
echo "/tracking/verbose 0"                               >> $CFG_MACRO

# generator
echo "/Generator/MuonAngleGenerator/region     HALLA_OUTER"   >> $CFG_MACRO
echo "/Generator/MuonAngleGenerator/angles_on  true"          >> $CFG_MACRO
echo "/Generator/MuonAngleGenerator/azimuth_rotation 150 deg" >> $CFG_MACRO
echo "/Generator/MuonAngleGenerator/angle_file $STORE/NEXUS/nexus/data/SimulatedMuonsProposalMCEq.csv" >> $CFG_MACRO
echo "/Generator/MuonAngleGenerator/angle_dist za"           >> $CFG_MACRO
echo "/Generator/MuonAngleGenerator/max_energy 2000 GeV"     >> $CFG_MACRO

# actions
echo "/Actions/DefaultEventAction/min_energy 2.4 MeV"        >> $CFG_MACRO
echo "/Actions/DefaultEventAction/max_energy 2.5 MeV"        >> $CFG_MACRO

# geometry
echo "/Geometry/Next100/max_step_size  1.  mm"        >> $CFG_MACRO
echo "/Geometry/Next100/pressure      13.5 bar"       >> $CFG_MACRO
echo "/Geometry/Next100/elfield       false"          >> $CFG_MACRO
echo "/Geometry/Next100/lab_walls     true"           >> $CFG_MACRO

# persistency
echo "/nexus/random_seed            $RNDSEED"       >> $CFG_MACRO
echo "/nexus/persistency/start_id   $STARTID"       >> $CFG_MACRO
echo "/nexus/persistency/outputFile $OUTFILE"       >> $CFG_MACRO
echo "/nexus/persistency/eventType  background"     >> $CFG_MACRO

#------------------------------------
#--------- Delayed macro ------------
#------------------------------------
echo "/process/had/rdm/nucleusLimits 137 137 54 54"  >> $DLY_MACRO
echo "/process/em/fluo         false"                >> $DLY_MACRO
echo "/process/em/auger        false"                >> $DLY_MACRO
echo "/process/em/augerCascade false"                >> $DLY_MACRO
echo "/process/em/pixe         false"                >> $DLY_MACRO



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
