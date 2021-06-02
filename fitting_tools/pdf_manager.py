"""
This module contains two classes that implements usefull pdf functionalities to perform
extended maximum likelihood fits

pdf class:
    define a pdf, either numerically or analitically
Extpdf class:
    a collection of psfs
"""

import numpy as np
from scipy.stats       import rv_continuous
from scipy.interpolate import interp1d


class pdf(rv_continuous):
    """
    Params:
    -------
    a, b   : lower and upper limits
    numpdf : tuple (x, y) of numerical pdf
    funcpdf: function defining pdf
    n      : number of partitions of to numerically compute the cdf
    kind   : kind of interpolation (see interp1d function)

    Methods:
    -------
    see scipy.stats.rv_continuos
    """
    def __init__(self, name=None, a=None, b=None, numpdf=None, funcpdf=None, n=10000, kind="cubic"):
        super().__init__(momtype=0, name=name, a=a, b=b)

        if numpdf and funcpdf:
            raise Exception("Both numerical and functional pdf introduced")
        if (numpdf is None) and (funcpdf is None):
            raise Exception("Introduce pdf")

        if numpdf:
            func = self.create_pdf_function(numpdf, kind)
            self.set_pdf(func)

            func = self.create_cdf_function(n, kind)
            self.set_cdf(func)

        if funcpdf:
            self.set_pdf(funcpdf)

    ## PDF
    def create_pdf_function(self, numpdf, kind):
        x, y = numpdf
        self.get_norm(x, y)
        self.a, self.b = min(x), max(x)
        f = interp1d(x, y/self.norm, kind=kind, bounds_error=False, fill_value=0)
        return f

    def set_pdf(self, func):
        self._pdf = func

    def get_norm(self, x, y):
        ym = (y[1:] + y[:-1])/2.
        norm = np.sum(np.diff(x)*ym)
        self.norm = norm
        return norm

    ## CDF (this greatly speeds up the computation of rvs)
    def create_cdf_function(self, n, kind):
        dx = (self.b - self.a)/n
        x = np.arange(self.a-dx, self.b + dx, dx)
        y = self.pdf(x)
        ym = (y[1:] + y[:-1])/2.
        cdf = np.cumsum(np.diff(x)*ym)
        f = interp1d(x[1:], cdf, kind=kind, bounds_error=False, fill_value=0)
        return f

    def set_cdf(self, func):
        self._cdf = func


class Extpdf:
    """
    defines an extended pdf for a pdf collection such that:

    ext-pdf = sum(w_i*pdf_i) where wi represents the psf_i weight

    Params:
    -------
    pdf collection: dictionary of (name, pdf instances)

    Methods:
    -------
    pdf, rvs (same as pdf class)
    eval_logL: returns the -log likelihood evaluated at given input
    """

    def __init__(self, collection):
        self.collection = collection
        self.n      = len(collection)
        self.names  = list(collection.keys())
        self.args_order = dict([(i, name) for i, name in enumerate(self.names)])

    def pdf(self, x, *params):
        N = np.sum(params)
        products = []
        for i in self.args_order:
            n    = params[i]
            name = self.args_order[i]
            p    = self.collection[name]
            products.append((n/N)*p.pdf(x))
        return np.sum(products, axis=0)

    def rvs(self, *params, size=1):
        r = []
        for i in self.args_order:
            n    = params[i]
            name = self.args_order[i]
            p    = self.collection[name]
            r.append(p.rvs(size=size*n))
        return np.concatenate(r)

    def eval_logL(self, x):
        def logL(*params):
            N = np.sum(params)
            p = self.pdf(x, *params)
            p = p[p>0]
            ll = -N + np.sum(np.log(N*p))
            return -ll
        return logL


def compute_chi2dof(data, bins, pdf, params):
    """Computes the chi2/dof from a mll fit.
    data is bined in bins, for which the expected value from pdf
    evaluated at params is computed.
    """
    observed, _ = np.histogram(data, bins=bins)
    expected = []
    for b in range(len(bins)-1):
        a, b = bins[b], bins[b+1]
        dx = (b-a)/100.
        xs = np.arange(a, b+dx, dx)
        expected.append(np.sum(pdf(xs, *params))*dx)
    expected = np.array(expected)*np.sum(observed)
    sel = expected>0
    N = np.sum(sel)
    n = len(params)
    chi2dof = np.sum((observed[sel]-expected[sel])**2/expected[sel])/(N-n)
    return chi2dof
