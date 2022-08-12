# Building JEDI code on Discover

Load the modules that JEDI bundle depends on

```
module use -a /discover/swdev/jcsda/spack-stack/modulefiles
module load miniconda
module load git-lfs
```

Load the JEDI bundle module

```
module use -a /discover/nobackup/drholdaw/JediOpt/modulefiles/core/
module load jedi_bundle
```

Create a directory where the source code and build directory will be stored:

```
mkdir jedi-work
cd jedi-work
jedi_bundle all
```

At this point the code will provide the opportunity to specify what it will do by modifying the `build.yaml` file that is produced. By default it will build all the bundles that are known about. Instead the `clone_options.bundles` list can be modified to control which bundles are built. For example, if working only with the UFO code the list would be modified to remove all the bundles except `ufo`. If working with `fv3-jedi` and `ufo` code only these two items would remain in the list. The fewer bundles that are included the faster the code will build.

To rebuild JEDI after making changes to the source code the following command is used:

```
cd jedi-work
jedi_bundle make build.yaml
```

This will just perform the `make -j6` operation to rebuild the code and it will use the `build.yaml` configuration that was already prepared.
