#!/usr/bin/env python

# (C) Copyright 2022 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration. All Rights Reserved.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

# --------------------------------------------------------------------------------------------------

import os
import requests
import subprocess

# --------------------------------------------------------------------------------------------------

def get_github_username_token(logger):

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
        logger.info(f'Credentials {git_cred_path} not found. Private repos wont be found.')
        username = ''
        token = ''

    return username, token

# --------------------------------------------------------------------------------------------------

def repo_is_reachable(logger, url, username, token):

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

def repo_has_branch(logger, url, branch):

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

def get_url_and_branch(logger, repo, repo_dict, github_orgs, special_branch):

    # Get GitHub username and token if .git-credentials file available
    username, token = get_github_username_token(logger)

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
        if repo_is_reachable(logger, github_api_url, username, token):

            # Assert that the repo was found somewhere
            repo_found_at.append(github_url)
            repo_url_found = True

            # Look for the branches
            has_special_branch = repo_has_branch(logger, github_url, special_branch)
            has_default_branch = repo_has_branch(logger, github_url, default_branch)

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
        logger.abort(f'ABORT: Repo {repo} not found at any of the URLs')

    # Update the
    if not found_special_branch:
        if found_default_branch:
            repo_url_to_use = default_repo_url_to_use
            repo_branch_to_use = default_repo_branch_to_use
        else:
            logger.abort(f'ABORT: neither the user branch \'{special_branch}\' or default branch '
                         f'\'{default_branch}\' was found anywhere for {repo_url_name}. Searched ' +
                         f'in {repo_found_at}')

    # Display information for the repo
    logger.info(f'For {repo.ljust(15)} branch {repo_branch_to_use.ljust(20)} will be cloned ' +
                f'from \'{repo_url_to_use}\'')

    return repo_url_to_use, repo_branch_to_use

# --------------------------------------------------------------------------------------------------

def clone_git_repo(logger, url, branch, target):

    # Check if directory already exists
    if not os.path.exists(target):

        # Write info
        logger.info(f'Cloning branch {branch} of {url} to {target}...')

        # Command to check if branch exists and pass exit code back
        git_clone_cmd = ['git', 'clone', '-b', branch, url, target]

        # Run command
        process = subprocess.run(git_clone_cmd)#, stdout=subprocess.DEVNULL,
                                 #stderr=subprocess.DEVNULL)

        # Assert that clone was successful
        if process.returncode != 0:
            logger.abort(f'ABORT: Git clone of branch {branch} from {url} failed.')

    else:

        # Write info
        logger.info(f'Repo {url}, already cloned. Updating branch...')

        # Switch to directory where repo is cloned
        cwd = os.getcwd()
        os.chdir(target)

        # Fetch
        cmd = ['git', 'fetch']
        process = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Switch to branch
        cmd = ['git', 'checkout', branch]
        process = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Pull latest
        cmd = ['git', 'pull', 'origin', branch]
        process = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Switch back to other directory
        os.chdir(cwd)

# --------------------------------------------------------------------------------------------------