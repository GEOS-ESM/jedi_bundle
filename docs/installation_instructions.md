# Installation instructions

The jedi_bundle package is available through [PyPi](https://pypi.org/project/jedibundle/) and can be installed following the instructions there.

To install from source, clone the repo from GitHub:

``` shell
git clone https://github.com/geos-esm/jedi_bundle
cd jedi_bundle
```

and install using Pip:

``` shell
pip install --prefix=/path/to/install/jedi_bundle .
```

The `--prefix` argument is optional and used to specify the location that the code is installed. Replace this with the desired path.

To make the software useable ensure `/path/to/install/jedi_bundle/bin` is in the `$PATH`. Also ensure that `/path/to/install/jedi_bundle/lib/python<version>/site-packages` is in the `$PYTHONPATH`, where `<version>` denotes the version of Python used to install, e.g. `3.9`.
