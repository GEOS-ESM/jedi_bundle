# (C) Copyright 2021-2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

# --------------------------------------------------------------------------------------------------


from jedi_bundle import __version__
from jedi_bundle.utils.logger import Logger


# --------------------------------------------------------------------------------------------------


def write_welcome_message():

    logger = Logger('')

    jedi_bundle_1 = f"   _          _ _   _                     _ _       "  # noqa
    jedi_bundle_2 = f"  (_) ___  __| (_) | |__  _   _ _ __   __| | | ___  "  # noqa
    jedi_bundle_3 = f"  | |/ _ \/ _` | | | '_ \| | | | '_ \ / _` | |/ _ \ "  # noqa
    jedi_bundle_4 = f"  | |  __/ (_| | | | |_) | |_| | | | | (_| | |  __/ "  # noqa
    jedi_bundle_5 = f" _/ |\___|\__,_|_| |_.__/ \__,_|_| |_|\__,_|_|\___| "  # noqa
    jedi_bundle_6 = f"|__/                                                "  # noqa

    logger.blank("")
    logger.blank(jedi_bundle_1)
    logger.blank(jedi_bundle_2 + f"   Jedi Bundle Build System")
    logger.blank(jedi_bundle_3 + f"   NASA Global Modelling and Assimilation Office")
    logger.blank(jedi_bundle_4 + f"   Version {__version__}")
    logger.blank(jedi_bundle_5 + f"   \x1B[4m\x1B[34mhttps://geos-esm.github.io/jedi_bundle\033[0m")
    logger.blank(jedi_bundle_6)
    logger.blank("")
