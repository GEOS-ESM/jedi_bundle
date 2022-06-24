#!/usr/bin/env python

# (C) Copyright 2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

# --------------------------------------------------------------------------------------------------

import yaml

# --------------------------------------------------------------------------------------------------

def load_yaml(logger, pathfile):

    # Convert the config file to a dictionary
    try:
        with open(pathfile, 'r') as pathfile_opened:
            dict = yaml.safe_load(pathfile_opened)
    except Exception as e:
            logger.abort('Jedi build code f is expecting a valid yaml file, but it encountered ' +
                         f'errors when attempting to load: {pathfile}, error: {e}')

    return dict

# --------------------------------------------------------------------------------------------------