# -*- coding: utf-8 -*-
"""A node or step for PACKMOL in a workflow"""

import molssi_workflow
from molssi_workflow import ureg, Q_, data, units_class  # nopep8
import logging
import mendeleev
from molssi_util import pdbfile
import molssi_util.printing as printing
from molssi_util.printing import FormattedText as __
import pprint  # nopep8

logger = logging.getLogger(__name__)
job = printing.getPrinter()
printer = printing.getPrinter('packmol')


class PACKMOL(molssi_workflow.Node):
    def __init__(self, workflow=None, extension=None):
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
            workflow=workflow, title='PACKMOL', extension=extension)

    def describe(self, indent='', json_dict=None):
        """Write out information about what this node will do
        If json_dict is passed in, add information to that dictionary
        so that it can be written out by the controller as appropriate.
        """

        next_node = super().describe(indent, json_dict)

        string = 'Creating a cubic supercell '
        if 'cubic' in self.method:
            size = self.cube_size
            if isinstance(size, units_class):
                string += '{:~P} on a side'.format(size)
            else:
                string += '{} on a side'.format(size)
        elif 'Volume' in self.method:
            volume = self.volume
            if isinstance(volume, units_class):
                string += 'with a volume of {:~P}'.format(volume)
            else:
                string += 'with a volume of {}'.format(volume)
        elif 'Density' in self.method:
            density = self.density
            if isinstance(density, units_class):
                string += 'with a density of {:~P}'.format(density)
            else:
                string += 'with a density of {}'.format(density)
        elif 'molecules' in self.method:
            n_molecules = self.n_molecules
            string += 'containing {} molecules'.format(n_molecules)
        elif 'atoms' in self.method:
            n_atoms = self.n_atoms
            string += 'containing about {} atoms'.format(n_atoms)
        elif 'moles' in self.method:
            n_moles = self.n_moles
            if isinstance(n_moles, units_class):
                string += 'containing {:~P}'.format(n_moles)
            else:
                string += 'containing {} moles'.format(n_moles)
        elif 'Mass' in self.method:
            mass = self.mass
            if isinstance(mass, units_class):
                string += 'with a mass of {:~P}'.format(mass)
            else:
                string += 'with a mass of {}'.format(mass)
        else:
            raise RuntimeError(
                "Don't recognize the method {}".format(self.method))


        if 'cubic' in self.submethod:
            size = self.cube_size
            if isinstance(size, units_class):
                string += ' in a cubic cell {:~P} on a side'.format(size)
            else:
                string += ' in a cubic {} on a side'.format(size)
        elif 'Volume' in self.submethod:
            volume = self.volume
            if isinstance(volume, units_class):
                string += ' with a volume of {:~P}'.format(volume)
            else:
                string += ' with a volume of {}'.format(volume)
        elif 'Density' in self.submethod:
            density = self.density
            if isinstance(density, units_class):
                string += ' with a density of {:~P}'.format(density)
            else:
                string += ' with a density of {}'.format(density)
        elif 'molecules' in self.submethod:
            n_molecules = self.n_molecules
            string += ' containing {} molecules'.format(n_molecules)
        elif 'atoms' in self.submethod:
            n_atoms = self.n_atoms
            string += ' containing about {} atoms'.format(n_atoms)
        elif 'moles' in self.submethod:
            n_moles = self.n_moles
            if isinstance(n_moles, units_class):
                string += ' containing {:~P}'.format(n_moles)
            else:
                string += ' containing {} moles'.format(n_moles)
        elif 'Mass' in self.submethod:
            mass = self.mass
            if isinstance(mass, units_class):
                string += ' with a mass of {:~P}'.format(mass)
            else:
                string += ' with a mass of {}'.format(mass)
        else:
            raise RuntimeError(
                "Don't recognize the submethod {}".format(self.submethod))

        job.job(__(string, indent=self.indent+'    '))

        return next_node

    def run(self):
        """Run a PACKMOL building step
        """

        next_node = super().run(printer)

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
            size = self.get_value(self.cube_size)
        elif 'Volume' in self.method:
            volume = self.get_value(self.volume)
        elif 'Density' in self.method:
            density = self.get_value(self.density)
            if isinstance(density, tuple) or isinstance(density, list):
                density = Q_(float(density[0]), density[1])
            elif not isinstance(density, units_class):
                try:
                    density = Q_(density)
                except:
                    density = Q_(float(density), 'g/mL')
        elif 'molecules' in self.method:
            n_molecules = self.get_value(self.n_molecules)
        elif 'atoms' in self.method:
            n_atoms = self.get_value(self.n_atoms)
        elif 'moles' in self.method:
            n_moles = self.get_value(self.n_moles)
        elif 'Mass' in self.method:
            mass = self.get_value(self.mass)
        else:
            raise RuntimeError(
                "Don't recognize the method {}".format(self.method))

        if 'cubic' in self.submethod:
            size = self.get_value(self.cube_size)
            if not isinstance(size, units_class):
                size = Q_(size, 'angstrom')
        elif 'Volume' in self.submethod:
            volume = self.get_value(self.volume)
            if not isinstance(volume, units_class):
                volume = Q_(volume, 'angstrom**3')
        elif 'Density' in self.submethod:
            density = self.get_value(self.density)
            if not isinstance(density, units_class):
                density = Q_(density, 'g/mL')
        elif 'molecules' in self.submethod:
            n_molecules = self.get_value(self.n_molecules)
        elif 'atoms' in self.submethod:
            n_atoms = self.get_value(self.n_atoms)
        elif 'moles' in self.submethod:
            n_moles = self.get_value(self.n_moles)
        elif 'Mass' in self.submethod:
            mass = self.get_value(self.mass)
            if isinstance(mass, tuple) or isinstance(mass, list):
                mass = Q_(mass[0], mass[1])
            elif not isinstance(mass, units_class):
                mass = Q_(mass, 'Da')
        else:
            raise RuntimeError(
                "Don't recognize the submethod {}".format(self.submethod))

        # Print what we are going to do...
        string = 'Creating a cubic supercell '
        if 'cubic' in self.method:
            string += '{:~P} on a side'.format(size)
        elif 'Volume' in self.method:
            string += 'with a volume of {:~P}'.format(volume)
        elif 'Density' in self.method:
            string += 'with a density of {:~P}'.format(density)
        elif 'molecules' in self.method:
            string += 'containing {} molecules'.format(n_molecules)
        elif 'atoms' in self.method:
            string += 'containing about {} atoms'.format(n_atoms)
        elif 'moles' in self.method:
            string += 'containing {:~P}'.format(n_moles)
        elif 'Mass' in self.method:
            string += 'with a mass of {:~P}'.format(mass)
        else:
            raise RuntimeError(
                "Don't recognize the method {}".format(self.method))

        if 'cubic' in self.submethod:
            string += ' in a cubic cell {:~P} on a side'.format(size)
        elif 'Volume' in self.submethod:
            string += ' with a volume of {:~P}'.format(volume)
        elif 'Density' in self.submethod:
            string += ' with a density of {:~P}'.format(density)
        elif 'molecules' in self.submethod:
            string += ' containing {} molecules'.format(n_molecules)
        elif 'atoms' in self.submethod:
            string += ' containing about {} atoms'.format(n_atoms)
        elif 'moles' in self.submethod:
            string += ' containing {:~P}'.format(n_moles)
        elif 'Mass' in self.submethod:
            string += ' with a mass of {:~P}'.format(mass)
        else:
            raise RuntimeError(
                "Don't recognize the submethod {}".format(self.submethod))

        printer.important(__(string, indent=self.indent+'    '))

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

        string = 'Created a cubic cell {size:.5~P} on a side'
        string += ' with {n_molecules} molecules'
        string += ' for a total of {n_atoms} atoms in the cell'
        string += ' and a density of {density:.5~P}.'
        printer.important(__(string, indent=self.indent+'    ', **tmp))

        logger.log(0, 'Structure created by PACKMOL:\n\n' +
                   pprint.pformat(data.structure))

        return next_node

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
        molecular_mass = tmp_mass * ureg.g / ureg.mol  # g/mol
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
                n_moles = n_molecules / ureg.N_A
            elif n_molecules is not None:
                mass = n_molecules * molecular_mass
                density = mass / volume
                n_atoms = n_molecules * n_atoms_per_molecule
                n_moles = n_molecules / ureg.N_A
            elif n_atoms is not None:
                n_molecules = round(n_atoms / n_atoms_per_molecule)
                if n_molecules == 0:
                    n_molecules = 1
                mass = n_molecules * molecular_mass
                density = mass / volume
                n_atoms = n_molecules * n_atoms_per_molecule
                n_moles = n_molecules / ureg.N_A
            elif n_moles is not None:
                n_molecules = n_moles * ureg.N_A
                mass = n_molecules * molecular_mass
                density = mass / volume
                n_atoms = n_molecules * n_atoms_per_molecule
            elif mass is not None:
                density = mass / volume
                n_molecules = mass / molecular_mass
                n_atoms = n_molecules * n_atoms_per_molecule
                n_moles = n_molecules / ureg.N_A
        elif density is not None:
            if n_molecules is not None:
                mass = n_molecules * molecular_mass
                volume = mass / density
                n_atoms = n_molecules * n_atoms_per_molecule
                n_moles = n_molecules / ureg.N_A
            elif n_atoms is not None:
                n_molecules = round(n_atoms / n_atoms_per_molecule)
                if n_molecules == 0:
                    n_molecules = 1
                mass = n_molecules * molecular_mass
                volume = mass / density
                n_atoms = n_molecules * n_atoms_per_molecule
                n_moles = n_molecules / ureg.N_A
            elif n_moles is not None:
                n_molecules = n_moles * ureg.N_A
                mass = n_molecules * molecular_mass
                volume = mass / density
                n_atoms = n_molecules * n_atoms_per_molecule
            elif mass is not None:
                volume = mass / density
                n_molecules = mass / molecular_mass
                n_atoms = n_molecules * n_atoms_per_molecule
                n_moles = n_molecules / ureg.N_A
            size = volume**(1/3)
        else:
            raise RuntimeError(
                "Number of molecules, number of atoms, "
                "number of moles or the mass are not independenet "
                "quantities!")

        # make the units pretty
        size.ito('Å')
        volume.ito('Å**3')
        density.ito('g/ml')
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
