import json
import sys

from pathlib import Path

import click

from thermalnetwork import VERSION
from thermalnetwork.enums import ComponentType, DesignType
from thermalnetwork.heat_pump import HeatPump


class Network:
    def __init__(self) -> None:
        self.des_method = None
        self.heat_pumps = []
        self.ghe = []

    def set_design(self, des_method_str: str):
        """
        Sets up the design method.

        :param des_method_str: design method string
        """

        if des_method_str == DesignType.AREAPROPORTIONAL.name:
            self.des_method = DesignType.AREAPROPORTIONAL
        elif des_method_str == DesignType.UPSTREAM.name:
            self.des_method = DesignType.UPSTREAM
        else:
            msg = "Design method not supported."
            print(msg, file=sys.stderr)

    def set_ground_heat_exchanger(self, ghe):
        """
        Creates a new ground heat exchanger instance and adds it to the list of all GHE objects
        """
        pass

    def set_heat_pump(self, hp_data):
        """
        Creates a new heat pump instance and adds it to the list of all HP objects

        :param cop_c: cooling coefficient of performance
        :param cop_h: heating coefficient of performance
        """

        name = str(hp_data['name']).strip().upper()
        cop_c = hp_data['cop_c']
        cop_h = hp_data['cop_h']

        for hp in self.heat_pumps:
            if hp.name == name:
                raise ValueError(f"Duplicate heat pump name \"{hp.name}\" encountered.")

        self.heat_pumps.append(HeatPump(name, cop_c, cop_h))

    def add_ghe_to_network(name: str, index=None):
        """
        Add existing GHE object to network. Optional 'index' argument could be used to set the position of the component.

        :param name: name of existing HP component
        :param index: index of position to insert component
        """
        pass

    def add_hp_to_network(name: str, index=None):
        """
        Add exisiting HP object to network. Optional 'index' argument could be used to set the position of the component.

        :param name: name of existing HP component
        :param index: index of position to insert component
        """
        pass

    def size_area_proportional(self):
        """
        Sizing method for area proportional approach.
        """
        pass

    def size_to_upstream_equipment(self):
        """
        Sizing method for upstream equipment approach.
        """
        pass

    def size_ghe(self):
        """
        Wrapper for GHEDesigner for GHE sizing calls.
        """
        pass

    def size(self):
        """
        High-level sizing call that handles any lower-level calls or iterations.
        """
        pass

    def write_outputs(self, output_path: Path):
        """
        Write all outputs.

        :param output_path: path to write outputs
        """

        # TODO: create output directory if it doesn't exist and we have made it this far.

        pass


def run_sizer_from_cli_worker(input_path: Path, output_path: Path):
    """
    Sizing worker function. Worker is called by tests, and thus not wrapped by `click`

    :param input_path: path to input file
    :param output_path: path to write outputs
    """

    # load input file
    with open(input_path) as f:
        d = json.load(f)

    # load all input data
    version = d["version"]  # type: int
    d_design = d["design"]  # type: dict
    d_network = d["network"]  # type: list
    d_heat_pumps = d["heat_pumps"]  # type: list
    d_ghes = d["ground_heat_exchangers"]  # type: list

    if version != VERSION:
        print("Mismatched versions, could be a problem", file=sys.stderr)

    # instantiate a new Network object
    network = Network()

    # begin populating structures in preparation for sizing

    network.set_design(des_method_str=d_design["method"])

    for ghe in d_ghes:
        network.set_ground_heat_exchanger(ghe)

    for hp in d_heat_pumps:
        network.set_heat_pump(hp)

    for component in d_network:
        comp_name = component["name"]
        comp_type_str = component["type"]
        if comp_type_str == ComponentType.GROUNDHEATEXCHANGER.name:
            network.add_ghe_to_network(comp_name)
        if comp_type_str == ComponentType.HEATPUMP.name:
            network.add_hp_to_network(comp_name)

    network.size()
    network.write_outputs(output_path)


@click.command(name="ThermalNetworkCommandLine")
@click.argument("input-path", type=click.Path(exists=True))
@click.argument("output-path", type=click.Path(exists=True))
@click.version_option(VERSION)
def run_sizer_from_cli(input_path: Path, output_path: Path):
    """
    CLI entrypoint for sizing runner.

    :param input_path: path to input file
    :param output_path: path to write outputs
    """

    input_path = Path(input_path).resolve()

    # will set up JSON schemas to validate inputs here before doing anything

    # calling the worker function here
    output_path = Path(output_path).resolve()
    return run_sizer_from_cli_worker(input_path, output_path)


if __name__ == "__main__":
    run_sizer_from_cli()
