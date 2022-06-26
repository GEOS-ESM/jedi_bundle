# Building the JEDI code

The jedi_bundle system has a single entry point called `jedi_bundle`. The arguments that are passed to the entry point are as follows:

``` shell
jedi_bundle [Tasks] build.yaml
```

The first argument is a list describing the tasks that are to be completed. The second argument is optional and points to a YAML configuration describing the options for the build.

The list of possible tasks are `Clone`, `Configure` and `Make`. You can also specify `All` meaning all three tasks.

If no YAML configuration file is passed the code will use the default configuration and provide the opportunity to modify the defaults before cloning and installing any code.

The tasks perform the following duties:

- **Clone**: Clone the JEDI repos


