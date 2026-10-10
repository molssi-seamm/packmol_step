.. _user-guide:

**********
User Guide
**********
The Packmol step builds a region (a cluster or a periodic cell) filled with molecules,
using Packmol_ [Martinez2009]_. You say which molecules and in what proportions, and how
big the region is or how much material it holds; the step works out the numbers of
molecules and the dimensions, has Packmol place the molecules without overlaps, and
replaces or adds a structure in SEAMM with the result.

.. _Packmol: https://m3g.github.io/packmol/

The molecules
=============
Each row of the table at the bottom of the dialog is one kind of molecule:

Component
   ``fluid`` or ``solute``. Fluid molecules fill the region in the given proportions.
   A solute is a single molecule fixed at the center of the region, with the fluid
   packed around it -- a protein in water, say, or a periodic cell of a zeolite or MOF
   to fill. There can be at most one solute.

Source and definition
   Where the molecule comes from:

   * ``SMILES``: the definition is a SMILES string, and the step builds the molecule
     with Open Babel. Charged species are fine: ``[Li+]``, ``F[P-](F)(F)(F)(F)F``.
   * ``configuration``: a structure already in SEAMM, from a Read Structure or
     From SMILES step earlier in the flowchart. The definition names it as
     ``system/configuration`` (e.g. ``PF6/initial``), or just ``configuration`` for one
     in the current system; an empty definition or ``current`` uses the current
     configuration. A source structure can be anything SMILES cannot describe well, such
     as a cluster of a lithium ion with its solvent shell. It is left unchanged.

Proportion
   For fluid molecules, the relative numbers of each kind: ``1`` and ``3`` give one
   molecule of the first kind for every three of the second. Only the ratios matter.
   For a solute it is ignored; there is always one.

Any of the entries can be a variable, e.g. ``$smiles`` or ``$ratio``.

The region
==========
**Create periodic system** chooses between a cluster (``No``) and a periodic cell
(``Yes``), and **Shape of the region** between ``cubic``, ``rectangular`` and
``spherical``; a periodic cell is cubic or rectangular. A periodic cell is packed
with Packmol's own periodic boundary conditions, so molecules near one face do not
overlap the images of those near the opposite face.

How big is it?
--------------
**The dimensions will be** sets the size of the region in one of five ways. Some of them
also fix how much fluid there is, and the rest leave that to **Get number of fluid
molecules by** (below).

``given explicitly``
   The edge of the cube, the three sides ``a``, ``b`` and ``c`` of a rectangular box, or
   the diameter of the sphere.

``calculated from the volume``
   The volume; for a rectangular box, also the ratios of its sides (``a ratio``,
   ``b ratio``, ``c ratio``, e.g. 1, 1, 2 for a box twice as long in *z*).

``calculated from the solute dimensions``
   For a solute: the region is the solute's bounding box or sphere plus a layer of
   fluid of the given **solvent thickness**. In a periodic cell the layer is added once
   per side, since the neighboring images supply the rest. A periodic solute -- a
   crystal cell to fill -- gives the cell itself; it must be orthorhombic.

``calculated from the density``
   The density of the whole region. The number of molecules comes first (from an
   approximate number of atoms or molecules), and the volume follows from their mass.

``calculated using the Ideal Gas Law``
   For a gas: the temperature and pressure. The number of molecules comes first, and the
   volume follows from :math:`PV = NkT`.

How much fluid?
---------------
**Get number of fluid molecules by** offers the choices that make sense with the
dimensions:

``rounding this number of atoms`` / ``rounding this number of molecules``
   An approximate total, from which the step takes the nearest whole numbers of
   molecules in the requested proportions. With a solute, its atoms count toward the
   number of atoms but it is not one of the molecules.

``using the density``
   The density of the region, given its size; the mass of fluid fills it to that
   density.

``using the Ideal Gas Law``
   The temperature and pressure, given the size of the region.

With ``calculated from the density`` or ``calculated using the Ideal Gas Law`` the
amount is one of the first two, since the density or T and P then sets the size; with
``calculated from the solute dimensions`` it is one of the last two.

Forcefields
===========
If a Forcefield step comes before the Packmol step, the step assigns the forcefield's
atom types and charges to each kind of molecule before packing, and the packed system
carries them, ready for LAMMPS. **Assign forcefield** controls this: ``If not assigned``
(the default) types only molecules that lack types for the current forcefield,
``Always`` retypes them all, and ``No`` leaves the molecules as they are. Machine-learned
potentials (PyTorch) and OpenKIM models need no atom types, so with them nothing is
assigned.

The new structure
=================
**First structure** says what to do with the packed structure: overwrite the current
configuration (the default), add a new configuration to the current system, or create
a new system. **System name** and **Configuration name** name it. The structure's
bonds, with their bond orders, come from the molecules; its charge is the sum of their
charges.

The output
==========
The step first prints what it will do, then what it built: the size of the region, and
a table of the molecules with the requested and actual percentages, the number of each
kind, and its molarity -- moles per liter of the whole region, solute included. Since
the numbers of molecules are whole, the actual percentages differ a little from the
requested ones, the more so the fewer molecules there are. Last come the total number of
atoms and the density.

Tips
====
* **Neutral cells.** For ions, make sure the counts give a neutral cell: one
  ``[Li+]`` for each ``F[P-](F)(F)(F)(F)F``, in equal proportions.
* **Dense or crowded systems.** Packmol keeps atoms of different molecules at least
  2 Å apart. Near or above the liquid density, especially with large molecules, it may
  take long or fail to converge. Pack at a somewhat lower density and let a
  constant-pressure (NPT) simulation bring the system to its equilibrium density.
* **Small cells.** A small cell holds few molecules, so minor components may round to
  zero or far from the requested proportion. Check the actual percentages in the output,
  or use more atoms.
* **Different every time.** Packmol starts from random positions, so each run gives a
  different packing of the same composition.

References
==========
.. [Martinez2009] L. Martínez, R. Andrade, E. G. Birgin, J. M. Martínez. PACKMOL: A
   package for building initial configurations for molecular dynamics simulations.
   *J. Comput. Chem.* **2009**, *30*, 2157-2164. DOI: 10.1002/jcc.21224

Index
=====

* :ref:`genindex`
