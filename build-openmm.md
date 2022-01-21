# OpenMM Installation Instructions


## Finding the version of the CUDA toolkit

GPU computing is a quickly evolving field and navigating among all the versions of cards, their drivers and compilers is essential. Locate the root of the CUDA installation and the CUDA compiler `nvcc`:

    which nvcc
    /usr/local/cuda/bin/nvcc --version

The command

    nvidia-smi

shows important information on NVIDIA GPU hardware present. In computing centers this doesn't work on frontal or submission machines because they don't have GPUs for calculations. You need to ssh into the computing nodes with GPUs to check, for example in the PSMN:

    ssh r730gpu01 nvidia-smi


## Installation

### OpenMM 7.6.0

When installed with `conda`, OpenMM 7.6.0 comes compiled with the CUDA 11 toolkit  (so it may not be properly configured for all hardware setups, namely the one on the PSMN). The code may run but some functionalities will not work with older GPUs or drivers. Luckily, OpenMM is distributed in versions compatible with older versions of CUDA:

    conda install -c conda-forge openmm cudatoolkit=9.2

This would be the simplest and recommended way to install OpenMM.

For more control, OpenMM can be compiled from source (instructions below).

### OpenMM 7.4.2

OpenMM 7.4.2 can be installed using `conda`, choosing a version compiled with CUDA 9.2, from https://anaconda.org/omnia/openmm

    conda install -c omnia/label/cuda92 openmm

OpenMM 7.4.2 is compatible with the temperature-grouped Nosé-Hoover thermostat (http://doi.org/10.1021/acs.jpclett.9b02983), which is the best one for Drude polarizable force fields. Unfortunately, OpenMM 7.4.2 doesn't seem to run well with `xml` input files of the latest polarizable force fields, including ours.


### Test the installation

        ssh <machine-with-GPU>
        python -m openmm.testInstallation


## Installation on IDRIS

The Jean Zay machine has V100 cards, so the recipe for the PSMN may well work there. I don't know what CUDA version they have.


## Installation on the PSMN

The PSMN has 40 NVIDIA RTX 2080Ti GPUs, which are fast in single and mixed precision. Mixed precision is a great choice for MD.

The 2080 cards are of Turing architecture, ideally used with the CUDA 10 (or later) toolkit of drivers and compilers. The optimum compilation flag for these cards is `--arch=sm_75`.

The PSMN machines have CUDA 9.2 and an upgrade seems unlikely. The latest OpenMM versions may produce code with `--arch=sm_75` or later, which is not supported in CUDA 9.2 (this was true for OpenMM 7.5.0; it is possible that a binary installation works fine for OpenMM 7.6). It is therefore necessary to modify one file in the source code in order to specify `--arch=sm_70` (which corresponds to the previous generation of architecture named Volta, e.g. the V100 cards).

Maybe try first to install using `conda` the version for CUDA 9.2. If that doesn't work, then you'll need to compile from source.


## Compilation of OpenMM on the PSMN

1. Install `miniconda3`, with `numpy` and not much else, since the PSMN machines already have most of the tools needed by OpenMM (`SWIG`, `Doxygen`, etc.) This will provide a local python installation for OpenMM. Activate `conda` if not by default:

        conda activate

    The version of `cmake` on the PSMN is too old for OpenMM 7.6, so install `cmake` also under `conda`.

2. Download the OpenMM source code from https://github.com/openmm/openmm/releases/tag/7.6.0 and expand into a `src` dir; create a `build` dir.

        mkdir ~/src
        cd ~/src
        tar xzvf openmm-7.6.0.tar.gz
        mkdir build_openmm
        cd build_openmm

3. Configure the build

    In the `build_openmm` dir do:

        ccmake ../openmm-7.6.0

    press `'c'` to configure. Set the installation dir (replacing `user`) and CUDA compiler, also check that your local `python` was found (if not go back to 1.):

        CMAKE_INSTALL_PREFIX=/home/<user>/openmm
        PYTHON_EXECUTABLE=/home/<user>/miniconda3/bin/python

    then press `'g'` to generate the build files.

4. Patch the source code to use `sm_70`. Edit the file `openmm-7.6.0/platforms/cuda/src/CudaContext.cpp` and add the two lines `major = 7;`, `minor = 0;` around line 227. Don't forget the end-of-line `';'` this is C++.

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
        gpuArchitecture = 10*major+minor;
        computeCapability = major+0.1*minor;

    Alternatively, you can apply the patch I created,

        cd ~/src
        patch -p0 < openmm-sm_70.patch

5. Compile and install,

        make -j 12
        make install
        make PythonInstall

6. Test the installation (it won't find a CUDA device on the frontal machine),

        python -m openmm.testInstallation

7. In your submission script (to `qsub`) you may need to add

        export LD_LIBRARY_PATH=$HOME/openmm/lib

    so that OpenMM libraries are found.

That's it. You can test the installation as indicated above. These build instructions should also work with OpenMM 7.4.2.


## TGNH Drude thermostat (OpenMM 7.4.2)

The temperature-grouped Nosé-Hoover thermostat (http://doi.org/10.1021/acs.jpclett.9b02983) is a plugin to OpenMM 7.4.2. The authors are in the process of upgrading it to the latest OpenMM but gave no estimated date.

1. Download or `git clone` the plugin from https://github.com/scychon/openmm_drudeNose

2. Configure

        mkdir build_drudeNose
        cd build_drudeNose
        ccmake ../openmm_drudeNose

    Set the following (change `user`):

        CMAKE_INSTALL_PREFIX=/home/user/openmm
        DRUDENOSE_BUILD_OPENCL_LIB=OFF
        OPENMM_DIR=/home/user/openmm
        PYTHON_EXECUTABLE=/home/user/miniconda3/bin/python

    Press `'c'` and '`g`'.

3. Build and install

        make
        make install
        make PythonInstall

Done.

