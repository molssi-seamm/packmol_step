User Documentation
==================

The PACKMOL step is used to create fluid systems or to solvate a single molecule or
structure. The fluid or solvent must be composed of reasonable small molecules,
otherwise it is impossible to pack them into the allowed volume using the algorithms in
PACKMOL. The solute, however, can be a large system or even a periodic, porous solid, in
which case the fluid will be packed inside the pores of the solid.

The resulting system can be periodic, giving a fluid box that can be simulated under
pressure, etc. Or the resulting system can be non-periodic, in which case it is a
droplet in vacuum. The fluid molecules can and probably will evaporate from such a
droplet if you run MD on the system.

After deciding whether you need a periodic system -- a fluid box -- or a non-periodic
droplet, you need to decide on the shape. For periodic systems the shape must fully tile
space, i.e. must be a unit cell. For simulations of pure fluids a cubic box is
satisfactory, but if you are solvating a large irregularly shaped molecule,
particularly if it is long and thin, you might want a rectangular box with three
different dimensions to better fit the solute molecule. At the moment, there is no provision
for cells with angles other than 90°.

Droplets can have any shape; however, the code is currently limited to spheres, cubes
and rectangular boxes with three differing edges. The general rectangular shape is again
useful for solvating large, irregular molecules.

After deciding upon a shape, you need to specify its dimensions, how many fluid
molecules to pack into it, and if there is more than one type of fluid molecule, the
ratios of the various types. If you want to solvate a system, you also need to specify
the solute or the porous solid to fill. You can specify the dimensions and numbers of
molecules explicitly or you can specify them implicitly by giving the density or using
the ideal gas law to calculate either the volume or the number of molecules.

Contents:

.. toctree::
   :maxdepth: 2

   overview

Indices and tables
------------------

* :ref:`genindex`
* :ref:`search`
