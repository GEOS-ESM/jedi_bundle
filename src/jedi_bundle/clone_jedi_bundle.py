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
    extra_repos = config_get(logger, clone_config, 'extra_repos')

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

    # Load build order list of dictionaries
    # -------------------------------------
    build_order_pathfile = os.path.join(return_config_path(), 'bundles', 'build-order.yaml')
    build_order_dicts = load_yaml(logger, build_order_pathfile)

    # Get list of repos in the build order
    # ------------------------------------
    build_order_repos = []
    for build_order_dict in build_order_dicts:
        build_order_repos.append(list(build_order_dict.keys())[0])

    # Add extra repos
    # ---------------
    req_repos_all = req_repos_all + extra_repos

    # Check that all required, optional and extra repos appear in the build order dictionaries
    # ----------------------------------------------------------------------------------------
    repos_all = req_repos_all + opt_repos_all
    for repo in repos_all:
        if repo not in build_order_repos:
            logger.abort(f'Repository \'{repo}\' not found anywhere in the build order. Make ' +
                         f'sure to add to the build-order.yaml in jedi_bundle.')

    # Remove repos from build order if not needed
    # -------------------------------------------
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
    is_tag_list = []

    optional_repos_not_found = []

    for index, build_order_dict in enumerate(build_order_dicts):

        repo = list(build_order_dict.keys())[0]

        # Extract repo information
        repo_dict = build_order_dict[repo]
        repo_url_name = config_get(logger, repo_dict, 'repo_url_name', repo)
        default_branch = config_get(logger, repo_dict, 'default_branch')
        cmakelists = config_get(logger, repo_dict, 'cmakelists', '')
        recursive = config_get(logger, repo_dict, 'recursive', False)
        is_tag_in = config_get(logger, repo_dict, 'tag', False)

        found, url, branch, is_tag = get_url_and_branch(logger, github_orgs, repo_url_name,
                                                        default_branch, user_branch, is_tag_in)

        if found:

            # List for writing CMakeLists.txt
            repo_list.append(repo)
            url_list.append(url)
            branch_list.append(branch)
            cmakelists_list.append(cmakelists)
            recursive_list.append(recursive)
            is_tag_list.append(is_tag)

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

    for repo, url, branch, is_tag in zip(repo_list, url_list, branch_list, is_tag_list):
        branch_or_tag = 'Branch'
        if is_tag:
            branch_or_tag = 'Tag'
        logger.info(f'{branch_or_tag.ljust(6)} {branch.ljust(branch_len)} of ' +
                    f'{repo.ljust(repo_len)} will be cloned from {url.ljust(url_len)}')

    if optional_repos_not_found:
        logger.info(f' ')
        logger.info(f'The following optional repos are not being built:')
        for optional_repo_not_found in optional_repos_not_found:
            logger.info(f' {optional_repo_not_found}')
    logger.info(f'-------------------------')

    # Do the cloning
    # --------------
    for repo, url, branch, is_tag in zip(repo_list, url_list, branch_list, is_tag_list):

        logger.info(f'Cloning \'{repo}\'.')
        clone_git_repo(logger, url, branch, os.path.join(path_to_source, repo), is_tag)

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

        for repo, url, branch, cmake, recursive, is_tag in zip(repo_list, url_list, branch_list,
                                                               cmakelists_list, recursive_list,
                                                               is_tag_list):

            urlq = f'\"{url}\"'

            # Default cloning options
            branch_or_tag = 'BRANCH'
            update = 'UPDATE'
            recursive_clone = ''

            # If cloning a tag then turn off update and specify tag
            if is_tag:
                branch_or_tag = 'TAG'
                update = ''

            # Add recursive if needed
            if recursive:
                recursive_clone = 'RECURSIVE'

            package_line = f'ecbuild_bundle( PROJECT {repo.ljust(repo_len)} GIT ' + \
                           f'{urlq.ljust(url_len)} {branch_or_tag.ljust(6)} ' + \
                           f'{branch.ljust(branch_len)} {update.ljust(6)} ' + \
                           f'{recursive_clone.ljust(9)})'

            if repo == 'jedicmake':
                # Special case for jedicmake'
                jedi_cmake_lines = [
                  'if(DEFINED ENV{jedi_cmake_ROOT})',
                  '  include( $ENV{jedi_cmake_ROOT}/share/jedicmake/Functions/' +
                  'git_functions.cmake )',
                  'else()',
                  '  ' + package_line,
                  '  include( jedicmake/cmake/Functions/git_functions.cmake )',
                  'endif()',
                  ''
                ]
                for jedi_cmake_line in jedi_cmake_lines:
                    output_file_open.write(jedi_cmake_line + '\n')

            else:

                output_file_open.write(package_line + '\n')
                if cmake != '':
                    output_file_open.write(cmake + '\n')

        for cmake_footer_line in cmake_footer_lines:
            output_file_open.write(cmake_footer_line + '\n')


# --------------------------------------------------------------------------------------------------
