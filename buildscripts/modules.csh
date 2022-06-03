module purge
setenv OPT /discover/swdev/jcsda/modules
module use $OPT/modulefiles/apps
module use $OPT/modulefiles/core
module load MODLOAD
module list
