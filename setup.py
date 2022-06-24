# (C) Copyright 2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

# --------------------------------------------------------------------------------------------------

# Setup and installation script
#
# Usage: "pip install --prefix=/path/to/install ."

# --------------------------------------------------------------------------------------------------

import setuptools

setuptools.setup(
    name='jedi-bundle',
    version='0.0.1',
    author='NASA Global Modeling and Assimilation Office',
    description='Tools for installing JEDI code',
    url='https://github.com/geos-esm/jedi-bundle',
    package_dir={'': 'src'},
    packages=setuptools.find_packages(where='src'),
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent'],
    python_requires='>=3.6',
    install_requires=[
        'pyyaml>=5.4',
        'pycodestyle>=2.8.0',
        'requests>=2.23.0',
    ],
    package_data={
        '': [
               'config/*',
               'config/platforms/*',
             ],
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'jedi_bundle = jedi_bundle.bin.jedi_bundle:jedi_bundle',
        ],
    },
    )

# --------------------------------------------------------------------------------------------------
