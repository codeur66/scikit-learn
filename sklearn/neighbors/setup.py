import os


def configuration(parent_package="", top_path=None):
    import numpy
    from numpy.distutils.misc_util import Configuration

    config = Configuration("neighbors", parent_package, top_path)
    libraries = []
    if os.name == "posix":
        libraries.append("m")

    config.add_extension(
        "_ball_tree",
        sources=["_ball_tree.pyx"],
        include_dirs=[numpy.get_include()],
        libraries=libraries,
    )

    config.add_extension(
        "_kd_tree",
        sources=["_kd_tree.pyx"],
        include_dirs=[numpy.get_include()],
        libraries=libraries,
    )

    config.add_extension(
        "_dist_metrics",
        sources=["_dist_metrics.pyx"],
        include_dirs=[numpy.get_include(), os.path.join(numpy.get_include(), "numpy")],
        libraries=libraries,
    )

    config.add_extension(
        "_typedefs",
        sources=["_typedefs.pyx"],
        include_dirs=[numpy.get_include()],
        libraries=libraries,
    )
    config.add_extension(
        "_quad_tree",
        sources=["_quad_tree.pyx"],
        include_dirs=[numpy.get_include()],
        libraries=libraries,
    )

    config.add_subpackage("tests")

    return config
