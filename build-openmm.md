# OpenMM Installation Instructions


## Installation using conda

The easiest and recommended way to install OpenMM is using the `conda` package manager. For that, install `Miniconda` in your user account.

    wget https://repo.anaconda.com/miniconda/Miniconda3-*.sh
    bash Miniconda3-*.sh

Append channel `conda-forge` to the list of channels:

    conda config --append channels conda-forge

Separate environments are recommended for large packages that have many dependencies:

    conda create --name omm
    conda activate omm

 Then install OpenMM

    conda install openmm


## Test the installation

    python -m openmm.testInstallation

Check that `cudatoolkit` has been installed too if you have access to NVIDIA GPUs.


## Accessory packages and tools

You may want to install accessory packages, for example `mdtraj`, `openmm-plumed`.

It may be necessary to request specific versions python or of other dependencies for compatibility.  You can find that out:

    conda search <package> --info

In that case reinstall python and then install the packages.

    conda install python=3.9



# Installing from source

This is a more complex procedure but can give more control on versions of libraries or other dependencies. Not justified unless it is impossible to install OpenMM out-of-the-box via `conda`.

## Finding the version of the CUDA toolkit

GPU computing is a quickly evolving field and navigating among all the versions of cards, their drivers and compilers is essential. Locate the root of the CUDA installation and the CUDA compiler `nvcc`:

    which nvcc
    /usr/local/cuda/bin/nvcc --version

The command

    nvidia-smi

shows important information on NVIDIA GPU hardware present. In computing centers this doesn't work on frontal or submission machines because they don't have GPUs for calculations. You need to find this information otherwise or, if possible, ssh into the computing nodes with GPUs to check.


## Compilation of OpenMM on the PSMN computing center

1. Install `miniconda3`, with `numpy` and not much else, since the PSMN machines already have most of the tools needed by OpenMM (`SWIG`, `Doxygen`, etc.) This will provide a local python installation for OpenMM. Activate `conda` if not by default:

        conda activate

    The version of `cmake` on the PSMN is too old for OpenMM 7.7, so install `cmake` also under `conda`.

2. Download the OpenMM source code from https://github.com/openmm/openmm/releases/tag/7.7.0 and expand into a `src` dir; create a `build` dir.

        mkdir ~/src
        cd ~/src
        tar xzvf openmm-7.7.0.tar.gz
        mkdir build_openmm
        cd build_openmm

3. Configure the build

    In the `build_openmm` dir do:

        ccmake ../openmm-7.7.0

    press `'c'` to configure. Set the installation dir (replacing `user`) and CUDA compiler, also check that your local `python` was found (if not go back to 1.):

        CMAKE_INSTALL_PREFIX=/home/<user>/openmm
        PYTHON_EXECUTABLE=/home/<user>/miniconda3/bin/python

    then press `'g'` to generate the build files.

4. (This is outdated since end of 2022) Patch the source code to use `sm_70`. Edit the file `openmm-7.6.0/platforms/cuda/src/CudaContext.cpp` and add the two lines `major = 7;`, `minor = 0;` around line 227. Don't forget the end-of-line `';'` this is C++.

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

