#!/bin/sh

set -e

# Usage of this script.
usage() { echo "Usage: $(basename $0) [-c intel-impi|gnu-impi] [-b debug|relwithdebinfo|release|bit|production] [-q debug|advda|...] [-a g0613|...]  [-s ON|OFF] [-h]" 1>&2; exit 1; }

# Set input argument defaults.
compiler="intel-impi"
build="release"
account="g0613"
queue="debug"
build_soca="OFF"

# Parse input arguments.
while getopts 'b:c:a:q:s:h:' OPTION; do
  case "$OPTION" in
    b)
        build="$OPTARG"
        [[ "$build" == "debug" || \
           "$build" == "relwithdebinfo" || \
           "$build" == "bit" || \
           "$build" == "release" || \
           "$build" == "production" ]] || usage
        ;;
    c)
        compiler="$OPTARG"
        [[ "$compiler" == "gnu-impi" || \
           "$compiler" == "intel-impi" ]] || usage
        ;;
    a)
        account="$OPTARG"
        ;;
    q)
        queue="$OPTARG"
        ;;
    s)
        build_soca="$OPTARG"
        [[ "$build_soca" == "ON" || \
           "$build_soca" == "OFF" ]] || usage
        ;;
    h|?)
        usage
        ;;
  esac
done
shift "$(($OPTIND -1))"

echo "Summary of input arguments:"
echo "         build = $build"
echo "      compiler = $compiler"
echo "       account = $account"
echo "         queue = $queue"
echo "         soca  = $build_soca"
echo

# Load JEDI modules
# -----------------
OPTPATH=/discover/swdev/jcsda/modules
MODLOAD=jedi/$compiler

source $MODULESHOME/init/sh
module purge
export OPT=$OPTPATH
module use $OPT/modulefiles/core
module use $OPT/modulefiles/apps
module load $MODLOAD
module list


# Set up paths (build and src)
# ----------------------------
compiler_build=`echo $compiler | tr / -`
JEDI_BUILD="$PWD/build-$compiler_build-$build"
cd $(dirname $0)/..
FV3JEDI_SRC=$(pwd)


mkdir -p $JEDI_BUILD && cd $JEDI_BUILD

# Create bash module file for future sourcing
# -------------------------------------------
file=modules.sh
cp ../buildscripts/$file ./
sed -i "s,OPTPATH,$OPTPATH,g" $file
sed -i "s,MODLOAD,$MODLOAD,g" $file

# Create csh/tsh module file for future sourcing
# ----------------------------------------------
file=modules.csh
cp ../buildscripts/$file ./
sed -i "s,OPTPATH,$OPTPATH,g" $file
sed -i "s,MODLOAD,$MODLOAD,g" $file

# Slurm job for running make
# --------------------------
file=make_slurm.sh
cp ../buildscripts/$file ./
sed -i "s,OPTPATH,$OPTPATH,g" $file
sed -i "s,MODLOAD,$MODLOAD,g" $file
sed -i "s,ACCOUNT,$account,g" $file
sed -i "s,QUEUE,$queue,g" $file
sed -i "s,BUILDDIR,$JEDI_BUILD,g" $file

# Slurm job for running tests
# ---------------------------
file=ctest_slurm.sh
cp ../buildscripts/$file ./
sed -i "s,OPTPATH,$OPTPATH,g" $file
sed -i "s,MODLOAD,$MODLOAD,g" $file
sed -i "s,ACCOUNT,$account,g" $file
sed -i "s,QUEUE,$queue,g" $file
sed -i "s,BUILDDIR,$JEDI_BUILD,g" $file


# Build soca
# ----------
[[ $build_soca == "ON" ]] && SOCA="-DBUILD_SOCA=ON"

# Build
# -----
BUILDCOMMAND="ecbuild --build=$build -DMPIEXEC=$MPIEXEC $SOCA $FV3JEDI_SRC"
echo "ecbuild command: " $BUILDCOMMAND
echo " "
echo " "
echo " Building... "
echo " "
FV3JEDI_TEST_TIER=2
$BUILDCOMMAND

# Update the repos
# ----------------
make update

# Build ioda converters
# ---------------------
sbatch --wait make_slurm.sh iodaconv

# Build fv3-jedi
# --------------
sbatch --wait make_slurm.sh fv3-jedi

# Build soca
# ----------
[[ $build_soca == "ON" ]] && sbatch --wait make_slurm.sh soca

# Get CRTM data before ctest_slurm
# --------------------------------
cd $JEDI_BUILD/fv3-jedi
ctest -R fv3jedi_get_crtm_test_data
cd $JEDI_BUILD

exit 0
