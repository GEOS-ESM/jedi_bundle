# Building JEDI code on Discover

Load the JEDI spack Python module

```
module purge
module use /discover/swdev/jcsda/spack-stack/modulefiles
module load miniconda/3.9.7
```

Load the latest `jedi_bundle` module

```
module use -a /discover/nobackup/drholdaw/JediOpt/modulefiles/core/
module load jedi_bundle
```

Create a directory where the source code and build directory will be stored e.g.:

```
mkdir jedi-work
cd jedi-work
```

Issue `jedi_bundle` without any arguments to generate the `build.yaml` configuration:

```
jedi_bundle
```

Before proceeding you may want to edit `build.yaml` to choose different options. It will default to building all bundles and you may wish to only build a specific bundle by modifying `clone_options.bundles`. Choosing `fv3-jedi` and `ufo`, for example, will result in building all the code for the `fv3-jedi` and `ufo` bundles. You may also want to change the modules used to build or change the type of build to use.

Once `build.yaml` is configured they way you wish, you can issue `jedi_bundle` again with the tasks you want. To clone the code on a login node and then build using a compute node issue:

```
jedi_bundle clone configure build.yaml
salloc --time=1:00:00
jedi_bundle make build.yaml
```

Note that you may wish to perform the make step using more than the default 6 cores. Edit `build.yaml` and change `make_options.cores_to_use_for_make` to a higher number, say 24 and then issue the `jedi_bundle make build.yaml` step again after requising the node(s) with `salloc`.
