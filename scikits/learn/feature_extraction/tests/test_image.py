# Authors: Emmanuelle Gouillart <emmanuelle.gouillart@normalesup.org>
#          Gael Varoquaux <gael.varoquaux@normalesup.org>
#          Olivier Grisel <olivier.grisel@ensta.org>
# License: BSD

import numpy as np
import scipy as sp
from scipy import ndimage

from nose.tools import assert_equal
from numpy.testing import assert_array_equal

from ..image import img_to_graph
from ..image import extract_patches2d
from ...utils.graph import cs_graph_components

def test_img_to_graph():
    x, y = np.mgrid[:4, :4] - 10
    grad_x = img_to_graph(x)
    grad_y = img_to_graph(y)
    assert_equal(grad_x.nnz, grad_y.nnz)
    # Negative elements are the diagonal: the elements of the original
    # image. Positive elements are the values of the gradient, they
    # shoudl all be equal on grad_x and grad_y
    assert_array_equal(grad_x.data[grad_x.data > 0],
                       grad_y.data[grad_y.data > 0])


def test_connect_regions():
    lena = sp.lena()
    for thr in (50, 150):
        mask = lena > thr
        graph = img_to_graph(lena, mask)
        assert_equal(ndimage.label(mask)[1], cs_graph_components(graph)[0])


def test_extract_patches2d():
    # make a collection of lenas
    lena = sp.lena()
    images = np.zeros((3,) + lena.shape)
    images[0] = lena
    images[1] = lena + 1
    images[2] = lena + 2

    # lena is shaped (512, 512): expect 32 * 32 patches with shape (16, 16)
    n_patches = images.shape[0] * 32 * 32

    patches = extract_patches2d(images, lena.shape, (16, 16))
    assert_equal(patches.shape, (n_patches, 16, 16))
