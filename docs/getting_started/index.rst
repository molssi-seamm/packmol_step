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
  proportion ``1``.
* **Create periodic system:** ``Yes``; **Shape of the region:** ``cubic``.
* **The dimensions will be** ``calculated from the density``, with a density of
  1.0 g/mL.
* **Get number of fluid molecules by** ``rounding this number of atoms``, with 3000
  atoms.

Running it prints what was built::

    Created a periodic cubic cell 31.0431 Å on a side with 1000 fluid molecules

        +-------------+-------------+---------------+----------+------------+----------------+
        |  Component  | Structure   |   Requested % |   Number |   Actual % |   Molarity (M) |
        |-------------+-------------+---------------+----------+------------+----------------|
        |    fluid    | O           |       100.000 |     1000 |    100.000 |        55.5078 |
        +-------------+-------------+---------------+----------+------------+----------------+

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

        +-------------+-------------+---------------+----------+------------+----------------+
        |  Component  | Structure   |   Requested % |   Number |   Actual % |   Molarity (M) |
        |-------------+-------------+---------------+----------+------------+----------------|
        |    fluid    | O=C1OCCO1   |        30.000 |       79 |     30.038 |         4.0287 |
        |    fluid    | COC(=O)OC   |        70.000 |      184 |     69.962 |         9.3833 |
        +-------------+-------------+---------------+----------+------------+----------------+

    There are a total of 2998 atoms in the cell giving a density of 1.2 g/ml.

The numbers of molecules are whole, so the actual percentages are close to, but not
exactly, the requested ones. The table reports both, and the molarity of each kind of
molecule in the cell.

That should be enough to get started. For the other ways of setting the size and
contents of the region, and how the step works, see the
:ref:`User Guide <user-guide>`.
