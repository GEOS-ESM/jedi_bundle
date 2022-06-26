# Fixed configuration options

So-called fixed configuration options represent the YAML files in the repo that are not adapted with each new build of the JEDI code. However these files might need to be modified from time to time to allow new options.

## Bundles

The directory `src/jedi_bundle/config/bundles` contains the configuration files associated with the bundles. There is a file `bundle.yaml` for each bundle that can be built as well as a files `build-order.yaml` that defines all the JEDI repositories required by all the bundles and shows them in the correct order for resolving the dependencies between them. For example, when creating the `CMakeLists.txt` the repo `oops` would have to built before all the repos that depend of `oops`. If new repos are added to any of the bundles then that repo needs to be added to the build order dictionary.

An example entry in the `build-order.yaml` file is shown below for `jedicmake`.

``` yaml
- jedicmake:
    repo_url_name: jedi-cmake
    cmakelists: 'include( jedicmake/cmake/Functions/git_functions.cmake )'
    default_branch: develop
```

The dictionary key is `jedicmake` which is the project name for the repo. The key `repo_url_name` is used when the project name is different from the name used for the repo in GitHub. The `cmakelists` key is used to denote that something needs to be entered in the results `CMakeLists.txt` file which usually isn't the case. It's an optional argument that can be neglected. The final key `default_branch` is used to denote the default branch of the repo. The default `default_branch` is `develop`.

In the configuration file used for each bundle, e.g. `fv3-jedi.yaml`, there are two entries: `optional repos` and `required repos`. The list of required repos lists all the repos necessary to build that bundle. Optional repos will only be build if they are found. There may some optional dependencies that come only from private repos, only build if the user has access to that code.

## Platforms


## CMakeLists
