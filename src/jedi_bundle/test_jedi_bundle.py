#!/usr/bin/env python

# (C) Copyright 2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

# --------------------------------------------------------------------------------------------------

import os
import subprocess
from pathlib import Path
from logging import Logger

from jedi_bundle.utils.config import config_get

# --------------------------------------------------------------------------------------------------


def test_jedi(logger: Logger, config: dict) -> None:

    bundles = config_get(logger, config, 'bundles')
    test_bundles = config_get(logger, config, 'ctest_bundles')
    path_to_build = config_get(logger, config, 'path_to_build')

    # Output directory to store output from tasks
    output_dir = Path(path_to_build) / 'ctests'
    output_dir.mkdir(exist_ok=True)

    # Make sure all ctest bundles are present in the built bundles
    if not all([test_bundle in bundles for test_bundle in test_bundles]):
        raise Exception(f'Not all test bundles were selected to build in build.yaml.')

    # Iterate through the bundles
    for bundle in test_bundles:

        logger.info('')
        logger.info(f'Running ctests for {bundle}')
        logger.info('')

        output_file = output_dir / f'{bundle}.txt'

        bundle_dir = Path(path_to_build) / bundle

        # Run ctests
        with open(output_file, 'w') as open_file:
            subprocess.run(['ctest', '-V'], cwd=bundle_dir, stdout=open_file)

# --------------------------------------------------------------------------------------------------
