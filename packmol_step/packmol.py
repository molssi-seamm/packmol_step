# -*- coding: utf-8 -*-
"""A node or step for PACKMOL in a workflow"""

import molssi_workflow
from molssi_workflow import units, Q_, data  # nopep8
import logging
import mendeleev
from molssi_util import pdbfile
import pprint  # nopep8

logger = logging.getLogger(__name__)


class PACKMOL(molssi_workflow.Node):
    def __init__(self, workflow=None, gui_object=None, extension=None):
        '''Setup the main PACKMOL step

        Keyword arguments:
        '''
        logger.debug('Creating PACKMOL {}'.format(self))

        self._data = {}
        self.method = 'Density'
        self.submethod = 'Approximate number of atoms'

        self.tolerance = Q_(2, 'angstrom')
        self.cube_size = Q_(40, 'angstrom')
        self.n_molecules = 100
        self.n_atoms = 2000
        self.volume = Q_(64000, 'angstrom**3')
        self.density = Q_(0.7, 'g/mL')
        self.n_moles = Q_(1, 'mole')
        self.mass = Q_(1, 'g')

        super().__init__(
            workflow=workflow, title='PACKMOL', gui_object=gui_object,
            extension=extension)

    def run(self):
        """Run a PACKMOL building step
        """

        logger.info('   method = {}'.format(self.method))
        logger.info('submethod = {}'.format(self.submethod))

        size = None
        volume = None
        density = None
        n_molecules = None
        n_atoms = None
        n_moles = None
        mass = None

        if 'cubic' in self.method:
            size = self.cube_size
        elif 'Volume' in self.method:
            volume = self.volume
        elif 'Density' in self.method:
            density = self.density
        elif 'molecules' in self.method:
            n_molecules = self.n_molecules
        elif 'atoms' in self.method:
            n_atoms = self.n_atoms
        elif 'moles' in self.method:
            n_moles = self.n_moles
        elif 'Mass' in self.method:
            mass = self.mass
        else:
            raise RuntimeError(
                "Don't recognize the method {}".format(self.method))

        if 'cubic' in self.submethod:
            size = self.cube_size
        elif 'Volume' in self.submethod:
            volume = self.volume
        elif 'Density' in self.submethod:
            density = self.density
        elif 'molecules' in self.submethod:
            n_molecules = self.n_molecules
        elif 'atoms' in self.submethod:
            n_atoms = self.n_atoms
        elif 'moles' in self.submethod:
            n_moles = self.n_moles
        elif 'Mass' in self.submethod:
            mass = self.mass
        else:
            raise RuntimeError(
                "Don't recognize the submethod {}".format(self.submethod))

        tmp = self.calculate(size=size, volume=volume, density=density,
                             n_molecules=n_molecules, n_atoms=n_atoms,
                             n_moles=n_moles, mass=mass)

        size = tmp['size'].to('Å').magnitude
        n_molecules = tmp['n_molecules']

        tolerance = self.tolerance.to('Å').magnitude
        lines = []
        lines.append('tolerance {}'.format(tolerance))
        lines.append('output packmol.pdb')
        lines.append('filetype pdb')
        lines.append('structure input.pdb')
        lines.append('number {}'.format(n_molecules))
        lines.append('inside cube 0.0 0.0 0.0 {:.4f}'.format(
            size - tolerance))
        lines.append('end structure')
        lines.append('')

        files = {'input.pdb': pdbfile.from_molssi(data.structure)}
        files['input.inp'] = '\n'.join(lines)

        logger.log(0, pprint.pformat(files))

        local = molssi_workflow.ExecLocal()
        result = local.run(
            cmd='packmol < input.inp',
            shell=True,
            files=files,
            return_files=['packmol.pdb']
        )

        logger.debug(pprint.pformat(result))

        # Parse the resulting PDB file
        new_structure = pdbfile.to_molssi(result['packmol.pdb']['data'])

        # Ouch! Packmol just gives back atoms and coordinates, so we
        # need to graft to the original structure.

        molecule = {**data.structure}
        n_atoms_per_molecule = len(molecule['atoms']['elements'])
        data.structure = new_structure
        atoms = data.structure['atoms']
        n_atoms = len(atoms['elements'])
        if n_atoms_per_molecule * n_molecules != n_atoms:
            raise RuntimeError(
                'Serious problem in PACKMOL with the number of atoms'
                ' {} != {}'.format(n_atoms,
                                   n_atoms_per_molecule * n_molecules)
            )
        # Set the bonds from the molecule
        molecule_bonds = molecule['bonds']
        bonds = data.structure['bonds'] = []
        offset = 0
        for molecule_number in range(1, n_molecules+1):
            for bond in molecule_bonds:
                i, j, order = bond
                bonds.append((i+offset, j+offset, order))
            offset += n_atoms_per_molecule

        # Duplicate the atom types if they exist
        ff = molssi_workflow.data.forcefield
        ff_name = ff.current_forcefield
        molecule_atoms = molecule['atoms']
        if 'atom_types' in molecule_atoms and \
           ff_name in molecule_atoms['atom_types']:
            if 'atom_types' not in atoms:
                atoms['atom_types'] = {}
            atoms['atom_types'][ff_name] = \
                molecule_atoms['atom_types'][ff_name] * n_molecules

        # make periodic of correct size
        data.structure['periodicity'] = 3
        data.structure['cell'] = [size, size, size, 90.0, 90.0, 90.0]

        logger.log(0, 'Structure created by PACKMOL:\n\n' +
                   pprint.pformat(data.structure))

        return super().run()

    def calculate(self, size=None, volume=None, density=None,
                  n_molecules=None, n_atoms=None, n_moles=None, mass=None):
        """Work out the other variables given any two independent ones"""

        if data.structure is None:
            logger.error('PACKMOL run(): there is no structure!')
            raise RuntimeError('PACKMOL run(): there is no structure!')

        elements = data.structure['atoms']['elements']
        n_atoms_per_molecule = len(elements)
        tmp_mass = 0.0
        for element in elements:
            tmp_mass += mendeleev.element(element).mass
        molecular_mass = tmp_mass * units.g / units.mol  # g/mol
        molecular_mass.ito('kg')

        n_parameters = 0
        if size is not None:
            n_parameters += 1
        if volume is not None:
            n_parameters += 1
        if density is not None:
            n_parameters += 1
        if n_molecules is not None:
            n_parameters += 1
        if n_atoms is not None:
            n_parameters += 1
        if n_moles is not None:
            n_parameters += 1
        if mass is not None:
            n_parameters += 1

        if n_parameters != 2:
            raise RuntimeError('Exactly two independent parameters '
                               'must be given, not {}'.format(n_parameters))

        if size is not None or volume is not None:
            if size is not None:
                if volume is not None:
                    raise RuntimeError("Size and volume are not independent!")

                volume = size**3
            else:
                size = volume**(1/3)

            if density is not None:
                # rho = mass/volume
                mass = density * volume
                n_molecules = mass / molecular_mass
                n_atoms = n_molecules * n_atoms_per_molecule
                n_moles = n_molecules / units.N_A
            elif n_molecules is not None:
                mass = n_molecules * molecular_mass
                density = mass / volume
                n_atoms = n_molecules * n_atoms_per_molecule
                n_moles = n_molecules / units.N_A
            elif n_atoms is not None:
                n_molecules = round(n_atoms / n_atoms_per_molecule)
                if n_molecules == 0:
                    n_molecules = 1
                mass = n_molecules * molecular_mass
                density = mass / volume
                n_atoms = n_molecules * n_atoms_per_molecule
                n_moles = n_molecules / units.N_A
            elif n_moles is not None:
                n_molecules = n_moles * units.N_A
                mass = n_molecules * molecular_mass
                density = mass / volume
                n_atoms = n_molecules * n_atoms_per_molecule
            elif mass is not None:
                density = mass / volume
                n_molecules = mass / molecular_mass
                n_atoms = n_molecules * n_atoms_per_molecule
                n_moles = n_molecules / units.N_A
        elif density is not None:
            if n_molecules is not None:
                mass = n_molecules * molecular_mass
                volume = mass / density
                n_atoms = n_molecules * n_atoms_per_molecule
                n_moles = n_molecules / units.N_A
            elif n_atoms is not None:
                n_molecules = round(n_atoms / n_atoms_per_molecule)
                if n_molecules == 0:
                    n_molecules = 1
                mass = n_molecules * molecular_mass
                volume = mass / density
                n_atoms = n_molecules * n_atoms_per_molecule
                n_moles = n_molecules / units.N_A
            elif n_moles is not None:
                n_molecules = n_moles * units.N_A
                mass = n_molecules * molecular_mass
                volume = mass / density
                n_atoms = n_molecules * n_atoms_per_molecule
            elif mass is not None:
                volume = mass / density
                n_molecules = mass / molecular_mass
                n_atoms = n_molecules * n_atoms_per_molecule
                n_moles = n_molecules / units.N_A
            size = volume**(1/3)
        else:
            raise RuntimeError(
                "Number of molecules, number of atoms, "
                "number of moles or the mass are not independenet "
                "quantities!")

        # make the units pretty
        size.ito_base_units()
        volume.ito_base_units()
        density.ito_base_units()
        n_moles.ito_base_units()
        mass.ito_base_units()

        logger.debug(" size = {:~P}".format(size))
        logger.debug("             volume = {:~P}".format(volume))
        logger.debug("            density = {:~P}".format(density))
        logger.debug("number of molecules = {}".format(n_molecules))
        logger.debug("    number of atoms = {}".format(n_atoms))
        logger.debug("    number of moles = {:~P}".format(n_moles))
        logger.debug("               mass = {:~P}".format(mass))

        return {
            'size': size,
            'volume': volume,
            'density': density,
            'n_molecules': n_molecules,
            'n_atoms': n_atoms,
            'n_moles': n_moles,
            'mass': mass
        }
