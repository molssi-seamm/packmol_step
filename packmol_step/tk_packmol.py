# -*- coding: utf-8 -*-

"""The graphical part of a Packmol step"""

import logging
import tkinter as tk
import tkinter.ttk as ttk

from packmol_step import PackmolParameters
import seamm
import seamm_widgets as sw

logger = logging.getLogger(__name__)


class TkPackmol(seamm.TkNode):
    """Graphical interface for using Packmol for fluid boxes"""

    def __init__(
        self, tk_flowchart=None, node=None, canvas=None, x=None, y=None, w=200, h=50
    ):
        """Initialize a node

        Keyword arguments:
        """

        self.dialog = None
        self._molecule_data = []
        self._add_molecule = None

        super().__init__(
            tk_flowchart=tk_flowchart, node=node, canvas=canvas, x=x, y=y, w=w, h=h
        )

    def create_dialog(self):
        """Create the dialog!"""
        frame = super().create_dialog(title="Edit PACKMOL parameters")

        # Create all the widgets
        P = self.node.parameters
        for key in P:
            if key not in ("molecules",):
                self[key] = P[key].widget(frame)

        # Frame for specifying molecules
        self["molecules"] = sw.ScrolledFrame(frame, height=500)
        w = self["molecules"].interior()
        self["component"] = ttk.Label(w, text="Component")
        self["source"] = ttk.Label(w, text="Source")
        self["definition"] = ttk.Label(w, text="Definition")
        self["stoichiometry"] = ttk.Label(w, text="proportion")

        # And the molecule data
        for molecule in P["molecules"].value:
            self._molecule_data.append({**molecule})

        for key in ("periodic", "shape", "dimensions", "fluid amount"):
            self[key].combobox.bind("<<ComboboxSelected>>", self.reset_dialog)
            self[key].combobox.bind("<Return>", self.reset_dialog)
            self[key].combobox.bind("<FocusOut>", self.reset_dialog)

        self.reset_dialog()

        # Resize the dialog to fill the screen, more or less.
        self.fit_dialog()

    def reset_dialog(self, widget=None):
        """Layout the widgets in the dialog contingent on the parameter values."""
        frame = self["frame"]

        # Reset everything
        columns, rows = frame.grid_size()
        for col in range(columns):
            frame.grid_columnconfigure(col, weight=0, minsize=0)
        for row in range(rows):
            frame.grid_rowconfigure(row, weight=0, minsize=0)
        for slave in frame.grid_slaves():
            slave.grid_forget()

        # The possible shapes depend on the periodicity
        periodic = self["periodic"].get()
        shape = self["shape"].get()
        if periodic == "Yes":
            shapes = PackmolParameters.periodic_shapes
        else:
            shapes = PackmolParameters.shapes
        self["shape"].combobox.config(values=shapes)
        if shape not in shapes:
            shape = shapes[0]
        self["shape"].set(shape)

        # The dimensions control the remaining widgets
        dimensions = self["dimensions"].get()

        widgets = []
        row = 0
        for key in ("periodic", "shape", "dimensions"):
            self[key].grid(row=row, column=0, sticky=tk.EW)
            row += 1
            widgets.append(self[key])

        if dimensions == "given explicitly":
            if shape == "cubic":
                keys = ("edge length",)
            elif shape == "rectangular":
                keys = ("a", "b", "c")
            elif shape == "spherical":
                keys = ("diameter",)
            else:
                raise RuntimeError(f"Do not recognize shape '{shape}'")
            for key in keys:
                self[key].grid(row=row, column=0, sticky=tk.EW)
                row += 1
                widgets.append(self[key])
        elif dimensions == "calculated from the volume":
            if shape == "rectangular":
                keys = ("volume", "a_ratio", "b_ratio", "c_ratio")
            else:
                keys = ("volume",)
            for key in keys:
                self[key].grid(row=row, column=0, sticky=tk.EW)
                row += 1
                widgets.append(self[key])
        elif dimensions == "calculated from the solute dimensions":
            keys = ("solvent thickness",)
            for key in keys:
                self[key].grid(row=row, column=0, sticky=tk.EW)
                row += 1
                widgets.append(self[key])
        elif dimensions == "calculated from the density":
            if shape == "rectangular":
                keys = ("density", "a_ratio", "b_ratio", "c_ratio")
            else:
                keys = ("density",)
            for key in keys:
                self[key].grid(row=row, column=0, sticky=tk.EW)
                row += 1
                widgets.append(self[key])
        elif dimensions == "calculated using the Ideal Gas Law":
            if shape == "rectangular":
                keys = ("temperature", "pressure", "a_ratio", "b_ratio", "c_ratio")
            else:
                keys = ("temperature", "pressure")
            for key in keys:
                self[key].grid(row=row, column=0, sticky=tk.EW)
                row += 1
                widgets.append(self[key])
        else:
            raise RuntimeError(f"Do not recognize dimensions '{dimensions}'")

        # Next we need the amount of material. However the options change depending on
        # the above
        amount = self["fluid amount"].get()
        if dimensions in (
            "calculated from the density",
            "calculated using the Ideal Gas Law",
        ):
            amounts = PackmolParameters.amounts_for_density
        elif dimensions in ("calculated from the solute dimensions",):
            amounts = PackmolParameters.amounts_for_layer
        else:
            amounts = PackmolParameters.amounts
        self["fluid amount"].combobox.config(values=amounts)
        if amount not in amounts:
            amount = amounts[0]
        self["fluid amount"].set(amount)

        for key in ("fluid amount",):
            self[key].grid(row=row, column=0, sticky=tk.EW)
            row += 1
            widgets.append(self[key])

        if amount == "rounding this number of atoms":
            for key in ("approximate number of atoms",):
                self[key].grid(row=row, column=0, sticky=tk.EW)
                row += 1
                widgets.append(self[key])
        elif amount == "rounding this number of molecules":
            for key in ("approximate number of molecules",):
                self[key].grid(row=row, column=0, sticky=tk.EW)
                row += 1
                widgets.append(self[key])
        elif amount == "using the density":
            for key in ("density",):
                self[key].grid(row=row, column=0, sticky=tk.EW)
                row += 1
                widgets.append(self[key])
        elif amount == "using the Ideal Gas Law":
            for key in ("temperature", "pressure"):
                self[key].grid(row=row, column=0, sticky=tk.EW)
                row += 1
                widgets.append(self[key])
        else:
            raise RuntimeError(f"Do not recognize amount '{amount}'")

        key = "assign forcefield"
        self[key].grid(row=row, column=0, sticky=tk.EW)
        row += 1
        widgets.append(self[key])

        sw.align_labels(widgets, sticky=tk.E)

        # The table of molecules to use
        self["molecules"].grid(row=row, column=0, columnspan=2, sticky=tk.NSEW)
        frame.grid_rowconfigure(row, weight=1, minsize=100)
        frame.grid_columnconfigure(1, weight=1)
        row += 1
        self.reset_molecules()

        # And finally, where to put the new system
        widgets = []
        for key in ("structure handling", "system name", "configuration name"):
            self[key].grid(row=row, column=0, sticky=tk.EW)
            row += 1
            widgets.append(self[key])

        sw.align_labels(widgets, sticky=tk.E)

    def reset_molecules(self):
        """Layout the table of molecules to use."""

        frame = self["molecules"].interior()

        # Unpack any widgets
        for slave in frame.grid_slaves():
            slave.grid_forget()

        # Put in the column headers.
        row = 0
        self["component"].grid(row=row, column=1, sticky=tk.EW)
        self["source"].grid(row=row, column=2, sticky=tk.EW)
        self["definition"].grid(row=row, column=3, sticky=tk.EW)
        self["stoichiometry"].grid(row=row, column=4, sticky=tk.EW)
        row += 1

        for data in self._molecule_data:
            if "widgets" not in data:
                widgets = data["widgets"] = {}
            else:
                widgets = data["widgets"]

            if "remove" not in widgets:
                # The button to remove a row...
                widgets["remove"] = ttk.Button(
                    frame,
                    text="-",
                    width=2,
                    command=lambda row=row: self.remove_molecule(row),
                    takefocus=True,
                )

            if "component" not in widgets:
                # the type of component
                widgets["component"] = ttk.Combobox(
                    frame,
                    values=("solute", "fluid"),
                    height=4,
                    width=6,
                    state="readonly",
                    takefocus=True,
                )
                widgets["component"].set(data["component"])

            if "source" not in widgets:
                # the type of source
                widgets["source"] = ttk.Combobox(
                    frame,
                    values=("configuration", "SMILES"),
                    height=4,
                    width=10,
                    state="readonly",
                    takefocus=True,
                )
                widgets["source"].set(data["source"])

            if "definition" not in widgets:
                # the SMILES ot system/configuration
                widgets["definition"] = ttk.Entry(frame, width=20, takefocus=True)
                widgets["definition"].insert("end", data["definition"])

            if "count" not in widgets:
                # The count for the stoichiometry
                widgets["count"] = ttk.Entry(frame, width=5, takefocus=True)
                widgets["count"].insert("end", data["count"])

            self.logger.debug("  widgets: " + str(widgets))
            widgets["remove"].grid(row=row, column=0, sticky=tk.W)
            widgets["component"].grid(row=row, column=1, stick=tk.EW)
            widgets["source"].grid(row=row, column=2, stick=tk.EW)
            widgets["definition"].grid(row=row, column=3, stick=tk.EW)
            widgets["count"].grid(row=row, column=4, stick=tk.EW)

            row += 1

        # The button to add a row...
        if self._add_molecule is None:
            self._add_molecule = ttk.Button(
                frame,
                text="+",
                width=5,
                command=self.add_molecule,
                takefocus=True,
            )
            self._add_molecule.focus_set()
        self._add_molecule.lift()
        self._add_molecule.grid(row=row, column=0, columnspan=3, sticky=tk.W)

        frame.grid_columnconfigure(3, weight=1)

    def right_click(self, event):
        """Probably need to add our dialog..."""

        super().right_click(event)
        self.popup_menu.add_command(label="Edit..", command=self.edit)

        self.popup_menu.tk_popup(event.x_root, event.y_root, 0)

    def handle_dialog(self, result):
        if result is None or result == "Cancel":
            self.dialog.deactivate(result)
            # Reset the molecules
            for data in self._molecule_data:
                if "widgets" in data:
                    widgets = data["widgets"]
                    for w in widgets.values():
                        w.destroy()
            self._molecule_data = []
            P = self.node.parameters
            for molecule in P["molecules"].value:
                self._molecule_data.append({**molecule})

            super().handle_dialog(result)

            return

        if result == "Help":
            # display help!!!
            return

        if result != "OK":
            self.dialog.deactivate(result)
            raise RuntimeError("Don't recognize dialog result '{}'".format(result))

        self.dialog.deactivate(result)

        # Shortcut for parameters
        P = self.node.parameters

        for key in P:
            if key not in ("molecules",):
                P[key].set_from_widget()

        # And handle the molecules
        molecules = []
        for data in self._molecule_data:
            widgets = data["widgets"]
            molecules.append(
                {
                    "component": widgets["component"].get(),
                    "source": widgets["source"].get(),
                    "definition": widgets["definition"].get(),
                    "count": widgets["count"].get(),
                }
            )
        P["molecules"].value = molecules

    def add_molecule(self):
        """Add a new row to the molecule table."""
        self._molecule_data.append(
            {
                "component": "fluid",
                "source": "SMILES",
                "definition": "",
                "count": "1",
            }
        )
        self.reset_molecules()

    def remove_molecule(self, row):
        """Remove a molecule entry from the table.

        Parameters
        ----------
        row : int
            The row in the table to remove. Note the first molecule is at row 1.
        """
        index = row - 1
        data = self._molecule_data[index]
        if "widgets" in data:
            for w in data["widgets"].values():
                w.destroy()
        del self._molecule_data[index]

        self.reset_molecules()
