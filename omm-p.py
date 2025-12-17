#!/usr/bin/env python

import sys
import datetime
import numpy as np

import openmm
from openmm import app
from openmm import unit

field = 'field-p-sc.xml'
config = 'config-p.pdb'
#config = 'last.pdb'

temperature = 353.0*unit.kelvin
pressure = 1.0*unit.bar

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
ly = modeller.topology.getUnitCellDimensions().y
lz = modeller.topology.getUnitCellDimensions().z
print('#   box', lx, ly, lz, 'nm')

system = forcefield.createSystem(modeller.topology, nonbondedMethod=app.PME,
    nonbondedCutoff=12.0*unit.angstrom, constraints=app.HBonds,
    ewaldErrorTolerance=1.0e-5)

#print('# Drude Nose-Hoover integrator', temperature)
#integrator = openmm.DrudeNoseHooverIntegrator(temperature, 5/unit.picosecond,
#    1*unit.kelvin, 20/unit.picosecond, 1*unit.femtosecond)
print('# Drude Langevin integrator', temperature)
integrator = openmm.DrudeLangevinIntegrator(temperature, 5/unit.picosecond,
    1*unit.kelvin, 20/unit.picosecond, 1*unit.femtosecond)
integrator.setMaxDrudeDistance(0.2*unit.angstrom)
print('#   max Drude distance', integrator.getMaxDrudeDistance())

print('#   barostat', pressure)
barostat = openmm.MonteCarloBarostat(pressure, temperature)
system.addForce(barostat)

platform = openmm.Platform.getPlatformByName('OpenCL')
#platform.setPropertyDefaultValue('Precision', 'mixed')
#properties = {'DeviceIndex': '0', 'Precision': 'mixed'}
properties = {'Precision': 'single'}

# force settings before creating Simulation
for i, f in enumerate(system.getForces()):
    f.setForceGroup(i)

sim = app.Simulation(modeller.topology, system, integrator, platform, properties)

sim.context.setPositions(modeller.positions)
sim.context.setVelocitiesToTemperature(temperature)

## read coords and velocities from checkpoint (replaces sim.context.setPositions and setVelocitiesToTemperature)
## do only on the same machine
#print('# coordinates and velocities from equil.chk')
#sim.loadCheckpoint('equil.chk')

## read coords and velocities from restart file (replaces sim.context.setPositions and setVelocitiesToTemperature)
## any machine
#print('# coordinates and velocities from equil.rst')
#with open('equil.rst', 'r') as f:
#   sim.context.setState(openmm.XmlSerializer.deserialize(f.read()))

#print('# coordinates and velocities from state.xml')
#sim.loadState('state.xml')

#state = sim.context.getState()
#sim.topology.setPeriodicBoxVectors(state.getPeriodicBoxVectors())

platform = sim.context.getPlatform()
print('# platform', platform.getName())
for prop in platform.getPropertyNames():
    print('#  ', prop, platform.getPropertyValue(sim.context, prop))

## minimize only when starting from fresh conf, not after equilibration
#print('# minimizing...')
#sim.minimizeEnergy(maxIterations=1000)
#state = sim.context.getState(getEnergy=True,getForces=True,getVelocities=True, getPositions=True)
#print('#   Epot', state.getPotentialEnergy(), 'Ekin', state.getKineticEnergy())
#coords = state.getPositions()
#app.PDBFile.writeFile(sim.topology, coords, open('min.pdb', 'w'))

sim.reporters = []
sim.reporters.append(app.StateDataReporter(sys.stdout, 1000, step=True,
    speed=True, temperature=True, separator='\t',
    totalEnergy=True, potentialEnergy=True, density=True))
#sim.reporters.append(app.PDBReporter('traj.pdb', 1000))
sim.reporters.append(app.DCDReporter('traj.dcd', 1000, enforcePeriodicBox=False))
#sim.reporters.append(app.CheckpointReporter('equil.chk', 100000))

print('# running...')

for i in range(10):
    sim.step(1000)

    print('#  Tdrude ',  integrator.computeDrudeTemperature())

print("# Force groups")
for i, f in enumerate(system.getForces()):
    state = sim.context.getState(getEnergy=True, groups={i})
    print('#  ', f.getName(), state.getPotentialEnergy())

state = sim.context.getState(getPositions=True, getVelocities=True)
coords = state.getPositions()
sim.topology.setPeriodicBoxVectors(state.getPeriodicBoxVectors())
app.PDBFile.writeFile(sim.topology, coords, open('last.pdb', 'w'))

sim.context.setTime(0)
sim.context.setStepCount(0)
sim.saveState('state-run.xml')
print('# state saved to state-run.xml')

# write restart file at the end of the run
#with open('equil.rst', 'w') as f:
#    f.write(openmm.XmlSerializer.serialize(state))

print()
print('#', datetime.datetime.now())
