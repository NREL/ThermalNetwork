import json
import sys
from pathlib import Path

import click

from thermalnetwork import VERSION
from thermalnetwork.enums import ComponentType, DesignType
from thermalnetwork.ground_heat_exchanger import GHE
from thermalnetwork.heat_pump import HeatPump


class Network:
    def __init__(self) -> None:
        self.des_method = None
        self.heat_pumps = []
        self.ground_heat_exchangers = []
        self.network = []

    def set_design(self, des_method_str: str):
        """
        Sets up the design method.

        :param des_method_str: design method string
        """

        des_method_str = des_method_str.strip().upper()

        if des_method_str == DesignType.AREAPROPORTIONAL.name:
            self.des_method = DesignType.AREAPROPORTIONAL
        elif des_method_str == DesignType.UPSTREAM.name:
            self.des_method = DesignType.UPSTREAM
        else:
            msg = "Design method not supported."
            print(msg, file=sys.stderr)

    def set_ground_heat_exchanger(self, ghe_data: dict):
        """
        Creates a new ground heat exchanger instance and adds it to the list of all GHE objects

        :param ghe_data: dictionary of ghe data
        """

        name = str(ghe_data['name']).strip().upper()
        length = ghe_data['length']
        width = ghe_data['width']

        for ghe in self.ground_heat_exchangers:
            if ghe.name == name:
                raise ValueError(f"Duplicate ground heat exchanger name \"{ghe.name}\" encountered.")

        self.ground_heat_exchangers.append(GHE(name, length, width))

    def set_heat_pump(self, hp_data: dict):
        """
        Creates a new heat pump instance and adds it to the list of all HP objects

        :param hp_data: dictionary of heat pump data
        """

        name = str(hp_data['name']).strip().upper()
        cop_c = hp_data['cop_c']
        cop_h = hp_data['cop_h']

        for hp in self.heat_pumps:
            if hp.name == name:
                raise ValueError(f"Duplicate heat pump name \"{hp.name}\" encountered.")

        self.heat_pumps.append(HeatPump(name, cop_c, cop_h))

    def add_ghe_to_network_by_name(self, name: str):
        """
        Add existing GHE object to network.

        :param name: name of existing HP component
        """

        name = name.strip().upper()

        for idx, ghe in enumerate(self.ground_heat_exchangers):
            if ghe.name == name:
                self.network.append(ghe)
                return

        raise ValueError(f"Ground heat exchanger \"{name}\" not found.")

    def add_ghe_to_network(self, name, index=None):
        """

        :param name:
        :param index:
        :return: nothing
        """

        new_ghe = GHE(name, 10, 20)

        if index is None:
            self.network.append(new_ghe)
        else:
            self.network.insert(index, new_ghe)

    def add_hp_to_network_by_name(self, name: str):
        """
        Add existing HP object to network.

        :param name: name of existing HP component
        """

        name = name.strip().upper()

        for idx, hp in enumerate(self.heat_pumps):
            if hp.name == name:
                self.network.append(hp)
                return

        raise ValueError(f"Heat pump \"{name}\" not found.")

    def add_hp_to_network(self, name, cop_c, cop_h, index=None):
        """
        Create new HP instance and add it to the network.

        :param name:
        :param cop_c:
        :param cop_h:
        :param index:
        :return: nothing
        """

        new_hp = HeatPump(name, cop_c, cop_h)

        if index is None:
            self.network.append(new_hp)
        else:
            self.network.insert(index, new_hp)

    def size_area_proportional(self):
        """
        Sizing method for area proportional approach.
        """
        pass

    def size_to_upstream_equipment(self):
        """
        Sizing method for upstream equipment approach.
        """
        print("size_to_upstream")
        # find all heatpumps between each groundheatexchanger
        # size to those buildings

        # debugging
        for i, device in enumerate(self.heat_pumps):
            print(f"Index {i}: {device}")
        for i, device in enumerate(self.ground_heat_exchangers):
            print(f"Index {i}: {device}")

        heatpumps_between_ghe = {}  # A dictionary to store the HEATPUMP devices between each GROUNDHEATEXCHANGER

        # Loop over each device in the network
        ghe_index = -1  # Initialize the index of the current GROUNDHEATEXCHANGER device
        for i, device in enumerate(self.network):
            print(f"Index {i}: {device}")
            if device.comp_type == ComponentType.GROUNDHEATEXCHANGER:
                # Found a GROUNDHEATEXCHANGER device
                if ghe_index >= 0:
                    # There was a previous GROUNDHEATEXCHANGER device, so we can find the HEATPUMP devices in between
                    heatpumps = [j for j in range(ghe_index + 1, i) if
                                 self.network[j].comp_type == ComponentType.HEATPUMP]
                    heatpumps_between_ghe[ghe_index] = heatpumps

                # Update the index of the current GROUNDHEATEXCHANGER device
                ghe_index = i

        # Check if there was a GROUNDHEATEXCHANGER device at the end of the list
        if ghe_index >= 0:
            heatpumps = [j for j in range(ghe_index + 1, len(self.network)) if
                         self.network[j]["type"] == ComponentType.HEATPUMP]
            heatpumps_between_ghe[ghe_index] = heatpumps

        print("HEATPUMP devices between each GROUNDHEATEXCHANGER device:")
        print(heatpumps_between_ghe)

    def size_ghe(self):
        """
        Wrapper for GHEDesigner for GHE sizing calls.
        """
        pass

    def size(self):
        """
        High-level sizing call that handles any lower-level calls or iterations.
        """
        print("size")
        if self.des_method == DesignType.AREAPROPORTIONAL:
            self.size_area_proportional()
        elif self.des_method == DesignType.UPSTREAM:
            self.size_to_upstream_equipment()
        else:
            raise ValueError("something is broken")

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

    for ghe_data in d_ghes:
        network.set_ground_heat_exchanger(ghe_data)

    for hp_data in d_heat_pumps:
        network.set_heat_pump(hp_data)

    for component in d_network:
        comp_name = component["name"]
        comp_type_str = str(component["type"]).strip().upper()
        if comp_type_str == ComponentType.GROUNDHEATEXCHANGER.name:
            network.add_ghe_to_network_by_name(comp_name)
        elif comp_type_str == ComponentType.HEATPUMP.name:
            network.add_hp_to_network_by_name(comp_name)
        else:
            raise ValueError("Unsupported object")

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
