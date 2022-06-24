#!/usr/bin/env python

# (C) Copyright 2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

# --------------------------------------------------------------------------------------------------


import os

from jedi_bundle.config.config import return_config_path
from jedi_bundle.utils.file_system import check_for_executable
from jedi_bundle.utils.git import get_url_and_branch, clone_git_repo
from jedi_bundle.utils.yaml import load_yaml


# --------------------------------------------------------------------------------------------------


def clone_jedi(logger, config):

    # Parse config
    # ------------
    user_branch = config['source code options']['user branch']
    github_orgs = config['source code options']['github orgs']
    bundles = config['source code options']['bundles']
    path_to_source = config['source code options']['path to source']

    # Check for needed executables
    # ----------------------------
    check_for_executable(logger, 'git')
    check_for_executable(logger, 'git-lfs')

    # Compile list of repos that need to be built
    # -------------------------------------------
    repos_all = []
    for bundle in bundles:

        # Get dictionary for the bundle
        bundle_pathfile = os.path.join(return_config_path(), bundle + '.yaml')
        bundle_dict = load_yaml(logger, bundle_pathfile)

        # Build order for this bundle
        repos_bun = bundle_dict['required repos']

        # Append complete list removing duplicates
        repos_all = list(set(repos_bun + repos_all))

    # Remove repos from build order if not needed
    # -------------------------------------------
    build_order_pathfile = os.path.join(return_config_path(), 'build-order.yaml')
    build_order_dicts = load_yaml(logger, build_order_pathfile)
    indices_to_remove = []
    for index, build_order_dict in enumerate(build_order_dicts):
        repo = list(build_order_dict.keys())[0]
        if repo not in repos_all:
            indices_to_remove.append(index)

    indices_to_remove.reverse()
    for index_to_remove in indices_to_remove:
        del build_order_dicts[index_to_remove]

    # Loop through build order and clone repo
    # ---------------------------------------
    repo_list = []
    url_list = []
    branch_list = []
    cmake_list = []
    for index, build_order_dict in enumerate(build_order_dicts):

        repo = list(build_order_dict.keys())[0]
        repo_dict = build_order_dict[repo]

        # Identify repo and branch to clone
        url, branch = get_url_and_branch(logger, repo, repo_dict, github_orgs, user_branch)

        # List for writing CMakeLists.txt
        repo_list.append(repo)
        url_list.append(url)
        branch_list.append(branch)

        # Extra things needed in the CMakeLists
        cmake_list.append(repo_dict.get('cmakelists', ''))

        # Clone the repos to the target directory
        target = os.path.join(path_to_source, repo)
        clone_git_repo(logger, url, branch, target)

    # Create the CMakeLists.txt
    # -------------------------
    cmake_pathfile = os.path.join(return_config_path(), 'cmake.yaml')
    cmake_dict = load_yaml(logger, cmake_pathfile)

    cmake_header_lines = cmake_dict['header']
    cmake_footer_lines = cmake_dict['footer']

    output_file = os.path.join(path_to_source, 'CMakeLists.txt')

    # Max length of lists
    repo_len = len(max(repo_list, key=len))
    url_len = len(max(url_list, key=len))+2
    branch_len = len(max(branch_list, key=len))

    # Remove file if it exists
    if os.path.exists(output_file):
        os.remove(output_file)

    with open(output_file, 'a') as output_file_open:
        for cmake_header_line in cmake_header_lines:
            output_file_open.write(cmake_header_line + '\n')

        for repo, url, branch, cmake in zip(repo_list, url_list, branch_list, cmake_list):

            urlq = f'\"{url}\"'

            package_line = f'ecbuild_bundle( PROJECT {repo.ljust(repo_len)} GIT ' + \
                           f'{urlq.ljust(url_len)} BRANCH {branch.ljust(branch_len)} UPDATE )'
            output_file_open.write(package_line + '\n')
            if cmake != '':
                output_file_open.write(cmake + '\n')

        for cmake_footer_line in cmake_footer_lines:
            output_file_open.write(cmake_footer_line + '\n')


# --------------------------------------------------------------------------------------------------
