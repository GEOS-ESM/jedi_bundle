# Installation instructions

The jedi-bundle package is written in Python and is installed using Pip. First clone the code:


``` shell
git clone https://github.com/geos-esm/jedi-bundle
```

Now, with Python 3 available, install the code using Pip:

``` shell
pip install --prefix=/path/to/install/jedi-bundle jedi-bundle
```

In the above the final argument is the path to the source code that was just cloned. The `--prefix` argument is optional and used to specify the location that the code is installed. Replace this with the desired path.

To make the software useable ensure `/path/to/install/jedi-bundle/bin` is in the `$PATH`. Also ensure that `/path/to/install/jedi-bundle/lib/python<version>/site-packages` in in the `$PYTHONPATH`, where `<version>` denotes the version of Python
used to install, e.g. `3.9`.
