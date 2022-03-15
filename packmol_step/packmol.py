# -*- coding: utf-8 -*-

"""A step for building fluids with Packmol in a SEAMM flowchart"""

import logging
import os.path
import pprint

from molsystem import SystemDB
import seamm
import seamm_util
from seamm_util import ureg, Q_, units_class  # noqa: F401
import seamm_util.printing as printing
from seamm_util.printing import FormattedText as __
import packmol_step

logger = logging.getLogger(__name__)
job = printing.getPrinter()
printer = printing.getPrinter("packmol")


class Packmol(seamm.Node):
    def __init__(self, flowchart=None, extension=None):
        """Setup the main Packmol step

        Keyword arguments:
        """

        logger.debug("Handling arguments in Packmol {}".format(self))

        super().__init__(
            flowchart=flowchart,
            title="Packmol",
            extension=extension,
            module=__name__,
            logger=logger,
        )

        self.parameters = packmol_step.PackmolParameters()

    @property
    def version(self):
        """The semantic version of this module."""
        return packmol_step.__version__

    @property
    def git_revision(self):
        """The git version of this module."""
        return packmol_step.__git_revision__

    def create_parser(self):
        """Setup the command-line / config file parser"""
        parser_name = self.step_type
        parser = seamm_util.getParser()

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
            "--packmol-path",
            default="",
            help="the path to the Packmol executables",
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

        operation = P["operation"]
        source = P["molecule source"]

        if "solvate" in operation:
            if "box" in operation:
                text = "Solvate the current molecule in a box with\n:"
            else:
                text = "Solvate the current molecule in a droplet with:\n"
        else:
            if source == "SMILES":
                text = "Create a cubic supercell (box) of fluid from these molecules:\n"
            else:
                text = (
                    "Create a cubic supercell (box) of fluid from the current system "
                )

        if "solvate" in operation or source == "SMILES":
            for molecule in self.parameters["molecules"].value:
                SMILES = molecule["molecule"]
                text += f"    {SMILES}\n"
            text += "\nThe will be controlled "

        if P["method"][0] == "$":
            text += "with the method given by {method}"
        elif "cubic" in P["method"]:
            text += "{size of cubic cell} on a side"
        elif "volume" in P["method"]:
            text += "with a volume of {volume}"
        elif "density" in P["method"]:
            text += "with a density of {density}"
        elif "molecules" in P["method"]:
            text += "containing {number of molecules} molecules"
        elif "atoms" in P["method"]:
            text += "containing about {approximate number of atoms} atoms"
        elif "pressure" in P["method"]:
            text += (
                " with P = {ideal gas pressure} and "
                "T = {ideal gas temperature}, assuming an ideal gas"
            )
        else:
            raise RuntimeError("Don't recognize the method {}".format(P["method"]))

        if P["submethod"][0] == "$":
            text += " and a submethod given by {submethod}"
        elif "cubic" in P["submethod"]:
            text += " in a cell {size of cubic cell} on a side"
        elif "volume" in P["submethod"]:
            text += " with a volume of {volume}"
        elif "density" in P["submethod"]:
            text += " with a density of {density}"
        elif "molecules" in P["submethod"]:
            text += " containing {number of molecules} molecules"
        elif "atoms" in P["submethod"]:
            text += " containing about {approximate number of atoms} atoms"
        elif "pressure" in P["submethod"]:
            text += (
                " with P = {ideal gas pressure} and "
                "T = {ideal gas temperature}, assuming an ideal gas"
            )
        else:
            raise RuntimeError(
                "Don't recognize the submethod {}".format(P["submethod"])
            )

        return self.header + "\n" + __(text, **P, indent=4 * " ").__str__()

    def run(self):
        """Run a Packmol building step"""

        next_node = super().run(printer)

        # Get the system
        system_db = self.get_variable("_system_db")

        # The options from command line, config file ...
        path = self.options["packmol_path"]

        packmol_exe = os.path.join(path, "packmol")

        seamm_util.check_executable(packmol_exe)

        P = self.parameters.current_values_to_dict(
            context=seamm.flowchart_variables._data
        )

        self.logger.info("   method = {}".format(P["method"]))
        self.logger.info("submethod = {}".format(P["submethod"]))

        # Print what we are doing. Have to fix formatting for printing...
        PP = dict(P)
        for key in PP:
            if isinstance(PP[key], units_class):
                PP[key] = "{:~P}".format(PP[key])
        printer.important(__(self.description_text(PP), indent=self.indent))

        operation = P["operation"]
        solvation = "solvate" in operation

        size = None
        volume = None
        density = None
        n_molecules = None
        n_atoms = None
        n_moles = None
        mass = None
        pressure = None
        temperature = None

        if "cubic" in P["method"]:
            size = P["size of cubic cell"]
        elif "volume" in P["method"]:
            volume = P["volume"]
        elif "density" in P["method"]:
            density = P["density"]
        elif "molecules" in P["method"]:
            n_molecules = P["number of molecules"]
        elif "atoms" in P["method"]:
            n_atoms = P["approximate number of atoms"]
        elif "pressure" in P["method"]:
            pressure = P["ideal gas pressure"]
            temperature = P["ideal gas temperature"]
        else:
            raise RuntimeError("Don't recognize the method {}".format(P["method"]))

        if "cubic" in P["submethod"]:
            size = P["size of cubic cell"]
        elif "volume" in P["submethod"]:
            volume = P["volume"]
        elif "density" in P["submethod"]:
            density = P["density"]
        elif "molecules" in P["submethod"]:
            n_molecules = P["number of molecules"]
        elif "atoms" in P["submethod"]:
            n_atoms = P["approximate number of atoms"]
        elif "temperature" in P["submethod"]:
            pass
        else:
            raise RuntimeError(
                "Don't recognize the submethod {}".format(P["submethod"])
            )

        source = P["molecule source"]
        molecules = []
        input_n_molecules = 0
        input_n_atoms = 0
        input_mass = 0.0
        n_solute_molecules = 0
        n_solute_atoms = 0
        solute_mass = 0.0
        if source == "current configuration" or solvation:
            configuration = system_db.system.configuration
            if configuration.n_atoms == 0:
                self.logger.error("Packmol calculate: there is no structure!")
                raise RuntimeError("Packmol calculate: there is no structure!")

            tmp_mass = configuration.mass * ureg.g / ureg.mol  # g/mol
            tmp_mass.ito("kg")
            if solvation:
                n_solute_molecules += 1
                n_solute_atoms += configuration.n_atoms
                solute_mass += tmp_mass
            else:
                input_n_molecules += 1
                input_n_atoms += configuration.n_atoms
                input_mass += tmp_mass

            tmp = {
                "configuration": configuration,
                "count": 1,
                "type": "solute",
                "mass": tmp_mass,
            }
            molecules.append(tmp)

        if source == "SMILES" or solvation:
            # Need to create the molecules.
            tmp_db = SystemDB(filename="file:tmp_db?mode=memory&cache=shared")
            for molecule in self.parameters["molecules"].value:
                SMILES = molecule["molecule"]
                tmp_system = tmp_db.create_system(name=SMILES)
                tmp_configuration = tmp_system.create_configuration(name="default")
                tmp_configuration.from_smiles(SMILES)

                count = int(molecule["count"])
                tmp_mass = count * tmp_configuration.mass * ureg.g / ureg.mol
                tmp_mass.ito("kg")

                if solvation:
                    input_n_molecules += count
                    input_n_atoms += count * tmp_configuration.n_atoms
                    input_mass += tmp_mass
                else:
                    n_solute_molecules += count
                    n_solute_atoms += count * tmp_configuration.n_atoms
                    solute_mass += mass

                tmp = {
                    "SMILES": SMILES,
                    "configuration": tmp_configuration,
                    "count": count,
                    "type": "solvent",
                    "mass": tmp_mass,
                }
                molecules.append(tmp)

        tmp = self.calculate(
            input_n_molecules=input_n_molecules,
            input_n_atoms=input_n_atoms,
            input_mass=input_mass,
            size=size,
            volume=volume,
            density=density,
            n_molecules=n_molecules,
            n_atoms=n_atoms,
            n_moles=n_moles,
            mass=mass,
            pressure=pressure,
            temperature=temperature,
            n_solute_molecules=n_solute_molecules,
            n_solute_atoms=n_solute_atoms,
            solute_mass=solute_mass,
        )

        size = tmp["size"].to("Å").magnitude
        n_copies = tmp["n_copies"]
        n_molecules = tmp["n_molecules"]

        gap = P["gap"].to("Å").magnitude

        # Prepare the input
        lines = []
        lines.append("tolerance {}".format(gap))
        lines.append("output packmol.pdb")
        lines.append("filetype pdb")
        lines.append("connect yes")

        files = {}
        for i, molecule in enumerate(molecules, start=1):
            count = molecule["count"]
            lines.append(f"structure input_{i}.pdb")
            lines.append(f"   inside cube 0.0 0.0 0.0 {size-gap:.4f}")
            if molecule["type"] == "solute":
                cxyz = (size - gap) / 2
                lines.append("   center")
                lines.append(f"   fixed {cxyz} {cxyz} {cxyz}  0.0 0.0 0.0")
                lines.append("   number 1")
            else:
                lines.append(f"   number {n_copies * count}")
            lines.append("end structure")
            configuration = molecule["configuration"]
            files[f"input_{i}.pdb"] = configuration.to_pdb_text()

        lines.append("")
        files["input.inp"] = "\n".join(lines)

        self.logger.log(0, pprint.pformat(files))

        # Save the files to disk.
        os.makedirs(self.directory, exist_ok=True)
        for filename in files:
            with open(os.path.join(self.directory, filename), mode="w") as fd:
                fd.write(files[filename])

        local = seamm.ExecLocal()
        result = local.run(
            cmd=(packmol_exe + " < input.inp"),
            shell=True,
            files=files,
            return_files=["packmol.pdb"],
        )

        self.logger.debug(pprint.pformat(result))

        # And write the output files out.
        with open(os.path.join(self.directory, "packmol.out"), "w") as fd:
            fd.write(result["stdout"])

        for filename in result["files"]:
            with open(os.path.join(self.directory, filename), mode="w") as fd:
                if result[filename]["data"] is not None:
                    fd.write(result[filename]["data"])
                else:
                    fd.write(result[filename]["exception"])

        # Get the bond orders and extra parameters like ff atom types
        bond_orders = []
        extra_data = {}
        for molecule in molecules:
            if molecule["type"] == "solute":
                n = 1
            else:
                n = n_copies * molecule["count"]
            orders = molecule["configuration"].bonds.get_column_data("bondorder")
            bond_orders.extend(orders * n)

            atoms = molecule["configuration"].atoms
            for key in atoms.keys():
                if "atom_types_" in key or "charges" in key:
                    if key in extra_data:
                        extra_data[key].extend(atoms.get_column_data(key) * n)
                    else:
                        extra_data[key] = atoms.get_column_data(key) * n

        # Remove the temporary database
        tmp_db.close()

        # Get the system to fill and make sure it is empty
        system, configuration = self.get_system_configuration(P)
        configuration.clear()

        # Create the configuration from the PDB output of PACKMOL
        configuration.from_pdb_text(result["packmol.pdb"]["data"])

        # And set the bond orders and extra data we saved earlier.
        configuration.bonds.get_column("bondorder")[:] = bond_orders
        for key, values in extra_data.items():
            atoms.get_column(key)[:] = values

        # Finally, make periodic of correct size
        configuration.periodicity = 3
        configuration.cell.parameters = (size, size, size, 90.0, 90.0, 90.0)

        string = "Created a cubic cell {size:.5~P} on a side"
        string += " with {n_molecules} molecules"
        string += " for a total of {n_atoms} atoms in the cell"
        string += " and a density of {density:.5~P}."
        printer.important(__(string, indent="    ", **tmp))
        printer.important("")

        # Since we have succeeded, add the citation.

        self.references.cite(
            raw=self._bibliography["doi:10.1002/jcc.21224"],
            alias="packmol",
            module="packmol_step",
            level=1,
            note="The principle PACKMOL citation.",
        )

        return next_node

    def calculate(
        self,
        input_n_molecules=1,
        input_n_atoms=None,
        input_mass=None,
        size=None,
        volume=None,
        density=None,
        n_molecules=None,
        n_atoms=None,
        n_moles=None,
        mass=None,
        pressure=None,
        temperature=None,
        n_solute_molecules=0,
        n_solute_atoms=0,
        solute_mass=0.0,
    ):
        """Work out the other variables given any two independent ones"""

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
        if pressure is not None:
            n_parameters += 1

        if n_parameters != 2:
            raise RuntimeError(
                "Exactly two independent parameters "
                "must be given, not {}".format(n_parameters)
            )

        if size is not None or volume is not None:
            if size is not None:
                if volume is not None:
                    raise RuntimeError("Size and volume are not independent!")

                volume = size**3
            else:
                size = volume ** (1 / 3)

            if density is not None:
                # rho = mass/volume
                mass = density * volume
                n_copies = int(round((mass - solute_mass) / input_mass))
                if n_copies <= 0:
                    n_copies = 1
                n_atoms = n_copies * input_n_atoms + n_solute_atoms
                n_molecules = n_copies * input_n_molecules + n_solute_molecules
                n_moles = n_molecules / ureg.N_A
            elif n_molecules is not None:
                n_copies = int(
                    round((n_molecules - n_solute_molecules) / input_n_molecules)
                )
                if n_copies <= 0:
                    n_copies = 1
                mass = n_molecules * input_mass + solute_mass
                density = mass / volume
                n_atoms = n_copies * input_n_atoms + n_solute_atoms
                n_molecules = n_copies * input_n_molecules + n_solute_molecules
                n_moles = n_molecules / ureg.N_A
            elif n_atoms is not None:
                n_copies = round((n_atoms - n_solute_atoms) / input_n_atoms)
                if n_copies <= 0:
                    n_copies = 1
                mass = n_copies * input_mass + solute_mass
                density = mass / volume
                n_atoms = n_copies * input_n_atoms + n_solute_atoms
                n_molecules = n_copies * input_n_molecules + n_solute_molecules
                n_moles = n_molecules / ureg.N_A
            elif n_moles is not None:
                n_molecules = int(round(n_moles * ureg.N_A))
                n_copies = int((n_molecules - n_solute_molecules) / input_n_molecules)
                if n_copies <= 0:
                    n_copies = 1
                n_molecules = n_copies * input_n_molecules + n_solute_molecules
                mass = n_molecules * input_mass + solute_mass
                density = mass / volume
                n_atoms = n_molecules * input_n_atoms + n_solute_atoms
            elif mass is not None:
                density = mass / volume
                n_copies = int(round((mass - solute_mass) / input_mass))
                if n_copies <= 0:
                    n_copies = 1
                n_atoms = n_copies * input_n_atoms + n_solute_atoms
                n_molecules = n_copies * input_n_molecules + n_solute_molecules
                n_moles = n_molecules / ureg.N_A
            elif pressure is not None:
                # PV = nRT
                n_molecules = pressure * volume / (temperature * ureg.k)
                n_copies = int((n_molecules - n_solute_molecules) / input_n_molecules)
                if n_copies <= 0:
                    n_copies = 1
                n_molecules = n_copies * input_n_molecules + n_solute_molecules
                volume = n_molecules * temperature * ureg.k / pressure
                mass = n_molecules * input_mass + solute_mass
                density = mass / volume
                n_atoms = n_molecules * input_n_atoms + n_solute_atoms
        elif density is not None:
            if n_molecules is not None:
                n_copies = int((n_molecules - n_solute_molecules) / input_n_molecules)
                if n_copies <= 0:
                    n_copies = 1
                mass = n_copies * input_mass + solute_mass
                volume = mass / density
                n_atoms = n_copies * input_n_atoms + n_solute_atoms
                n_molecules = n_copies * input_n_molecules + n_solute_molecules
                n_moles = n_molecules / ureg.N_A
            elif n_atoms is not None:
                n_copies = int(round((n_atoms - n_solute_atoms) / input_n_atoms))
                if n_copies <= 0:
                    n_copies = 1
                n_atoms = n_copies * input_n_atoms + n_solute_atoms
                n_molecules = n_copies * input_n_molecules + n_solute_molecules
                n_moles = n_molecules / ureg.N_A
                mass = n_copies * input_mass + solute_mass
                volume = mass / density
            elif n_moles is not None:
                n_copies = int(
                    round((n_moles * ureg.N_A - n_solute_molecules) / input_n_molecules)
                )
                if n_copies <= 0:
                    n_copies = 1
                n_molecules = n_copies * input_n_molecules + n_solute_molecules
                mass = n_molecules * input_mass + solute_mass
                volume = mass / density
                n_atoms = n_molecules * input_n_atoms + n_solute_atoms
            elif mass is not None:
                volume = mass / density
                n_copies = int(round((mass - solute_mass) / input_mass))
                if n_copies <= 0:
                    n_copies = 1
                n_atoms = n_copies * input_n_atoms + n_solute_atoms
                n_molecules = n_copies * input_n_molecules + n_solute_molecules
                n_moles = n_molecules / ureg.N_A
            size = volume ** (1 / 3)
        elif n_molecules is not None:
            if pressure is None or temperature is None:
                raise RuntimeError(
                    "For ideal gas, the number of molecules or atoms, plus the "
                    "pressure and temperature must be given."
                )
            n_copies = int((n_molecules - n_solute_molecules) / input_n_molecules)
            if n_copies <= 0:
                n_copies = 1
            n_molecules = n_copies * input_n_molecules + n_solute_molecules
            # PV = nRT
            volume = n_molecules * temperature * ureg.k / pressure
            size = volume ** (1 / 3)
            density = (n_copies * input_mass + solute_mass) / volume
            n_atoms = n_copies * input_n_atoms + n_solute_atoms
        elif n_atoms is not None:
            if pressure is None or temperature is None:
                raise RuntimeError(
                    "For ideal gas, the number of molecules or atoms, plus the "
                    "pressure and temperature must be given."
                )
            n_copies = int(round((n_atoms - n_solute_molecules) / input_n_atoms))
            if n_copies <= 0:
                n_copies = 1
            n_molecules = input_n_molecules * n_copies + n_solute_molecules
            # PV = nRT
            volume = n_molecules * temperature * ureg.k / pressure
            size = volume ** (1 / 3)
            density = (n_copies * input_mass + solute_mass) / volume
            n_atoms = n_copies * input_n_atoms + n_solute_atoms
        else:
            raise RuntimeError(
                "The number of moles or the mass are not independent quantities!"
            )
        # make the units pretty
        size.ito("Å")
        volume.ito("Å**3")
        density.ito("g/ml")

        self.logger.debug(" size = {:~P}".format(size))
        self.logger.debug("             volume = {:~P}".format(volume))
        self.logger.debug("            density = {:~P}".format(density))
        self.logger.debug("number of molecules = {}".format(n_molecules))
        self.logger.debug("    number of atoms = {}".format(n_atoms))

        return {
            "size": size,
            "volume": volume,
            "density": density,
            "n_molecules": n_molecules,
            "n_atoms": n_atoms,
            "n_copies": n_copies,
        }
