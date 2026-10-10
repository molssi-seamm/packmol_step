# -*- coding: utf-8 -*-

"""Smoke test of the Tk dialog: create it and re-lay it out for every choice
that drives the layout. Skipped when no display is available."""

import pytest

from packmol_step import PackmolParameters


@pytest.fixture()
def tk_node():
    import tkinter as tk

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("no display available for Tk")
    root.withdraw()
    import Pmw
    import seamm

    Pmw.initialise(root)
    flowchart = seamm.Flowchart(namespace="org.molssi.seamm", directory=".")
    tk_flowchart = seamm.TkFlowchart(
        master=root, flowchart=flowchart, namespace="org.molssi.seamm.tk"
    )
    node = flowchart.create_node("Packmol")
    flowchart.add_node(node)
    node.parameters["molecules"].value = [
        {"component": "solute", "source": "SMILES", "definition": "c1ccccc1",
         "count": "1"},
        {"component": "fluid", "source": "SMILES", "definition": "O=C1OCCO1",
         "count": "3", "measure": "proportion"},
        {"component": "fluid", "source": "SMILES", "definition": "[Li+]",
         "count": "1.0", "measure": "molarity (mol/L)"},
    ]  # fmt: skip
    plugin = tk_flowchart.plugin_manager.get("Packmol")
    tk_node = plugin.create_tk_node(
        tk_flowchart=tk_flowchart, node=node, canvas=tk_flowchart.canvas, x=100, y=100
    )
    yield tk_node
    root.destroy()


def rows(tk_node):
    return [data["widgets"] for data in tk_node._molecule_data]


def test_dialog_layouts(tk_node):
    tk_node.create_dialog()
    tk_node.reset_dialog()
    for periodic in ("Yes", "No"):
        tk_node["periodic"].set(periodic)
        for dimensions in PackmolParameters.parameters["dimensions"]["enumeration"]:
            tk_node["dimensions"].set(dimensions)
            tk_node.reset_dialog()
            assert tk_node["proportions"].grid_info() != {}
    tk_node["dimensions"].set("calculated from the density")
    tk_node.reset_dialog()

    solute, solvent, salt = rows(tk_node)
    # The solute has no amount; the others do, with the measure as saved
    assert solute["count"].grid_info() == {} and solute["measure"].grid_info() == {}
    assert solvent["measure"].get() == "proportion"
    assert salt["measure"].get() == "molarity (mol/L)"
    assert "molarity (mol/L)" in salt["measure"].cget("values")

    # The Ideal Gas Law gives no volume, so molarities are not offered
    tk_node["dimensions"].set("calculated using the Ideal Gas Law")
    tk_node.reset_dialog()
    assert "molarity (mol/L)" not in salt["measure"].cget("values")
    assert salt["measure"].get() == "proportion"

    # Making a fluid the solute hides its amount
    solvent["component"].set("solute")
    tk_node.reset_molecules()
    assert solvent["count"].grid_info() == {}


def test_measures_saved_and_rows_removed(tk_node):
    tk_node.create_dialog()
    tk_node.reset_dialog()
    tk_node.add_molecule()
    tk_node.add_molecule()
    assert len(tk_node._molecule_data) == 5
    new = tk_node._molecule_data[3]
    new["widgets"]["definition"].insert("end", "COC(=O)OC")
    new["widgets"]["measure"].set("molality (mol/kg)")
    new["widgets"]["measure"].event_generate("<<ComboboxSelected>>")
    new["widgets"]["measure"].update()

    # Remove the salt, then the last row: each button removes its own row
    tk_node._molecule_data[2]["widgets"]["remove"].invoke()
    tk_node._molecule_data[-1]["widgets"]["remove"].invoke()
    definitions = [d["widgets"]["definition"].get() for d in tk_node._molecule_data]
    assert definitions == ["c1ccccc1", "O=C1OCCO1", "COC(=O)OC"]

    tk_node.handle_dialog("OK")
    molecules = tk_node.node.parameters["molecules"].value
    assert [m["measure"] for m in molecules[1:]] == [
        "proportion",
        "molality (mol/kg)",
    ]


def test_measure_survives_other_dimensions(tk_node):
    """Looking at the Ideal Gas Law and back keeps a molarity."""
    tk_node.create_dialog()
    tk_node["dimensions"].set("calculated using the Ideal Gas Law")
    tk_node.reset_dialog()
    salt = rows(tk_node)[2]
    assert salt["measure"].get() == "proportion"
    tk_node["dimensions"].set("calculated from the density")
    tk_node.reset_dialog()
    assert salt["measure"].get() == "molarity (mol/L)"
