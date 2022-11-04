# Fixed configuration options

So-called fixed configuration options represent the YAML files in the repo that are not adapted with each new build of the JEDI code. However these files might need to be modified from time to time to allow new options.

## Bundles

The directory `src/jedi_bundle/config/bundles` contains the configuration files associated with the bundles. There is a file `bundle.yaml` for each bundle that can be built. As an example the `ufo.yaml` is shown below:

``` yaml
optional_repos:
  - ropp-ufo
  - geos-aero

required_repos:
  - jedicmake
  - oops
  - saber
  - ioda
  - crtm
  - gsw
  - ufo
  - ioda-data
  - ufo-data
```

These represent all the repositories that have to be cloned (given by the ecbuild project name) in order to successfully run all the ufo tests. The order in this file is not of importance, a list is used purely for convenience. The `optional repos` section describes repos that are optional dependencies of ufo. The code will still attempt to clone and build this code, but if the repo is not found it will not cause a failure. The `required repos` represents the repos that will need to be found in order to build this bundle. The build will fail if any are not found during clone.

## Build order

Note that the order in which repos are built is important and additionally it is critical to know the name of the URL where the code resides (if different from the project name) and what the default branch is. In addition to the file for each bundle there is a `build-order.yaml` that describes all these critical details. An example entry in the `src/jedi_bundle/config/build-order.yaml` file is shown below for `jedicmake`.

``` yaml
- jedicmake:
    repo_url_name: jedi-cmake
    cmakelists: 'include( jedicmake/cmake/Functions/git_functions.cmake )'
    default_branch: develop
    recursive: true
    tag: false
```

The dictionary key is `jedicmake` which is the project name for the repo. This is referred to by all the other bundle files. The role of the keys within the dictionary are as follows:

| YAML Key       | Default          | Description |
| ---------------| ---------------- | ----------- |
|`repo_url_name` | Project name     | Used when the project name and URL differ (case sensitive) |
|`cmakelists`    | `None`           | Used when lines are needed in the CMakeLists.txt after the repo definition |
|`default_branch`| *Mandatory*      | The name of the default branch to clone |
|`recursive`     | False            | Whether the repo requires a recursive clone |
|`tag`           | False            | Whether the default thing to clone is a tag (rather than a branch) |


## Platforms

Generally speaking the commands for building the code on different machines do not differ. However, there are often steps taken before the build commences that typically do depend on the compute platform. This is especially true on high performance clusters, where the use of containers is non-standard and there is a need to load the JEDI stack modules.

The directory `src/jedi_bundle/config/platforms` contains YAML files for each supported platform. These files are configured as, for example:

``` yaml
modules:
  intel:
    load:
      - export OPT=/path/to/some/modules
      - module use $OPT/modulefiles/apps
      - module use $OPT/modulefiles/core
      - module load module
    configure: -DMPIEXEC=$MPIEXEC
  gnu:
    - ...
```

Under the `modules.load` section the different module options for that platform can be added as a list. The set of commands for loading the modules will be translated into a sourceable bash file that lives in the build directory. The purpose of this file is to be sourced ahead of the configure and make steps. The user can also source the file when running tests or rebuilding manually. Users can later translate the generated module file to other shells if needed.

The `modules.configure` section allows for platform specific entries to be added to the `ecbuild` configure step.

When the platform and modules are chosen in the main configuration file passed to `jedi_bundle` the code will look for a matching platform file and associated set of instructions for loading the chosen modules.


## CMakeLists

Before the source code can be configured and built there needs to be a `CMakeLists.txt` file in place in the source code directory. This file is generated dynamically depending on which bundles are being built. In addition to the dynamic lines there is typically a header and footer part of the `CMakeLists.txt` file. These are defined in `src/jedi_bundle/config/cmake.yaml`.
