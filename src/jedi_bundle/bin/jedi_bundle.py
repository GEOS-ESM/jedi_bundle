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
    parser.add_argument('task_and_config', type=str, nargs='+',
                        help='Task to run followed by configuration ' +
                        'YAML. Task to run should be one of, or a combination of Clone, ' +
                        'Configure and Build. If task to run is omitted then all three steps ' +
                        'will be executed')

    # Create the logger
    logger = Logger('JediBundle')

    # Parse inputs
    args = parser.parse_args()
    task_and_config = args.task_and_config

    # Prepare the configuration
    # -------------------------

    # Standard config file name
    config_file_name = 'build.yaml'

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

        # Config file name
        config_file_name = os.path.basename(config_file)

    # If config not passed, copy to current directory
    if not config_passed:
        internal_config_file = os.path.join(return_config_path(), config_file_name)
        internal_config_dict = load_yaml(logger, internal_config_file)

        internal_config_dict_cnfig = internal_config_dict['configure_options']

        cwdfilelist = os.listdir(os.getcwd())
        if not cwdfilelist or cwdfilelist[0] == config_file_name:
            # If directory is empty or contains build.yaml then make the current directory the
            # default path
            default_paths = os.getcwd()
        else:
            # If directory is not empty then default to a sub directory called jedi_bundle
            default_paths = os.path.join(os.getcwd(), 'jedi_bundle')

        internal_config_dict['clone_options']['path_to_source'] = default_paths

        # Set default build directory
        build_dir = os.path.join(default_paths, 'build')

        # Guess the platform
        hostname = os.uname()[1].lower()
        supported_platforms_yaml = os.listdir(os.path.join(return_config_path(), 'platforms'))
        found_a_platform = False
        for supported_platform_yaml in supported_platforms_yaml:
            supported_platform = supported_platform_yaml.split('.')[0]
            if supported_platform in hostname:
                platform = supported_platform
                found_a_platform = True
                break

        if found_a_platform:
            # Set found platform in the dictionary
            internal_config_dict['configure_options']['platform'] = platform

            # Load platform config and set default modules
            platform_pathfile = os.path.join(return_config_path(), 'platforms', platform + '.yaml')
            platform_dict = load_yaml(logger, platform_pathfile)
            default_modules = platform_dict['modules']['default_modules']
            internal_config_dict['configure_options']['modules'] = default_modules

            # Append build with the modules being used
            build_dir = build_dir + '-' + default_modules

        # Set the list of bundles
        bundles_yaml = os.listdir(os.path.join(return_config_path(), 'bundles'))
        bundles = []
        for bundle_yaml in bundles_yaml:
            if bundle_yaml != 'build-order.yaml':
                bundles.append(bundle_yaml.split('.')[0])
        internal_config_dict['clone_options']['bundles'] = bundles

        # Set the path to the build directory
        cmake_build_type = internal_config_dict['configure_options']['cmake_build_type']
        build_dir = build_dir + '-' + cmake_build_type

        internal_config_dict['configure_options']['path_to_build'] = build_dir

        # Set path to new file and remove if existing
        config_file = os.path.join(os.getcwd(), config_file_name)
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
    path_to_source = config_dict['clone_options']['path_to_source']
    if path_to_source == './':
        path_to_source = os.getcwd()
    if path_to_source != config_file_path:
        os.makedirs(path_to_source, exist_ok=True)
        os.chmod(path_to_source, mode=0o755)
        os.rename(config_file, os.path.join(path_to_source, config_file_name))

    # Prepare the Tasks
    # -----------------

    # Check that the options are valid
    valid_tasks = ['Clone', 'Configure', 'Make', 'All']
    for task in tasks:
        if task not in valid_tasks:
            logger.abort(f'Task \'{task}\' not in the valid tasks {valid_tasks}. Ensure the ' +
                         f'configuration is passed as the last argument.')

    # Dictionaries
    clone_dict = config_dict['clone_options']
    configure_dict = {**clone_dict, **config_dict['configure_options']}
    make_dict = {**configure_dict, **config_dict['make_options']}

    # Run the build stages
    if 'All' in tasks or 'Clone' in tasks:
        clone_jedi(logger, clone_dict)
    if 'All' in tasks or 'Configure' in tasks:
        configure_jedi(logger, configure_dict)
    if 'All' in tasks or 'Make' in tasks:
        make_jedi(logger, make_dict)

# --------------------------------------------------------------------------------------------------
