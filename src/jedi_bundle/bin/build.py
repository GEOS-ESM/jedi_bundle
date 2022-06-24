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
import subprocess
import sys
import yaml

# --------------------------------------------------------------------------------------------------

def load_yaml(pathfile):

    # Convert the config file to a dictionary
    try:
        with open(pathfile, 'r') as pathfile_opened:
            dict = yaml.safe_load(pathfile_opened)
    except Exception as e:
            print('Jedi build code f is expecting a valid yaml file, but it encountered ' +
                    f'errors when attempting to load: {pathfile}, error: {e}')
            exit(1)

    return dict

# --------------------------------------------------------------------------------------------------

def get_github_username_token():

    # Extract github username from /home/user/git-credentials
    user = os.getenv('USER')
    git_cred_path = os.path.join('/home', user, '.git-credentials')
    try:
        with open(git_cred_path) as f:
            git_cred_line = f.readlines()[0].rstrip()
        git_cred_line = git_cred_line.replace('https://', '')
        git_cred_line = git_cred_line.replace('@github.com', '')
        username, token = git_cred_line.split(':')
    except Exception as e:
        print("Error reading /home/$USER/.git-credentials not found. Private repos wont be used.")
        username = ''
        token = ''

    return username, token

# --------------------------------------------------------------------------------------------------

def repo_is_reachable(url, username, token):

    # Default is that the repo is not reachable
    is_reachable = False

    try:
        get = requests.get(url, auth=(username,token))
        if get.status_code == 200:
            # Check that the full name provided by API is expected path.
            # Sometimes this value is inconsistent with the repo path.
            gh_api_dict = get.json()
            if 'full_name' in gh_api_dict:
                full_name = gh_api_dict['full_name']
                if full_name in url:
                    is_reachable = True
    except:
        is_reachable = False

    return is_reachable

# --------------------------------------------------------------------------------------------------

def repo_has_branch(url, branch):

    # Command to check if branch exists and pass exit code back
    git_ls_cmd = ['git', 'ls-remote', '--heads', '--exit-code', url, branch]

    # Run command
    process = subprocess.run(git_ls_cmd, stdout=subprocess.DEVNULL)

    # Print the exit code.
    if process.returncode == 0:
        return True
    else:
        return False

# --------------------------------------------------------------------------------------------------

def clone_git_repo(url, branch, target):

    # Check if directory already exists
    if not os.path.exists(target):

        # Write info
        print(f'Cloning branch {branch} of {url} to {target}...')

        # Command to check if branch exists and pass exit code back
        git_clone_cmd = ['git', 'clone', '-b', branch, url, target]

        # Run command
        process = subprocess.run(git_clone_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Assert that clone was successful
        if process.returncode != 0:
            print(f'ABORT: Git clone of branch {branch} from {url} failed.')
            exit(1)

    else:

        # Write info
        print(f'Repo {url}, already cloned. Updating branch...')

        # Fetch, change branch and pull latest
        cwd = os.getcwd()
        os.chdir(target)
        process = subprocess.run(['git', 'fetch'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        process = subprocess.run(['git', 'checkout', branch], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        process = subprocess.run(['git', 'pull', 'origin', branch], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.chdir(cwd)

# --------------------------------------------------------------------------------------------------

def get_url_and_branch(repo, repo_dict, github_orgs, special_branch):

    # Get GitHub username and token if .git-credentials file available
    username, token = get_github_username_token()

    # Name of repo in the url
    repo_url_name = repo_dict.get('repo url name', repo)

    # Name of default branch for repo
    default_branch = repo_dict.get('default branch', 'develop')

    # Check the repo is found at at least one url
    repo_url_found = False

    # Track urls where repo was found
    repo_found_at = []

    # Track finding of the user branch and the default branch
    found_special_branch = False
    found_default_branch = False

    # Loop over URLs
    for github_org in github_orgs:

        # Full path of the repo url
        github_url = os.path.join('https://github.com', github_org, repo_url_name)
        github_api_url = os.path.join('https://api.github.com/repos', github_org, repo_url_name)

        # Check it the repo url is reachable
        if repo_is_reachable(github_api_url, username, token):

            # Assert that the repo was found somewhere
            repo_found_at.append(github_url)
            repo_url_found = True

            # Look for the branches
            has_special_branch = repo_has_branch(github_url, special_branch)
            has_default_branch = repo_has_branch(github_url, default_branch)

            # Update the flags if the branch is found
            if not found_special_branch and has_special_branch:
                found_special_branch = True
                repo_url_to_use = github_url
                repo_branch_to_use = special_branch
            if not found_default_branch and has_default_branch:
                found_default_branch = True
                default_repo_url_to_use = github_url
                default_repo_branch_to_use = default_branch

    # Assert that the repo is found somewhere
    if not repo_url_found:
        print(f'ABORT: Repo {repo} not found at any of the URLs')
        exit(1)

    # Update the
    if not found_special_branch:
        if found_default_branch:
            repo_url_to_use = default_repo_url_to_use
            repo_branch_to_use = default_repo_branch_to_use
        else:
            print(f'ABORT: neither the user branch \'{special_branch}\' or default branch '
                  f'\'{default_branch}\' was found anywhere for {repo_url_name}. Searched in {repo_found_at}')
            exit(1)

    # Display information for the repo
    print(f'For {repo.ljust(15)} branch {repo_branch_to_use.ljust(20)} will be cloned from \'{repo_url_to_use}\'')

    return repo_url_to_use, repo_branch_to_use

# --------------------------------------------------------------------------------------------------

def create_cmakelist_for_bundle(cmake_dict, path_to_source, repo_list, url_list, branch_list):

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

        for repo, url, branch in zip(repo_list, url_list, branch_list):

            urlq = f'\"{url}\"'

            package_line = f'ecbuild_bundle( PROJECT {repo.ljust(repo_len)} GIT {urlq.ljust(url_len)} BRANCH {branch.ljust(branch_len)} UPDATE )'
            output_file_open.write(package_line + '\n')

        for cmake_footer_line in cmake_footer_lines:
            output_file_open.write(cmake_footer_line + '\n')


# --------------------------------------------------------------------------------------------------

def run_cmake_configure(build_dir, source_dir, build):

    # File to hold configure steps
    configure_file = os.path.join(build_dir, 'run_configure.sh')

    # Remove if it exists
    if os.path.exists(configure_file):
        os.remove(configure_file)

    # Write steps to file
    with open(configure_file, 'a') as configure_file_open:
        configure_file_open.write('#!/usr/bin/env bash' + '\n')
        configure_file_open.write('source modules' + '\n')
        configure_file_open.write(f'ecbuild --build={build} -DMPIEXEC=$MPIEXEC {source_dir}' + '\n')

    # Make file executable
    os.chmod(configure_file, 0o755)

    # Configure command
    configure = [f'./run_configure.sh']

    # Run command
    cwd = os.getcwd()
    os.chdir(build_dir)
    process = subprocess.run(configure)
    os.chdir(cwd)

# --------------------------------------------------------------------------------------------------

def build(build_config):

    # Argument check
    # --------------
    assert isinstance(build_config, dict), "Input to build routine is not a dictionary"

    # Parse configuration
    # -------------------
    root_path = build_config['root path']

    # Build things
    platform = build_config['build options']['platform']
    modules = build_config['build options']['modules']
    build = build_config['build options']['build']
    configure = build_config['build options']['configure']
    path_to_build = build_config['build options']['path to build']

    # Source code things
    user_branch = build_config['source code options']['user branch']
    github_orgs = build_config['source code options']['github orgs']
    bundles = build_config['source code options']['bundles']
    path_to_source = build_config['source code options']['path to source']

    # CMakeLists.txt config
    cmake_pathfile = os.path.join(root_path, 'cmake.yaml')
    cmake_dict = load_yaml(cmake_pathfile)

    # Platform config
    platform_pathfile = os.path.join(root_path, 'platforms', platform + '.yaml')
    platform_dict = load_yaml(platform_pathfile)
    module_directives = platform_dict['modules'][modules]

    # Compile list of repos that need to be built
    # -------------------------------------------
    repos_all = []
    for bundle in bundles:

        # Get dictionary for the bundle
        bundle_pathfile = os.path.join(root_path, bundle + '.yaml')
        bundle_dict = load_yaml(bundle_pathfile)

        # Build order for this bundle
        repos_bun = bundle_dict['required repos']

        # Append complete list removing duplicates
        repos_all = list(set(repos_bun + repos_all))

    # Remove repos from build if not needed
    # -------------------------------------
    build_order_pathfile = os.path.join(root_path, 'build-order.yaml')
    build_order_dicts = load_yaml(build_order_pathfile)
    indices_to_remove = []
    for index, build_order_dict in enumerate(build_order_dicts):
        repo = list(build_order_dict.keys())[0]
        if repo not in repos_all:
            indices_to_remove.append(index)

    indices_to_remove.reverse()
    for index_to_remove in indices_to_remove:
        del build_order_dicts[index_to_remove]

    # Clone, configure and build
    # --------------------------
    repo_list = []
    url_list = []
    branch_list = []
    for index, build_order_dict in enumerate(build_order_dicts):

        repo = list(build_order_dict.keys())[0]
        repo_dict = build_order_dict[repo]

        # Identify repo and branch to clone
        url, branch = get_url_and_branch(repo, repo_dict, github_orgs, user_branch)

        # List for writing CMakeLists.txt
        repo_list.append(repo)
        url_list.append(url)
        branch_list.append(branch)

        # Clone the repos to the target directory
        target = os.path.join(path_to_source, repo)
        os.makedirs(target, mode=0o755, exist_ok=True)
        #clone_git_repo(url, branch, target)

    # Create CMakeLists.txt
    create_cmakelist_for_bundle(cmake_dict, path_to_source, repo_list, url_list, branch_list)

    # Create build directory
    build_dir = os.path.join(path_to_build, f'build-{modules}-{build}')
    os.makedirs(build_dir, mode=0o755, exist_ok=True)

    # Create modules file
    modules_file = os.path.join(build_dir, 'modules')
    if os.path.exists(modules_file):
        os.remove(modules_file)
    with open(modules_file, 'a') as modules_file_open:
        for module_directive in module_directives:
            modules_file_open.write(module_directive + '\n')

    # Run configure step
    run_cmake_configure(build_dir, path_to_source, build)

        # Run make step
        #run_cmake_build()




    # Write the CM




# --------------------------------------------------------------------------------------------------

def main():

    # Arguments
    # ---------
    parser = argparse.ArgumentParser()
    parser.add_argument('config_file', type=str, help='Configuration YAML file for driving ' +
                        'the build system.')

    # Get the configuration file
    args = parser.parse_args()
    config_file = args.config_file

    assert os.path.exists(config_file), "File " + config_file + " not found"

    # Convert the config file to a dictionary
    config_dict = load_yaml(config_file)

    # Add the path to the source code to config
    config_dict['root path'] = os.path.split(sys.argv[0])[0]

    # Run the diagnostic(s)
    build(config_dict)

# --------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    main()

 # -------------------------------------------------------------------------------------------------