# -*- coding: utf-8 -*-

"""A node or step for PACKMOL in a seamm"""

import logging
import mendeleev
import seamm
from seamm import data
from seamm_util import ureg, Q_, units_class  # noqa: F401
from seamm_util import pdbfile
import seamm_util.printing as printing
from seamm_util.printing import FormattedText as __
import packmol_step
import pprint  # nopep8

logger = logging.getLogger(__name__)
job = printing.getPrinter()
printer = printing.getPrinter('packmol')


class PACKMOL(seamm.Node):

    def __init__(self, flowchart=None, extension=None):
        '''Setup the main PACKMOL step

        Keyword arguments:
        '''
        logger.debug('Creating PACKMOL {}'.format(self))

        super().__init__(
            flowchart=flowchart, title='PACKMOL', extension=extension
        )

        self.parameters = packmol_step.PACKMOL_Parameters()

    def description(self, P):
        """Prepare information about what this node will do
        """

        text = 'Creating a cubic supercell '
        if P['method'][0] == '$':
            text += 'with the method given by {method}'
        elif 'cubic' in P['method']:
            text += '{size of cubic cell} on a side'
        elif 'volume' in P['method']:
            text += 'with a volume of {volume}'
        elif 'density' in P['method']:
            text += 'with a density of {density}'
        elif 'molecules' in P['method']:
            text += 'containing {number of molecules} molecules'
        elif 'atoms' in P['method']:
            text += 'containing about {approximate number of atoms} atoms'
        else:
            raise RuntimeError(
                "Don't recognize the method {}".format(P['method'])
            )

        if P['submethod'][0] == '$':
            text += ' and a submethod given by {submethod}'
        elif 'cubic' in P['submethod']:
            text += ' in a cubic {size of cubic cell} on a side'
        elif 'volume' in P['submethod']:
            text += ' with a volume of {volume}'
        elif 'density' in P['submethod']:
            text += ' with a density of {density}'
        elif 'molecules' in P['submethod']:
            text += ' containing {number of molecules} molecules'
        elif 'atoms' in P['submethod']:
            text += ' containing about {approximate number of atoms} atoms'
        else:
            raise RuntimeError(
                "Don't recognize the submethod {}".format(P['submethod'])
            )

        return text

    def describe(self, indent='', json_dict=None):
        """Write out information about what this node will do
        If json_dict is passed in, add information to that dictionary
        so that it can be written out by the controller as appropriate.
        """

        next_node = super().describe(indent, json_dict)

        P = self.parameters.values_to_dict()

        text = self.description(P)

        job.job(__(text, **P, indent=self.indent + '    '))

        return next_node

    def run(self):
        """Run a PACKMOL building step
        """

        next_node = super().run(printer)

        P = self.parameters.current_values_to_dict(
            context=seamm.flowchart_variables._data
        )

        logger.info('   method = {}'.format(P['method']))
        logger.info('submethod = {}'.format(P['submethod']))

        # Print what we are doing
        text = self.description(P)
        printer.important(__(text, **P, indent='    '))

        size = None
        volume = None
        density = None
        n_molecules = None
        n_atoms = None
        n_moles = None
        mass = None

        if 'cubic' in P['method']:
            size = P['size of cubic cell']
        elif 'volume' in P['method']:
            volume = P['volume']
        elif 'density' in P['method']:
            density = P['density']
        elif 'molecules' in P['method']:
            n_molecules = P['number of molecules']
        elif 'atoms' in P['method']:
            n_atoms = P['approximate number of atoms']
        else:
            raise RuntimeError(
                "Don't recognize the method {}".format(P['method'])
            )

        if 'cubic' in P['submethod']:
            size = P['size of cubic cell']
        elif 'volume' in P['submethod']:
            volume = P['volume']
        elif 'density' in P['submethod']:
            density = P['density']
        elif 'molecules' in P['submethod']:
            n_molecules = P['number of molecules']
        elif 'atoms' in P['submethod']:
            n_atoms = P['approximate number of atoms']
        else:
            raise RuntimeError(
                "Don't recognize the submethod {}".format(P['submethod'])
            )

        tmp = self.calculate(
            size=size,
            volume=volume,
            density=density,
            n_molecules=n_molecules,
            n_atoms=n_atoms,
            n_moles=n_moles,
            mass=mass
        )

        size = tmp['size'].to('Å').magnitude
        n_molecules = tmp['n_molecules']

        gap = P['gap'].to('Å').magnitude
        lines = []
        lines.append('tolerance {}'.format(gap))
        lines.append('output packmol.pdb')
        lines.append('filetype pdb')
        lines.append('structure input.pdb')
        lines.append('number {}'.format(n_molecules))
        lines.append('inside cube 0.0 0.0 0.0 {:.4f}'.format(size - gap))
        lines.append('end structure')
        lines.append('')

        files = {'input.pdb': pdbfile.from_molssi(data.structure)}
        files['input.inp'] = '\n'.join(lines)

        logger.log(0, pprint.pformat(files))

        local = seamm.ExecLocal()
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
                ' {} != {}'.format(
                    n_atoms, n_atoms_per_molecule * n_molecules
                )
            )
        # Set the bonds from the molecule
        molecule_bonds = molecule['bonds']
        bonds = data.structure['bonds'] = []
        offset = 0
        for molecule_number in range(1, n_molecules + 1):
            for bond in molecule_bonds:
                i, j, order = bond
                bonds.append((i + offset, j + offset, order))
            offset += n_atoms_per_molecule

        # Duplicate the atom types if they exist
        ff = seamm.data.forcefield
        if ff:
            ff_name = ff.current_forcefield
            if ff_name:
                molecule_atoms = molecule['atoms']
                if (
                    'atom_types' in molecule_atoms and
                    ff_name in molecule_atoms['atom_types']
                ):
                    if 'atom_types' not in atoms:
                        atoms['atom_types'] = {}
                        atoms['atom_types'][ff_name] = (
                            molecule_atoms['atom_types'][ff_name] * n_molecules
                        )

        # make periodic of correct size
        data.structure['periodicity'] = 3
        data.structure['cell'] = [size, size, size, 90.0, 90.0, 90.0]

        string = 'Created a cubic cell {size:.5~P} on a side'
        string += ' with {n_molecules} molecules'
        string += ' for a total of {n_atoms} atoms in the cell'
        string += ' and a density of {density:.5~P}.'
        printer.important(__(string, indent='    ', **tmp))

        logger.log(
            0, 'Structure created by PACKMOL:\n\n' +
            pprint.pformat(data.structure)
        )

        return next_node

    def calculate(
        self,
        size=None,
        volume=None,
        density=None,
        n_molecules=None,
        n_atoms=None,
        n_moles=None,
        mass=None
    ):
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
            raise RuntimeError(
                'Exactly two independent parameters '
                'must be given, not {}'.format(n_parameters)
            )

        if size is not None or volume is not None:
            if size is not None:
                if volume is not None:
                    raise RuntimeError("Size and volume are not independent!")

                volume = size**3
            else:
                size = volume**(1 / 3)

            if density is not None:
                # rho = mass/volume
                mass = density * volume
                n_molecules = int(round(mass / molecular_mass))
                if n_molecules == 0:
                    n_molecules = 1
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
                n_molecules = int(round(n_moles * ureg.N_A))
                if n_molecules == 0:
                    n_molecules = 1
                mass = n_molecules * molecular_mass
                density = mass / volume
                n_atoms = n_molecules * n_atoms_per_molecule
            elif mass is not None:
                density = mass / volume
                n_molecules = int(round(mass / molecular_mass))
                if n_molecules == 0:
                    n_molecules = 1
                n_atoms = n_molecules * n_atoms_per_molecule
                n_moles = n_molecules / ureg.N_A
        elif density is not None:
            if n_molecules is not None:
                mass = n_molecules * molecular_mass
                volume = mass / density
                n_atoms = n_molecules * n_atoms_per_molecule
                n_moles = n_molecules / ureg.N_A
            elif n_atoms is not None:
                n_molecules = int(round(n_atoms / n_atoms_per_molecule))
                if n_molecules == 0:
                    n_molecules = 1
                mass = n_molecules * molecular_mass
                volume = mass / density
                n_atoms = n_molecules * n_atoms_per_molecule
                n_moles = n_molecules / ureg.N_A
            elif n_moles is not None:
                n_molecules = int(round(n_moles * ureg.N_A))
                if n_molecules == 0:
                    n_molecules = 1
                mass = n_molecules * molecular_mass
                volume = mass / density
                n_atoms = n_molecules * n_atoms_per_molecule
            elif mass is not None:
                volume = mass / density
                n_molecules = int(round(mass / molecular_mass))
                if n_molecules == 0:
                    n_molecules = 1
                n_atoms = n_molecules * n_atoms_per_molecule
                n_moles = n_molecules / ureg.N_A
            size = volume**(1 / 3)
        else:
            raise RuntimeError(
                "Number of molecules, number of atoms, "
                "number of moles or the mass are not independenet "
                "quantities!"
            )

        # make the units pretty
        size.ito('Å')
        volume.ito('Å**3')
        density.ito('g/ml')

        logger.debug(" size = {:~P}".format(size))
        logger.debug("             volume = {:~P}".format(volume))
        logger.debug("            density = {:~P}".format(density))
        logger.debug("number of molecules = {}".format(n_molecules))
        logger.debug("    number of atoms = {}".format(n_atoms))

        return {
            'size': size,
            'volume': volume,
            'density': density,
            'n_molecules': n_molecules,
            'n_atoms': n_atoms,
        }
