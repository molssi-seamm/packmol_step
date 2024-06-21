=======
History
=======
2024.6.21.1 -- Internal release for Docker
    * There was an internal issue creating the Docker image.
      
2024.6.21 -- Switching to RDKit for SMILES
    * Using RDKit for SMILES since we found some issues with OpenBabel, and also the
      atom typing uses RDKit, so this is more compatible.
      
2024.3.19 -- Updated installer for new scheme
    * packmol-step-installer now uses the new scheme, which supports both Conda and
      Docker installation.
    * Added seamm-packmol Docker image

2024.1.16 -- Adding support for containers
    * Added the ability to work in Docker containers.
      
2023.9.6 -- Using fractional coordinates for periodic systems.
    * By convention, SEAMM is using fractional coordinates for periodic systems. The
      PACKMOL step was creating periodic structures with Cartesian coordinates, which
      can be a bit confusing, though it did not affect any reauls. This change fixes the
      issue. 
      
2023.2.15 -- Restructured documentation and moved to new theme.

2022.5.31 -- Substantial enhancements
    Added ability to solvate molecules and increased the options to include

    * spherical regions
    * cubic and rectangular regions
    * cubic and rectangular unit cells for periodic systems
    * input molecules from any combination of system/configurations and SMILES
    * reworked GUI to be more intuitive.

2021.11.27 -- Fixed bug with atom types.

2021.10.25 -- Bugfix for problems with ideal gas approach.

2021.8.29 -- Multiple different molecules available via SMILES
   This release adds

   * the ability to directly generate multiple different molecules from SMILES, giving
     the stoichiometry for packing into the fluid box.
   * specifying the desired cell with the temperature and pressure, along with one of
     the volume, length of the box side, number of molecules or number of atoms. This
     uses the ideal gas law, so will only be reasonable at higher temperatures and lower
     densities. 

   Additionally, internally the release adds integration tests to check whether the module works properly in the SEAMM environment.

2021.6.3 -- internal change for improvements in parsing the commandline

2021.5.25 -- Added installer for Packmol executable.

2021.2.11 (11 February 2021)
----------------------------

* Updated the README file to give a better description.
* Updated the short description in setup.py to work with the new installer.
* Added keywords for better searchability.

2021.2.4 (4 February 2021)
--------------------------

* Updated for compatibility with the new system classes in MolSystem
  2021.2.2 release.

2020.12.5 (5 December 2020)
---------------------------

* Internal: switching CI from TravisCI to GitHub Actions, and in the
  process moving documentation from ReadTheDocs to GitHub Pages where
  it is consolidated with the main SEAMM documentation.

2020.11.2 (2 November 2020)
---------------------------

* Updated to be compatible with the new command-line argument
  handling.

2020.10.7 (7 October 2020)
----------------------------

* Added citations to be printed and stored.

2020.9.29 (29 September 2020)
-----------------------------

* Updated to be compatible with the new system classes in MolSystem.

2020.8.1 (1 August 2020)
------------------------

* Fixed bugs in the edit dialog.

0.9 (15 April 2020)
-------------------

* General bug fixing and code cleanup.
* Part of release of all modules.

0.7.0 (17 December 2019)
------------------------

* General clean-up of code and output.
* Part of release of all modules.

v0.3.0 (27 August 2019)
-----------------------

* First running version with reasonable output.

0.2.0 (13 August 2019)
----------------------

* First release on PyPI.
