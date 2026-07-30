# Dynamic configuration options

The default configuration file is shown below. The configuration is split into sections corresponding to the first task that references that part of the configuration. Each subsequent task receives the config for the proceeding tasks.

``` YAML
clone_options:
  bundles:
  - soca
  - iodaconv
  - da-utils
  - saber
  - ufo
  - fv3-jedi
  - oops
  - ioda
  - vader
  crtm_tag_or_branch: v2.4.1-jedi.2
  extra_repos:
  - gsibec
  github_orgs:
  - JCSDA-internal
  - JCSDA
  - GEOS-ESM
  - NOAA-EMC
  path_to_source: jedi_bundle
  user_branch: ''
configure_options:
  cmake_build_type: release
  custom_configure_options: ''
  external_modules: false
  modules: intel
  path_to_build: jedi_bundle/build-intel-release
  platform: nccs_discover_sles15
make_options:
  cores_to_use_for_make: 6
```

#### Clone options
| YAML Key                | Description |
| ------------------------| ----------- |
|`bundles`                | List of specific bundles that are to be built. Each bundle must have a corresponding YAML configuration file located in the `src/config/bundles` directory. |
|`crtm_tag_or_branch`     | A GEOS specific tag for default CRTM version. Certain CRTM static files are downloaded preemptively to prevent the need for additional data downloads. Users typically do not need to change this setting unless developing for an upcoming DAS version. |
|`extra_repos`            | Additional repos that can be built without dependencies. They should have corresponding repo URL and tag information in `build-order.yaml`. |
|`github_orgs`            | List of GitHub organizations to use and the order in which to search through them for matching branches. |
|`path_to_source`         | Path where the source code will be cloned. It defaults to the same location as where the build directory will be located. |
|`user_branch`            | Custom branch to use for cloned repos. For example if picking `feature/work` the code will search all repos in all organizations for a branch called `feature/work`. It will choose the first location it finds the branch. If the branch is not found it will fall back to the default branch and use the first location the default branch is found. If nothing is provided no search will be performed. |
|`download_lfs_data`      | Option whether or not to download data within the `jedi-model-data` repository. If set to `False`, the repository will need to be made available by the user. |

#### Configure options

| YAML Key                  | Description |
| ------------------------- | ----------- |
| `cmake_build_type`        | The `CMAKE_BUILD_TYPE` to use, e.g. release, debug etc. |
| `custom_configure_options`| User provided options to pass to ecbuild. E.g. `"-DMYOPTION=1"`. This can be useful if not using `platform` and `modules`. |
| `external_modules`| Bool option to create a `modules` and `modules-init` files inside the JEDI `build` directory. Default behavoir, `false`, generates these files using the `~/config/platform` specific directives from the `jedi_bundle` source folder. |
| `modules`                 | Type of modules to use. These are specific to the platform choice and the directives for loading the modules are specified in the `src/config/platforms/platform.yaml` file. The `platform` and `modules` directive work together.       |
| `path_to_build`           | Path where the build directory will be located. |
| `platform`                | The compute platform to use. E.g. Discover or Orion. Each supported platform has a corresponding configuration files in the `src/config/platforms/` directory. Can be kept as `none` if for example working on a closed system that does not use modules.      |

#### Make options

| YAML Key                | Description |
| ------------------------| ----------- |
| `cores_to_use_for_make` | Number of processors to use in the make step. |

### Test options

| YAML Key                | Description |
| ------------------------| ----------- |
| `test_bundles` | Select bundles to run ctests on during the `test` step. |

**Note that the code does not generally employ defaults for any of the options above. In a sense the defaults are set when configuration is generated or created. As such it is worth starting by allowing jedi_bundle to generate the configuration.**
