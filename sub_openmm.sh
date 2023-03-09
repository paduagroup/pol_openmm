#!/bin/bash
#SBATCH -J emimdca
#SBATCH --partition=E5-GPU
#SBATCH -o %j.out
#SBATCH -e %j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --mem=8G 
#SBATCH --time=0:15:00
#SBATCH --exclude=r730gpu21,r730gpu22,r730gpu23,r730gpu24
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=agilio.padua@ens-lyon.fr

module purge

module use /applis/PSMN/debian11/E5/modules/all
module use /home/tjiang/modules/lmod/debian11/

module load foss/2021b
module load CUDA/11.4.1

#export LD_LIBRARY_PATH=$HOME/openmm/lib:$LD_LIBRARY_PATH
#export LD_LIBRARY_PATH=/Xnfs/chimie/debian11/openmm/openmm-7.7.0/lib/:$LD_LIBRARY_PATH
#export PYTHONPATH=/Xnfs/chimie/debian11/anaconda3/lib/python3.7/site-packages/:$PYTHONPATH

#sleep 60
#OMPI_MCA_btl='^ofi'
#OMPI_MCA_mtl='^ofi'

HOMEDIR="$SLURM_SUBMIT_DIR"
HOSTFILE=$TMPDIR/machines

#scratch
#E5 partition
#SCRATCHDIR=$HOMEDIR/scratch/E5N
#Lake partition
SCRATCHDIR=/scratch/Chimie/${USER}/${SLURM_JOB_ID}/

echo $SCRATCHDIR
/bin/mkdir -p $SCRATCHDIR

cd ${HOMEDIR}
#cp -f run-fixq.py topol.psf ff.prm conf.gro ${SCRATCHDIR}/
#cp -r ../mstools/ ${SCRATCHDIR}/
cp -f *.py field*.xml config*.pdb ${SCRATCHDIR}/

cd ${SCRATCHDIR}

source /home/${USER}/.bashrc
source activate omm7
#export OPENMM_CPU_THREADS=16

#/Xnfs/chimie/debian11/anaconda3/bin/python omm-p.py > omm.out
python omm-p.py > omm.out

cp -rpf $SCRATCHDIR/* ${HOMEDIR}
	      
rm -rf $SCRATCHDIR/*
rmdir $SCRATCHDIR
