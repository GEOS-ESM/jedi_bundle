### License:

(C) Copyright 2022-2022 United States Government as represented by the Administrator of the National
Aeronautics and Space Administration. All Rights Reserved.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

### Description:

Bundle containing all the repositories that are needed to compile the JEDI repos needed by the GMAO.

### Installation:

If building on NASA's Discover the provided build scripts are a convenient way of building:

    git clone https://github.com/GEOS-ESM/jedi-bundle
    cd jedi-bundle

Then to see the compiler options available on that machine do:

    cd jedi-bundle
    ./buildscripts/build_discover.sh -h

The first option listed is the default that would be chosen if no arguments are provided. Typically,
the only options needed are `-c` for the compiler choice and `-b` for release or debug build mode.
