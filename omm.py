#!/usr/bin/env python

import sys
import datetime
import numpy as np

import openmm
from simtk import unit
from simtk.openmm import app

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

platform = openmm.Platform.getPlatformByName('CUDA')
#platform.setPropertyDefaultValue('Precision', 'mixed')
properties = {'DeviceIndex': '1', 'Precision': 'mixed'}

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

# minimize only when starting from fresh conf, not after equilibration
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
sim.reporters.append(app.PDBReporter('traj.pdb', 5000))
#sim.reporters.append(app.DCDReporter('traj.dcd', 5000))
sim.reporters.append(app.CheckpointReporter('equil.chk', 100000))

kB = unit.BOLTZMANN_CONSTANT_kB/(unit.joule/unit.kelvin)
NA = unit.AVOGADRO_CONSTANT_NA*unit.mole

iat = [ i for i, atom in enumerate(modeller.topology.atoms()) if atom.name[0] != 'D' ]
idr = [ i for i, atom in enumerate(modeller.topology.atoms()) if atom.name[0] == 'D' ]
nat = len(iat)
ndr = len(idr)

nall = modeller.topology.getNumAtoms()
mall = np.array([ system.getParticleMass(i)/unit.dalton for i in range(nall) ])

ncons = system.getNumConstraints()

# reduced mass of DC-DP pairs
mu = np.zeros(nall)
for i in idr:
    mu[i] = 1.0/(1.0/mall[i-1] + 1.0/mall[i])
mu = mu.reshape((nall, 1))
vdr = np.zeros((nall, 3))

# add Drude masses back to cores
mat = np.copy(mall)
for i in idr:
    mat[i-1] += 0.4
mat = mat.take(iat)
mat = mat.reshape((nat, 1))

mall = mall.reshape((nall, 1))

print('#', nat, 'atoms', ndr, 'DP', ncons, 'constraints')
print('# running...')

dof_all = 3*nall - ncons
dof_at = 3*nat - ncons
dof_dr = 3*ndr
for i in range(100):
    sim.step(10000)
    state = sim.context.getState(getVelocities=True)
    vel = state.getVelocities(asNumpy=True)/(unit.nanometer/unit.picosecond)
    Tall = np.sum(mall*vel**2)/(dof_all*kB)*(1e3/NA)*unit.kelvin
    vat = vel.take(iat, axis=0)
    Tat = np.sum(mat*vat**2)/(dof_at*kB)*(1e3/NA)*unit.kelvin

    for i in idr:
        vdr[i] = vel[i] - vel[i-1]
    Tdr = np.sum(mu*vdr**2)/(dof_dr*kB)*(1e3/NA)*unit.kelvin
    print('# Tall', Tall, 'Tatoms', Tat, 'Tdrude', Tdr)

state = sim.context.getState(getPositions=True, getVelocities=True)
coords = state.getPositions()
sim.topology.setPeriodicBoxVectors(state.getPeriodicBoxVectors())
app.PDBFile.writeFile(sim.topology, coords, open('last.pdb', 'w'))

#sim.saveState('state.xml')

# write restart file at the end of the run
#with open('equil.rst', 'w') as f:
#    f.write(openmm.XmlSerializer.serialize(state))

print()
print('#', datetime.datetime.now())
