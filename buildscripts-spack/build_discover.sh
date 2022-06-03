#!/bin/sh

set -e

# Usage of this script.
usage() { echo "Usage: $(basename $0) [-c intel] [-b debug|relwithdebinfo|release|bit|production] [-j jcsda|jcsda-internal] [-q debug|advda|...] [-a g0613|...] [-o ON|OFF] [-s ON|OFF] [-h]" 1>&2; exit 1; }

# Set input argument defaults.
compiler="intel"
build="release"
jcsda="jcsda"
account="g0613"
queue="debug"
build_ooo="ON"
build_soca="OFF"

# Parse input arguments.
while getopts 'c:b:j:q:a:o:s:h:' OPTION; do
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
        [[ "$compiler" == "gnu" || \
           "$compiler" == "intel" ]] || usage
        ;;
    j)
        jcsda="$OPTARG"
        [[ "$jcsda" == "jcsda" || \
           "$jcsda" == "jcsda-internal" ]] || usage
        ;;
    a)
        account="$OPTARG"
        ;;
    q)
        queue="$OPTARG"
        ;;
    o)
        build_ooo="$OPTARG"
        [[ "$build_ooo" == "ON" || \
            "$build_ooo" == "OFF" ]] || usage
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
echo "            build = $build"
echo "         compiler = $compiler"
echo "            jcsda = $jcsda"
echo "          account = $account"
echo "            queue = $queue"
echo "            soca  = $build_soca"
echo "optioanal ob ops  = $build_ooo"
echo

# Build soca
# ----------
[[ $build_soca == "ON" ]] && SOCA="-DBUILD_SOCA=ON"

# Optional obs operators
# ----------------------
[[ $build_ooo == "ON" ]] && OOO="-DBUNDLE_SKIP_GEOS-AERO=OFF -DBUNDLE_SKIP_ROPP-UFO=OFF"

# Enable tier 2 tests with fv3-jedi
# ---------------------------------
FV3JEDI_TEST_TIER=2

# Build directory
# ---------------
JEDI_BUILD="$PWD/build-$compiler-$build"
mkdir -p $JEDI_BUILD

# Copy modules file
# -----------------
cp buildscripts-spack/modules-$compiler $JEDI_BUILD/modules

# Copy make file
# --------------
cp buildscripts-spack/make_slurm.sh $JEDI_BUILD/make_slurm.sh
sed -i -e 's/ACCOUNT/'"$account"'/g' $JEDI_BUILD/make_slurm.sh
sed -i -e 's/QUEUE/'"$queue"'/g' $JEDI_BUILD/make_slurm.sh

# Update the CMakeLists with chosen JCSDA org
# -------------------------------------------
cp CMakeListsTemplate.txt CMakeLists.txt
sed -i -e 's/JCSDAORG/'"$jcsda"'/g' CMakeLists.txt

# Move to build directory
# -----------------------
cd $JEDI_BUILD

# Load JEDI modules
# -----------------
source ./modules

# Build
# -----
BUILDCOMMAND="ecbuild --build=$build -DMPIEXEC=$MPIEXEC $OOO $SOCA ../"
echo "ecbuild command: " $BUILDCOMMAND
echo " "
$BUILDCOMMAND

# Build ioda converters
# ---------------------
sbatch --wait make_slurm.sh $JEDI_BUILD iodaconv

# Build fv3-jedi
# --------------
sbatch --wait make_slurm.sh $JEDI_BUILD fv3-jedi

# Build soca
# ----------
[[ $build_soca == "ON" ]] && sbatch --wait make_slurm.sh $JEDI_BUILD soca
