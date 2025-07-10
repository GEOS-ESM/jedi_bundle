#!/usr/bin/env python

# (C) Copyright 2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

import copy
import os
import re
import concurrent.futures

from jedi_bundle.config.config import return_config_path
from jedi_bundle.utils.config import config_get
from jedi_bundle.utils.file_system import check_for_executable
from jedi_bundle.utils.git import get_url_and_branch, clone_git_repo
from jedi_bundle.utils.yaml import load_yaml

def clone_jedi(logger, clone_config):
    """Clone JEDI repositories and generate CMakeLists.txt file.

    Args:
        logger: Logger object for output
        clone_config: Configuration dictionary
    """
    # Parse config
    # ------------
    user_branch = config_get(logger, clone_config, 'user_branch', '')
    github_orgs = config_get(logger, clone_config, 'github_orgs')
    bundles = config_get(logger, clone_config, 'bundles')
    path_to_source = config_get(logger, clone_config, 'path_to_source')
    extra_repos = config_get(logger, clone_config, 'extra_repos')
    crtm_tag_or_branch = config_get(logger, clone_config, 'crtm_tag_or_branch', 'v2.4-jedi.2')

    # Convert pinned_versions to a dictionary for efficient lookups
    pinned_versions_dict = {}
    if 'pinned_versions' in clone_config:
        for item in config_get(logger, clone_config, 'pinned_versions', []):
            for repo_name, repo_info in item.items():
                pinned_versions_dict[repo_name] = repo_info

    # Check for needed executables
    # ----------------------------
    check_for_executable(logger, 'git')
    check_for_executable(logger, 'git-lfs')

    # Compile list of repos that need to be built
    # -------------------------------------------
    req_repos_all = []
    opt_repos_all = []
    for bundle in bundles:
        bundle_pathfile = os.path.join(return_config_path(), 'bundles', bundle + '.yaml')
        bundle_dict = load_yaml(logger, bundle_pathfile)

        # Get required and optional repos for this bundle
        req_repos_bun = config_get(logger, bundle_dict, 'required_repos')
        opt_repos_bun = config_get(logger, bundle_dict, 'optional_repos', [])

        # Add to master lists, removing duplicates
        req_repos_all = list(set(req_repos_bun + req_repos_all))
        opt_repos_all = list(set(opt_repos_bun + opt_repos_all))

    # Load build order
    # ---------------
    build_order_pathfile = os.path.join(return_config_path(), 'bundles', 'build-order.yaml')
    build_order_dicts = load_yaml(logger, build_order_pathfile)

    # Adjust CRTM version if necessary
    # --------------------------------
    for index, build_order_dict in enumerate(build_order_dicts):
        if list(build_order_dict.keys())[0] == 'crtm':
            crtm_dict = copy.copy(build_order_dict)
            crtm_dict['crtm']['default_branch'] = crtm_tag_or_branch

            # Handle CRTM versioning
            if 'feature' in crtm_tag_or_branch or 'develop' in crtm_tag_or_branch:
                crtm_dict['crtm']['tag'] = False
                crtm_dict['crtm']['repo_url_name'] = 'CRTMv3'
            else:
                crtm_dict['crtm']['tag'] = True
                crtm_tag_major = re.sub(r'[^0-9]', '', crtm_tag_or_branch)[0]
                if int(crtm_tag_major) >= 3:
                    crtm_dict['crtm']['repo_url_name'] = 'CRTMv3'

            build_order_dicts[index] = crtm_dict
            break

    # Get list of repos in the build order
    # ------------------------------------
    build_order_repos = [list(d.keys())[0] for d in build_order_dicts]

    # Add extra repos to required list
    # --------------------------------
    req_repos_all.extend(extra_repos)

    # Validate all required/optional repos are in build order
    # ------------------------------------------------------
    all_repos = req_repos_all + opt_repos_all
    for repo in all_repos:
        if repo not in build_order_repos:
            logger.abort(f"Repository '{repo}' not found in build order. "
                         f"Add it to build-order.yaml in jedi_bundle.")

    # Filter build order to only include needed repos
    # ----------------------------------------------
    filtered_build_order = [
        d for d in build_order_dicts
        if list(d.keys())[0] in req_repos_all or list(d.keys())[0] in opt_repos_all
    ]

    # Process repositories to get clone information
    # --------------------------------------------
    repositories = []
    optional_repos_not_found = []
    url_branch_cache = {}  # Cache for URL and branch information

    logger.info('Gathering repository information...')
    for build_order_dict in filtered_build_order:
        repo = list(build_order_dict.keys())[0]
        repo_dict = build_order_dict[repo]

        # Extract repo information
        repo_url_name = config_get(logger, repo_dict, 'repo_url_name', repo)
        cmakelists = config_get(logger, repo_dict, 'cmakelists', '')
        recursive = config_get(logger, repo_dict, 'recursive', False)
        default_branch = config_get(logger, repo_dict, 'default_branch')
        is_tag = config_get(logger, repo_dict, 'tag', False)
        is_commit = config_get(logger, repo_dict, 'commit', False)

        # Apply pinned version overrides if available
        if repo in pinned_versions_dict:
            repo_info = pinned_versions_dict[repo]
            if 'branch' in repo_info:
                default_branch = repo_info['branch']
            if 'tag' in repo_info:
                is_tag = repo_info['tag']
            if 'commit' in repo_info:
                is_commit = repo_info['commit']
                if isinstance(is_commit, str):
                    default_branch = is_commit

        # Determine commit parameter for get_url_and_branch
        commit_param = False
        if isinstance(is_commit, str):
            commit_param = is_commit
        elif is_commit:
            commit_param = default_branch

        # Check cache first
        cache_key = f"{repo_url_name}:{default_branch}:{user_branch}:{is_tag}:{is_commit}"
        if cache_key in url_branch_cache:
            found, url, branch, final_is_tag, final_is_commit = url_branch_cache[cache_key]
        else:
            found, url, branch, final_is_tag, final_is_commit = get_url_and_branch(
                logger, github_orgs, repo_url_name, default_branch, user_branch, is_tag,
                commit_param
            )

            # Ensure branch displays commit hash for string commits
            if final_is_commit and isinstance(is_commit, str) and not branch:
                branch = is_commit

            # Ensure url and branch are strings
            url = url or ''
            branch = branch or ''

            # Save in cache
            url_branch_cache[cache_key] = (found, url, branch, final_is_tag, final_is_commit)

        if found:
            repositories.append({
                'name': repo,
                'url': url,
                'branch': branch,
                'cmake': cmakelists,
                'recursive': recursive,
                'is_tag': final_is_tag,
                'is_commit': final_is_commit
            })
        else:
            if repo in req_repos_all:
                logger.abort(f"No matching branch for '{repo}' was found in any organizations.")
            else:
                optional_repos_not_found.append(repo)

    # Print clone summary
    # ------------------
    if repositories:
        name_len = max(len(r['name']) for r in repositories)
        url_len = max(len(r['url']) for r in repositories)
        branch_len = max(len(r['branch']) for r in repositories)

        logger.info('Repository clone summary:')
        logger.info('-------------------------')

        for repo_info in repositories:
            branch_type = (
                'Tag' if repo_info['is_tag']
                else 'Commit' if repo_info['is_commit']
                else 'Branch'
            )
            logger.info(f"{branch_type.ljust(6)} {repo_info['branch'].ljust(branch_len)} of "
                        f"{repo_info['name'].ljust(name_len)} will be cloned from "
                        f"{repo_info['url'].ljust(url_len)}")

        if optional_repos_not_found:
            logger.info('')
            logger.info('The following optional repos are not being built:')
            for repo in optional_repos_not_found:
                logger.info(f' {repo}')
        logger.info('-------------------------')

    # Clone repositories in parallel
    # -----------------------------
    if repositories:
        logger.info(f"Starting parallel cloning of {len(repositories)} repositories")

        # Filter out jedicmake as it's handled specially
        clone_repos = [r for r in repositories if r['name'] != 'jedicmake']

        # Define worker function for clone operations
        def clone_worker(repo_info):
            try:
                repo_name = repo_info['name']
                url = repo_info['url']
                branch = repo_info['branch']
                is_tag = repo_info['is_tag']
                is_commit = repo_info['is_commit']

                logger.info(f"Cloning '{repo_name}'")
                if url:
                    clone_git_repo(
                        logger, url, branch,
                        os.path.join(path_to_source, repo_name),
                        is_tag, is_commit
                    )
                else:
                    logger.info(f"Skipping clone for {repo_name} because URL is empty")
                return True, repo_name
            except Exception as e:
                return False, f"Error cloning {repo_name}: {str(e)}"

        # Use ThreadPoolExecutor for parallel cloning
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            # Submit tasks
            future_to_repo = {
                executor.submit(clone_worker, repo_info): repo_info['name']
                for repo_info in clone_repos
            }

            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_repo):
                repo_name = future_to_repo[future]
                try:
                    success, result = future.result()
                    if not success:
                        logger.error(result)
                except Exception as e:
                    logger.error(f"Exception occurred while cloning {repo_name}: {str(e)}")

    # Log special case info
    if any(r['name'] == 'jedicmake' for r in repositories):
        logger.info("Skipping explicit clone of 'jedicmake' since it's usually a module. "
                    "If it's not a module it will be cloned at configure time.")

    # Create CMakeLists.txt file
    # --------------------------
    cmake_pathfile = os.path.join(return_config_path(), 'cmake.yaml')
    cmake_dict = load_yaml(logger, cmake_pathfile)

    cmake_header_lines = cmake_dict['header']
    cmake_footer_lines = cmake_dict['footer']

    output_file = os.path.join(path_to_source, 'CMakeLists.txt')

    # Calculate max lengths for formatting
    name_len = max(len(r['name']) for r in repositories) if repositories else 10
    url_len = max(len(r['url']) for r in repositories) if repositories else 0
    url_len += 2  # Add quotes
    branch_len = max(len(r['branch']) for r in repositories) if repositories else 0

    with open(output_file, 'w') as output_file_open:
        # Write header
        for line in cmake_header_lines:
            output_file_open.write(f"{line}\n")

        # Write packages in order from build-order.yaml
        for repo_info in repositories:
            repo = repo_info['name']
            url = repo_info['url']
            branch = repo_info['branch']
            cmake = repo_info['cmake']
            recursive = repo_info['recursive']
            is_tag = repo_info['is_tag']
            is_commit = repo_info['is_commit']

            # Format repository entry
            urlq = f'"{url}"'
            branch_or_tag = 'TAG' if is_tag else 'BRANCH'
            update = '' if (is_tag or is_commit) else 'UPDATE'
            recursive_clone = 'RECURSIVE' if recursive else ''

            package_line = (
                f'ecbuild_bundle( PROJECT {repo.ljust(name_len)} GIT '
                f'{urlq.ljust(url_len)} {branch_or_tag.ljust(6)} '
                f'{branch.ljust(branch_len)} {update.ljust(6)} '
                f'{recursive_clone.ljust(9)})'
            )

            # Special case for jedicmake
            if repo == 'jedicmake':
                jedi_cmake_lines = [
                    'if(DEFINED ENV{jedi_cmake_ROOT})',
                    '  include( $ENV{jedi_cmake_ROOT}/share/jedicmake/'
                    'Functions/git_functions.cmake )',
                    'else()',
                    f'  {package_line}',
                    '  include( jedicmake/cmake/Functions/git_functions.cmake )',
                    'endif()',
                    ''
                ]
                for line in jedi_cmake_lines:
                    output_file_open.write(f"{line}\n")
            else:
                output_file_open.write(f"{package_line}\n")
                if cmake:
                    output_file_open.write(f"{cmake}\n")

        # Write footer
        for line in cmake_footer_lines:
            output_file_open.write(f"{line}\n")
