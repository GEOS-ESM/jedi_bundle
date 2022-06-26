# Dynamic configuration options

The default configuration file is shown below. The configuration is split into build options and source code options.

``` YAML
build options:

  platform: discover
  modules: intelclassic
  cmake_build_type: release
  configure: ecbuild
  path to build: &path_to_build ./
  cores to use for make: 6

source code options:

  path to source: *path_to_build
  user branch: develop
  github orgs:
    - JCSDA-internal
    - JCSDA

  bundles:
    - fv3-jedi
    - soca
    - iodaconv
```

#### Build options

| YAML Key                | Description |
| ------------------------| ----------- |
| `platform`              | The compute platform to use. E.g. Discover. Each supported platform has a corresponding configuration files in the `src/config/platforms/` directory.       |
| `modules`               | Type of modules to use. These are specific to the platform choice and the directives for loading the modules are specified in the `src/config/platforms/platform.yaml` file.        |
| `cmake_build_type`      | The `CMAKE_BUILD_TYPE` to use, e.g. release, debug etc. |
| `path_to_build`         | Path where the build directory will be located. |
| `cores_to_use_for_make` | Number of processors to use in the make step. |

#### Source code options
| YAML Key                | Description |
| ------------------------| ----------- |
|`path_to_source`         | Path where the source code will be cloned. It defaults to the same location as where the build directory will be located. |
|`user_branch`            | Custom branch to use for cloned repos. For example if picking `feature/work` the code will search all repos in all organizations for a branch called `feature/work`. It will choose the first location it finds the branch. If the branch is not found it will fall back to the default branch and use the first location the default branch is found. |
|`github_orgs`            | List of GitHub organizations to use and the order in which to search through them for matching branches. |
|`bundles`                | List of specific bundles that are to be built. Each bundle must have a corresponding YAML configuration file located in the `src/config/bundles` directory. |
