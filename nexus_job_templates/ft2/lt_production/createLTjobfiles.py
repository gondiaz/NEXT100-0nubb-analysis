import os
import glob
import numpy as np

#------------------------
#----- Configuration ----
#------------------------
template   = os.path.expandvars("$PWD/LT_Template.sh")
jobsoutdir = os.path.expandvars("$LUSTRE/NEXT100/LightTables/pmt/jobs/{z}")

z    = np.array([-5.0])
rmax = 492
n  = 50
dr = 2

#-----------------------------
#----- Create grid points ----
#-----------------------------
X = np.round(np.linspace(-(rmax-dr), (rmax-dr), n), 2)
x, y = np.meshgrid(X, X)
r = (x**2 + y**2)**0.5
sel = r<rmax
x, y = x[sel], y[sel]

#-----------------------------
#----- Create job files ------
#-----------------------------
Template = open(template).read()
zidx = 0
while zidx<len(z):
    z_ = z[zidx]

    jobdir = jobsoutdir.format(z=z_)
    print("Creating jobs in:", jobdir)
    os.makedirs(jobdir, exist_ok=True)

    for i, pos in enumerate(zip(x, y), 1):
        x_, y_ = pos
        filename = os.path.join(jobdir, f"nexus_x_{x_}_y_{y_}_z_{z_}_LT.sh")
        with open(filename, "w") as file:
            file.write(Template.format(RNDSEED=zidx + i, X=x_, Y=y_, Z=z_))
    zidx +=1
