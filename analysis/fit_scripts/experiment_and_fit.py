import os
import argparse
import tables as tb
import numpy  as np
import pandas as pd
os.environ["ZFIT_DISABLE_TF_WARNINGS"] = "1"
import zfit
zfit.settings.changed_warnings.all = False
from invisible_cities.database.load_db     import RadioactivityData
from invisible_cities.core.system_of_units import year, s, kg, dalton, mBq, m, cm

# Experiment config
parser = argparse.ArgumentParser(description="Run experiments and fits")
parser.add_argument(  "-n", dest="Nexperiments", type=  int, help="number of experiments"  , required=True)
parser.add_argument(  "-s", dest="pdf_filename", type=  str, help="number of experiments"  , required=True)
parser.add_argument(  "-o", dest="out_filename", type=  str, help="output filename"        , required=True)
parser.add_argument("-T12", dest=   "T12_0nubb", type=float, help="0nubb half-life (years)", required=True)
parser.add_argument(  "-t", dest=    "fit_type", type=  str, help="fit type"               , required=True)
args = parser.parse_args()

Nexperiments = args.Nexperiments
pdf_filename = os.path.expandvars(args.pdf_filename)
out_filename = os.path.expandvars(args.out_filename)
T12_0nubb    = args.T12_0nubb
fit_type     = args.fit_type

enrichment = 0.9
xenon_mass = 71.5 * kg
exposure   = 3.
detector_db = "next100"

# PDFs
def create_pdf(array, obs, obs_ext):
    data = zfit.Data.from_numpy (obs=obs_ext, array=array)
    pdf  = zfit.pdf.KDE1DimExact(obs=obs, data=data, bandwidth="adaptive_zfit")
    return pdf

energy_obs_ext = zfit.Space("energy", limits=(2.40, 2.50))
energy_obs     = zfit.Space("energy", limits=(2.42, 2.48))
eblob2_obs     = zfit.Space("eblob2", limits=(0.00, 1.20))

eff_df = pd.read_hdf(pdf_filename, "efficiencies")
with tb.open_file(pdf_filename) as hdf:
    pdf_energy_bb = create_pdf(getattr(hdf.root.energy, "0nubb").read(), energy_obs, energy_obs_ext)
    pdf_energy_Bi = create_pdf(getattr(hdf.root.energy, "214Bi").read(), energy_obs, energy_obs_ext)
    pdf_energy_Tl = create_pdf(getattr(hdf.root.energy, "208Tl").read(), energy_obs, energy_obs_ext)
    pdf_energy_Xe = create_pdf(getattr(hdf.root.energy, "137Xe").read(), energy_obs, energy_obs_ext)

    if fit_type == "typeIII":
        pdf_energy_bb_bkg = create_pdf(getattr(hdf.root.energy, "0nubb").read(), energy_obs, energy_obs_ext)
        pdf_energy_Bi_bkg = create_pdf(getattr(hdf.root.energy, "214Bi").read(), energy_obs, energy_obs_ext)
        pdf_energy_Tl_bkg = create_pdf(getattr(hdf.root.energy, "208Tl").read(), energy_obs, energy_obs_ext)
        pdf_energy_Xe_bkg = create_pdf(getattr(hdf.root.energy, "137Xe").read(), energy_obs, energy_obs_ext)

    pdf_eblob2_bb = create_pdf(getattr(hdf.root.eblob2, "0nubb").read(), eblob2_obs, eblob2_obs)
    pdf_eblob2_Bi = create_pdf(getattr(hdf.root.eblob2, "214Bi").read(), eblob2_obs, eblob2_obs)
    pdf_eblob2_Tl = create_pdf(getattr(hdf.root.eblob2, "208Tl").read(), eblob2_obs, eblob2_obs)
    pdf_eblob2_Xe = create_pdf(getattr(hdf.root.eblob2, "137Xe").read(), eblob2_obs, eblob2_obs)

pdf_bb = zfit.pdf.ProductPDF([pdf_energy_bb, pdf_eblob2_bb])
pdf_Tl = zfit.pdf.ProductPDF([pdf_energy_Tl, pdf_eblob2_Tl])
pdf_Bi = zfit.pdf.ProductPDF([pdf_energy_Bi, pdf_eblob2_Bi])
pdf_Xe = zfit.pdf.ProductPDF([pdf_energy_Xe, pdf_eblob2_Xe])


muon_flux = 0.78 * 5.26e-3 /(m**2 * s)
R     = 7.64 * m
theta =  np.arctan(R / (86 * cm + 207.6 * cm))
A     = (2.*np.pi-theta) * R * (5.0 * m)
muon_activity = muon_flux * A /mBq

enrichment = 0.9
xenon_mass = 71.5 * kg
N0 = enrichment*(xenon_mass/(136. * dalton))

# activities
act_df, _ = RadioactivityData("next100")
act_df.loc[len(act_df)] = (   "ACTIVE", "137Xe", muon_activity*3.965e-05) # Xe137 per muon
act_df = act_df.set_index(["Isotope", "G4Volume"])
# simulated exposure
eff_df["exposure"] = eff_df.nsim / (act_df.TotalActivity * mBq) /year
# signal eff
signal_eff = eff_df.loc[("0nubb", "ACTIVE")].npdf / eff_df.loc[("0nubb", "ACTIVE")].nsim
eff_df.drop(("0nubb", "ACTIVE"), inplace=True)
# rates
rates = eff_df.npdf / eff_df.exposure
rates = rates.groupby(level=0).sum()
rates.loc["0nubb"] = N0 * (np.log(2)/T12_0nubb) * signal_eff

nevents = rates * exposure

# FIT model
N = int(rates.sum()*10)
nbb = zfit.Parameter("nbb", 1, 0, N)
nTl = zfit.Parameter("nTl", 1, 0, N)
nBi = zfit.Parameter("nBi", 1, 0, N)
nXe = zfit.Parameter("nXe", 1, 0, N)

# different fit strategies:
#  - typeI  : signal cut on Eb2 and fit to energy
#  - typeII : no cut, combined fit to energy and eblob2
#  - typeIII: cut on background and combined energy fit for background selection with no-cut
if fit_type == "typeI":
    pdf_energy_bb.set_yield(nbb)
    pdf_energy_Tl.set_yield(nTl)
    pdf_energy_Bi.set_yield(nBi)
    pdf_energy_Xe.set_yield(nXe)
    model = zfit.pdf.SumPDF(pdfs=[pdf_energy_bb, pdf_energy_Tl, pdf_energy_Bi, pdf_energy_Xe])

if fit_type == "typeII":
    pdf_bb.set_yield(nbb)
    pdf_Tl.set_yield(nTl)
    pdf_Bi.set_yield(nBi)
    pdf_Xe.set_yield(nXe)
    model = zfit.pdf.SumPDF(pdfs=[pdf_bb, pdf_Tl, pdf_Bi, pdf_Xe])

if fit_type == "typeIII":
    pdf_energy_bb.set_yield(nbb)
    pdf_energy_Tl.set_yield(nTl)
    pdf_energy_Bi.set_yield(nBi)
    pdf_energy_Xe.set_yield(nXe)
    model = zfit.pdf.SumPDF(pdfs=[pdf_energy_bb, pdf_energy_Tl, pdf_energy_Bi, pdf_energy_Xe])

    # background
    eff_bb = zfit.param.ConstantParameter("eff_bb", 0.323)
    eff_Tl = zfit.param.ConstantParameter("eff_Tl", 0.8985)
    eff_Bi = zfit.param.ConstantParameter("eff_Bi", 0.8985)
    eff_Xe = zfit.param.ConstantParameter("eff_Xe", 0.8985)
    mult_params = lambda *params: params[0]*params[1]
    eff_n_bb = zfit.ComposedParameter("eff_n_bb", mult_params, params=[eff_bb, nbb])
    eff_n_Tl = zfit.ComposedParameter("eff_n_Tl", mult_params, params=[eff_Tl, nTl])
    eff_n_Bi = zfit.ComposedParameter("eff_n_Bi", mult_params, params=[eff_Bi, nBi])
    eff_n_Xe = zfit.ComposedParameter("eff_n_Xe", mult_params, params=[eff_Xe, nXe])
    pdf_energy_bb_bkg.set_yield(eff_n_bb)
    pdf_energy_Tl_bkg.set_yield(eff_n_Tl)
    pdf_energy_Bi_bkg.set_yield(eff_n_Bi)
    pdf_energy_Xe_bkg.set_yield(eff_n_Xe)
    model_bkg = zfit.pdf.SumPDF(pdfs=[pdf_energy_bb_bkg, pdf_energy_Tl_bkg, pdf_energy_Bi_bkg, pdf_energy_Xe_bkg])

minimizer = zfit.minimize.Minuit(tol=1e-3)

if __name__ == "__main__":

    valid = []
    nbbt, nTlt, nBit, nXet = [], [], [], []
    nbbs, nTls, nBis, nXes = [], [], [], []
    for i in range(Nexperiments):

        # sample from pdfs
        bb_sample = pdf_bb.sample(np.random.poisson(nevents.loc["0nubb"])).numpy()
        Tl_sample = pdf_Tl.sample(np.random.poisson(nevents.loc["208Tl"])).numpy()
        Bi_sample = pdf_Bi.sample(np.random.poisson(nevents.loc["214Bi"])).numpy()
        Xe_sample = pdf_Xe.sample(np.random.poisson(nevents.loc["137Xe"])).numpy()
        sample = np.concatenate([bb_sample, Tl_sample, Bi_sample, Xe_sample])

        # fit strategies
        if fit_type == "typeI":
            Eb2 = 0.54
            bb_selected_sample = bb_sample[bb_sample[:, -1]>Eb2]
            Tl_selected_sample = Tl_sample[Tl_sample[:, -1]>Eb2]
            Bi_selected_sample = Bi_sample[Bi_sample[:, -1]>Eb2]
            Xe_selected_sample = Xe_sample[Xe_sample[:, -1]>Eb2]
            selected_sample = np.concatenate([bb_selected_sample, Tl_selected_sample, Bi_selected_sample, Xe_selected_sample])
            data = zfit.Data.from_numpy(obs=energy_obs, array=selected_sample[:, 0])
            nbbt.append(len(bb_selected_sample))
            nTlt.append(len(Tl_selected_sample))
            nBit.append(len(Bi_selected_sample))
            nXet.append(len(Xe_selected_sample))

            nll = zfit.loss.ExtendedUnbinnedNLL(model, data)
            result = minimizer.minimize(nll)
            result.hesse()

        if fit_type == "typeII":
            data = zfit.Data.from_numpy(obs=energy_obs * eblob2_obs, array=sample)
            nbbt.append(len(bb_sample))
            nTlt.append(len(Tl_sample))
            nBit.append(len(Bi_sample))
            nXet.append(len(Xe_sample))

            nll = zfit.loss.ExtendedUnbinnedNLL(model, data)
            result = minimizer.minimize(nll)
            result.hesse()

        if fit_type == "typeIII":
            Eb2 = 0.54
            bb_selected_sample = bb_sample[bb_sample[:, -1]<Eb2]
            Tl_selected_sample = Tl_sample[Tl_sample[:, -1]<Eb2]
            Bi_selected_sample = Bi_sample[Bi_sample[:, -1]<Eb2]
            selected_sample = np.concatenate([bb_selected_sample, Tl_selected_sample, Bi_selected_sample])
            data          = zfit.Data.from_numpy(obs=energy_obs, array=         sample[:, 0])
            selected_data = zfit.Data.from_numpy(obs=energy_obs, array=selected_sample[:, 0])
            nbbt.append(len(bb_sample))
            nTlt.append(len(Tl_sample))
            nBit.append(len(Bi_sample))
            nXet.append(len(Xe_sample))

            nll     = zfit.loss.ExtendedUnbinnedNLL(model    , data)
            nll_bkg = zfit.loss.ExtendedUnbinnedNLL(model_bkg, selected_data)
            nll_simultaneous = nll + nll_bkg
            result = minimizer.minimize(nll_simultaneous)
            result.hesse()

        # append fit result
        valid.append(result.valid)
        nbbs.append((result.params["nbb"]["value"], result.params["nbb"]["hesse"]["error"]))
        nTls.append((result.params["nTl"]["value"], result.params["nTl"]["hesse"]["error"]))
        nBis.append((result.params["nBi"]["value"], result.params["nBi"]["hesse"]["error"]))
        nXes.append((result.params["nXe"]["value"], result.params["nXe"]["hesse"]["error"]))

        zfit.run.clear_graph_cache()

    nbbs = np.array(nbbs)
    nTls = np.array(nTls)
    nBis = np.array(nBis)
    nXes = np.array(nXes)

    # save results
    df = pd.DataFrame()
    df["valid"]= valid
    df["nbbt"] = nbbt
    df["nTlt"] = nTlt
    df["nBit"] = nBit
    df["nXet"] = nXet
    df["nbb"]  = nbbs[:, 0]
    df["nTl"]  = nTls[:, 0]
    df["nBi"]  = nBis[:, 0]
    df["nXe"]  = nXes[:, 0]
    df["sbb"]  = nbbs[:, 1]
    df["sTl"]  = nTls[:, 1]
    df["sBi"]  = nBis[:, 1]
    df["sXe"]  = nXes[:, 1]

    df.to_csv(out_filename, index=False)
