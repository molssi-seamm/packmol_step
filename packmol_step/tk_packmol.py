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
    """Graphical interface for using Packmol for fluid boxes
    """

    def __init__(
        self,
        tk_flowchart=None,
        node=None,
        canvas=None,
        x=None,
        y=None,
        w=200,
        h=50
    ):
        '''Initialize a node

        Keyword arguments:
        '''

        self.dialog = None

        super().__init__(
            tk_flowchart=tk_flowchart,
            node=node,
            canvas=canvas,
            x=x,
            y=y,
            w=w,
            h=h
        )

    def create_dialog(self):
        """Create the dialog!"""
        self.dialog = Pmw.Dialog(
            self.toplevel,
            buttons=('OK', 'Help', 'Cancel'),
            master=self.toplevel,
            title='Edit Packmol step',
            command=self.handle_dialog
        )
        self.dialog.withdraw()

        frame = ttk.Frame(self.dialog.interior())
        frame.pack(expand=tk.YES, fill=tk.BOTH)
        self['frame'] = frame

        # Create all the widgets
        P = self.node.parameters
        for key in P:
            self[key] = P[key].widget(frame)

        self['method'].combobox.bind("<<ComboboxSelected>>", self.reset_dialog)
        self['method'].combobox.bind("<Return>", self.reset_dialog)
        self['method'].combobox.bind("<FocusOut>", self.reset_dialog)
        self['submethod'].combobox.bind(
            "<<ComboboxSelected>>", self.reset_dialog
        )
        self['submethod'].combobox.bind("<Return>", self.reset_dialog)
        self['submethod'].combobox.bind("<FocusOut>", self.reset_dialog)

        self.reset_dialog()

    def reset_dialog(self, widget=None):
        methods = packmol_step.PackmolParameters.methods

        method = self['method'].get()
        submethod = self['submethod'].get()

        logger.debug('reset_dialog: {} {}'.format(method, submethod))

        frame = self['frame']
        for slave in frame.grid_slaves():
            slave.grid_forget()

        row = 0
        self['method'].grid(row=row, column=0, sticky=tk.E)
        if method[0] != '$':
            self[method].grid(row=row, column=1, sticky=tk.W)
            self[method].show('combobox', 'entry', 'units')
        row += 1

        if method[0] == '$':
            self['submethod'].combobox.config(values=[*methods])
            self['submethod'].set(submethod)
            if submethod[0] == '$':
                # Both are variables, so any combination is possible
                self['submethod'].grid(row=row, column=0, sticky=tk.E)
                row += 1
                widgets = []
                for key in methods:
                    widgets.append(self[key])
                    self[key].grid(row=row, column=1, sticky=tk.EW)
                    self[key].show('all')
                    row += 1
                sw.align_labels(widgets)
            else:
                # Submethod is given, so it controls the choices for the method
                widgets = []
                for key in methods[submethod]:
                    widgets.append(self[key])
                    self[key].grid(row=row, column=1, sticky=tk.EW)
                    self[key].show('all')
                    row += 1
                sw.align_labels(widgets)
                self['submethod'].grid(row=row, column=0, sticky=tk.E)
                self[submethod].grid(row=row, column=1, sticky=tk.W)
                self[submethod].show('combobox', 'entry', 'units')
        else:
            if submethod[0] == '$':
                self['submethod'].grid(row=row, column=0, sticky=tk.E)
                row += 1
                widgets = []
                for key in methods[method]:
                    widgets.append(self[key])
                    self[key].grid(row=row, column=1, sticky=tk.EW)
                    self[key].show('all')
                    row += 1
                sw.align_labels(widgets)
            else:
                self['submethod'].combobox.config(values=methods[method])
                if submethod in methods[method]:
                    self['submethod'].set(submethod)
                else:
                    self['submethod'].combobox.current(0)
                    submethod = self['submethod'].get()

                self['submethod'].grid(row=row, column=0, sticky=tk.E)
                self[submethod].grid(row=row, column=1, sticky=tk.W)
                self[submethod].show('combobox', 'entry', 'units')
        row += 1

    def right_click(self, event):
        """Probably need to add our dialog...
        """

        super().right_click(event)
        self.popup_menu.add_command(label="Edit..", command=self.edit)

        self.popup_menu.tk_popup(event.x_root, event.y_root, 0)

    def edit(self):
        """Present a dialog for editing the Packmol input
        """
        if self.dialog is None:
            self.create_dialog()

        self.dialog.activate(geometry='centerscreenfirst')

    def handle_dialog(self, result):
        if result is None or result == 'Cancel':
            self.dialog.deactivate(result)
            return

        if result == 'Help':
            # display help!!!
            return

        if result != "OK":
            self.dialog.deactivate(result)
            raise RuntimeError(
                "Don't recognize dialog result '{}'".format(result)
            )

        self.dialog.deactivate(result)

        # Shortcut for parameters
        P = self.node.parameters

        for key in P:
            P[key].set_from_widget()

    def handle_help(self):
        print('Help')
