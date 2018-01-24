# -*- coding: utf-8 -*-
"""The graphical part of a PACKMOL step"""

import molssi_workflow
import molssi_util.molssi_widgets as mw
import packmol_step
import Pmw
import pprint  # nopep8
import tkinter as tk
import tkinter.ttk as ttk

methods = {
    'Size of cubic cell': [
        'Density',
        'Number of molecules',
        'Approximate number of atoms',
        'moles',
        'Mass'
    ],
    'Volume': [
        'Density',
        'Number of molecules',
        'Approximate number of atoms',
        'moles',
        'Mass'
    ],
    'Density': [
        'Size of cubic cell',
        'Volume',
        'Number of molecules',
        'Approximate number of atoms',
        'moles',
        'Mass'
    ],
    'Number of molecules': [
        'Size of cubic cell',
        'Volume',
        'Density',
    ],
    'Approximate number of atoms': [
        'Size of cubic cell',
        'Volume',
        'Density',
    ],
    'moles': [
        'Size of cubic cell',
        'Volume',
        'Density',
    ],
    'Mass': [
        'Size of cubic cell',
        'Volume',
        'Density',
    ]
}


class TkPACKMOL(molssi_workflow.TkNode):
    """The node_class is the class of the 'real' node that this
    class is the Tk graphics partner for
    """

    node_class = packmol_step.PACKMOL

    def __init__(self, node=None, canvas=None, x=None, y=None, w=None, h=None):
        '''Initialize a node

        Keyword arguments:
        '''

        self.dialog = None

        super().__init__(node=node, canvas=canvas, x=x, y=y, w=w, h=h)

    def create_dialog(self):
        """Create the dialog!"""
        self.dialog = Pmw.Dialog(
            self.toplevel,
            buttons=('OK', 'Help', 'Cancel'),
            defaultbutton='OK',
            master=self.toplevel,
            title='Edit PACKMOL step',
            command=self.handle_dialog)
        self.dialog.withdraw()

        self._tmp = {}
        frame = ttk.Frame(self.dialog.interior())
        frame.pack(expand=tk.YES, fill=tk.BOTH)
        self._tmp['frame'] = frame

        # Set the first parameter -- which will be exactly matched
        method = ttk.Combobox(
            frame, state='readonly', values=list(methods),
            justify=tk.RIGHT, width=28
        )
        method.set(self.node.method)
        self._tmp['method'] = method

        submethod = ttk.Combobox(
            frame, state='readonly',
            justify=tk.RIGHT, width=28
        )
        submethod.set(self.node.submethod)
        self._tmp['submethod'] = submethod

        # Size of cubic cell
        cube_size = mw.UnitEntry(frame, width=15)
        cube_size.set(self.node.cube_size)
        self._tmp['cube_size'] = cube_size

        # Number of molecules
        n_molecules = ttk.Entry(frame, width=15)
        n_molecules.insert(0, self.node.n_molecules)
        self._tmp['n_molecules'] = n_molecules

        # Number of atoms
        n_atoms = ttk.Entry(frame, width=15)
        n_atoms.insert(0, self.node.n_atoms)
        self._tmp['n_atoms'] = n_atoms

        # Volume
        volume = mw.UnitEntry(frame, width=15)
        volume.set(self.node.volume)
        self._tmp['volume'] = volume

        # Density
        density = mw.UnitEntry(frame, width=15)
        density.set(self.node.density)
        self._tmp['density'] = density

        # Number of moles
        n_moles = mw.UnitEntry(frame, width=15)
        n_moles.set(self.node.n_moles)
        self._tmp['n_moles'] = n_moles

        # Mass
        mass = mw.UnitEntry(frame, width=15)
        mass.set(self.node.mass)
        self._tmp['mass'] = mass

        method.bind("<<ComboboxSelected>>", self.reset_dialog)
        submethod.bind("<<ComboboxSelected>>", self.reset_dialog)

        self.reset_dialog()

    def reset_dialog(self, widget=None):
        method_widget = self._tmp['method']
        submethod_widget = self._tmp['submethod']

        cube_size_widget = self._tmp['cube_size']
        n_molecules_widget = self._tmp['n_molecules']
        n_atoms_widget = self._tmp['n_atoms']
        volume_widget = self._tmp['volume']
        density_widget = self._tmp['density']
        n_moles_widget = self._tmp['n_moles']
        mass_widget = self._tmp['mass']

        method = method_widget.get()
        submethod = submethod_widget.get()

        frame = self._tmp['frame']
        for slave in frame.grid_slaves():
            slave.grid_forget()

        row = 0
        method_widget.grid(row=row, column=0, sticky=tk.E)
        if 'cubic' in method:
            cube_size_widget.grid(row=row, column=1, sticky=tk.W)
        elif 'Volume' in method:
            volume_widget.grid(row=row, column=1, sticky=tk.W)
        elif 'Density' in method:
            density_widget.grid(row=row, column=1, sticky=tk.W)
        elif 'molecules' in method:
            n_molecules_widget.grid(row=row, column=1, sticky=tk.W)
        elif 'atoms' in method:
            n_atoms_widget.grid(row=row, column=1, sticky=tk.W)
        elif 'moles' in method:
            n_moles_widget.grid(row=row, column=1, sticky=tk.W)
        elif 'Mass' in method:
            mass_widget.grid(row=row, column=1, sticky=tk.W)
        else:
            raise RuntimeError(
                "Don't recognize the method {}".format(method))
        row += 1

        submethod_widget.config(values=methods[method])
        if submethod in methods[method]:
            submethod_widget.set(submethod)
        else:
            submethod_widget.current(0)
            submethod = submethod_widget.get()

        submethod_widget.grid(row=row, column=0, sticky=tk.E)
        if 'cubic' in submethod:
            cube_size_widget.grid(row=row, column=1, sticky=tk.W)
        elif 'Volume' in submethod:
            volume_widget.grid(row=row, column=1, sticky=tk.W)
        elif 'Density' in submethod:
            density_widget.grid(row=row, column=1, sticky=tk.W)
        elif 'molecules' in submethod:
            n_molecules_widget.grid(row=row, column=1, sticky=tk.W)
        elif 'atoms' in submethod:
            n_atoms_widget.grid(row=row, column=1, sticky=tk.W)
        elif 'moles' in submethod:
            n_moles_widget.grid(row=row, column=1, sticky=tk.W)
        elif 'Mass' in submethod:
            mass_widget.grid(row=row, column=1, sticky=tk.W)
        else:
            raise RuntimeError(
                "Don't recognize the sub method {}".format(submethod))
        row += 1

    def right_click(self, event):
        """Probably need to add our dialog...
        """

        super().right_click(event)
        self.popup_menu.add_command(label="Edit..", command=self.edit)

        self.popup_menu.tk_popup(event.x_root, event.y_root, 0)

    def edit(self):
        """Present a dialog for editing the PACKMOL input
        """
        if self.dialog is None:
            self.create_dialog()

        self.dialog.activate(geometry='centerscreenfirst')

    def handle_dialog(self, result):
        if result == 'Cancel':
            self.dialog.deactivate(result)
            return

        if result == 'Help':
            # display help!!!
            return

        if result != "OK":
            self.dialog.deactivate(result)
            raise RuntimeError(
                "Don't recognize dialog result '{}'".format(result))

        self.dialog.deactivate(result)

        method_widget = self._tmp['method']
        submethod_widget = self._tmp['submethod']

        cube_size_widget = self._tmp['cube_size']
        n_molecules_widget = self._tmp['n_molecules']
        n_atoms_widget = self._tmp['n_atoms']
        volume_widget = self._tmp['volume']
        density_widget = self._tmp['density']
        n_moles_widget = self._tmp['n_moles']
        mass_widget = self._tmp['mass']

        method = method_widget.get()
        submethod = submethod_widget.get()

        self.node.method = method
        if 'cubic' in method:
            self.node.cube_size = cube_size_widget.get()
        elif 'Volume' in method:
            self.node.volume = volume_widget.get()
        elif 'Density' in method:
            self.node.density = density_widget.get()
        elif 'molecules' in method:
            self.node.n_molecules = int(n_molecules_widget.get())
        elif 'atoms' in method:
            self.node.n_atoms = int(n_atoms_widget.get())
        elif 'moles' in method:
            self.node.n_moles = n_moles_widget.get()
        elif 'Mass' in method:
            self.node.mass = mass_widget.get()
        else:
            raise RuntimeError(
                "Don't recognize the method {}".format(method))

        self.node.submethod = submethod
        if 'cubic' in submethod:
            self.node.cube_size = cube_size_widget.get()
        elif 'Volume' in submethod:
            self.node.volume = volume_widget.get()
        elif 'Density' in submethod:
            self.node.density = density_widget.get()
        elif 'molecules' in submethod:
            self.node.n_molecules = int(n_molecules_widget.get())
        elif 'atoms' in submethod:
            self.node.n_atoms = int(n_atoms_widget.get())
        elif 'moles' in submethod:
            self.node.n_moles = n_moles_widget.get()
        elif 'Mass' in submethod:
            self.node.mass = mass_widget.get()
        else:
            raise RuntimeError(
                "Don't recognize the sub method {}".format(submethod))

    def handle_help(self):
        print('Help')
