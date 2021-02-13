import os

#------------------------------------
#------- Configuration --------------
#------------------------------------
batchjob_filename = os.path.expandvars("$HOME/NEXT/NEXT100-0nubb-analysis/nexus_job_templates/NEXT100_PSF_generator.sh")

out_init_mac = os.path.expandvars("$PWD/test.init.mac")
out_conf_mac = os.path.expandvars("$PWD/test.config.mac")
out_dlyd_mac = os.path.expandvars("$PWD/test.dlyd.mac")

OUTFILE=os.path.expandvars("$PWD/nexus_test")
FULLSIM="false"
RNDSEED="1"
STARTID="0"
NPHOTONS="1"


#---------------------------------
#------- Generation --------------
#---------------------------------
if __name__ == "__main__":

    with open(batchjob_filename) as file:
        file = file.read()
    split_in_lines = file.splitlines()

    init_mac = [line.split('"')[1] for line in split_in_lines if "INI_MACRO" in line and line[:4] == "echo"]
    conf_mac = [line.split('"')[1] for line in split_in_lines if "CFG_MACRO" in line and line[:4] == "echo"]
    dlyd_mac = [line.split('"')[1] for line in split_in_lines if "DLY_MACRO" in line and line[:4] == "echo"]

    init_mac = "\n".join(init_mac)
    conf_mac = "\n".join(conf_mac)
    dlyd_mac = "\n".join(dlyd_mac)

    init_mac = init_mac.replace("${CFG_MACRO}", out_conf_mac)
    init_mac = init_mac.replace("${DLY_MACRO}", out_dlyd_mac)

    conf_mac = conf_mac.replace("/nexus/RegisterMacro ${CFG_MACRO}\n", "")
    conf_mac = conf_mac.replace("${NPHOTONS}", NPHOTONS)
    conf_mac = conf_mac.replace("${FULLSIM}", FULLSIM)
    conf_mac = conf_mac.replace("${RNDSEED}", RNDSEED)
    conf_mac = conf_mac.replace("${STARTID}", STARTID)
    conf_mac = conf_mac.replace("${OUTFILE}", OUTFILE)

    dlyd_mac = dlyd_mac.replace("/nexus/RegisterDelayedMacro ${DLY_MACRO}\n", "")

    with open(out_init_mac, "w") as init:
        init.write(init_mac)
    with open(out_conf_mac, "w") as conf:
        conf.write(conf_mac)
    with open(out_dlyd_mac, "w") as dlyd:
        dlyd.write(dlyd_mac)
