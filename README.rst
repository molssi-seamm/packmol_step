=====================
SEAMM Packmol Plug-in
=====================

.. image:: https://img.shields.io/github/issues-pr-raw/molssi-seamm/packmol_step
   :target: https://github.com/molssi-seamm/packmol_step/pulls
   :alt: GitHub pull requests

.. image:: https://github.com/molssi-seamm/packmol_step/workflows/CI/badge.svg
   :target: https://github.com/molssi-seamm/packmol_step/actions
   :alt: Build Status

.. image:: https://codecov.io/gh/molssi-seamm/packmol_step/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/molssi-seamm/packmol_step
   :alt: Code Coverage

.. image:: https://github.com/molssi-seamm/packmol_step/workflows/CodeQL/badge.svg
   :target: https://github.com/molssi-seamm/packmol_step/security/code-scanning
   :alt: Code Quality

.. image:: https://github.com/molssi-seamm/packmol_step/workflows/Release/badge.svg
   :target: https://molssi-seamm.github.io/packmol_step/index.html
   :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/packmol_step.svg
   :target: https://pypi.python.org/pypi/packmol_step
   :alt: PyPi VERSION

A SEAMM plug-in for building periodic boxes of fluid using Packmol_

This plug-in takes the molecule in the current system and creates a
periodic box containing many copies of the molecule in order to
simulate a fluid.

* Free software: BSD license
* Documentation: https://molssi-seamm.github.io/packmol_step/index.html
* Code: https://github.com/molssi-seamm/packmol_step

.. _Packmol: http://m3g.iqm.unicamp.br/packmol/home.shtml

Features
--------

* Multiple ways to specify final cell:

  - Size of the cubic cell *and* density *or* number of molecules *or*
    number of atoms.
  - Volume *and* density *or* number of molecules *or* number of atoms.
  - density *and* size of the cubic cell *or* volume *or* number of
    molecules *or* of atoms.

Acknowledgements
----------------

This package was created with Cookiecutter_ and the `molssi-seamm/cookiecutter-seamm-plugin`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`molssi-seamm/cookiecutter-seamm-plugin`: https://github.com/molssi-seamm/cookiecutter-seamm-plugin

Developed by the Molecular Sciences Software Institute (MolSSI_),
which receives funding from the `National Science Foundation`_ under
awards OAC-1547580 and CHE-2136142

.. _MolSSI: https://www.molssi.org
.. _`National Science Foundation`: https://www.nsf.gov
