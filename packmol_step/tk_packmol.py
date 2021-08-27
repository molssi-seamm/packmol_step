# -*- coding: utf-8 -*-

"""The graphical part of a Packmol step"""

import logging
import seamm
import seamm_widgets as sw
import packmol_step
import Pmw
import tkinter as tk
import tkinter.ttk as ttk

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
        self.dialog = Pmw.Dialog(
            self.toplevel,
            buttons=("OK", "Help", "Cancel"),
            master=self.toplevel,
            title="Edit Packmol step",
            command=self.handle_dialog,
        )
        self.dialog.withdraw()

        frame = ttk.Frame(self.dialog.interior())
        frame.pack(expand=tk.YES, fill=tk.BOTH)
        self["frame"] = frame

        # Create all the widgets
        P = self.node.parameters
        for key in P:
            if key not in ("molecules",):
                self[key] = P[key].widget(frame)

        self["molecule source"].combobox.config(state="readonly")

        # Frame for specifying molecules
        self["molecules"] = sw.ScrolledFrame(frame, height=500)
        w = self["molecules"].interior()
        self["smiles"] = ttk.Label(w, text="SMILES")
        self["stoichiometry"] = ttk.Label(w, text="stoichiometry")

        # And the molecule data
        for molecule in P["molecules"].value:
            _type = molecule["type"]
            value = molecule["molecule"]
            count = molecule["count"]
            self._molecule_data.append(
                {"type": _type, "molecule": value, "count": count}
            )

        for key in ("molecule source", "method", "submethod"):
            self[key].combobox.bind("<<ComboboxSelected>>", self.reset_dialog)
            self[key].combobox.bind("<Return>", self.reset_dialog)
            self[key].combobox.bind("<FocusOut>", self.reset_dialog)

        self.reset_dialog()

    def reset_dialog(self, widget=None):
        methods = packmol_step.PackmolParameters.methods

        molecule_source = self["molecule source"].get()
        method = self["method"].get()
        submethod = self["submethod"].get()

        logger.debug("reset_dialog: {} {}".format(method, submethod))

        frame = self["frame"]
        frame.grid_rowconfigure(1, weight=0, minsize=0)
        frame.grid_columnconfigure(2, weight=0)
        for slave in frame.grid_slaves():
            slave.grid_forget()

        row = 0
        self["molecule source"].grid(row=row, column=0, columnspan=3, sticky=tk.EW)
        row += 1

        if molecule_source == "SMILES":
            self["molecules"].grid(row=row, column=0, columnspan=3, sticky=tk.NSEW)
            frame.grid_rowconfigure(row, weight=1, minsize=200)
            frame.grid_columnconfigure(2, weight=1)
            row += 1
            self.reset_molecules()

        self["method"].grid(row=row, column=0, sticky=tk.E)
        if method[0] != "$":
            self[method].grid(row=row, column=1, sticky=tk.W)
            self[method].show("combobox", "entry", "units")
        row += 1

        if "pressure" in method:
            key = "ideal gas temperature"
            self[key].grid(row=row, column=0, sticky=tk.W)
            self[key].show("all")
            row += 1
            sw.align_labels([self["method"], self[key]])

        if method[0] == "$":
            self["submethod"].combobox.config(values=[*methods])
            self["submethod"].set(submethod)
            if submethod[0] == "$":
                # Both are variables, so any combination is possible
                self["submethod"].grid(row=row, column=0, sticky=tk.E)
                row += 1
                widgets = []
                for key in (
                    *methods,
                    "ideal gas temperature",
                ):
                    widgets.append(self[key])
                    self[key].grid(row=row, column=1, sticky=tk.EW)
                    self[key].show("all")
                    row += 1
                sw.align_labels(widgets)
            else:
                # Submethod is given, so it controls the choices for the method
                widgets = []
                for key in methods[submethod]:
                    widgets.append(self[key])
                    self[key].grid(row=row, column=1, sticky=tk.EW)
                    self[key].show("all")
                    row += 1

                if "pressure" in methods[submethod]:
                    key = "ideal gas temperature"
                    widgets.append(self[key])
                    self[key].grid(row=row, column=1, sticky=tk.EW)
                    self[key].show("all")
                    row += 1

                sw.align_labels(widgets)
                self["submethod"].grid(row=row, column=0, sticky=tk.E)
                self[submethod].grid(row=row, column=1, sticky=tk.W)
                self[submethod].show("combobox", "entry", "units")
        else:
            if submethod[0] == "$":
                self["submethod"].grid(row=row, column=0, sticky=tk.E)
                row += 1
                widgets = []
                for key in methods[method]:
                    widgets.append(self[key])
                    self[key].grid(row=row, column=1, sticky=tk.EW)
                    self[key].show("all")
                    row += 1

                if "pressure" in methods[submethod]:
                    for key in (
                        "ideal gas pressure",
                        "ideal gas temperature",
                    ):
                        widgets.append(self[key])
                        self[key].grid(row=row, column=0, sticky=tk.EW)
                        self[key].show("all")
                        row += 1

                sw.align_labels(widgets)
            else:
                self["submethod"].combobox.config(values=methods[method])
                if submethod in methods[method]:
                    self["submethod"].set(submethod)
                else:
                    self["submethod"].combobox.current(0)
                    submethod = self["submethod"].get()

                self["submethod"].grid(row=row, column=0, sticky=tk.E)
                self[submethod].grid(row=row, column=1, sticky=tk.W)
                self[submethod].show("combobox", "entry", "units")
                row += 1

                if "pressure" in submethod:
                    key = "ideal gas temperature"
                    self[key].grid(row=row, column=1, sticky=tk.EW)
                    self[key].show("combobox", "entry", "units")
                    row += 1

    def reset_molecules(self):
        """Layout the table of molecules to use."""

        frame = self["molecules"].interior()

        # Unpack any widgets
        for slave in frame.grid_slaves():
            slave.grid_forget()

        # Put in the column headers.
        row = 0
        self["smiles"].grid(row=row, column=1, sticky=tk.EW)
        self["stoichiometry"].grid(row=row, column=2, sticky=tk.EW)
        row += 1

        for data in self._molecule_data:
            molecule = data["molecule"]
            self.logger.debug(molecule)
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

            if "molecule" not in widgets:
                # the molecule (SMILES at the moment)
                widgets["molecule"] = ttk.Entry(frame, width=50, takefocus=True)
                widgets["molecule"].insert("end", molecule)

            if "count" not in widgets:
                # The count for the stoichiometry
                widgets["count"] = ttk.Entry(frame, width=5, takefocus=True)
                widgets["count"].insert("end", data["count"])

            self.logger.debug("  widgets: " + str(widgets))
            widgets["remove"].grid(row=row, column=0, sticky=tk.W)
            widgets["molecule"].grid(row=row, column=1, stick=tk.EW)
            widgets["count"].grid(row=row, column=2, stick=tk.EW)

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

        frame.grid_columnconfigure(1, weight=1)

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
                _type = molecule["type"]
                value = molecule["molecule"]
                count = molecule["count"]
                self._molecule_data.append(
                    {"type": _type, "molecule": value, "count": count}
                )

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
                    "type": data["type"],
                    "molecule": widgets["molecule"].get(),
                    "count": widgets["count"].get(),
                }
            )
        P["molecules"].value = molecules

    def add_molecule(self):
        """Add a new row to the molecule table."""
        self._molecule_data.append({"type": "smiles", "molecule": "", "count": "1"})
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
