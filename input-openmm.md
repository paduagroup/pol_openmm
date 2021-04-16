# Creating Input Files for OpenMM

1. Use `fftool` and `packmol` as usual, only in the second round give the `-x --type` options:

        fftool 200 ch.xyz 200 Cl.zmat 400 EG.zmat -b 55
        packmol < pack.inp
        fftool 200 ch.xyz 200 Cl.zmat 400 EG.zmat -b 55 -x --type

    This creates `field.xml` and `config.pdb`

2. Add Drude particles using the `polxml` script (a version of the `polarizer`), supposing an `alpha.ff` force field file describing the Drude parameters is present:

        polxml

    This  creates `field-p.xml` and `config-p.pdb` with Drude particles added after each core, and the necessary force field therms. These files should run with OpenMM 7.5.

3. Scale the LJ potentials, for which you will need fragment molecular files (in this example add `meoh.zmat` for the fragments of ethyleneglycol) and a `fragment.inp` file specifying which atoms belong to which fragments. Here the identification is by atom name:

        # fragment.inp for ChCl:EG
        ch N4 C1 C1A COL H1 HC OH
        cl Cl 
        meoh CTO OHG H1O

    Then

        scaleLJxml

    will generate `field-p-sc.xml`

4. Use `field-p-sc.xml` and `config-p.pdb` to run OpenMM. Since Drude particles are already present in the `pdb` file, no need to have OpenMM add the Drude particles with

        modeller.addExtraParticles(forcefield)

    It should also be possible to use the initial `config.pdb` and have OpenMM add the Drude particles.
