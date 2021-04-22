#!/bin/bash
#
#$ -S /bin/bash
#$ -N romm
#$ -q r730gpuRTX2080ti
#$ -cwd
#$ -V
##$ -m be

echo $PATH

module load cuda/9.2
export LD_LIBRARY_PATH=$HOME/openmm/lib:$LD_LIBRARY_PATH

cd $SGE_O_WORKDIR

if [[ -d "/scratch/Lake" ]]; then
    SCRATCHDIR=/scratch/Lake/$USER/$JOB_ID/
else
    echo "/scratch not found, cannot create $SCRATCHDIR"
    exit 1
fi

echo $SCRATCHDIR
/bin/mkdir -p $SCRATCHDIR

cp -f *.py field*.xml config*.pdb $SCRATCHDIR/

cd $SCRATCHDIR
ls -l

#conda activate

#export OPENMM_CPU_THREADS=16

python omm.py > openmm.out
#python testomm.py > test.out

cp -rpf $SCRATCHDIR/* $SGE_O_WORKDIR/
 
rm -f $SCRATCHDIR/*
rmdir $SCRATCHDIR

