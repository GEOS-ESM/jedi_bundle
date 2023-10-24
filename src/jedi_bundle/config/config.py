# (C) Copyright 2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.


# --------------------------------------------------------------------------------------------------


import os
import subprocess
import yaml

from jedi_bundle.utils.yaml import load_yaml


# --------------------------------------------------------------------------------------------------


def return_config_path():
    return os.path.split(__file__)[0]


# --------------------------------------------------------------------------------------------------


def determine_platform(logger):

    # Get the supported platforms
    possible_platforms = os.listdir(os.path.join(return_config_path(), 'platforms'))

    # Remove anything that does not start with a character (avoid system files)
    possible_platforms = [platform for platform in possible_platforms if platform[0].isalnum()]

    # Loop over possible platforms
    for platform in possible_platforms:

        # Open the dictionary
        platform_dict = load_yaml(logger, os.path.join(return_config_path(), 'platforms', platform))

        # List of commands to check if this is the platform
        is_it_me = platform_dict['is_it_me']

        # Loop over commands
        for is_it_me_command in is_it_me:

            # Run command_in in shell and get return
            command_out = subprocess.run(is_it_me_command['command'], shell=True,
                                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                text=True)

            # If command_out is not in command_out_actual go to next platform
            if is_it_me_command['contains'] not in command_out.stdout:
                break

        # If we made it here all commands were successful for this platform
        return platform_dict['platform_name'], platform_dict['modules']['default_modules']

    # If we made it here no matching platform identified
    return None, None


# --------------------------------------------------------------------------------------------------


def check_platform(platform):

    # Get the supported platforms
    possible_configs = os.listdir(os.path.join(return_config_path(), 'platforms'))

    # Remove anything that does not start with a character (avoid system files)
    possible_configs = [platform for platform in possible_configs if platform[0].isalnum()]

    # List of possible platforms
    possible_platforms = []

    # Loop over possible platforms
    for possible_config in possible_configs:

        # Open the dictionary
        possible_config_path = os.path.join(return_config_path(), 'platforms', possible_config)
        with open(possible_config_path, 'r') as possible_config_opened:
           possible_dict = yaml.safe_load(possible_config_opened)

        # Append list
        possible_platforms.append(possible_dict['platform_name'])

    # Check if platform is in possible platforms
    return platform in possible_platforms


# --------------------------------------------------------------------------------------------------
