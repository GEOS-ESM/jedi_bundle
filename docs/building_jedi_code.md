# Building the JEDI code

The jedi_bundle system has a single entry point accessed with `jedi_bundle`. The arguments that are passed to the entry point are as follows:

``` shell
jedi_bundle [Tasks] build.yaml
```

The first argument is a list describing the tasks that are to be completed. The second argument is optional and points to a YAML configuration describing the options for the build.

The list of possible tasks are `Clone`, `Configure` and `Make`. You can also specify `All`, meaning all three tasks.

If no YAML configuration file is passed, the code will use the default configuration. However an opportunity to modify the defaults before cloning and installing any code will be offered. A copy of the configuration will be placed in the current directory and then will also be copied into the directory where the source code will be cloned. If resubmitting certain tasks the user can then point to that configuration file with the `jedi_bundle` call.

The tasks perform the following duties:

| Task    | Description |
| --------| ----------- |
|Clone    | Clone the JEDI repos according the branch name and organisations specified in the configuration. |
|Configure| Run the CMake (ecbuild) configure step. Also create shortcut modules file for later sourcing with the build.|
|Make     | Run the parallel make step, i.e. make -j6. |


## Basic Examples

To run **All** tasks with an externally provided configuration file the command would be:

``` shell
jedi_bundle All build.yaml
```

To run **Clone** and **Configure** starting with the default settings the command would be:

``` shell
jedi_bundle Clone Configure
```

To run **Make** with the default settings the command would be:

``` shell
jedi_bundle Clone Configure
```

### Understanding the use of configuration

Lets say the desire is to clone the source code to a directory called `/home/code/` but hold off on configuring and building the code. The first step would be to issue:

``` shell
jedi_bundle Clone
```

Assuming the above command was issued while sitting in the `/home` directory this will first copy the default configuration file to `/home/build.yaml`. A prompt will occur offering the opportunity to modify the config file. In order to have the source code be cloned to `/home/code` the setting `clone_options.path_to_source` would be adjusted by editing the file in another window. Once modified the prompt would be completed by pressing a key and the cloning of the repos would begin. Note `build.yaml` is moved to `/home/code/build.yaml` and reflects all the changes made to it at the prompt.

See the section on [dynamic configuration options](dynamic_configuration_options.md) for a description of all the other settings that can be chosen.

Now that the code has been cloned it might be time to configure and make the build. This could then be done by issuing:

``` shell
jedi_bundle Configure Make /home/code/build.yaml
```

Note that if the above command was issued without providing the configuration files it would fall back to the default and the path to the source code would not be correct by default.
