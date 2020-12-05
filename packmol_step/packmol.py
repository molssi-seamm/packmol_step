# -*- coding: utf-8 -*-

"""A step for building fluids with Packmol in a SEAMM flowchart"""

import logging
import os.path
import seamm
import seamm_util
from seamm_util import ureg, Q_, units_class  # noqa: F401
import seamm_util.printing as printing
from seamm_util.printing import FormattedText as __
import packmol_step
import pprint

logger = logging.getLogger(__name__)
job = printing.getPrinter()
printer = printing.getPrinter('packmol')


class Packmol(seamm.Node):

    def __init__(self, flowchart=None, extension=None):
        """Setup the main Packmol step

        Keyword arguments:
        """

        logger.debug('Handling arguments in Packmol {}'.format(self))

        super().__init__(
            flowchart=flowchart,
            title='Packmol',
            extension=extension,
            module=__name__,
            logger=logger
        )

        self.parameters = packmol_step.PackmolParameters()

    @property
    def version(self):
        """The semantic version of this module.
        """
        return packmol_step.__version__

    @property
    def git_revision(self):
        """The git version of this module.
        """
        return packmol_step.__git_revision__

    def create_parser(self):
        """Setup the command-line / config file parser
        """
        parser_name = self.step_type
        parser = seamm.getParser()

        # Remember if the parser exists ... this type of step may have been
        # found before
        parser_exists = parser.exists(parser_name)

        # Create the standard options, e.g. log-level
        result = super().create_parser(name=parser_name)

        if parser_exists:
            return result

        # Options for Packmol
        parser.add_argument(
            self.step_type,
            '--packmol-path',
            default='',
            help='the path to the Packmol executables'
        )

        return result

    def description_text(self, P=None):
        """Return a short description of this step.

        Return a nicely formatted string describing what this step will
        do.

        Keyword arguments:
            P: a dictionary of parameter values, which may be variables
                or final values. If None, then the parameters values will
                be used as is.
        """

        if not P:
            P = self.parameters.values_to_dict()

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
            text += ' in a cell {size of cubic cell} on a side'
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

        return self.header + '\n' + __(text, **P, indent=4 * ' ').__str__()

    def run(self):
        """Run a Packmol building step
        """

        next_node = super().run(printer)

        # Get the system
        systems = self.get_variable('_systems')
        system = self.get_variable('_system')

        # The options from command line, config file ...
        path = self.options['packmol_path']

        packmol_exe = os.path.join(path, 'packmol')

        seamm_util.check_executable(packmol_exe)

        P = self.parameters.current_values_to_dict(
            context=seamm.flowchart_variables._data
        )

        self.logger.info('   method = {}'.format(P['method']))
        self.logger.info('submethod = {}'.format(P['submethod']))

        # Print what we are doing
        printer.important(__(self.description_text(P), indent=self.indent))

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
            system,
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

        files = {'input.pdb': system.to_pdb_text()}
        files['input.inp'] = '\n'.join(lines)

        self.logger.log(0, pprint.pformat(files))

        local = seamm.ExecLocal()
        result = local.run(
            cmd=(packmol_exe + ' < input.inp'),
            shell=True,
            files=files,
            return_files=['packmol.pdb']
        )

        self.logger.debug(pprint.pformat(result))

        with open(os.path.join(self.directory, 'packmol.out'), 'w') as fd:
            fd.write(result['stdout'])

        # Ouch! Packmol just gives back atoms and coordinates, so we
        # need to graft to the original structure.

        # Create a new, temporary system and get the coordinates
        tmp_sys = systems.create_system('tmp_sys', temporary=True)
        tmp_sys.from_pdb_text(result['packmol.pdb']['data'])
        n_atoms = tmp_sys.n_atoms()
        xs = [*tmp_sys.atoms['x']]
        ys = [*tmp_sys.atoms['y']]
        zs = [*tmp_sys.atoms['z']]
        del systems['tmp_sys']

        n_atoms_per_molecule = system.n_atoms()
        if n_atoms_per_molecule * n_molecules != n_atoms:
            raise RuntimeError(
                'Serious problem in Packmol with the number of atoms'
                ' {} != {}'.format(
                    n_atoms, n_atoms_per_molecule * n_molecules
                )
            )

        # get the initial atoms so that we can duplicate them
        rows = system.atoms.atoms()
        atom_data = {}
        columns = [x[0] for x in rows.description]
        for column in columns:
            atom_data[column] = []
        for row in rows:
            for column, value in zip(columns, row):
                atom_data[column].append(value)
        atom_ids = atom_data['id']
        del atom_data['id']
        to_index = {j: i for i, j in enumerate(atom_ids)}

        # and bonds
        rows = system.bonds.bonds()
        bond_data = {}
        columns = [x[0] for x in rows.description]
        for column in columns:
            bond_data[column] = []
        for row in rows:
            for column, value in zip(columns, row):
                bond_data[column].append(value)
        i_index = [to_index[i] for i in bond_data['i']]
        j_index = [to_index[j] for j in bond_data['j']]

        # Append the atoms and bonds n_molecules-1 times to give n_molecules
        for copy in range(1, n_molecules):
            new_atoms = system.atoms.append(**atom_data)

            bond_data['i'] = [new_atoms[i] for i in i_index]
            bond_data['j'] = [new_atoms[j] for j in j_index]
            system.bonds.append(**bond_data)

        # And set the coordinates to the correct ones
        system.atoms['x'] = xs
        system.atoms['y'] = ys
        system.atoms['z'] = zs

        # make periodic of correct size
        system.periodicity = 3
        system.cell.set_cell(size, size, size, 90.0, 90.0, 90.0)

        string = 'Created a cubic cell {size:.5~P} on a side'
        string += ' with {n_molecules} molecules'
        string += ' for a total of {n_atoms} atoms in the cell'
        string += ' and a density of {density:.5~P}.'
        printer.important(__(string, indent='    ', **tmp))
        printer.important('')

        # Since we have succeeded, add the citation.

        self.references.cite(
            raw=self._bibliography['doi:10.1002/jcc.21224'],
            alias='packmol',
            module='packmol_step',
            level=1,
            note='The principle PACKMOL citation.'
        )
        self.references.cite(
            raw=self._bibliography['packmol_step'],
            alias='packmol_step',
            module='packmol_step',
            level=1,
            note='The principle citation for the PACKMOL step in SEAMM.'
        )

        return next_node

    def calculate(
        self,
        system,
        size=None,
        volume=None,
        density=None,
        n_molecules=None,
        n_atoms=None,
        n_moles=None,
        mass=None
    ):
        """Work out the other variables given any two independent ones"""

        if system.n_atoms() == 0:
            self.logger.error('Packmol calculate: there is no structure!')
            raise RuntimeError('Packmol calculate: there is no structure!')

        elements = system.atoms.symbols()
        n_atoms_per_molecule = len(elements)
        molecular_mass = system.mass() * ureg.g / ureg.mol  # g/mol
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
                n_atoms = n_molecules * n_atoms_per_molecule
                n_moles = n_molecules / ureg.N_A
                mass = n_molecules * molecular_mass
                volume = mass / density
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

        self.logger.debug(" size = {:~P}".format(size))
        self.logger.debug("             volume = {:~P}".format(volume))
        self.logger.debug("            density = {:~P}".format(density))
        self.logger.debug("number of molecules = {}".format(n_molecules))
        self.logger.debug("    number of atoms = {}".format(n_atoms))

        return {
            'size': size,
            'volume': volume,
            'density': density,
            'n_molecules': n_molecules,
            'n_atoms': n_atoms,
        }
