#!/bin/sh

#SBATCH --account ACCOUNT
#SBATCH --qos=QUEUE
#SBATCH --job-name=jedimake
#SBATCH --output=jedimake.o%j
#SBATCH --ntasks-per-node=24
#SBATCH --nodes=1
#SBATCH --time=00:30:00

cd $1

source $MODULESHOME/init/sh
source ./modules

cd $2

make -j24
