import os
import glob
import numpy as np

#------------------------
#----- Configuration ----
#------------------------
template   = os.path.expandvars("$PWD/LT_Template.sh")
jobsoutdir = os.path.expandvars("$LUSTRE/NEXUS/LT_generation/NEXT100/{z}/jobs/")

z    = np.array([-5.5])
rmax = 492
ds   = 50

#-----------------------------
#----- Create grid points ----
#-----------------------------
X = np.arange(-rmax, rmax + ds, ds)
Y = np.arange(-rmax, rmax + ds, ds)
x, y = np.meshgrid(X, Y)
r = (x**2 + y**2)**0.5
sel = r<=rmax
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

    for i, pos in enumerate(zip(x, y)):
        x_, y_ = pos
        filename = os.path.join(jobdir, f"nexus_x_{x_}_y_{y_}_z_{z_}_next100LT.sh")
        with open(filename, "w") as file:
            file.write(Template.format(RNDSEED=zidx + i, X=x_, Y=y_, Z=z_))
    zidx +=1
