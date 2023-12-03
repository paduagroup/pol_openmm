# CL&Pol force field in xml format for use with OpenMM

These tools follow the same procedure as in [paduagroup/clandpol](https://github.com/paduagroup/clandpol) to create input files for polarizable simulations, so for more detailed information check the instructions there.

## Creating Input Files

1. Use `fftool` and `packmol` as usual, only in the second round give the `-x --type` options:

        fftool 200 ch.xyz 200 Cl.zmat 400 EG.zmat -b 55
        packmol < pack.inp
        fftool 200 ch.xyz 200 Cl.zmat 400 EG.zmat -b 55 -x --type

    This creates `field.xml` and `config.pdb`.

2. Add Drude particles using the `polxml` script (analogous to the `polarizer` script from [paduagroup/clandpol](https://github.com/paduagroup/clandpol)). Supposing an `alpha.ff` force field file describing the Drude parameters is present, run

        polxml

    This  creates files `field-p.xml` and `config-p.pdb` with Drude particles added after each core and the necessary force field terms. These files should run with OpenMM.

3. If necessary scale the LJ potentials, for which the fragment database `fragment.ff` and fragment molecular files are required (in this example the additional `meoh.zmat` for the fragments of ethyleneglycol). A `frag.inp` file specifying which atoms belong to which fragments needs to be prepared. The identification is by atom name:

        # frag.inp for ChCl:EG
        ch N4 C1 C1A COL H1 HC OH
        cl Cl 
        meoh CTO OHG H1O

    Then run

        scaleLJxml

    will generate `field-p-sc.xml`

4. Tun OpenMM using the  `field-p-sc.xml` and `config-p.pdb` as force field and topology. Since Drude particles are already present in `config-p.pdb`, it is not necessary to add Drude particles in the OpenMM script, although it should also be possible to use the initial `config.pdb` and have OpenMM add Drude particles with `modeller.addExtraParticles(forcefield)`.

5. (optional) Add Coulomb damping between charges and induced dipoles, as required to avoid the polarization catastrophe in systems with strong hydrogen bonds or densely-charged ions. The following script creates OpenMM code implementing the Tang-Toennies damping function:

        coulttxml field-p-sc.xml config-p.pdb

The code generated is to be included in the OpenMM script (the atoms involved have to be identified).


## Some points worth mentioning

### The fragment input file is different from the one for use with LAMMPS

This is unfortunate when using the `scaleLJxml` script. It happens because LAMMPS uses numerical atom type IDs, so the `fragment.inp` input file for scaling LJ parameters in LAMMPS input files has to use atom type numbers. In `xml` input files the atom types are character strings, therefore the two tools are not perfectly compatible in terms of input specification. 


### Unique atom names and types

The `--type` option of `fftool` creates unique atom types (within the entire system), as required by OpenMM to set Drude particle-core pairs. The unique atom `type` is composed from 3 characters from the molecule (`residue`) name, plus the atom name (non-bonded type), plus a serial number. Drude particles will get a preceding `D-`. As a consequence of using the unique atom types, the non-bonded types of the force field are used as the atom `class` (instead of the bonded types), which causes some redundancies in the bonded terms.

Within each `residue` the atom `name` is composed of the chemical element plus a serial number if more than 1 atom of the same element are present. These have to be unique within a `residue` because they are used to specify bonds. This is the CHARMM convention, quite different from the OPLS one that we use mostly. We suppose it is also used by TRAVIS. In order to circumvent the limits of the PDB format (4 characters for the atom name), 32-decimal notation is used for the serial number in very large molecules or materials (which are considered as a single molecule).


### Choice of Drude thermostat (and OpenMM version) 

Although the TGNH thermostat is certainly superior, we couldn't make it work with our `xml` force field files, which run fine in the latest OpenMM versions. There may be bugs or incomplete implementations in OpenMM 7.4.2.

The authors of the TGNH should update it to a more recent version of OpenMM. We think that reverse engineering the force field formats for our systems to run with TGNH in OpenMM 7.4.2 is not worth the effort.

As a result, we would favour using the standard Drude dual thermostats that come with vanilla OpenMM. Maybe these are not the very best but they should be ok for equilibrium quantities (but maybe not ideal for transport properties). Anyway, this is what almost everyone else is using.

Another point is that the Langevin integrators can be considerably faster than Nosé-Hoover, also in their Drude versions. The Langevin are stochastic and not reliable for transport properties, but should be ok for equilibrium quantities.


### Temperatures

The Drude integrators in OpenMM don't compute the temperatures of atoms and Drude particles (relative to cores) and show a global temperature that is lower than the set point. The temperatures corresponding to atoms and Drude particles have to be computed separately by the user (as shown in the `omm.py` script).
