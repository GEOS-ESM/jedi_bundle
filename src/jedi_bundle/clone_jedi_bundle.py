#!/usr/bin/env python

# (C) Copyright 2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

# --------------------------------------------------------------------------------------------------

import copy
import os
import re
import concurrent.futures

from jedi_bundle.config.config import return_config_path
from jedi_bundle.utils.config import config_get
from jedi_bundle.utils.file_system import check_for_executable
from jedi_bundle.utils.git import get_url_and_branch, clone_git_repo, clone_git_file
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
    crtm_tag_or_branch = config_get(logger, clone_config, 'crtm_tag_or_branch', 'v2.4-jedi.2')
    if 'pinned_versions' in clone_config:
        pinned_versions = config_get(logger, clone_config, 'pinned_versions')
        # Convert pinned_versions to a dictionary for O(1) lookups
        pinned_versions_dict = {}
        for d in pinned_versions:
            for repo_name, repo_info in d.items():
                pinned_versions_dict[repo_name] = repo_info
    else:
        pinned_versions = None
        pinned_versions_dict = {}

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

    # Adjust CRTM version if necessary
    # --------------------------------
    crtm_index = None
    for index, build_order_dict in enumerate(build_order_dicts):
        if list(build_order_dict.keys())[0] == 'crtm':
            crtm_dict = copy.copy(build_order_dicts[index])
            break

    # Set the crtm tag/branch
    crtm_dict['crtm']['default_branch'] = crtm_tag_or_branch

    # Strip any numbers from crtm version and convert to integer
    if 'feature' in crtm_tag_or_branch or 'develop' in crtm_tag_or_branch:
        # Not a tag
        crtm_dict['crtm']['tag'] = False
        # If user wants a branch assume crtm V3
        crtm_dict['crtm']['repo_url_name'] = 'CRTMv3'
    else:
        # Is a tag
        crtm_dict['crtm']['tag'] = True
        # Determine major version
        crtm_tag_major = re.sub(r'[^0-9]', '', crtm_tag_or_branch)[0]
        # Switch to V3 repo if major version is 3 or greater
        if int(crtm_tag_major) >= 3:
            crtm_dict['crtm']['repo_url_name'] = 'CRTMv3'

    # Pass dictionary back
    build_order_dicts[index] = crtm_dict

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
    is_commit_list = []

    optional_repos_not_found = []

    # Cache for URL and branch information
    url_branch_cache = {}

    logger.info(f'Gathering repository information...')
    for index, build_order_dict in enumerate(build_order_dicts):
        repo = list(build_order_dict.keys())[0]

        # Extract repo information
        repo_dict = build_order_dict[repo]
        repo_url_name = config_get(logger, repo_dict, 'repo_url_name', repo)
        cmakelists = config_get(logger, repo_dict, 'cmakelists', '')
        recursive = config_get(logger, repo_dict, 'recursive', False)
        default_branch = config_get(logger, repo_dict, 'default_branch')
        is_tag_in = config_get(logger, repo_dict, 'tag', False)
        is_commit_in = config_get(logger, repo_dict, 'commit', False)

        # Extract information from pinned_versions if applicable - use direct dictionary lookup
        if pinned_versions_dict and repo in pinned_versions_dict:
            repo_info = pinned_versions_dict[repo]
            if 'branch' in repo_info:
                default_branch = repo_info['branch']
            if 'tag' in repo_info:
                is_tag_in = repo_info['tag']
            if 'commit' in repo_info:
                is_commit_in = repo_info['commit']
                # For commits that are strings, use as default_branch
                if isinstance(is_commit_in, str):
                    default_branch = is_commit_in

        # Check cache first
        cache_key = f"{repo_url_name}:{default_branch}:{user_branch}:{is_tag_in}:{is_commit_in}"
        if cache_key in url_branch_cache:
            found, url, branch, is_tag, is_commit = url_branch_cache[cache_key]
        else:
            # For commits, ensure proper parameter format
            if isinstance(is_commit_in, str):  # If commit is a string, use it directly
                commit_param = is_commit_in
            elif is_commit_in:  # If commit is True but not a string, use default branch
                commit_param = default_branch
            else:  # Otherwise, it's False
                commit_param = False

            found, url, branch, is_tag, is_commit = get_url_and_branch(
                logger, github_orgs, repo_url_name, default_branch, user_branch, is_tag_in,
                commit_param
            )

            # Ensure branch displays commit hash for commits
            if is_commit and isinstance(is_commit_in, str) and not branch:
                branch = is_commit_in

            # Ensure url and branch are always strings (even if empty)
            url = url or ''
            branch = branch or ''

            # Save in cache
            url_branch_cache[cache_key] = (found, url, branch, is_tag, is_commit)

        if found:
            # List for writing CMakeLists.txt
            repo_list.append(repo)
            url_list.append(url)
            branch_list.append(branch)
            cmakelists_list.append(cmakelists)
            recursive_list.append(recursive)
            is_tag_list.append(is_tag)
            is_commit_list.append(is_commit)
        else:
            if repo in req_repos_all:
                logger.abort(f'No matching branch for repo \'{repo}\' was found in any ' +
                             f'organisations.')
            else:
                optional_repos_not_found.append(repo)

    # Write out information about clone
    # ---------------------------------
    if repo_list:  # Only if we have repos to clone
        repo_len = len(max(repo_list, key=len))
        url_len = len(max(url_list, key=len) or '')  # Handle possible empty list
        branch_len = len(max(branch_list, key=len) or '')  # Handle possible empty list

        logger.info(f'Repository clone summary:')
        logger.info(f'-------------------------')

        for repo, url, branch, is_tag, is_commit in zip(repo_list, url_list, branch_list,
                                                        is_tag_list, is_commit_list):
            branch_or_tag = 'Branch'
            if is_tag:
                branch_or_tag = 'Tag'
            if is_commit:
                branch_or_tag = 'Commit'
            logger.info(f'{branch_or_tag.ljust(6)} {branch.ljust(branch_len)} of ' +
                        f'{repo.ljust(repo_len)} will be cloned from {url.ljust(url_len)}')

        if optional_repos_not_found:
            logger.info(f' ')
            logger.info(f'The following optional repos are not being built:')
            for optional_repo_not_found in optional_repos_not_found:
                logger.info(f' {optional_repo_not_found}')
        logger.info(f'-------------------------')

    # Special case for fv3 - grab fv3-interface.cmake first
    fv3_index = None
    fv3_info = None
    if 'fv3' in repo_list:
        fv3_index = repo_list.index('fv3')
        logger.info('Preparing fv3-interface.cmake from the jedi-bundle repo')
        found, url_tmp, branch_tmp, _, _ = get_url_and_branch(
            logger, github_orgs, 'jedi-bundle', 'develop', user_branch, False, False
        )
        if found:
            clone_git_file(logger, url_tmp, ['fv3-interface.cmake'], path_to_source, depth=1)

        # Store fv3 info but don't remove it from the lists
        # We'll handle its position in CMakeLists.txt separately
        fv3_info = {
            'index': fv3_index,
            'url': url_list[fv3_index],
            'branch': branch_list[fv3_index],
            'cmake': cmakelists_list[fv3_index],
            'recursive': recursive_list[fv3_index],
            'is_tag': is_tag_list[fv3_index],
            'is_commit': is_commit_list[fv3_index],
        }

    # Do the cloning in parallel
    # --------------------------
    if repo_list:  # Only if we have repos to clone
        logger.info(f'Starting parallel cloning of {len(repo_list)} repositories')

        # Filter out jedicmake as it's handled specially
        clone_repos = []
        clone_urls = []
        clone_branches = []
        clone_is_tags = []
        clone_is_commits = []

        for i, repo in enumerate(repo_list):
            if repo != 'jedicmake':
                clone_repos.append(repo)
                clone_urls.append(url_list[i])
                clone_branches.append(branch_list[i])
                clone_is_tags.append(is_tag_list[i])
                clone_is_commits.append(is_commit_list[i])

        # Define a worker function for clone operations
        def clone_worker(repo, url, branch, is_tag, is_commit):
            try:
                logger.info(f'Cloning \'{repo}\'')
                if url:  # Only attempt cloning if URL is provided
                    clone_git_repo(logger, url, branch, os.path.join(path_to_source, repo), is_tag,
                                   is_commit)
                else:
                    logger.info(f'Skipping clone for {repo} because URL is empty')
                return True, repo
            except Exception as e:
                return False, f"Error cloning {repo}: {str(e)}"

        # Use ThreadPoolExecutor for parallel cloning
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            # Submit tasks
            future_to_repo = {
                executor.submit(clone_worker, repo, url, branch, is_tag, is_commit): repo
                for repo, url, branch, is_tag, is_commit in zip(
                    clone_repos, clone_urls, clone_branches, clone_is_tags, clone_is_commits
                )
            }

            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_repo):
                repo = future_to_repo[future]
                try:
                    success, result = future.result()
                    if not success:
                        logger.error(result)
                except Exception as e:
                    logger.error(f"Exception occurred while cloning {repo}: {str(e)}")

    # Handle special cases
    if 'jedicmake' in repo_list:
        logger.info(f'Skipping explicit clone of \'jedicmake\' since it\'s usually a module. ')

    # Create CMakeLists.txt file
    # --------------------------
    cmake_pathfile = os.path.join(return_config_path(), 'cmake.yaml')
    cmake_dict = load_yaml(logger, cmake_pathfile)

    cmake_header_lines = cmake_dict['header']
    cmake_footer_lines = cmake_dict['footer']

    output_file = os.path.join(path_to_source, 'CMakeLists.txt')

    # Calculate max lengths for formatting
    repo_len = len(max(repo_list, key=len)) if repo_list else 10
    url_len = len(max([u for u in url_list if u], key=len, default='')) + 2  # +2 for quotes
    branch_len = len(max([b for b in branch_list if b], key=len, default=''))

    with open(output_file, 'w') as output_file_open:
        # Write header
        for cmake_header_line in cmake_header_lines:
            output_file_open.write(cmake_header_line + '\n')

        # Helper function to write repository entry to CMakeLists.txt
        def write_repo_entry(repo, url, branch, cmake, recursive, is_tag, is_commit):
            urlq = f'\"{url}\"'

            # Default cloning options
            branch_or_tag = 'BRANCH'
            update = 'UPDATE'
            recursive_clone = ''

            # If cloning a tag then turn off update and specify tag
            if is_tag:
                branch_or_tag = 'TAG'
                update = ''

            # if commit, proceed as you would with branch but turn off update
            if is_commit:
                branch_or_tag = 'BRANCH'
                update = ''

            # Add recursive if needed
            if recursive:
                recursive_clone = 'RECURSIVE'

            package_line = f'ecbuild_bundle( PROJECT {repo.ljust(repo_len)} GIT ' + \
                           f'{urlq.ljust(url_len)} {branch_or_tag.ljust(6)} ' + \
                           f'{branch.ljust(branch_len)} {update.ljust(6)} ' + \
                           f'{recursive_clone.ljust(9)})'

            if repo == 'jedicmake':
                # Special case for jedicmake
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
                if cmake:
                    output_file_open.write(cmake + '\n')

        # Process repositories in correct order:
        # 1. First all repositories up to fv3-* repositories
        # 2. Then fv3 with its special includes
        # 3. Then all fv3-* repositories
        # 4. Finally all remaining repositories

        fv3_related_indices = []
        for i, repo in enumerate(repo_list):
            if repo.startswith('fv3-'):
                fv3_related_indices.append(i)

        # Write all repositories before fv3-* ones
        for i, repo in enumerate(repo_list):
            if (
                i not in fv3_related_indices
                and (fv3_index is None or i < fv3_index)
                and repo != 'fv3'
            ):
                write_repo_entry(
                    repo, url_list[i], branch_list[i], cmakelists_list[i],
                    recursive_list[i], is_tag_list[i], is_commit_list[i]
                )

        # Write fv3 if it exists (with special includes)
        if fv3_info:
            # First add the interface include and rpath commands
            output_file_open.write(' include(fv3-interface.cmake )\n')
            output_file_open.write(f' list( APPEND CMAKE_INSTALL_RPATH ' +
                                   '${{CMAKE_CURRENT_BINARY_DIR}}/fv3 )\n')

            # Then add the actual fv3 repo
            write_repo_entry(
                'fv3', fv3_info['url'], fv3_info['branch'], fv3_info['cmake'],
                fv3_info['recursive'], fv3_info['is_tag'], fv3_info['is_commit']
            )

        # Write all fv3-* repositories
        for i in fv3_related_indices:
            write_repo_entry(
                repo_list[i], url_list[i], branch_list[i], cmakelists_list[i],
                recursive_list[i], is_tag_list[i], is_commit_list[i]
            )

        # Write all remaining repositories (after fv3-* ones)
        remaining_indices = [i for i in range(len(repo_list))
                             if i not in fv3_related_indices and
                             (fv3_index is None or i > fv3_index) and
                             repo_list[i] != 'fv3']
        for i in remaining_indices:
            write_repo_entry(
                repo_list[i], url_list[i], branch_list[i], cmakelists_list[i],
                recursive_list[i], is_tag_list[i], is_commit_list[i]
            )

        # Write footer
        for cmake_footer_line in cmake_footer_lines:
            output_file_open.write(cmake_footer_line + '\n')
