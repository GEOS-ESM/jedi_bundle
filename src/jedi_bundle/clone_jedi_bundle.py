#!/usr/bin/env python

# (C) Copyright 2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

# --------------------------------------------------------------------------------------------------


import os

from jedi_bundle.config.config import return_config_path
from jedi_bundle.utils.config import config_get
from jedi_bundle.utils.file_system import check_for_executable
from jedi_bundle.utils.git import get_url_and_branch, clone_git_repo
from jedi_bundle.utils.yaml import load_yaml


# --------------------------------------------------------------------------------------------------


def clone_jedi(logger, clone_config):

    # Parse config
    # ------------
    user_branch = config_get(logger, clone_config, 'user_branch', '')
    github_orgs = config_get(logger, clone_config, 'github_orgs')
    bundles = config_get(logger, clone_config, 'bundles')
    path_to_source = config_get(logger, clone_config, 'path_to_source')

    # Check for needed executables
    # ----------------------------
    check_for_executable(logger, 'git')
    check_for_executable(logger, 'git-lfs')

    # Compile list of repos that need to be built
    # -------------------------------------------
    req_repos_all = []
    opt_repos_all = []
    for bundle in bundles:

        # Get dictionary for the bundle
        bundle_pathfile = os.path.join(return_config_path(), 'bundles', bundle + '.yaml')
        bundle_dict = load_yaml(logger, bundle_pathfile)

        # Repos that need to (can be) be built for this repo
        req_repos_bun = config_get(logger, bundle_dict, 'required_repos')
        opt_repos_bun = config_get(logger, bundle_dict, 'optional_repos', [])

        # Append complete list removing duplicates
        req_repos_all = list(set(req_repos_bun + req_repos_all))
        opt_repos_all = list(set(opt_repos_bun + opt_repos_all))

    # Remove repos from build order if not needed
    # -------------------------------------------
    build_order_pathfile = os.path.join(return_config_path(), 'bundles', 'build-order.yaml')
    build_order_dicts = load_yaml(logger, build_order_pathfile)
    indices_to_remove = []
    for index, build_order_dict in enumerate(build_order_dicts):
        repo = list(build_order_dict.keys())[0]
        if repo not in req_repos_all and repo not in opt_repos_all:
            indices_to_remove.append(index)

    indices_to_remove.reverse()
    for index_to_remove in indices_to_remove:
        del build_order_dicts[index_to_remove]

    # Loop through build order and clone repo
    # ---------------------------------------
    repo_list = []
    url_list = []
    branch_list = []
    cmakelists_list = []
    recursive_list = []

    optional_repos_not_found = []

    for index, build_order_dict in enumerate(build_order_dicts):

        repo = list(build_order_dict.keys())[0]

        # Extract repo information
        repo_dict = build_order_dict[repo]
        repo_url_name = config_get(logger, repo_dict, 'repo_url_name', repo)
        default_branch = config_get(logger, repo_dict, 'default_branch')
        cmakelists = config_get(logger, repo_dict, 'cmakelists', '')
        recursive = config_get(logger, repo_dict, 'recursive', False)

        found, url, branch = get_url_and_branch(logger, github_orgs, repo_url_name, default_branch,
                                                user_branch)

        if found:

            # List for writing CMakeLists.txt
            repo_list.append(repo)
            url_list.append(url)
            branch_list.append(branch)
            cmakelists_list.append(cmakelists)
            recursive_list.append(recursive)

        else:

            if repo in req_repos_all:
                logger.abort(f'No matching branch for repo \'{repo}\' was found in any ' +
                             f'organisations.')
            else:
                optional_repos_not_found.append(repo)

    # Print out information about clone
    # ---------------------------------
    repo_len = len(max(repo_list, key=len))
    url_len = len(max(url_list, key=len))
    branch_len = len(max(branch_list, key=len))

    logger.info(f'Repository clone summary:')
    logger.info(f'-------------------------')

    for repo, url, branch in zip(repo_list, url_list, branch_list):
        logger.info(f'Branch {branch.ljust(branch_len)} of {repo.ljust(repo_len)} ' +
                    f'will be cloned from {url.ljust(url_len)}')

    if optional_repos_not_found:
        logger.info(f' ')
        logger.info(f'The following optional repos are not being built:')
        for optional_repo_not_found in optional_repos_not_found:
            logger.info(f' {optional_repo_not_found}')
    logger.info(f'-------------------------')

    # Do the cloning
    # --------------
    for repo, url, branch in zip(repo_list, url_list, branch_list):

        logger.info(f'Cloning \'{repo}\'.')
        clone_git_repo(logger, url, branch, os.path.join(path_to_source, repo))

    # Create CMakeLists.txt file
    # --------------------------
    cmake_pathfile = os.path.join(return_config_path(), 'cmake.yaml')
    cmake_dict = load_yaml(logger, cmake_pathfile)

    cmake_header_lines = cmake_dict['header']
    cmake_footer_lines = cmake_dict['footer']

    output_file = os.path.join(path_to_source, 'CMakeLists.txt')

    # Max length of lists
    repo_len = len(max(repo_list, key=len))
    url_len = len(max(url_list, key=len))+2  # Plus 2 because of the quotes
    branch_len = len(max(branch_list, key=len))

    # Remove file if it exists
    if os.path.exists(output_file):
        os.remove(output_file)

    with open(output_file, 'a') as output_file_open:
        for cmake_header_line in cmake_header_lines:
            output_file_open.write(cmake_header_line + '\n')

        for repo, url, branch, cmake, recursive in zip(repo_list, url_list, branch_list,
                                                       cmakelists_list, recursive_list):

            urlq = f'\"{url}\"'

            package_line = f'ecbuild_bundle( PROJECT {repo.ljust(repo_len)} GIT ' + \
                           f'{urlq.ljust(url_len)} BRANCH {branch.ljust(branch_len)} UPDATE )'
            if recursive:
                package_line = package_line.replace('UPDATE )', 'UPDATE RECURSIVE)')
            output_file_open.write(package_line + '\n')
            if cmake != '':
                output_file_open.write(cmake + '\n')

        for cmake_footer_line in cmake_footer_lines:
            output_file_open.write(cmake_footer_line + '\n')


# --------------------------------------------------------------------------------------------------
