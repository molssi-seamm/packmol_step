***************
Getting Started
***************

Installation
============
The Packmol step is probably already installed in your SEAMM installation. If not, or
to bring it up to date, use the SEAMM manager::

    seamm-manager install packmol-step

This installs both the plug-in and Packmol itself, in a ``seamm-packmol`` environment
that the step finds through ``packmol.ini`` in your SEAMM root (``~/SEAMM`` by
default). See the `installation guide`_ for more about installing and updating SEAMM.

.. _installation guide: https://molssi-seamm.github.io/getting_started/installation/index.html

A box of water
==============
The simplest use of the step needs nothing else in the flowchart: Packmol builds the
molecules from SMILES. This flowchart (:download:`water_box.flow`) has a single Packmol
step that packs about 3000 atoms of water into a periodic cubic cell at 1.0 g/mL:

* **Molecules:** one row, component ``fluid``, source ``SMILES``, definition ``O``,
  amount ``1`` as a ``proportion``.
* **Create periodic system:** ``Yes``; **Shape of the region:** ``cubic``.
* **The dimensions will be** ``calculated from the density``, with a density of
  1.0 g/mL.
* **Get number of fluid molecules by** ``rounding this number of atoms``, with 3000
  atoms.

Running it prints what was built::

    Created a periodic cubic cell 31.0431 Å on a side with 1000 fluid molecules

        +-------------+-------------+-------------+----------+-----------+----------------+
        |  Component  | Structure   |   Requested |   Number |    Actual |   Molarity (M) |
        |-------------+-------------+-------------+----------+-----------+----------------|
        |    fluid    | O           |   100.000 % |     1000 | 100.000 % |        55.5078 |
        +-------------+-------------+-------------+----------+-----------+----------------+

    There are a total of 3000 atoms in the cell giving a density of 1.0 g/ml.

The new structure replaces the current configuration, ready for a forcefield or
quantum-chemistry step. To use it with a forcefield, put a Forcefield step before the
Packmol step: the step then assigns the atom types and charges to each kind of molecule
before packing, and the packed system carries them.

A mixture
=========
Each kind of molecule is a row of the table, and the proportions are the relative
numbers of molecules. This flowchart (:download:`carbonate_mixture.flow`) packs
ethylene carbonate (``O=C1OCCO1``) and dimethyl carbonate (``COC(=O)OC``) in the
ratio 3:7 into about 3000 atoms at 1.2 g/mL::

    Created a periodic cubic cell 31.9328 Å on a side with 263 fluid molecules

        +-------------+-------------+-------------+----------+----------+----------------+
        |  Component  | Structure   |   Requested |   Number |   Actual |   Molarity (M) |
        |-------------+-------------+-------------+----------+----------+----------------|
        |    fluid    | O=C1OCCO1   |    30.000 % |       79 | 30.038 % |         4.0287 |
        |    fluid    | COC(=O)OC   |    70.000 % |      184 | 69.962 % |         9.3833 |
        +-------------+-------------+-------------+----------+----------+----------------+

    There are a total of 2998 atoms in the cell giving a density of 1.2 g/ml.

The numbers of molecules are whole, so the actual percentages are close to, but not
exactly, the requested ones. The table reports both, and the molarity of each kind of
molecule in the cell.

An electrolyte
==============
Electrolytes are usually described by the concentration of the salt in a solvent mixture
given by weight, e.g. 1.0 M LiPF\ :sub:`6` in EC:DMC 3:7 (w/w). The step takes them
that way (:download:`lipf6_electrolyte.flow`):

* **Molecules:** EC and DMC with amounts ``3`` and ``7`` as ``proportion``, and
  ``[Li+]`` and ``F[P-](F)(F)(F)(F)F`` each with amount ``1.0`` as
  ``molarity (mol/L)``.
* **Proportions are** ``by mass``.
* A periodic cube from the density, 1.3 g/mL, with about 5000 atoms.

::

    Created a periodic cubic cell 37.7387 Å on a side with 480 fluid molecules

        +-------------+--------------------+-------------+----------+------------+----------------+---------------------+
        |  Component  | Structure          |   Requested |   Number |     Actual |   Molarity (M) |   Molality (mol/kg) |
        |-------------+--------------------+-------------+----------+------------+----------------+---------------------|
        |    fluid    | O=C1OCCO1          |  30.000 wt% |      127 | 30.051 wt% |         3.9237 |                     |
        |    fluid    | COC(=O)OC          |  70.000 wt% |      289 | 69.949 wt% |         8.9286 |                     |
        |    fluid    | [Li+]              |    1.0000 M |       32 |   0.9886 M |         0.9886 |              0.8598 |
        |    fluid    | F[P-](F)(F)(F)(F)F |    1.0000 M |       32 |   0.9886 M |         0.9886 |              0.8598 |
        +-------------+--------------------+-------------+----------+------------+----------------+---------------------+

    There are a total of 4994 atoms in the cell giving a density of 1.3 g/ml.

The molecules given as proportions are the solvent; the salt's ions are added to give
the molarity, here 32 of each, and the solvent's composition is by weight. The table
also gives the molality, per kilogram of the solvent. The molecules can equally be given
by molality (``molality (mol/kg)``), which needs no density or volume.

That should be enough to get started. For the other ways of setting the size and
contents of the region, and how the step works, see the
:ref:`User Guide <user-guide>`.
