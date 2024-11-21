"""Workgraph to carry out fine-tuning."""

from pathlib import Path
from typing import Callable, Union

from aiida.engine import CalcJob, WorkChain
from aiida_workgraph import WorkGraph, task
from ase.io import read

from aiida_mlip.helpers.help_load import load_structure


@task.graph_builder(outputs=[{"name": "final_structures", "from": "context.structs"}])
def fine_tune_builder(
    calc: Union[CalcJob, Callable, WorkChain, WorkGraph],
    folder: Path,
    calc_inputs: dict,
    input_struct_key: str = "struct",
    final_struct_key: str = "final_structure",
) -> WorkGraph:
    """
    Build high throughput calculation WorkGraph.

    The `calc` must take a structure, by default `struct`, as one of its inputs.
    Tasks will then be created to carry out the calculation for each structure file in
    `folder`.

    Parameters
    ----------
    calc : Union[CalcJob, Callable, WorkChain, WorkGraph]
        Calculation to be performed on all structures.
    folder : Path
        Path to the folder containing input structure files.
    calc_inputs : dict
        Dictionary of inputs, shared by all the calculations. Must not contain
        `struct_key`.
    input_struct_key : str
        Keyword for input structure for `calc`. Default is "struct".
    final_struct_key : str
        Key for final structure output from `calc`. Default is "final_structure".

    Returns
    -------
    WorkGraph
        The workgraph with calculation tasks for each structure.

    Raises
    ------
    FileNotFoundError
        If `folder` has no valid structure files.
    """
    wg = WorkGraph()
    structure = None

    for child in folder.glob("**/*"):
        try:
            read(child.as_posix())
        except Exception:
            continue
        structure = load_structure(child)
        calc_inputs[f"{input_struct_key}"] = structure
        calc_task = wg.add_task(
            calc,
            name=f"calc_{child.stem}",
            **calc_inputs,
        )
        calc_task.set_context({f"{final_struct_key}": f"structs.{child.stem}"})

    if structure is None:
        raise FileNotFoundError(
            "The specified folder is empty or has no readable structure files."
        )

    return wg


def get_fine_tuning_workgraph(
    calc: Union[CalcJob, Callable, WorkChain, WorkGraph],
    folder: Path,
    calc_inputs: dict,
    input_struct_key: str = "struct",
    final_struct_key: str = "final_structure",
    max_number_jobs: int = 10,
) -> WorkGraph:
    """
    Get WorkGraph to carry out calculation on all structures in a directory.

    Parameters
    ----------
    calc : Union[CalcJob, Callable, WorkChain, WorkGraph]
        Calculation to be performed on all structures.
    folder : Path
        Path to the folder containing input structure files.
    calc_inputs : dict
        Dictionary of inputs, shared by all the calculations. Must not contain
        `struct_key`.
    input_struct_key : str
        Keyword for input structure for `calc`. Default is "struct".
    final_struct_key : str
        Key for final structure output from `calc`. Default is "final_structure".
    max_number_jobs : int
        Max number of subprocesses running within the WorkGraph. Default is 10.

    Returns
    -------
    WorkGraph
        The workgraph ready to be submitted.
    """
    wg = WorkGraph("ht_calculation")

    wg.add_task(
        ht_calc_builder,
        name="ht_calc",
        calc=calc,
        folder=folder,
        calc_inputs=calc_inputs,
        input_struct_key=input_struct_key,
        final_struct_key=final_struct_key,
    )

    wg.group_outputs = [
        {"name": "final_structures", "from": "ht_calc.final_structures"}
    ]
    wg.max_number_jobs = max_number_jobs

    return wg
