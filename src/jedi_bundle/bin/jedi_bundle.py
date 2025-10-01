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

from jedi_bundle.config.config import return_config_path, determine_platform
from jedi_bundle.utils.file_system import prompt_and_remove_file
from jedi_bundle.utils.logger import Logger, colors
from jedi_bundle.utils.yaml import load_yaml
from jedi_bundle.utils.welcome_message import write_welcome_message


# --------------------------------------------------------------------------------------------------


def get_default_config():

    internal_config_file = os.path.join(return_config_path(), 'build.yaml')
    with open(internal_config_file, 'r') as internal_config_file_opened:
        internal_config_dict = yaml.safe_load(internal_config_file_opened)
    return internal_config_dict


# --------------------------------------------------------------------------------------------------


def get_bundles():

    bundles_yaml = os.listdir(os.path.join(return_config_path(), 'bundles'))
    bundles = []
    for bundle_yaml in bundles_yaml:
        if bundle_yaml != 'build-order.yaml':
            bundles.append(bundle_yaml.split('.')[0])

    return bundles

# --------------------------------------------------------------------------------------------------


def execute_tasks(tasks, config_dict):

    # Create the logger
    logger = Logger('JediBundle')

    # Convert to lower case
    tasks = [task.lower() for task in tasks]

    # Check that the options are valid
    valid_tasks = ['clone', 'configure', 'make', 'all']
    for task in tasks:
        if task not in valid_tasks:
            logger.abort(f'Task \'{task}\' not in the valid tasks {valid_tasks}. Ensure the ' +
                         f'configuration is passed as the last argument.')

    # Dictionaries
    clone_dict = config_dict['clone_options']
    configure_dict = {**clone_dict, **config_dict['configure_options']}
    make_dict = {**configure_dict, **config_dict['make_options']}

    # Run the build stages
    if 'all' in tasks or 'clone' in tasks:
        if 'pinned_versions' in config_dict:
            clone_dict['pinned_versions'] = config_dict['pinned_versions']
        clone_jedi(logger, clone_dict)
    if 'all' in tasks or 'configure' in tasks:
        configure_jedi(logger, configure_dict)
    if 'all' in tasks or 'make' in tasks:
        make_jedi(logger, make_dict)


# --------------------------------------------------------------------------------------------------


def jedi_bundle():

    # Arguments
    # ---------
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('tasks_and_config', type=str, nargs='*', default=None,
                        help='There are two ways of running jedi_bundle. Either with no arguments '
                             'or two (or more) arguments. \nWhen no argument is provided the code '
                             'will generate the config file build.yaml in the working \ndirectory '
                             'and then exit. When two (or more) arguments are passed the final '
                             'argument must be the \npath to the configuration file. The '
                             'proceeding arguments are the choice of task(s) to run.'
                             '\n\nThe valid tasks are \'Clone\', \'Configure\', \'Build\' and '
                             '\'All\', where \'All\' runs all of the above. \nTasks names are case '
                             'insensitive. ' +
                             '\n\nExamples:\n' +
                             '  jedi_bundle                             (Generate config) \n' +
                             '  jedi_bundle All build.yaml              (All tasks) \n' +
                             '  jedi_bundle all build.yaml              (All tasks) \n' +
                             '  jedi_bundle Clone build.yaml            (Clone task) \n'
                             '  jedi_bundle Clone Configure build.yaml  (Clone & Configure task)\n')
    parser.add_argument('--pinned_versions', '-pv', action='store_true',
                        help='Invoke flag to use pinned versions instead of defaults')

    # Write the welcome message
    write_welcome_message()

    # Create the logger
    logger = Logger('JediBundleSetup')

    # Parse input string
    args = parser.parse_args()
    tasks_and_config = args.tasks_and_config
    pinned_versions = args.pinned_versions

    # If there are no arguments create build.yaml and exit
    if tasks_and_config == []:

        # Prepare the configuration from default
        # --------------------------------------
        internal_config_dict = get_default_config()

        # Set current directory for source code
        internal_config_dict['clone_options']['path_to_source'] = os.getcwd()

        # Set default build directory
        build_dir = os.path.join(os.getcwd(), 'build')

        # Determine platform
        platform, modules = determine_platform(logger)

        # Show message about platform
        logger.info(f'Platform identified as {platform}')

        if platform is not None:
            # Set found platform in the dictionary
            internal_config_dict['configure_options']['platform'] = platform
            internal_config_dict['configure_options']['modules'] = modules

            # Append build with the modules being used
            build_dir = build_dir + '-' + modules

        # Set the list of bundles
        bundles = get_bundles()
        internal_config_dict['clone_options']['bundles'] = bundles

        # Set the path to the build directory
        cmake_build_type = internal_config_dict['configure_options']['cmake_build_type']
        build_dir = build_dir + '-' + cmake_build_type

        internal_config_dict['configure_options']['path_to_build'] = build_dir

        # Add pinned_versions to build config if applicable
        if pinned_versions:
            pinned_config_file = os.path.join(return_config_path(), 'pinned_versions.yaml')
            pinned_versions_dict = load_yaml(logger, pinned_config_file)
            internal_config_dict['pinned_versions'] = pinned_versions_dict

        # Set path to new file and remove if existing
        config_file = os.path.join(os.getcwd(), 'build.yaml')
        prompt_and_remove_file(logger, config_file)

        # Write dictionary to user directory
        with open(config_file, 'w') as config_file_handle:
            yaml.dump(internal_config_dict, config_file_handle, default_flow_style=False)

        # Tell user to update the file
        logger.info(f'Configuration file generated and written to {config_file}')

        exit(0)

    else:

        if len(tasks_and_config) < 2:
            logger.abort('The number of arguments passed to jedi_bundle must be 0 or >= 2')

        tasks = tasks_and_config[0:-1]
        config_file_name = tasks_and_config[-1]

        # Read the config
        # ---------------
        config_dict = load_yaml(logger, config_file_name)

        # Execute the tasks
        # -----------------
        execute_tasks(tasks, config_dict)


# --------------------------------------------------------------------------------------------------
