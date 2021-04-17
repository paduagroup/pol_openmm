#!/usr/bin/env python

import sys
import datetime
import numpy as np

from simtk import openmm
from simtk import unit
from simtk.openmm import app

field = 'field-p-sc.xml'
config = 'config-p.pdb'

print('#', datetime.datetime.now())
print()

print('#', field, config)
forcefield = app.ForceField(field)
pdb = app.PDBFile(config)

modeller = app.Modeller(pdb.topology, pdb.positions)
#print('#   adding extra particles')
#modeller.addExtraParticles(forcefield)

print('#  ', modeller.topology.getNumResidues(), 'molecules',
    modeller.topology.getNumAtoms(), 'atoms',
    modeller.topology.getNumBonds(), 'bonds')

lx = modeller.topology.getUnitCellDimensions().x
ly = modeller.topology.getUnitCellDimensions().x
lz = modeller.topology.getUnitCellDimensions().x
print('#   box', lx, ly, lz, 'nm')

system = forcefield.createSystem(modeller.topology, nonbondedMethod=app.PME,
    nonbondedCutoff=12.0*unit.angstrom, constraints=app.HBonds,
    ewaldErrorTolerance=1.0e-5)

#print('# Drude Nose-Hoover integrator')
#integrator = openmm.DrudeNoseHooverIntegrator(300*unit.kelvin, 5/unit.picosecond,
#    1*unit.kelvin, 20/unit.picosecond, 1*unit.femtosecond)
print('# Drude Langevin integrator')
integrator = openmm.DrudeLangevinIntegrator(300*unit.kelvin, 5/unit.picosecond,
    1*unit.kelvin, 20/unit.picosecond, 1*unit.femtosecond)
integrator.setMaxDrudeDistance(0.2*unit.angstrom)
print('#   max Drude distance', integrator.getMaxDrudeDistance())

print('#   barostat')
barostat = openmm.MonteCarloBarostat(1*unit.bar, 300*unit.kelvin)
system.addForce(barostat)

platform = openmm.Platform.getPlatformByName('CUDA')
#platform.setPropertyDefaultValue('Precision', 'mixed')
properties = {'Precision': 'mixed'}

sim = app.Simulation(modeller.topology, system, integrator, platform, properties)
sim.context.setPositions(modeller.positions)
sim.context.setVelocitiesToTemperature(300*unit.kelvin)

platform = sim.context.getPlatform()
print('# platform', platform.getName())
for prop in platform.getPropertyNames():
    print('#  ', prop, platform.getPropertyValue(sim.context, prop))

print('# minimizing...')
sim.minimizeEnergy(maxIterations=1000)
state = sim.context.getState(getEnergy=True,getForces=True,getVelocities=True,getPositions=True)
print('#   Epot', state.getPotentialEnergy(), 'Ekin', state.getKineticEnergy())
coords = state.getPositions()
app.PDBFile.writeFile(sim.topology, coords, open('min.pdb', 'w'))

sim.reporters = []
sim.reporters.append(app.StateDataReporter(sys.stdout, 1000, step=True,
    speed=True, temperature=True, separator='\t',
    totalEnergy=True, potentialEnergy=True, density=True))
sim.reporters.append(app.PDBReporter('traj.pdb', 10000))

kB = 1.38064e-23
NA = 6.022e23

iat = [ i for i, atom in enumerate(modeller.topology.atoms()) if atom.name[0] != 'D' ]

natom = modeller.topology.getNumAtoms()
mass = np.array([ system.getParticleMass(i)/unit.dalton for i in range(natom) ])
# add Drude masses back to cores
for i in range(natom):
    if mass[i] > 1.1:
            mass[i] += 0.4

m = mass.take(iat)
n = len(m)
m = m.reshape((n, 1))
print('#', n, 'atoms', natom - n, 'DP')
print('# running...')

for i in range(100):
    sim.step(10000)
    state = sim.context.getState(getVelocities=True)
    vel = state.getVelocities(asNumpy=True)/(unit.nanometer/unit.picosecond)
    v = vel.take(iat, axis=0)
    T = np.sum(m*v**2)/(3*n*kB)*(1e3/NA)*unit.kelvin
    print('# T atoms', T)

print()
print('#', datetime.datetime.now())
