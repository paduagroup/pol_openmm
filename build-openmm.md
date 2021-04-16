# OpenMM Installation Instructions


## Finding the version of the CUDA toolkit

GPU computing is a quickly evolving field and navigating among all the versions of cards, their drivers and compilers is essential. Locate the root of the CUDA installation and the CUDA compiler `nvcc`:

    which nvcc
    /usr/local/cuda/bin/nvcc --version

The command

    nvidia-smi

shows important information on NVIDIA GPU hardware present, but this doesn't work on frontal machines.


## Installation on the PSMN

The PSMN has 40 NVIDIA RTX 2080Ti GPUs, which are fast in single and mixed precision. Mixed precision is a great choice for MD.

The 2080 cards are of Turing architecture, ideally used with the CUDA 10 (or later) toolkit of drivers and compilers. The optimum compilation flag for these cards is `--arch=sm_75`.

The PSMN machines have CUDA 9.2 and an upgrade seems unlikely. 

### OpenMM 7.4.2

OpenMM 7.4.2 can be installed using `conda`, choosing a version compiled with CUDA 9.2, from https://anaconda.org/omnia/openmm

    conda install -c omnia/label/cuda92 openmm

OpenMM 7.4.2 is compatible with the temperature-grouped Nosé-Hoover thermostat (http://doi.org/10.1021/acs.jpclett.9b02983), which is the best one for Drude polarizable force fields. Unfortunately, OpenMM 7.4.2 doesn't seem to run well with `xml` input files of the latest polarizable force fields, including ours.


### OpenMM 7.5.0

When installed with `conda`, OpenMM 7.5.0 comes compiled with the CUDA 11 toolkit, so it will not be properly configured on the PSMN. The code may run but some functionalities will not work.

Therefore OpenMM should be compiled from source, which is straightforward (instructions below). There is one detail: the latest OpenMM 7.5.0 will produce code with `--arch=sm_75`, which is not supported in CUDA 9.2. It is therefore necessary to modify one file in the source code in order to specify `--arch=sm_70` (which corresponds to the previous generation of architecture named Volta, e.g. the V100 cards).


## Installation on IDRIS

The Jean Zay machine has V100 cards, so the recipe for the PSMN may well work there. I don't know what CUDA version they have.


## OpenMM Compilation

1. Install `miniconda3`, with `numpy` and not much else, since the PSMN machines already have most of the tools needed by OpenMM (`SWIG`, `Doxygen`, etc.) This will provide a local python installation for OpenMM. Activate `conda` if not by default:

        conda activate

2. Download the OpenMM source code from https://github.com/openmm/openmm/releases/tag/7.5.0 and expand into a `src` dir; create a `build` dir.

        mkdir ~/src
        cd ~/src
        tar xzvf openmm-7.5.0.tar.gz
        mkdir build_openmm
        cd build_openmm

3. Configure the build

    In the `build_openmm` dir do:

        ccmake ../openmm-7.5.0

    press `'c'` to configure. Set the installation dir (replacing `user`) and CUDA compiler, also check that your local `python` was found (if not go back to 1.):

        CMAKE_INSTALL_PREFIX=/home/user/openmm
        CUDA_HOST_COMPILER=/usr/local/cuda/bin/nvcc
        PYTHON_EXECUTABLE=/home/user/miniconda3/bin/python

    then press `'c'` and `'g'` to generate the build files.

4. Patch the source code to use `sm_70`. Edit the file `openmm-7.5.0/platforms/cuda/src/CudaContext.cpp` and add the two lines `major = 7;`, `minor = 0;` around line 227. Don't forget the end-of-line `';'` this is C++.

        if (cudaDriverVersion < 8000) {
            // This is a workaround to support Pascal with CUDA 7.5.  It reports
            // its compute capability as 6.x, but the compiler doesn't support
            // anything beyond 5.3.
            if (major == 6) {
                major = 5;
                minor = 3;
            }
        }
        major = 7;
        minor = 0;
        gpuArchitecture = intToString(major)+intToString(minor);
        computeCapability = major+0.1*minor;

5. Compile and install,

        make -j 12
        make install
        make PythonInstall

6. Test the installation (it's not going to find a CUDA device on the frontal machine),

        python -m simtk.testInstallation

7. In your submission script (to `qsub`) you should add:

        export LD_LIBRARY_PATH=$HOME/openmm/lib

    so that OpenMM libraries are found.

That's it. This build should also work for OpenMM 7.4.2.


## Compiling the TGNH Drude thermostat

The TGNH thermostat (http://doi.org/10.1021/acs.jpclett.9b02983) is a plugin to OpenMM 7.4.2. The authors are in the process of upgrading to the latest OpenMM 7.5.

1. Download or `git clone` the plugin from https://github.com/scychon/openmm_drudeNose

2. Configure

        mkdir build_drudeNose
        cd build_drudeNose
        ccmake ../openmm_drudeNose

    Set the following (change `user`):

        CMAKE_INSTALL_PREFIX=/home/user/openmm
        CUDA_HOST_COMPILER=/usr/local/cuda/bin/nvcc
        DRUDENOSE_BUILD_OPENCL_LIB=OFF
        OPENMM_DIR=/home/user/openmm
        PYTHON_EXECUTABLE=/home/user/miniconda3/bin/python

    Press `'c'` and '`g`'.

3. Build and install

        make
        make install
        make PythonInstall

Done.

## Choice of OpenMM version and Drude thermostat

Although the TGNH thermostat is certainly superior, I couldn't make it run with our `xml` input files, which run fine in the latest OpenMM 7.5. So there are some bugs or incomplete implementations in OpenMM 7.4.2.

I suspect the authors of the TGNH will in sometime update to OpenMM 7.5, so it's probably not worth the effort to reverse engineer the force field file formats that would run in OpenMM 7.4.2.

As a result, I would opt to use the default Drude thermostats that come with OpenMM 7.5. Maybe these are not the very best for transport properties but they may be ok for structural quantities.

Also, the Langevin thermostats can be considerably faster than Nosé-Hoover, also in their Drude versions. 

