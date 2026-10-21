# -*- coding: utf-8 -*-

"""A step for building fluids with Packmol in a SEAMM flowchart"""

import configparser
import importlib
import logging
import math
import os
from pathlib import Path
import pprint
import shutil
import textwrap

from tabulate import tabulate

from molsystem import SystemDB
import seamm
import seamm_util
from seamm_util import Configuration, ureg, Q_, units_class  # noqa: F401
import seamm_util.printing as printing
from seamm_util.printing import FormattedText as __
import packmol_step

is_expr = seamm.Node.is_expr

logger = logging.getLogger(__name__)
job = printing.getPrinter()
printer = printing.getPrinter("packmol")


def atom_columns(molecules):
    """The atom data to carry into the packed configuration, in its order: the atom
    types and charges of the forcefield, and the formal charges.

    Parameters
    ----------
    molecules : [dict]
        Each molecule's "configuration" and "number" of copies, in order.

    Returns
    -------
    dict
        Column name -> the values for every atom of the packed configuration.
    """
    columns = {}
    for molecule in molecules:
        n = molecule["number"]
        atoms = molecule["configuration"].atoms
        for key in atoms.keys():
            if "atom_types_" in key or "charges" in key or key == "formal_charge":
                columns.setdefault(key, []).extend(atoms.get_column_data(key) * n)
    return columns


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
            "Amount": [],
        }
        units = {"molality (mol/kg)": " mol/kg", "molarity (mol/L)": " M"}
        context = seamm.flowchart_variables
        for molecule in self.parameters["molecules"].value:
            component = molecule["component"]
            if is_expr(component):
                try:
                    component = context.value(component)
                except Exception:
                    pass

            definition = molecule["definition"]
            if is_expr(definition):
                try:
                    definition = context.value(definition)
                except Exception:
                    pass

            count = molecule["count"]
            if is_expr(count):
                try:
                    count = context.value(count)
                except Exception:
                    pass

            measure = molecule.get("measure", "proportion")
            if is_expr(measure):
                try:
                    measure = context.value(measure)
                except Exception:
                    pass

            table["Component"].append(component)
            table["Structure"].append(definition)
            if molecule["component"] == "solute":
                table["Amount"].append("")
            else:
                table["Amount"].append(f"{count}{units.get(measure, '')}")

        description = self.header + "\n" + str(__(text, indent=self.indent + 4 * " "))
        text_lines = tabulate(
            table, headers="keys", tablefmt="psql", colalign=("center", "left", "right")
        )
        description += textwrap.indent(text_lines, self.indent + 8 * " ")

        # And the rest of the control
        dimensions = P["dimensions"]
        text = ""
        if P.get("proportions") == "by mass":
            text += "\n\nThe proportions of the molecules are by mass."
        text += f"\n\nThe dimensions of the region will be {dimensions}"
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
                "Otherwise for molecules, the region will be a box with "
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

    def _forcefield(self):
        """The forcefield to type the molecules with, or None.

        A forcefield model chemistry (``FF@oplsaa``, ``ReaxFF@...``) from a
        Model Chemistry step, built by the step that offers it; otherwise the
        Forcefield step's forcefield. OpenKIM and PyTorch models have no atom
        types.
        """
        if self.variable_exists("_model_chemistry"):
            mc = self.get_variable("_model_chemistry")
            if mc.get("type") in ("FF", "ReaxFF"):
                provider = self.flowchart.plugin_manager.get(mc["step"])
                return provider.forcefield(mc, node=self)
        try:
            ff = self.get_variable("_forcefield")
        except Exception:
            return None
        if ff in ("OpenKIM", "PyTorch"):
            return None
        return ff

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
            ff = self._forcefield()

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

        # If the config file doesn't exist, write the default, which runs Packmol
        # from the seamm-packmol conda environment. Without conda (e.g. a pip or uv
        # installation), leave it to the search of the PATH below.
        if not path.exists() and "CONDA_EXE" in os.environ:
            resources = importlib.resources.files("packmol_step") / "data"
            ini_text = (resources / "packmol.ini").read_text()
            txt_config = Configuration(path)
            txt_config.from_string(ini_text)

            # Work out the conda info needed
            txt_config.set_value("local", "conda", os.environ["CONDA_EXE"])
            txt_config.set_value("local", "conda-environment", "seamm-packmol")
            txt_config.save()

        full_config.read(path)

        # Getting desperate! Look for an executable in the path
        if executor_type not in full_config:
            code = shutil.which("packmol")
            if code is None:
                raise RuntimeError(
                    f"No section for '{executor_type}' in Packmol ini file "
                    f"({path}), nor in the defaults, nor in the path!"
                )
            else:
                # Add the section to the ini file -- not to the executable
                txt_config = Configuration(path)
                txt_config.add_section(executor_type)
                txt_config.set_value(executor_type, "installation", "local")
                txt_config.set_value(executor_type, "code", str(code))
                txt_config.save()
                full_config.read(path)

        config = dict(full_config.items(executor_type))

        result = executor.run(
            cmd=["{code}", "<", "input.inp", ">", "packmol.out"],
            config=config,
            directory=self.directory,
            files=files,
            return_files=["packmol.pdb", "packmol.out"],
            in_situ=True,
            shell=True,
        )

        if not result:
            self.logger.error("There was an error running Packmol")
            return None

        self.logger.debug(pprint.pformat(result))

        # Get the bond orders and extra parameters like ff atom types
        total_q = 0.0
        offset = 0
        i_indices = []
        j_indices = []
        bond_orders = []
        for molecule in molecules:
            n = molecule["number"]
            for _ in range(n):
                for i, j, bond_order in molecule["bonds"]:
                    i_indices.append(i + offset)
                    j_indices.append(j + offset)
                    bond_orders.append(bond_order)
                offset += molecule["configuration"].n_atoms

            total_q += n * molecule["configuration"].charge
        extra_data = atom_columns(molecules)

        # What is in the box, for its name, while the molecules' database is open
        composition = composition_text(molecules)

        # Remove the temporary database
        tmp_db.close()

        # Get the system to fill and make sure it is empty
        system, configuration = self.get_system_configuration(P, same_as=None)
        configuration.clear()
        configuration.charge = int(round(total_q))

        # Create the configuration from the PDB output of Packmol
        configuration.coordinate_system = "Cartesian"
        configuration.from_pdb_text((Path(self.directory) / "packmol.pdb").read_text())

        ids = configuration.atoms.ids
        i_atoms = [ids[x] for x in i_indices]
        j_atoms = [ids[x] for x in j_indices]
        configuration.bonds.append(i=i_atoms, j=j_atoms, bondorder=bond_orders)

        # And set the extra data we saved earlier.
        for key, values in extra_data.items():
            if key not in configuration.atoms:
                if "atom_types_" in key:
                    configuration.atoms.add_attribute(key, coltype="str")
                elif "charges" in key:
                    configuration.atoms.add_attribute(key, coltype="float")
                elif key == "formal_charge":
                    # The ions' formal charges, which analyses of an MD without
                    # fixed charges (an MLFF) need to find the ions
                    configuration.atoms.add_attribute(key, coltype="int", default=0)
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

        # Name the system and configuration: by default after what is in the box,
        # rather than leaving the new system without a name
        if system.name in (None, ""):
            system.name = composition
        if configuration.name in (None, ""):
            configuration.name = "packed"
        seamm.standard_parameters.set_names(
            system, configuration, P, _first=True, composition=composition
        )

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
            """Whole numbers of each molecule for this many copies of the solvent.

            Molecules given as proportions or molalities scale with the copies;
            those given as molarities have their own number, ``molecule["fixed"]``.
            """
            total_atoms = 0
            total_molecules = 0
            total_mass = 0.0
            for molecule in molecules:
                if molecule["type"] == "solute":
                    n = 1
                elif molecule["measure"] == "molarity (mol/L)":
                    n = int(round(molecule["fixed"]))
                else:
                    n = int(round(n_copies * molecule["ratio"]))
                molecule["number"] = n
                if n > 0:
                    total_atoms += n * molecule["n_atoms"]
                    total_molecules += n
                    total_mass += n * molecule["mass"]
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

        # Whether the proportions of the solvent are relative masses
        by_mass = P.get("proportions", "by number of molecules") == "by mass"

        # Need to know if there is a solute
        have_solute = False

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
            measure = molecule.get("measure", "proportion")
            if is_expr(measure):
                measure = context.value(measure)
            if component == "solute":
                measure = "proportion"
            if measure not in packmol_step.PackmolParameters.measures:
                measures = packmol_step.PackmolParameters.measures
                raise RuntimeError(
                    f"The amount of '{definition}' is given as '{measure}', which "
                    f"is not one of {', '.join(measures)}."
                )

            if count == 0:
                continue

            if source == "SMILES":
                tmp_system = tmp_db.create_system(name=definition)
                tmp_configuration = tmp_system.create_configuration(name="default")
                tmp_configuration.from_smiles(definition, flavor="openbabel")
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
                        tmp_system = system_db.system
                        confname = definition
                    tmp_configuration = tmp_system.get_configuration(confname)
                if ff is not None:
                    if ff_key not in tmp_configuration.atoms or assign_ff_always:
                        ff.assign_forcefield(tmp_configuration)
                    else:
                        if any(typ is None for typ in tmp_configuration.atoms[ff_key]):
                            ff.assign_forcefield(tmp_configuration)

            tmp_mass = tmp_configuration.mass * ureg.g / ureg.mol
            tmp_mass.ito("kg")

            # How many of this molecule are in one "copy" of the solvent. The
            # molecules given as proportions are the solvent; a proportion by mass
            # becomes a number by dividing by the molecule's mass.
            ratio = 0.0
            if component == "solute":
                # There is only ever one solute, whatever its proportion
                have_solute = True
                n_solute_molecules += 1
                n_solute_atoms += tmp_configuration.n_atoms
                solute_mass += tmp_mass
                if solute_configuration is None:
                    solute_configuration = tmp_configuration
                else:
                    raise RuntimeError("More than one solute system!")
            elif measure == "proportion":
                if by_mass:
                    ratio = count / tmp_configuration.mass
                else:
                    ratio = count
                n_fluid_molecules += ratio
                n_fluid_atoms += ratio * tmp_configuration.n_atoms
                fluid_mass += ratio * tmp_mass

            # Keep track of the bonding information to add at the end. The input
            # PDB files carry no bonds (see below), and the configurations are
            # left as they are: a "configuration" source is the user's structure.
            bonds = []
            index = {_id: i for i, _id in enumerate(tmp_configuration.atoms.ids)}
            for row in tmp_configuration.bonds.bonds():
                bonds.append((index[row["i"]], index[row["j"]], row["bondorder"]))

            molecules.append(
                {
                    "configuration": tmp_configuration,
                    "count": count,
                    "measure": measure,
                    "ratio": ratio,
                    "type": component,
                    "mass": tmp_mass,
                    "n_atoms": tmp_configuration.n_atoms,
                    "definition": definition,
                    "bonds": bonds,
                }
            )

        # The solvent -- the molecules given as proportions -- sets the scale: the
        # molecules given as molalities are in proportion to its mass, and those
        # given as molarities to the volume of the region.
        fluids = [m for m in molecules if m["type"] == "fluid"]
        if fluids and not any(m["measure"] == "proportion" for m in fluids):
            raise RuntimeError(
                "At least one fluid molecule must be given as a proportion: the "
                "solvent, which sets the scale for the molecules given as "
                "molalities or molarities."
            )
        avogadro = Q_(1, "N_A").to("1/mol").magnitude
        solvent_kg = fluid_mass.m_as("kg") if fluids else 0.0  # per copy
        for molecule in fluids:
            if molecule["measure"] == "molality (mol/kg)":
                ratio = molecule["count"] * avogadro * solvent_kg
                molecule["ratio"] = ratio
                n_fluid_molecules += ratio
                n_fluid_atoms += ratio * molecule["n_atoms"]
                fluid_mass += ratio * molecule["mass"]
        molar = [m for m in fluids if m["measure"] == "molarity (mol/L)"]

        def copies(amount, volume=None):
            """The number of copies of the solvent (with the molecules given as
            molalities) for the amount of fluid, and the numbers of the molecules
            given as molarities.

            With the volume (Å^3) known, the molarities give fixed numbers. Without
            it the volume follows from the density, and depends on the copies: with
            x copies of mass M0 (kg), the solute's mass ms and the molarities c_i of
            molecules of mass m_i, V = (x M0 + ms) / (rho - N_A sum(c_i m_i)), and
            the molecule given as c_i numbers c_i N_A V.
            """
            M0 = fluid_mass.m_as("kg")
            ms = solute_mass.m_as("kg") if have_solute else 0.0
            if volume is not None:
                liters = volume * 1.0e-27
                for m in molar:
                    m["fixed"] = m["count"] * avogadro * liters
            else:
                rho = P["density"].m_as("kg/L")
                dissolved = avogadro * sum(
                    m["count"] * m["mass"].m_as("kg") for m in molar
                )
                if dissolved >= rho:
                    raise RuntimeError(
                        "The molecules given as molarities alone have a density of "
                        f"{dissolved:.3f} g/mL, more than the density requested, "
                        f"{rho:.3f} g/mL."
                    )
                # number of molecule i = gamma_i (x M0 + ms)
                for m in molar:
                    m["gamma"] = m["count"] * avogadro / (rho - dissolved)
            if amount == "rounding this number of atoms":
                target = P["approximate number of atoms"] - n_solute_atoms
                if volume is not None:
                    target -= sum(m["fixed"] * m["n_atoms"] for m in molar)
                    x = target / n_fluid_atoms
                else:
                    per_mass = sum(m["gamma"] * m["n_atoms"] for m in molar)
                    x = (target - per_mass * ms) / (n_fluid_atoms + per_mass * M0)
            elif amount == "rounding this number of molecules":
                target = P["approximate number of molecules"]
                if volume is not None:
                    target -= sum(m["fixed"] for m in molar)
                    x = target / n_fluid_molecules
                else:
                    per_mass = sum(m["gamma"] for m in molar)
                    x = (target - per_mass * ms) / (n_fluid_molecules + per_mass * M0)
            elif amount == "using the density":
                mass = (Q_(volume, "Å^3") * P["density"]).m_as("kg")
                mass -= ms + sum(m["fixed"] * m["mass"].m_as("kg") for m in molar)
                x = mass / M0
            elif amount == "using the Ideal Gas Law":
                n = P["pressure"] * Q_(volume, "Å^3") / (P["temperature"] * ureg.k)
                n = n.m_as("dimensionless") - sum(m["fixed"] for m in molar)
                x = n / n_fluid_molecules
            else:
                raise RuntimeError(f"Do not recognize fluid amount '{amount}'")
            if volume is None:
                for m in molar:
                    m["fixed"] = m["gamma"] * (x * M0 + ms)
            if x <= 0:
                raise RuntimeError(
                    "There is no room for the solvent: the solute and the molecules "
                    "given as molarities already fill the region."
                )
            return x

        periodic = P["periodic"]
        shape = P["shape"]
        dimensions = P["dimensions"]
        amount = P["fluid amount"]
        cell = None
        if molar and dimensions == "calculated using the Ideal Gas Law":
            raise RuntimeError(
                "Molarities need the volume, which the Ideal Gas Law gives only from "
                "the total number of molecules. Give the dimensions another way, or "
                "the amounts as proportions or molalities."
            )

        # Get information about the solute for placing it
        periodic_solute = False
        if solute_configuration is not None:
            xyzs = solute_configuration.atoms.get_coordinates(fractionals=False)
            if solute_configuration.periodicity == 3:
                periodic_solute = True
                periodic = True
                a, b, c, alpha, beta, gamma = solute_configuration.cell.parameters
                if (
                    abs(alpha - 90) > 0.1
                    or abs(beta - 90) > 0.1
                    or abs(gamma - 90) > 0.1
                ):
                    raise RuntimeError("Cannot handle a non-orthorhomic solute")
                if abs(a - b) < 0.01 and abs(a - c) < 0.01:
                    b = c = a
                    shape = "cubic"
                else:
                    shape = "rectangular"
                center = (a / 2, b / 2, c / 2)
                sides = (a, b, c)
                cell = (a, b, c)
                dimensions = "calculated from the solute dimensions"
            else:
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
                    b = c = a
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
                    b = c = a
                    region = f"   inside cube 0.0 0.0 0.0 {a:.4f}"
                else:
                    region = f"   inside cube 0.0 0.0 0.0 {a:.4f}"
                if solute_configuration is not None:
                    dx, dy, dz = recenter(center, (a / 2, a / 2, a / 2))
                    fixed = f"   fixed {dx:.4f} {dy:.4f} {dz:.4f} 0.0 0.0 0.0"
            elif shape == "rectangular":
                # The shape from the ratios the dialog shows; the size from the volume
                a = float(P["a_ratio"])
                b = float(P["b_ratio"])
                c = float(P["c_ratio"])
                volume1 = a * b * c
                factor = (volume / volume1) ** (1 / 3)
                a *= factor
                b *= factor
                c *= factor
                if periodic:
                    cell = (a, b, c)
                    region = f"   inside box 0.0 0.0 0.0 {a:.4f} {b:.4f} {c:.4f}"
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
                        b = c = a
                        cell = (a, a, a)
                        region = f"   inside cube 0.0 0.0 0.0 {a:.4f}"
                    else:
                        a += 2 * thickness
                        b = c = a
                        volume = a**3
                        region = f"   inside cube 0.0 0.0 0.0 {a:.4f}"
                    # Move the solute molecule to the center of the box
                    if periodic_solute:
                        fixed = "   fixed 0.0 0.0 0.0 0.0 0.0 0.0"
                    else:
                        dx, dy, dz = recenter(center, (a / 2, a / 2, a / 2))
                        fixed = f"   fixed {dx:.4f} {dy:.4f} {dz:.4f} 0.0 0.0 0.0"
                else:
                    if periodic:
                        if periodic_solute:
                            fixed = "   fixed 0.0 0.0 0.0 0.0 0.0 0.0"
                            volume = a * b * c
                        else:
                            a += thickness
                            b += thickness
                            c += thickness
                            cell = (a, b, c)
                            volume = a * b * c
                            region = (
                                f"   inside box 0.0 0.0 0.0 {a:.4f} {b:.4f} {c:.4f}"
                            )
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
            n_copies = copies(amount)
            n_atoms, n_molecules, mass = round_copies(n_copies, molecules)
            volume = mass / density
            volume = volume.to("Å^3").magnitude

            if shape == "cubic":
                a = volume ** (1 / 3)
                if solute_configuration is not None:
                    dx = dy = dz = a / 2
                    fixed = f"   fixed {dx:.4f} {dy:.4f} {dz:.4f} 0.0 0.0 0.0"
                if periodic:
                    cell = (a, a, a)
                    b = c = a
                    region = f"   inside cube 0.0 0.0 0.0 {a:.4f}"
                    if have_solute:
                        sx, sy, sz = sides
                        x0 = a / 2 - sx / 2
                        y0 = a / 2 - sy / 2
                        z0 = a / 2 - sz / 2
                        x1 = a / 2 + sx / 2
                        y1 = a / 2 + sy / 2
                        z1 = a / 2 + sz / 2
                        region += (
                            f"\n    outside box {x0:.5f} {y0:.5f} {z0:.5f} "
                            f"{x1:.5f} {y1:.5f} {z1:.5f}"
                        )
                else:
                    region = f"   inside cube 0.0 0.0 0.0 {a:.4f}"
            elif shape == "rectangular":
                # The shape from the ratios the dialog shows; the size from the volume
                a = float(P["a_ratio"])
                b = float(P["b_ratio"])
                c = float(P["c_ratio"])
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
            n_copies = copies(amount)
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
                    b = c = a
                region = f"   inside cube 0.0 0.0 0.0 {a:.4f}"
            elif shape == "rectangular":
                # The shape from the ratios the dialog shows; the size from the volume
                a = float(P["a_ratio"])
                b = float(P["b_ratio"])
                c = float(P["c_ratio"])
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

        # Now that we have the volume, get the number of molecules. From the density
        # or the Ideal Gas Law they came first, and gave the volume.
        if dimensions not in (
            "calculated from the density",
            "calculated using the Ideal Gas Law",
        ):
            n_copies = copies(amount, volume)
            n_atoms, n_molecules, mass = round_copies(n_copies, molecules)

        # Prepare the input. For a periodic cell, Packmol's "pbc" option does not
        # keep the molecules apart across the faces of the cell: with water, dozens
        # of pairs end up closer than 1.8 Å, some at 0.8 Å, so MD fails at once.
        # Instead the molecules are packed in the cell shrunk by half the tolerance
        # on each side, so their periodic images are at least the tolerance apart.
        tolerance = 2.0
        lines = []
        lines.append("seed -1")
        lines.append(f"tolerance {tolerance}")
        lines.append("output packmol.pdb")
        lines.append("filetype pdb")
        lines.append("connect yes")
        if periodic:
            t = tolerance / 2
            a, b, c = cell
            region = (
                f"   inside box {t:.4f} {t:.4f} {t:.4f} {a - t:.4f} {b - t:.4f} "
                f"{c - t:.4f}"
            )

        files = {}
        for i, molecule in enumerate(molecules, start=1):
            lines.append(f"structure input_{i}.pdb")
            if not periodic or molecule["type"] != "solute":
                lines.append(region)
            if molecule["type"] == "solute":
                if not periodic_solute:
                    lines.append("   center")
                lines.append(fixed)
                lines.append("   number 1")
            else:
                lines.append(f"   number {molecule['number']}")
            lines.append("end structure")
            # Without CONECT records: Packmol would copy them to its output, but
            # PDB has no bond orders and the reader takes at most four neighbors,
            # so the bonds are added from the configurations afterwards instead.
            configuration = molecule["configuration"]
            files[f"input_{i}.pdb"] = (
                "\n".join(
                    line
                    for line in configuration.to_pdb_text().splitlines()
                    if not line.startswith("CONECT")
                )
                + "\n"
            )

        lines.append("")
        files["input.inp"] = "\n".join(lines)

        string = "\n"
        if periodic:
            a, b, c = cell
            if shape == "cubic":
                string += f"Created a periodic cubic cell {a:.4f} Å on a side"
            else:
                string += f"Created a periodic {a:.4f} x {b:.4f} x {c:.4f} Å cell"
        else:
            if shape == "cubic":
                string += f"Created a cubic region {a:.4f} Å on a side"
            elif shape == "rectangular":
                string += f"Created a rectangular {a:.4f} x {b:.4f} x {c:.4f} Å region"
            else:
                string += (
                    f"Created a spherical region with a diameter of {diameter:.4f} Å"
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

        # Reprint table of molecules, with the requested and actual amounts: for the
        # solvent its composition (by number or mass), for the other molecules their
        # concentration.
        liters = volume.to("L").magnitude
        avogadro = Q_(1, "N_A").to("1/mol").magnitude
        solvent = [
            m
            for m in molecules
            if m["type"] == "fluid" and m["measure"] == "proportion"
        ]
        unit = "wt%" if by_mass else "%"

        def share(m):
            return m["number"] * m["mass"].m_as("kg") if by_mass else m["number"]

        total_requested = sum(m["count"] for m in solvent)
        total_actual = sum(share(m) for m in solvent)
        solvent_kg = sum(m["number"] * m["mass"].m_as("kg") for m in solvent)

        table = {
            "Component": [],
            "Structure": [],
            "Requested": [],
            "Number": [],
            "Actual": [],
            "Molarity (M)": [],
            "Molality (mol/kg)": [],
        }
        for molecule in molecules:
            measure = molecule["measure"]
            molarity = molecule["number"] / avogadro / liters
            molality = (
                molecule["number"] / avogadro / solvent_kg if solvent_kg > 0 else 0.0
            )
            molecule["molarity"] = molarity
            table["Component"].append(molecule["type"])
            table["Structure"].append(molecule["definition"])
            table["Number"].append(molecule["number"])
            table["Molarity (M)"].append(f"{molarity:.4f}")
            if molecule["type"] == "solute":
                requested = actual = molality = ""
            elif measure == "proportion":
                requested = f"{molecule['count'] / total_requested * 100:.3f} {unit}"
                actual = f"{share(molecule) / total_actual * 100:.3f} {unit}"
                molality = ""
            elif measure == "molality (mol/kg)":
                requested = f"{molecule['count']:.4f} mol/kg"
                actual = f"{molality:.4f} mol/kg"
                molecule["molality"] = molality
                molality = f"{molality:.4f}"
            else:
                requested = f"{molecule['count']:.4f} M"
                actual = f"{molarity:.4f} M"
                molecule["molality"] = molality
                molality = f"{molality:.4f}"
            table["Requested"].append(requested)
            table["Actual"].append(actual)
            table["Molality (mol/kg)"].append(molality)

        # Molality only for the molecules dissolved in the solvent, if there are any
        if not any(table["Molality (mol/kg)"]):
            del table["Molality (mol/kg)"]

        # The amounts are already formatted, so keep them as they are: newer
        # tabulate releases would otherwise reparse and reformat them.
        text_lines = tabulate(
            table,
            headers="keys",
            tablefmt="psql",
            colalign=("center", "left") + ("right",) * (len(table) - 2),
            disable_numparse=True,
        )
        string += textwrap.indent(text_lines, 4 * " ")

        string += f"\n\nThere are a total of {n_atoms} atoms in the cell"
        string += f" giving a density of {density:.5~P}."

        return molecules, files, string, cell


def composition_text(molecules):
    """What is in the box, e.g. "512 H2O, 9 Na+, 9 Cl-".

    Parameters
    ----------
    molecules : [dict]
        The molecules packed, each with its "number" and "configuration".
    """
    parts = []
    for molecule in molecules:
        # The formula includes any charge, e.g. "[Na]+"
        formula = molecule["configuration"].formula[0]
        formula = formula.replace(" ", "").replace("[", "").replace("]", "")
        parts.append(f"{molecule['number']} {formula}")
    return ", ".join(parts)


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
