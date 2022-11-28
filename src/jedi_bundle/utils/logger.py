# (C) Copyright 2021-2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

# --------------------------------------------------------------------------------------------------


import os
import sys


# --------------------------------------------------------------------------------------------------
#  @package logger
#
#  Class containing a logger.
#
# --------------------------------------------------------------------------------------------------


class colors:
    norm = '\033[0m'
    abort = '\033[91m'
    warning = '\033[93m'


# --------------------------------------------------------------------------------------------------


class Logger:

    def __init__(self, task_name):

        self.task_name = task_name

        # Set default logging levels
        self.loggerdict = {'BLANK': True,
                           'INFO': True,
                           'TRACE': False,
                           'DEBUG': False, }

        # Loop over logging levels
        for loglevel in self.loggerdict:

            # Check for environment variable e.g. LOG_TRACE=1 will activiate trace logging
            log_env = os.environ.get('LOG_'+loglevel)

            # If found set element to environment variable
            if log_env is not None:
                self.loggerdict[loglevel] = int(log_env) == 1

    # ----------------------------------------------------------------------------------------------

    def send_message(self, level, message):

        level_show = ''
        if level != 'BLANK':
            level_show = level + ' '+self.task_name+': '

        if level == 'ABORT' or self.loggerdict[level]:
            print(level_show+message)

    # ----------------------------------------------------------------------------------------------

    def info(self, message):

        self.send_message('INFO', f'{message}')

    # ----------------------------------------------------------------------------------------------

    def trace(self, message):

        self.send_message('TRACE', f'{message}')

    # ----------------------------------------------------------------------------------------------

    def debug(self, message):

        self.send_message('DEBUG', f'{message}')

    # ----------------------------------------------------------------------------------------------

    def blank(self, message):

        self.send_message('BLANK', message)

    # ----------------------------------------------------------------------------------------------

    def abort(self, message):

        self.send_message(f'ABORT', f'{colors.abort}{message} ABORTING... {colors.norm}')
        sys.exit()

    # ----------------------------------------------------------------------------------------------

    def input(self, *messages):

        # Print messages
        for message in messages:
            self.send_message('INFO', f'{colors.warning}{message}{colors.norm}')

        # Print continuation message
        input(f'INFO {self.task_name}: {colors.warning}Press any key to continue...{colors.norm}\n')

    # ----------------------------------------------------------------------------------------------
