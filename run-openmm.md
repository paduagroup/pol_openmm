# Running OpenMM

## Creating Input Files

1. Use `fftool` and `packmol` as usual, only in the second round give the `-x --type` options:

        fftool 200 ch.xyz 200 Cl.zmat 400 EG.zmat -b 55
        packmol < pack.inp
        fftool 200 ch.xyz 200 Cl.zmat 400 EG.zmat -b 55 -x --type

    This creates `field.xml` and `config.pdb`

2. Add Drude particles using the `polxml` script (a version of the `polarizer`). Supposing an `alpha.ff` force field file describing the Drude parameters is present, run

        polxml

    This  creates files `field-p.xml` and `config-p.pdb` with Drude particles added after each core and the necessary force field terms. These files should run with OpenMM 7.5.

3. Scale the LJ potentials, for which fragment molecular files are required (in this example the additional `meoh.zmat` for the fragments of ethyleneglycol). A `fragment.inp` file specifying which atoms belong to which fragments needs to be prepared. The identification is by atom name:

        # fragment.inp for ChCl:EG
        ch N4 C1 C1A COL H1 HC OH
        cl Cl 
        meoh CTO OHG H1O

    Then run

        scaleLJxml

    will generate `field-p-sc.xml`

4. Use `field-p-sc.xml` and `config-p.pdb` to run OpenMM. Since Drude particles are already present in the `pdb` file, no need to have OpenMM add the Drude particles with

        modeller.addExtraPart
        icles(forcefield)

    It should also be possible to use the initial `config.pdb` and have OpenMM add the Drude particles.


## Interesting points


### Unique atom names and types

The `polxml` script creates unique atom names (called `type` in the `xml` force field) and bonded types (`class` in the `xml` format) for the whole system because OpenMM assigns the Drude particles to their cores by looking for a specific atom `type`. Although the bonded part of the force field can be spoecified by atom `class`, which is compact, the unique atom names give rise to a huge number of pair interactions, so the non-bonded part is bloated.

The unique atom `type` and `class` are composed from 3 characters from the molecule (`residue`) name, plus the atom name, plus a serial number. Drude particles get a preceding `D`.

Within each `residue` the atom `name` is composed of the chemical element plus a serial number if more than 1. These have to be unique within a `residue` because they are used to specify bonds. This is the CHARMM convention, quite different from the OPLS one that we use mostly. I guess it is also used by TRAVIS.


### Choice of Drude thermostat (and OpenMM version) 

Although the TGNH thermostat is certainly superior, I couldn't make it work with our `xml` force field files, which run fine in the latest OpenMM 7.5. There may be bugs or incomplete implementations in OpenMM 7.4.2.

The authors of the TGNH are updating it to OpenMM 7.5, but gave no date. I think it is probably not worth the effort to reverse engineer the force field formats that would make our systems run with TGNH in OpenMM 7.4.2.

As a result, I'm inclined to use the standard Drude dual thermostats that come with OpenMM 7.5. Maybe these are not the very best for transport properties but they may be ok for structural quantities. Anyway, this is what almost everyone else is using.

Another point is that the Langevin integrators can be considerably faster than Nosé-Hoover, also in their Drude versions. Again, maybe not good for transport properties but probably ok for equilibrium quantities.


### Temperatures

The Drude integrators in OpenMM don't seem to compute the actual temperatures of atoms and Drude particles (relative to cores). OpenMM computes an overall temperature that is lower than the set-point, I suspect because of the Drudes. The 'true' temperature likely will have to be computed from velocities in the python script.

