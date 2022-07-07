import os
import argparse
import tables as tb
import numpy  as np
import pandas as pd
os.environ["ZFIT_DISABLE_TF_WARNINGS"] = "1"
import zfit
import hist

from invisible_cities.core.system_of_units import year, kg, dalton
from invisible_cities.evm.mixer            import get_mixer_nevents

# Experiment config
parser = argparse.ArgumentParser(description="Run experiments and fits")
parser.add_argument(  "-n", dest="Nexperiments", type=  int, help="number of experiments"  , required=True)
parser.add_argument(  "-s", dest="sel_filename", type=  str, help="number of experiments"  , required=True)
parser.add_argument(  "-o", dest="out_filename", type=  str, help="output filename"        , required=True)
parser.add_argument("-T12", dest=   "T12_0nubb", type=float, help="0nubb half-life (years)", required=True)
parser.add_argument(  "-t", dest=    "fit_type", type=  str, help="fit type"               , required=True)
args = parser.parse_args()

Nexperiments = args.Nexperiments
sel_filename = os.path.expandvars(args.sel_filename)
out_filename = os.path.expandvars(args.out_filename)
T12_0nubb    = args.T12_0nubb * year
fit_type     = args.fit_type

enrichment = 0.9
xenon_mass = 71.5 * kg
exposure   = 3. * year
detector_db = "next100"
isotopes = ["208Tl", "214Bi", "0nubb"]

# PDFs
def create_pdf_from_histogram(bins, histo, obs, name):
    h    = hist.Hist(hist.axis.Variable(edges=bins, name=name), data=histo)
    pdf  = zfit.pdf.HistogramPDF(h)
    data = zfit.Data.from_numpy (obs=obs, array=binc, weights=h)
    pdf  = zfit.pdf.KDE1DimExact(obs=obs, data=data, bandwidth=np.mean(np.diff(bins)))
    return pdf

with tb.open_file(sel_filename) as h5file:
    # energy pdfs
    name = "energy"
    bins = h5file.root.energy.bins.read()
    binc = (bins[1:] + bins[:-1])/2.
    emin, emax = bins[0], bins[-1]
    energy_obs = zfit.Space(name, limits=(emin, emax))

    h = h5file.root.energy.bb0nu.read()
    pdf_energy_bb = create_pdf_from_histogram(bins, h, energy_obs, name)
    if fit_type == "typeIII": pdf_energy_bb_bkg = create_pdf_from_histogram(bins, h, energy_obs, name)
    h = h5file.root.energy.Bi.read()
    pdf_energy_Bi = create_pdf_from_histogram(bins, h, energy_obs, name)
    if fit_type == "typeIII": pdf_energy_Bi_bkg = create_pdf_from_histogram(bins, h, energy_obs, name)
    h = h5file.root.energy.Tl.read()
    pdf_energy_Tl = create_pdf_from_histogram(bins, h, energy_obs, name)
    if fit_type == "typeIII": pdf_energy_Tl_bkg = create_pdf_from_histogram(bins, h, energy_obs, name)

    # eblob2
    name = "eblob2"
    bins = h5file.root.eblob2.bins.read()
    binc = (bins[1:] + bins[:-1])/2.
    eb2min, eb2max = bins[0], bins[-1]
    eblob2_obs     = zfit.Space(name, limits=(eb2min, eb2max))

    h = h5file.root.eblob2.bb0nu.read()
    pdf_eblob2_bb = create_pdf_from_histogram(bins, h, eblob2_obs, name)
    h = h5file.root.eblob2.Bi.read()
    pdf_eblob2_Bi = create_pdf_from_histogram(bins, h, eblob2_obs, name)
    h = h5file.root.eblob2.Tl.read()
    pdf_eblob2_Tl = create_pdf_from_histogram(bins, h, eblob2_obs, name)


pdf_bb = zfit.pdf.ProductPDF([pdf_energy_bb, pdf_eblob2_bb])
pdf_Tl = zfit.pdf.ProductPDF([pdf_energy_Tl, pdf_eblob2_Tl])
pdf_Bi = zfit.pdf.ProductPDF([pdf_energy_Bi, pdf_eblob2_Bi])


# Nevents per isotope/g4volume
eff_ic  = pd.read_csv("../efficiencies_ic.csv").set_index(["Isotope", "G4Volume"])
eff_sel = pd.read_hdf(sel_filename, "efficiencies")
total_eff = ((eff_ic.nreco/eff_ic.nsim) * (eff_sel.nevts/eff_ic.nreco)).fillna(0).loc[isotopes].sort_index()
N0 = enrichment*(xenon_mass/(136. * dalton))
nevent_df = get_mixer_nevents(exposure, detector_db, isotopes)
if "0nubb" in isotopes:
    nevts = N0 * (np.log(2)/T12_0nubb) * exposure
    nevent_df.loc[len(nevent_df)] = ("ACTIVE", "0nubb", nevts)
nevent_df = nevent_df.set_index(["Isotope", "G4Volume"]).sort_index()
indexes = total_eff.index
assert (indexes == nevent_df.index).all()


# FIT model
N = int(10*nevent_df.nevts.sum())
nbb = zfit.Parameter("nbb", 1, 0, N)
nTl = zfit.Parameter("nTl", 1, 0, N)
nBi = zfit.Parameter("nBi", 1, 0, N)

# different fit strategies:
#  - typeI  : signal cut on Eb2 and fit to energy
#  - typeII : no cut, combined fit to energy and eblob2
#  - typeIII: cut on background and combined energy fit for background selection with no-cut
if fit_type == "typeI":
    pdf_energy_bb.set_yield(nbb)
    pdf_energy_Tl.set_yield(nTl)
    pdf_energy_Bi.set_yield(nBi)
    model = zfit.pdf.SumPDF(pdfs=[pdf_energy_bb, pdf_energy_Tl, pdf_energy_Bi])

if fit_type == "typeII":
    pdf_bb.set_yield(nbb)
    pdf_Tl.set_yield(nTl)
    pdf_Bi.set_yield(nBi)
    model = zfit.pdf.SumPDF(pdfs=[pdf_bb, pdf_Tl, pdf_Bi])

if fit_type == "typeIII":
    pdf_energy_bb.set_yield(nbb)
    pdf_energy_Tl.set_yield(nTl)
    pdf_energy_Bi.set_yield(nBi)
    model = zfit.pdf.SumPDF(pdfs=[pdf_energy_bb, pdf_energy_Tl, pdf_energy_Bi])

    # background
    eff_bb = zfit.param.ConstantParameter("eff_bb", 0.323)
    eff_Tl = zfit.param.ConstantParameter("eff_Tl", 0.8985)
    eff_Bi = zfit.param.ConstantParameter("eff_Bi", 0.8985)
    mult_params = lambda *params: params[0]*params[1]
    eff_n_bb = zfit.ComposedParameter("eff_n_bb", mult_params, params=[eff_bb, nbb])
    eff_n_Tl = zfit.ComposedParameter("eff_n_Tl", mult_params, params=[eff_Tl, nTl])
    eff_n_Bi = zfit.ComposedParameter("eff_n_Bi", mult_params, params=[eff_Bi, nBi])
    pdf_energy_bb_bkg.set_yield(eff_n_bb)
    pdf_energy_Tl_bkg.set_yield(eff_n_Tl)
    pdf_energy_Bi_bkg.set_yield(eff_n_Bi)
    model_bkg = zfit.pdf.SumPDF(pdfs=[pdf_energy_bb_bkg, pdf_energy_Tl_bkg, pdf_energy_Bi_bkg])

minimizer = zfit.minimize.Minuit(gradient=True)

if __name__ == "__main__":

    valid = []
    nbbt, nTlt, nBit = [], [], []
    nbbs, nTls, nBis = [], [], []
    for i in range(Nexperiments):

        # randomize (binomial) and sample
        nevents = np.random.binomial(nevent_df.nevts, total_eff)
        nevents_roi = pd.DataFrame(index=indexes, data={"nevts": nevents})
        nevents = nevents_roi.groupby(level=0).nevts.sum()

        # sample from pdfs
        bb_sample = pdf_bb.sample(nevents.get("0nubb")).numpy()
        Tl_sample = pdf_Tl.sample(nevents.get("208Tl")).numpy()
        Bi_sample = pdf_Bi.sample(nevents.get("214Bi")).numpy()
        sample = np.concatenate([bb_sample, Tl_sample, Bi_sample])

        # fit strategies
        if fit_type == "typeI":
            Eb2 = 0.54
            bb_selected_sample = bb_sample[bb_sample[:, -1]>Eb2]
            Tl_selected_sample = Tl_sample[Tl_sample[:, -1]>Eb2]
            Bi_selected_sample = Bi_sample[Bi_sample[:, -1]>Eb2]
            selected_sample = np.concatenate([bb_selected_sample, Tl_selected_sample, Bi_selected_sample])
            data = zfit.Data.from_numpy(obs=energy_obs, array=selected_sample[:, 0])
            nbbt.append(len(bb_selected_sample))
            nTlt.append(len(Tl_selected_sample))
            nBit.append(len(Bi_selected_sample))

            nll = zfit.loss.ExtendedUnbinnedNLL(model, data)
            result = minimizer.minimize(nll)
            result.hesse()

        if fit_type == "typeII":
            data = zfit.Data.from_numpy(obs=energy_obs * eblob2_obs, array=sample)
            nbbt.append(nevents.get("0nubb"))
            nTlt.append(nevents.get("208Tl"))
            nBit.append(nevents.get("214Bi"))

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

        zfit.run.clear_graph_cache()

    nbbs = np.array(nbbs)
    nTls = np.array(nTls)
    nBis = np.array(nBis)

    # save results
    df = pd.DataFrame()
    df["valid"]= valid
    df["nbbt"] = nbbt
    df["nTlt"] = nTlt
    df["nBit"] = nBit
    df["nbb"]  = nbbs[:, 0]
    df["nTl"]  = nTls[:, 0]
    df["nBi"]  = nBis[:, 0]
    df["sbb"]  = nbbs[:, 1]
    df["sTl"]  = nTls[:, 1]
    df["sBi"]  = nBis[:, 1]

    df.to_csv(out_filename, index=False)
