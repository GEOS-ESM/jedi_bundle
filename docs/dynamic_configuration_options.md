# Dynamic configuration options

The default configuration file is shown below. The configuration is split into sections corresponding to the first task that references that part of the configuration. Each subsequent task receives the config for the proceeding tasks.

``` YAML
clone_options:
  path_to_source: jedi_bundle
  user_branch: ''
  github_orgs:
    - JCSDA-internal
    - JCSDA
    - GEOS-ESM
  bundles:
    - soca
    - saber
    - ufo
    - fv3-jedi
    - oops
    - ioda
    - vader

configure_options:
  platform: 'none'
  modules: 'none'
  cmake_build_type: release
  path_to_build: jedi_bundle/build
  custom_configure_options: ''

make_options:
  cores_to_use_for_make: 6
```

#### Clone options
| YAML Key                | Description |
| ------------------------| ----------- |
|`path_to_source`         | Path where the source code will be cloned. It defaults to the same location as where the build directory will be located. |
|`user_branch`            | Custom branch to use for cloned repos. For example if picking `feature/work` the code will search all repos in all organizations for a branch called `feature/work`. It will choose the first location it finds the branch. If the branch is not found it will fall back to the default branch and use the first location the default branch is found. If nothing is provided no search will be performed. |
|`github_orgs`            | List of GitHub organizations to use and the order in which to search through them for matching branches. |
|`bundles`                | List of specific bundles that are to be built. Each bundle must have a corresponding YAML configuration file located in the `src/config/bundles` directory. |

#### Configure options

| YAML Key                  | Description |
| ------------------------- | ----------- |
| `platform`                | The compute platform to use. E.g. Discover or Orion. Each supported platform has a corresponding configuration files in the `src/config/platforms/` directory. Can be kept as `none` if for example working on a closed system that does not use modules.      |
| `modules`                 | Type of modules to use. These are specific to the platform choice and the directives for loading the modules are specified in the `src/config/platforms/platform.yaml` file. The `platform` and `modules` directive work together.       |
| `cmake_build_type`        | The `CMAKE_BUILD_TYPE` to use, e.g. release, debug etc. |
| `path_to_build`           | Path where the build directory will be located. |
| `custom_configure_options`| User provided options to pass to ecbuild. E.g. `"-DMYOPTION=1"`. This can be useful if not using `platform` and `modules`. |

#### Make options

| YAML Key                | Description |
| ------------------------| ----------- |
| `cores_to_use_for_make` | Number of processors to use in the make step. |


**Note that the code does not generally employ defaults for any of the options above. In a sense the defaults are set when configuration is generated or created. As such it is worth starting by allowing jedi_bundle to generate the configuration.**
