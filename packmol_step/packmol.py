# -*- coding: utf-8 -*-

"""A step for building fluids with Packmol in a SEAMM flowchart"""

import configparser
import importlib
import logging
import math
from pathlib import Path
import pprint
import shutil
import textwrap

from tabulate import tabulate

from molsystem import SystemDB
import seamm
import seamm_util
from seamm_util import ureg, Q_, units_class  # noqa: F401
import seamm_util.printing as printing
from seamm_util.printing import FormattedText as __
import packmol_step

is_expr = seamm.Node.is_expr

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

        periodic = P["periodic"]
        if isinstance(periodic, str):
            periodic = periodic.lower() == "yes"
        shape = P["shape"]

        if periodic:
            text = f"Will create a {shape} periodic cell"
        else:
            text = f"Will create a {shape} region"
        text += " containing the following molecules:\n\n"

        # Print table of molecules
        table = {
            "Component": [],
            "Structure": [],
            "Ratio": [],
        }
        for molecule in self.parameters["molecules"].value:
            table["Component"].append(molecule["component"])
            table["Structure"].append(molecule["definition"])
            if molecule["component"] == "solute":
                table["Ratio"].append("")
            else:
                table["Ratio"].append(molecule["count"])

        description = self.header + "\n" + str(__(text, indent=self.indent + 4 * " "))
        text_lines = tabulate(
            table, headers="keys", tablefmt="psql", colalign=("center", "left", "right")
        )
        description += textwrap.indent(text_lines, self.indent + 8 * " ")

        # And the rest of the control
        dimensions = P["dimensions"]
        text = f"\n\nThe dimensions of the region will be {dimensions}"
        if dimensions == "given explicitly":
            if shape == "cubic":
                text += f" by the edge length {P['edge length']}."
            elif shape == "rectangular":
                text += f" by the three sides {P['a']} x{P['b']} x{P['c']}."
            elif shape == "spherical":
                text += f" by the diameter {P['diameter']}."
            else:
                raise RuntimeError(f"Do not recognize shape '{shape}'")
        elif dimensions == "calculated from the volume":
            text += f" {P['volume']}."
        elif dimensions == "calculated from the solute dimensions":
            text += (
                ". If the input structure is periodic, its dimensions will be used. "
                "Otherwise for molecules, a the region will be a box with "
                f"extra space of {P['solvent thickness']} around the molecule."
            )
        elif dimensions == "calculated from the density":
            text += f" {P['density']}."
        elif dimensions == "calculated using the Ideal Gas Law":
            text += f" (PV=NRT) with P={P['pressure']} and T={P['temperature']}."
        else:
            raise RuntimeError(f"Do not recognize dimensions '{dimensions}'")

        amount = P["fluid amount"]
        text += " The number of molecules of the fluid will be obtained "
        if amount == "rounding this number of atoms":
            text += (
                f"by rounding {P['approximate number of atoms']} atoms to give "
                "a whole number of molecules with the requested ratios."
            )
        elif amount == "rounding this number of molecules":
            text += (
                f"by rounding {P['approximate number of molecules']} molecules to give "
                "the requested ratios of species."
            )
        elif amount == "using the density":
            text += f" by using the density {P['density']}."
        elif amount == "using the Ideal Gas Law":
            text += (
                f" by using the Ideal Gas Law (PV=NRT) with P={P['pressure']} and "
                f"T={P['temperature']}."
            )
        else:
            raise RuntimeError(f"Do not recognize amount '{amount}'")

        description += str(__(text, indent=self.indent + 4 * " "))
        return description

    def run(self):
        """Run a Packmol building step"""

        next_node = super().run(printer)

        # Get the system database
        system_db = self.get_variable("_system_db")

        # Access the options
        seamm_options = self.global_options

        P = self.parameters.current_values_to_dict(
            context=seamm.flowchart_variables._data
        )
        periodic = P["periodic"]

        # Print what we are doing. Have to fix formatting for printing...
        PP = dict(P)
        for key in PP:
            if isinstance(PP[key], units_class):
                PP[key] = "{:~P}".format(PP[key])
        printer.important(self.description_text(PP))

        ff = None
        if P["assign forcefield"] != "No":
            try:
                ff = self.get_variable("_forcefield")
            except Exception:
                ff = None
            if ff == "OpenKIM":
                ff = None

        # Get the input files and any more output to print
        tmp_db = SystemDB(filename="file:tmp_db?mode=memory&cache=shared")
        molecules, files, output, cell = Packmol.get_input(
            P, system_db, tmp_db, seamm.flowchart_variables, ff=ff
        )

        self.logger.log(0, pprint.pformat(files))

        executor = self.flowchart.executor

        # Read configuration file for Packmol if it exists
        executor_type = executor.name
        full_config = configparser.ConfigParser()
        ini_dir = Path(seamm_options["root"]).expanduser()
        path = ini_dir / "packmol.ini"

        if path.exists():
            full_config.read(ini_dir / "packmol.ini")

        # If the section we need doesn't exists, get the default
        if not path.exists() or executor_type not in full_config:
            resources = importlib.resources.files("packmol_step") / "data"
            ini_text = (resources / "packmol.ini").read_text()
            full_config.read_string(ini_text)

        # Getting desperate! Look for an executable in the path
        if executor_type not in full_config:
            path = shutil.which("packmol")
            if path is None:
                raise RuntimeError(
                    f"No section for '{executor_type}' in Packmol ini file "
                    f"({ini_dir / 'packmol.ini'}), nor in the defaults, nor "
                    "in the path!"
                )
            else:
                full_config[executor_type] = {
                    "installation": "local",
                    "code": str(path),
                }

        # If the ini file does not exist, write it out!
        if not path.exists():
            with path.open("w") as fd:
                full_config.write(fd)
            printer.normal(f"Wrote the Packmol configuration file to {path}")
            printer.normal("")

        config = dict(full_config.items(executor_type))

        # Use the matching version of the seamm-packmol image by default.
        config["version"] = self.version

        result = executor.run(
            cmd=["{code}", "<", "input.inp", ">", "packmol.out"],
            config=config,
            directory=self.directory,
            files=files,
            return_files=["packmol.pdb"],
            in_situ=True,
            shell=True,
        )

        if not result:
            self.logger.error("There was an error running Packmol")
            return None

        self.logger.debug(pprint.pformat(result))

        # Get the bond orders and extra parameters like ff atom types
        bond_orders = []
        extra_data = {}
        total_q = 0.0
        for molecule in molecules:
            n = molecule["number"]
            orders = molecule["configuration"].bonds.get_column_data("bondorder")
            bond_orders.extend(orders * n)

            total_q += n * molecule["configuration"].charge

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
        system, configuration = self.get_system_configuration(P, same_as=None)
        configuration.clear()
        configuration.charge = total_q

        # Create the configuration from the PDB output of Packmol
        configuration.coordinate_system = "Cartesian"
        configuration.from_pdb_text(result["packmol.pdb"]["data"])

        # And set the bond orders and extra data we saved earlier.
        configuration.bonds.get_column("bondorder")[:] = bond_orders
        for key, values in extra_data.items():
            if key not in configuration.atoms:
                if "atom_types_" in key:
                    configuration.atoms.add_attribute(key, coltype="str")
                elif "charges" in key:
                    configuration.atoms.add_attribute(key, coltype="float")
                else:
                    raise RuntimeError(f"Can't handle extra column '{key}'")
            configuration.atoms.get_column(key)[:] = values

        # Finally, make periodic of correct size
        if periodic:
            configuration.periodicity = 3
            a, b, c = cell
            configuration.cell.parameters = (a, b, c, 90.0, 90.0, 90.0)
            # by convention we keep periodic systems in fractional coordinates
            xyz = configuration.atoms.get_coordinates(fractionals=False)
            configuration.coordinate_system = "fractional"
            configuration.atoms.set_coordinates(xyz, fractionals=False)

        printer.important(__(output, indent=4 * " "))
        printer.important("")

        # Since we have succeeded, add the citation.

        self.references.cite(
            raw=self._bibliography["doi:10.1002/jcc.21224"],
            alias="packmol",
            module="packmol_step",
            level=1,
            note="The principle Packmol citation.",
        )

        return next_node

    @staticmethod
    def get_input(P, system_db, tmp_db, context, ff=None):
        """Create the input for Packmol."""

        # Return the translation from points a to b
        def recenter(a, b):
            return b[0] - a[0], b[1] - a[1], b[2] - a[2]

        # Work out integer numbers of molecules, atoms, etc.
        def round_copies(n_copies, molecules):
            total_atoms = 0
            total_molecules = 0
            total_mass = 0.0
            total = 0.0
            total_count = 0.0
            for molecule in molecules:
                count = molecule["count"]
                component = molecule["type"]
                mass = molecule["mass"]
                n_atoms = molecule["n_atoms"]

                if component == "solute":
                    total_atoms += n_atoms
                    total_molecules += 1
                    total_mass += mass
                    molecule["number"] = 1
                else:
                    n = int(round(n_copies * count))
                    if n > 0:
                        total_atoms += n * n_atoms
                        total_molecules += n
                        total_mass += n * mass
                    molecule["number"] = n
                    total_count += molecule["count"]
                    total += n

            # Get the actual mol percent
            for molecule in molecules:
                if molecule["type"] == "solute":
                    molecule["actual %"] = ""
                    molecule["requested %"] = ""
                else:
                    molecule["actual %"] = f"{molecule['number']/total*100:.3f}"
                    molecule["requested %"] = f"{molecule['count']/total_count*100:.3f}"

            return total_atoms, total_molecules, total_mass

        # Start by handling the molecules
        n_solute_molecules = 0
        n_solute_atoms = 0
        solute_mass = 0.0
        n_fluid_molecules = 0
        n_fluid_atoms = 0
        fluid_mass = 0.0

        if ff is not None:
            ffname = ff.current_forcefield
            ff_key = f"atom_types_{ffname}"
            assign_ff_always = P["assign forcefield"] == "Always"

        # May need to create molecules.
        solute_configuration = None
        molecules = []
        for molecule in P["molecules"]:
            component = molecule["component"]
            if is_expr(component):
                component = context.value(component)
            source = molecule["source"]
            if is_expr(source):
                source = context.value(source)
            definition = molecule["definition"]
            if is_expr(definition):
                definition = context.value(definition)
            count = molecule["count"]
            if is_expr(count):
                count = context.value(count)
            count = float(count)

            if source == "SMILES":
                tmp_system = tmp_db.create_system(name=definition)
                tmp_configuration = tmp_system.create_configuration(name="default")
                tmp_configuration.from_smiles(definition, rdkit=True)
                if ff is not None:
                    ff.assign_forcefield(tmp_configuration)
            elif source == "configuration":
                if definition == "" or definition == "current":
                    tmp_system = system_db.system
                    tmp_configuration = tmp_system.configuration
                else:
                    if "/" in definition:
                        sysname, confname = definition.split("/")
                        tmp_system = system_db.get_system(sysname)
                    else:
                        confname = definition
                    tmp_configuration = tmp_system.get_configuration(confname)
                if ff is not None:
                    if ff_key not in tmp_configuration.atoms or assign_ff_always:
                        ff.assign_forcefield(tmp_configuration)

            tmp_mass = tmp_configuration.mass * ureg.g / ureg.mol
            tmp_mass.ito("kg")

            if component == "solute":
                n_solute_molecules += count
                n_solute_atoms += count * tmp_configuration.n_atoms
                solute_mass += count * tmp_mass
                if solute_configuration is None:
                    solute_configuration = tmp_configuration
                else:
                    raise RuntimeError("More than one solute system!")
            else:
                n_fluid_molecules += count
                n_fluid_atoms += count * tmp_configuration.n_atoms
                fluid_mass += count * tmp_mass

            molecules.append(
                {
                    "configuration": tmp_configuration,
                    "count": count,
                    "type": component,
                    "mass": tmp_mass,
                    "n_atoms": tmp_configuration.n_atoms,
                    "definition": definition,
                }
            )

        periodic = P["periodic"]
        shape = P["shape"]
        dimensions = P["dimensions"]
        amount = P["fluid amount"]
        cell = None

        # Get information about the solute for placing it
        if solute_configuration is not None:
            xyzs = solute_configuration.atoms.get_coordinates(fractionals=False)
            if shape == "cubic":
                center, sides = bounding_box(xyzs)
            elif shape == "rectangular":
                center, sides = bounding_box(xyzs)
            elif shape == "spherical":
                center, solute_radius = bounding_sphere(xyzs)

        # Work out the dimensions of the region
        if dimensions == "given explicitly":
            if shape == "cubic":
                a = P["edge length"].to("Å").magnitude
                if periodic:
                    cell = (a, a, a)
                    gap = P["gap"].to("Å").magnitude
                    a -= gap
                    x0 = f"{gap/2:.4f}"
                    region = f"   inside cube {x0} {x0} {x0} {a:.4f}"
                else:
                    region = f"   inside cube 0.0 0.0 0.0 {a:.4f}"
                if solute_configuration is not None:
                    dx, dy, dz = recenter(center, (a / 2, a / 2, a / 2))
                    fixed = f"   fixed {dx:.4f} {dy:.4f} {dz:.4f} 0.0 0.0 0.0"
                volume = a**3
            elif shape == "rectangular":
                a = P["a"].to("Å").magnitude
                b = P["b"].to("Å").magnitude
                c = P["c"].to("Å").magnitude
                if periodic:
                    cell = (a, b, c)
                    gap = P["gap"].to("Å").magnitude
                    a -= gap
                    b -= gap
                    c -= gap
                    x0 = f"{gap/2:.4f}"
                    region = f"   inside box {x0} {x0} {x0} {a:.4f} {b:.4f} {c:.4f}"
                else:
                    region = f"   inside box 0.0 0.0 0.0 {a:.4f} {b:.4f} {c:.4f}"
                if solute_configuration is not None:
                    dx, dy, dz = recenter(center, (a / 2, b / 2, c / 2))
                    fixed = f"   fixed {dx:.4f} {dy:.4f} {dz:.4f} 0.0 0.0 0.0"
                volume = a * b * c
            elif shape == "spherical":
                diameter = P["diameter"].to("Å").magnitude
                region = f"   inside sphere 0.0 0.0 0.0 {diameter/2:.4f}"
                if solute_configuration is not None:
                    dx, dy, dz = center
                    fixed = f"   fixed {-dx:.4f} {-dy:.4f} {-dz:.4f} 0.0 0.0 0.0"
                volume = 4 / 3 * math.pi * (diameter / 2) ** 3
            else:
                raise RuntimeError(f"Do not recognize shape '{shape}'")
        elif dimensions == "calculated from the volume":
            volume = P["volume"].to("Å^3").magnitude
            if shape == "cubic":
                a = volume ** (1 / 3)
                if periodic:
                    cell = (a, a, a)
                    gap = P["gap"].to("Å").magnitude
                    a -= gap
                    x0 = f"{gap/2:.4f}"
                    region = f"   inside cube {x0} {x0} {x0} {a:.4f}"
                else:
                    region = f"   inside cube 0.0 0.0 0.0 {a:.4f}"
                if solute_configuration is not None:
                    dx, dy, dz = recenter(center, (a / 2, a / 2, a / 2))
                    fixed = f"   fixed {dx:.4f} {dy:.4f} {dz:.4f} 0.0 0.0 0.0"
            elif shape == "rectangular":
                a = P["a"].to("Å").magnitude
                b = P["b"].to("Å").magnitude
                c = P["c"].to("Å").magnitude
                volume1 = a * b * c
                factor = (volume / volume1) ** (1 / 3)
                a *= factor
                b *= factor
                c *= factor
                if periodic:
                    cell = (a, b, c)
                    gap = P["gap"].to("Å").magnitude
                    a -= gap
                    b -= gap
                    c -= gap
                    x0 = f"{gap/2:.4f}"
                    region = f"   inside box {x0} {x0} {x0} {a:.4f} {b:.4f} {c:.4f}"
                else:
                    region = f"   inside box 0.0 0.0 0.0 {a:.4f} {b:.4f} {c:.4f}"
                if solute_configuration is not None:
                    dx, dy, dz = recenter(center, (a / 2, b / 2, c / 2))
                    fixed = f"   fixed {dx:.4f} {dy:.4f} {dz:.4f} 0.0 0.0 0.0"
            elif shape == "spherical":
                diameter = 2 * (volume / (4 / 3 * math.pi)) ** (1 / 3)
                region = f"   inside sphere 0.0 0.0 0.0 {diameter/2:.4f}"
                if solute_configuration is not None:
                    dx, dy, dz = center
                    fixed = f"   fixed {-dx:.4f} {-dy:.4f} {-dz:.4f} 0.0 0.0 0.0"
            else:
                raise RuntimeError(f"Do not recognize shape '{shape}'")
        elif dimensions == "calculated from the solute dimensions":
            if shape == "spherical":
                thickness = P["solvent thickness"].to("Å").magnitude
                region = f"   inside sphere 0.0 0.0 0.0 {solute_radius+thickness:.4f}"
                dx, dy, dz = center
                fixed = f"   fixed {-dx:.4f} {-dy:.4f} {-dz:.4f} 0.0 0.0 0.0"
                diameter = 2 * (solute_radius + thickness)
                volume = 4 / 3 * math.pi * (diameter / 2) ** 3
            else:
                thickness = P["solvent thickness"].to("Å").magnitude
                a, b, c = sides
                if shape == "cubic":
                    a = max(a, b, c)
                    if periodic:
                        volume = (a + thickness) ** 3
                        a += thickness
                        cell = (a, a, a)
                        gap = P["gap"].to("Å").magnitude
                        a -= gap
                        x0 = f"{gap/2:.4f}"
                        region = f"   inside cube {x0} {x0} {x0} {a:.4f}"
                    else:
                        a += 2 * thickness
                        volume = a**3
                        region = f"   inside cube 0.0 0.0 0.0 {a:.4f}"
                    # Move the solute molecule to the center of the box
                    dx, dy, dz = recenter(center, (a / 2, a / 2, a / 2))
                    fixed = f"   fixed {dx:.4f} {dy:.4f} {dz:.4f} 0.0 0.0 0.0"
                else:
                    if periodic:
                        a += thickness
                        b += thickness
                        c += thickness
                        cell = (a, b, c)
                        volume = a * b * c
                        gap = P["gap"].to("Å").magnitude
                        a -= gap
                        b -= gap
                        c -= gap
                        x0 = f"{gap/2:.4f}"
                        region = f"   inside box {x0} {x0} {x0} {a:.4f} {b:.4f} {c:.4f}"
                    else:
                        a += 2 * thickness
                        b += 2 * thickness
                        c += 2 * thickness
                        volume = a * b * c
                        region = f"   inside box 0.0 0.0 0.0 {a:.4f} {b:.4f} {c:.4f}"
                    # Move the solute molecule to the center of the box
                    dx, dy, dz = recenter(center, (a / 2, b / 2, c / 2))
                    fixed = f"   fixed {dx:.4f} {dy:.4f} {dz:.4f} 0.0 0.0 0.0"
        elif dimensions == "calculated from the density":
            density = P["density"]
            if amount == "rounding this number of atoms":
                n_atoms = P["approximate number of atoms"]
                n_copies = (n_atoms - n_solute_atoms) / n_fluid_atoms
            elif amount == "rounding this number of molecules":
                n_molecules = P["approximate number of molecules"]
                n_copies = n_molecules / n_fluid_molecules
            else:
                raise RuntimeError(f"Do not recognize fluid amount '{amount}'")
            n_atoms, n_molecules, mass = round_copies(n_copies, molecules)
            volume = mass / density
            volume = volume.to("Å^3").magnitude

            if shape == "cubic":
                a = volume ** (1 / 3)
                if solute_configuration is not None:
                    dx, dy, dz = recenter(center, (a / 2, a / 2, a / 2))
                    fixed = f"   fixed {dx:.4f} {dy:.4f} {dz:.4f} 0.0 0.0 0.0"
                if periodic:
                    cell = (a, a, a)
                    gap = P["gap"].to("Å").magnitude
                    a -= gap
                    x0 = f"{gap/2:.4f}"
                    region = f"   inside cube {x0} {x0} {x0} {a:.4f}"
                else:
                    region = f"   inside cube 0.0 0.0 0.0 {a:.4f}"
            elif shape == "rectangular":
                a = P["a"].to("Å").magnitude
                b = P["b"].to("Å").magnitude
                c = P["c"].to("Å").magnitude
                volume1 = a * b * c
                factor = (volume / volume1) ** (1 / 3)
                a *= factor
                b *= factor
                c *= factor
                if solute_configuration is not None:
                    dx, dy, dz = recenter(center, (a / 2, b / 2, c / 2))
                    fixed = f"   fixed {dx:.4f} {dy:.4f} {dz:.4f} 0.0 0.0 0.0"
                if periodic:
                    cell = (a, b, c)
                    gap = P["gap"].to("Å").magnitude
                    a -= gap
                    b -= gap
                    c -= gap
                    x0 = f"{gap/2:.4f}"
                    region = f"   inside box {x0} {x0} {x0} {a:.4f} {b:.4f} {c:.4f}"
                else:
                    region = f"   inside box 0.0 0.0 0.0 {a:.4f} {b:.4f} {c:.4f}"
            elif shape == "spherical":
                diameter = 2 * (volume / (4 / 3 * math.pi)) ** (1 / 3)
                region = f"   inside sphere 0.0 0.0 0.0 {diameter/2:.4f}"
                if solute_configuration is not None:
                    dx, dy, dz = center
                    fixed = f"   fixed {-dx:.4f} {-dy:.4f} {-dz:.4f} 0.0 0.0 0.0"
            else:
                raise RuntimeError(f"Do not recognize shape '{shape}'")
        elif dimensions == "calculated using the Ideal Gas Law":
            temperature = P["temperature"]
            pressure = P["pressure"]
            if amount == "rounding this number of atoms":
                n_atoms = P["approximate number of atoms"]
                n_copies = (n_atoms - n_solute_atoms) / n_fluid_atoms
            elif amount == "rounding this number of molecules":
                n_molecules = P["approximate number of molecules"]
                n_copies = n_molecules / n_fluid_molecules
            else:
                raise RuntimeError(f"Do not recognize fluid amount '{amount}'")
            n_atoms, n_molecules, mass = round_copies(n_copies, molecules)

            # PV = NRT
            volume = n_molecules * temperature * ureg.k / pressure
            volume = volume.to("Å^3").magnitude
            if shape == "cubic":
                a = volume ** (1 / 3)
                if solute_configuration is not None:
                    dx, dy, dz = recenter(center, (a / 2, a / 2, a / 2))
                    fixed = f"   fixed {dx:.4f} {dy:.4f} {dz:.4f} 0.0 0.0 0.0"
                if periodic:
                    cell = (a, a, a)
                    gap = P["gap"].to("Å").magnitude
                    a -= gap
                    x0 = f"{gap/2:.4f}"
                    region = f"   inside cube {x0} {x0} {x0} {a:.4f}"
                else:
                    region = f"   inside cube 0.0 0.0 0.0 {a:.4f}"
            elif shape == "rectangular":
                a = P["a"].to("Å").magnitude
                b = P["b"].to("Å").magnitude
                c = P["c"].to("Å").magnitude
                volume1 = a * b * c
                factor = (volume / volume1) ** (1 / 3)
                a *= factor
                b *= factor
                c *= factor
                if solute_configuration is not None:
                    dx, dy, dz = recenter(center, (a / 2, b / 2, c / 2))
                    fixed = f"   fixed {dx:.4f} {dy:.4f} {dz:.4f} 0.0 0.0 0.0"
                if periodic:
                    cell = (a, b, c)
                    gap = P["gap"].to("Å").magnitude
                    a -= gap
                    b -= gap
                    c -= gap
                    x0 = f"{gap/2:.4f}"
                    region = f"   inside box {x0} {x0} {x0} {a:.4f} {b:.4f} {c:.4f}"
                else:
                    region = f"   inside box 0.0 0.0 0.0 {a:.4f} {b:.4f} {c:.4f}"
            elif shape == "spherical":
                diameter = 2 * (volume / (4 / 3 * math.pi)) ** (1 / 3)
                region = f"   inside sphere 0.0 0.0 0.0 {diameter/2:.4f}"
                if solute_configuration is not None:
                    dx, dy, dz = center
                    fixed = f"   fixed {-dx:.4f} {-dy:.4f} {-dz:.4f} 0.0 0.0 0.0"
            else:
                raise RuntimeError(f"Do not recognize shape '{shape}'")
        else:
            raise RuntimeError(f"Do not recognize dimensions '{dimensions}'")

        # Now that we have the volume, get the number of molecules
        if amount == "rounding this number of atoms":
            n_atoms = P["approximate number of atoms"]
            n_copies = (n_atoms - n_solute_atoms) / n_fluid_atoms
        elif amount == "rounding this number of molecules":
            n_molecules = P["approximate number of molecules"]
            n_copies = n_molecules / n_fluid_molecules
        elif amount == "using the density":
            density = P["density"]
            mass = Q_(volume, "Å^3") * density
            mass.ito("kg")
            n_copies = (mass - solute_mass) / fluid_mass
        elif amount == "using the Ideal Gas Law":
            # PV = NRT
            n_molecules = pressure * volume / (temperature * ureg.k)
            n_copies = n_molecules / n_fluid_molecules
        else:
            raise RuntimeError(f"Do not recognize fluid amount '{amount}'")
        n_atoms, n_molecules, mass = round_copies(n_copies, molecules)

        # Prepare the input
        lines = []
        lines.append("tolerance 2.0")
        lines.append("output packmol.pdb")
        lines.append("filetype pdb")
        lines.append("connect yes")

        files = {}
        for i, molecule in enumerate(molecules, start=1):
            lines.append(f"structure input_{i}.pdb")
            lines.append(region)
            if molecule["type"] == "solute":
                lines.append("   center")
                lines.append(fixed)
                lines.append("   number 1")
            else:
                lines.append(f"   number {molecule['number']}")
            lines.append("end structure")
            configuration = molecule["configuration"]
            files[f"input_{i}.pdb"] = configuration.to_pdb_text()

        lines.append("")
        files["input.inp"] = "\n".join(lines)

        string = "\n"
        if periodic:
            a, b, c = cell
            if shape == "cubic":
                string += f"Created a periodic cubic cell {a:.2f} Å on a side"
            else:
                string += f"Created a periodic {a:.2f} x {b:.2f} x {c:.2f} Å cell"
        else:
            if shape == "cubic":
                string += f"Created a cubic region {a:.2f} Å on a side"
            elif shape == "rectangular":
                string += f"Created a rectangular {a:.2f} x {b:.2f} x {c:.2f} Å region"
            else:
                string += (
                    f"Created a spherical region with a diameter of {diameter:.2f} Å"
                )
        volume = Q_(volume, "Å^3")
        density = mass / volume
        density.ito("g/ml")

        if n_solute_molecules > 0:
            string += (
                f" with the solute and {n_molecules-n_solute_molecules} solvent "
                "molecules\n\n"
            )
        else:
            string += f" with {n_molecules} fluid molecules\n\n"

        # Reprint table of molecules
        table = {
            "Component": [],
            "Structure": [],
            "Requested %": [],
            "Number": [],
            "Actual %": [],
        }
        for molecule in molecules:
            table["Component"].append(molecule["type"])
            table["Structure"].append(molecule["definition"])
            table["Requested %"].append(molecule["requested %"])
            table["Number"].append(molecule["number"])
            table["Actual %"].append(molecule["actual %"])

        text_lines = tabulate(
            table, headers="keys", tablefmt="psql", colalign=("center", "left", "right")
        )
        string += textwrap.indent(text_lines, 4 * " ")

        string += f"\n\nThere are a total of {n_atoms} atoms in the cell"
        string += f" giving a density of {density:.5~P}."

        return molecules, files, string, cell


def bounding_sphere(points):
    """A fast, approximate method for finding the sphere containing a set of points.

    See https://www.researchgate.net/publication/242453691_An_Efficient_Bounding_Sphere

    This method is approximate. While the sphere is guaranteed to contain all the points
    it is a few percent larger than necessary on average.
    """

    # euclidean metric
    def dist(a, b):
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5

    def cent(a, b):
        return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)

    p0 = points[0]  # any arbitrary point in the point cloud works
    # choose point y furthest away from x
    p1 = max(points, key=lambda p: dist(p, p0))
    # choose point z furthest away from y
    p2 = max(points, key=lambda p: dist(p, p1))

    # initial bounding sphere
    center = cent(p1, p2)
    radius = dist(p1, p2) / 2

    # while there are points lying outside the bounding sphere, update the sphere by
    # growing it to fit
    for p in points:
        distance = dist(p, center)
        if distance > radius:
            delta = (distance - radius) / 2
            radius = (radius + distance) / 2

            cx, cy, cz = center
            x, y, z = p
            cx += (x - cx) / distance * delta
            cy += (y - cy) / distance * delta
            cz += (z - cz) / distance * delta

            center = (cx, cy, cz)

    return (center, radius)


def bounding_box(points):
    minx, miny, minz = points[0]
    maxx, maxy, maxz = points[0]
    for p in points:
        x, y, z = p
        minx = x if x < minx else minx
        miny = y if y < miny else miny
        minz = z if z < minz else minz
        maxx = x if x > maxx else maxx
        maxy = y if y > maxy else maxy
        maxz = z if z > maxz else maxz

    return (
        ((minx + maxx) / 2, (miny + maxy) / 2, (minz + maxz) / 2),
        ((maxx - minx), (maxy - miny), (maxz - minz)),
    )
