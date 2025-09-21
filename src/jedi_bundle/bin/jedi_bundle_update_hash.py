#!/usr/bin/env python

# (C) Copyright 2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

# --------------------------------------------------------------------------------------------------

import argparse
from datetime import datetime, date, time, timezone
from jedi_bundle.utils.logger import Logger
from jedi_bundle.utils.update_hash import update_hash


def jedi_bundle_update_hash():

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('date', type=str,
                        help='Provide a date using YYYY-MM-DD format to update pinned versions \n'
                             'to the latest commit hashes before the provided date')

    logger = Logger('JediBundleUpdateHash')
    args = parser.parse_args()
    input_date = args.date

    # Convert date to datetime object
    dt_object = datetime.combine(date.fromisoformat(input_date), time(0, 0, tzinfo=timezone.utc))

    print(f'dt_object =  {dt_object}')

    # Call update hashes
    update_hash(logger, dt_object)

    logger.info(f'Updated pinned_versions.yaml to latest commits before {input_date}')
