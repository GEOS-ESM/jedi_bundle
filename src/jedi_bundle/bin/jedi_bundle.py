#!/usr/bin/env python

# (C) Copyright 2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

# --------------------------------------------------------------------------------------------------


import argparse
import os
import requests
import shutil
import yaml

from jedi_bundle.clone_jedi_bundle import clone_jedi
from jedi_bundle.configure_jedi_bundle import configure_jedi
from jedi_bundle.make_jedi_bundle import make_jedi

from jedi_bundle.config.config import return_config_path
from jedi_bundle.utils.file_system import prompt_and_remove_file
from jedi_bundle.utils.logger import Logger, colors
from jedi_bundle.utils.yaml import load_yaml


# --------------------------------------------------------------------------------------------------


def jedi_bundle():

    # Arguments
    # ---------
    parser = argparse.ArgumentParser()
    parser.add_argument('task_and_config', type=str, nargs='+', default='All',
                        help='Task to run followed by configuration ' +
                        'YAML. Task to run should be one of, or a combination of Clone, ' +
                        'Configure and Build. If task to run is omitted then all three steps ' +
                        'will be executed')

    # Create the logger
    logger = Logger('JediBundle')

    # Get the configuration file
    args = parser.parse_args()
    task_and_config = args.task_and_config

    # Prepare the configuration
    # -------------------------

    # Determine if config file was passed
    tasks = task_and_config
    config_passed = False
    if '.yaml' in task_and_config[-1]:
        config_file = task_and_config[-1]
        tasks = task_and_config[0:-1]
        config_passed = True

        # Check that file exists
        if not os.path.exists(config_file):
            logger.abort(f'Configuration file \'{config_file}\' passed in argument list not found.')

    # If config not passed, copy to current directory
    if not config_passed:
        cwd = os.getcwd()

        internal_config_file = os.path.join(return_config_path(), 'build.yaml')
        internal_config_dict = load_yaml(logger, internal_config_file)

        internal_config_dict['build_options']['path_to_build'] = cwd
        internal_config_dict['source_code_options']['path_to_source'] = cwd

        config_file = os.path.join(cwd, 'build.yaml')
        prompt_and_remove_file(logger, config_file)

        # Write dictionary to user directory
        with open(config_file, 'w') as config_file_handle:
            yaml.dump(internal_config_dict, config_file_handle, default_flow_style=False)

        # Tell user to update the file
        logger.input(f'Since no configuration file was provided, the default file will be used. ' +
                     f'This can be edited ', f'at the below location before continuing',
                     f'  {config_file}')

    # Read the config_file and convert to dictionary
    config_dict = load_yaml(logger, config_file)

    # Copy the config to the source directory
    config_file_path = os.path.dirname(config_file)
    path_to_source = config_dict['source_code_options']['path_to_source']
    if path_to_source == './':
        path_to_source = os.getcwd()
    if path_to_source != config_file_path:
        os.makedirs(path_to_source, exist_ok=True)
        os.chmod(path_to_source, mode=0o755)
        shutil.copyfile(config_file, os.path.join(path_to_source, 'build.yaml'))

    # Prepare the Tasks
    # -----------------

    # Check that the options are valid
    valid_tasks = ['Clone', 'Configure', 'Make', 'All']
    for task in tasks:
        if task not in valid_tasks:
            logger.abort(f'Task \'{task}\' not in the valid tasks {valid_tasks}. Ensure the ' +
                         f'configuration is passed as the last argument.')

    # Set flags for the different phases of the build
    run_clone = False
    run_configure = False
    run_make = False
    if 'All' in tasks or 'Clone' in tasks:
        run_clone = True
    if 'All' in tasks or 'Configure' in tasks:
        run_configure = True
    if 'All' in tasks or 'Make' in tasks:
        run_make = True

    # Run the build stages
    if run_clone:
        clone_jedi(logger, config_dict)
    if run_configure:
        configure_jedi(logger, config_dict)
    if run_make:
        make_jedi(logger, config_dict)

# --------------------------------------------------------------------------------------------------
