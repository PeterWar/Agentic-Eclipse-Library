# -*- coding: utf-8 -*-

import numpy as np
import scipy.ndimage
from multiprocessing import Pool, cpu_count, freeze_support


def membership_function(n, ngauss=12):
    """Membership function defining a fuzzy neighborhood of the current pixel

    Parameters
    ----------
    n: int
      Fuzzy neighborhood (square) size
    ngauss: int
      Number of Gaussians used to build the membership function

    Return
    ------
    array: membership function values in neighborhood

    Example
    -------
    >>> membership_function(5)
    array([[ 0.65289406,  0.73715583,  0.7741782 ,  0.73715583,  0.65289406],
         [ 0.73715583,  0.86813217,  0.92826105,  0.86813217,  0.73715583],
         [ 0.7741782 ,  0.92826105,  1.        ,  0.92826105,  0.7741782 ],
         [ 0.73715583,  0.86813217,  0.92826105,  0.86813217,  0.73715583],
         [ 0.65289406,  0.73715583,  0.7741782 ,  0.73715583,  0.65289406]])
    """
    if n % 2 != 1:
        raise ValueError("n should be an odd integer")
    x = np.arange(n) - n // 2
    k, l = np.meshgrid(x, x)  # indices of the neighborhood
    sigma_sum = 0
    g_sum = 0
    for m in range(1, ngauss + 1):
        sigma_sum += 1 / np.sqrt(2 ** (m / 2))
        g_sum += (
            1
            / (2 * np.pi * np.sqrt(2 ** (m / 2)))
            * np.exp(-0.5 * (k**2 + l**2) * ((2 ** (m / 2)) ** -2))
        )  # Gaussians sum
    d = 2 * np.pi / sigma_sum  # normalization factor
    return d * g_sum


class Im:
    def __init__(self, im, n, sigma):
        self._im = im
        self.n = n
        self.sigma = sigma
        self.Lkl = membership_function(self.n, ngauss=12)
        self.ax, self.ay = im.shape
        self.n2 = n // 2
        self.nbins = 500

    def y1(self, uv):
        u, v = uv[0], uv[1]
        u0 = max(u - self.n2, 0)
        u1 = min(u + self.n2 + 1, self.ax)
        v0 = max(v - self.n2, 0)
        v1 = min(v + self.n2 + 1, self.ay)
        im0 = self._im[u0:u1, v0:v1]
        lkl = self.Lkl[
            u0 - u + self.n2 : u1 - u + self.n2, v0 - v + self.n2 : v1 - v + self.n2
        ]
        # histogram for one pixel of 'image'
        h, bins = np.histogram(im0, bins=self.nbins, weights=lkl)
        # standard deviation of the convolution gaussian
        sigma0 = self.sigma / ((bins[-1] - bins[0]) / self.nbins)
        bins = (bins[:-1] + bins[1:]) / 2  # centers of bins
        H = np.cumsum(h)
        H /= H[-1]
        # convolved cumulative fuzzy histogram
        H = scipy.ndimage.gaussian_filter(H, sigma0, mode="nearest")
        return np.interp(self._im[uv[0], uv[1]], bins, H)

    def y1_chunk(self, uvs):
        result = list()
        for uv in uvs:
            result.append(self.y1(uv))
        return result


def chunker(iterable, nchunks):
    """
    Split iterable into some number of chunks. Each chunk is a list.
    """
    nelements = len(iterable)
    size0, remainder = divmod(nelements, nchunks)
    sizes = [size0 + 1 if ichunk < remainder else size0 for ichunk in range(nchunks)]
    starts = np.cumsum([0, *sizes][:-1])
    chunks = [iterable[start : start + size] for start, size in zip(starts, sizes)]
    return chunks


def nafe(
    image,
    n=129,
    a=(5.0, 5000.0),
    b=(0.0, 1.0),
    w=0.2,
    gamma=2.4,
    sigma=5,
    nproc=cpu_count(),
):
    """NAFE algorithm (Druckmüller, M. A noise adaptive fuzzy equalization
    method for processing solar extreme ultraviolet images.  Astrophys. J.
    Supp. Ser. 207, 25, 2013).

    Parameters
    ----------
    image: ndarray
      Image
    n: int
      Size (width) of fuzzy neighborhood
    a: tuple
      Minimum and maximum input values in image
    b: tuple
      Minimum and maximum output values in image
    w: float
      Weight of the NAFE-processed image in output image
    gamma: float
      Gamma exponent for background image in output image
    sigma: float
      Additive noise level (do not amplify noise in input image below this level)
    nproc: int
      Number of CPU cores to use.

    Return
    ------
    array: output image
    """
    ax, ay = image.shape
    image = image.clip(a[0], a[1])
    if n % 2 != 1:
        raise ValueError("n should be an odd integer")
    # Gamma-corrected / rescaled image
    img = b[0] + (b[1] - b[0]) * ((image - a[0]) / (a[1] - a[0])) ** (1.0 / gamma)
    if w == 0:  # no need for NAFE
        return img
    # NAFE detailed layer
    ima = Im(image, n=n, sigma=sigma)
    i, j = np.meshgrid(range(ax), range(ay), indexing="ij")

    ij = zip(i.flat, j.flat)
    if nproc == 1:
        imy = map(ima.y1, ij)
    else:
        freeze_support()
        p = Pool(nproc)
        ij_chunks = chunker(list(ij), nproc * 100)
        imy0 = p.map(ima.y1_chunk, ij_chunks)
        imy = []
        for sublist in imy0:
            imy += sublist
    imy = np.array(list(imy)).reshape(ax, ay)
    imf = (1 - w) * img + w * imy
    return imf
