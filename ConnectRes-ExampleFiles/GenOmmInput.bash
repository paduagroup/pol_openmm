#!/bin/bash

# Paths to other programs needed
FFTOOL="/Users/rclark/Documents/Git/fftool/fftool"
PACKMOL="/Users/rclark/Documents/Git/packmol/packmol"
POLARIZER="/Users/rclark/Documents/Git/pol_openmm/polxml"
SCALELJ="/Users/rclark/Documents/Git/pol_openmm/scaleLJxml"

STIME=$(date)
start_time="$(date -u +%s)"
echo "Start at: $STIME"

XDIM=51.712
YDIM=51.712
ZDIM=600.0

# IL
NOIONS=465 
CATION='P66614'
ANION='Cl'

echo '---------- CREATING SIMBOX ----------#'
${PACKMOL} < pack.inp
# This should not be built with fftool as it would disrupt the ordering of the ZIF. This packmol input uses an xyz file with the ZIF ordered correctly. 
# In other systems a similar approach will probably be needed, bypassing using fftool to write the pack files and creating inputs manually.

echo '---------- CREATING NON-POL OPENMM FILE ----------'
${FFTOOL} -b ${XDIM},${YDIM},${ZDIM} -p xyz -ax 252 'Zn_at.xyz' 468 'Imid_Linker.xyz' 72 'Imid_Terminal.xyz' ${NOIONS} ${CATION}'.zmat' ${NOIONS} ${ANION}'.zmat' --types

echo '---------- POLARISING LAMMPS FILE ----------'
${POLARIZER} -ix field.xml -ip config.pdb 
# When using the polarizer line 69 needs to be commented out so the program does not exit when it identifies atoms in different residues connected.
# Should we change this to a warning or not?
# alpha.ff has the polarisabilities required for this example

echo '---------- SCALING LJ INTERACTIONS ----------'
${SCALELJ} 
# fragment.ff and fragment.inp have the scaling parameters for this example
# The imid and zn fragment files are also in the example files

echo '---------- CONNECTING RESIDUES  ----------'
./ConnectRes -id config-p.pdb -if field-p-sc.xml Zn,Zn NZ,ImL Zn,Zn NZ,ImT
# Connects the residues in the polarised and scaled files.
# It is best to do this last, as the polarizer and scalelj programs do not like external bonds.

