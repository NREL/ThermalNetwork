import json
from pathlib import Path
from sys import exit, stderr
from typing import Union

import click
from jsonschema import ValidationError

from thermalnetwork import VERSION
from thermalnetwork.energy_transfer_station import ETS
from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType, DesignType
from thermalnetwork.fan import Fan
from thermalnetwork.ground_heat_exchanger import GHE
from thermalnetwork.heat_pump import HeatPump
from thermalnetwork.pump import Pump
from thermalnetwork.validate import validate_input_file



class Network:
    def __init__(self) -> None:
        self.des_method = None
        self.components: list[BaseComponent] = []
        self.network: list[BaseComponent] = []

    def set_design(self, des_method_str: str, throw: bool = True) -> int:
        """
        Sets up the design method.

        :param des_method_str: design method string
        :param throw: by default, function will raise an exception on error, override to false to not raise exception
        :returns: zero if successful, nonzero if failure
        :rtype: int
        """

        des_method_str = des_method_str.strip().upper()

        if des_method_str == DesignType.AREAPROPORTIONAL.name:
            self.des_method = DesignType.AREAPROPORTIONAL
        elif des_method_str == DesignType.UPSTREAM.name:
            self.des_method = DesignType.UPSTREAM
        else:
            if throw:
                msg = "Design method not supported."
                print(msg, file=stderr)
            return 1
        return 0

    def check_for_existing_component(self, name: str, comp_type: ComponentType, throw: bool = True):
        for comp in self.components:
            if comp.name == name and comp.comp_type == comp_type:
                if throw:
                    msg = f"Duplicate {comp_type.name} name \"{name}\" encountered."
                    print(msg, file=stderr)
                return 1
        return 0

    def get_component(self, name: str, comp_type: ComponentType) -> Union[None, BaseComponent]:
        for comp in self.components:
            if comp.name == name and comp.comp_type == comp_type:
                return comp
        return None

    def set_component(self, data: dict, throw: bool = True) -> int:
        comp_type_str = str(data["type"]).strip().upper()

        if comp_type_str == ComponentType.ENERGYTRANSFERSTATION.name:
            return self.set_ets(data, throw)
        elif comp_type_str == ComponentType.FAN.name:
            return self.set_fan(data, throw)
        elif comp_type_str == ComponentType.GROUNDHEATEXCHANGER.name:
            return self.set_ground_heat_exchanger(data, throw)
        elif comp_type_str == ComponentType.HEATPUMP.name:
            return self.set_heat_pump(data, throw)
        elif comp_type_str == ComponentType.PUMP.name:
            return self.set_pump(data, throw)
        else:
            if throw:
                msg = f"Unsupported component type {comp_type_str}."
                print(msg, file=stderr)
            return 1

    def set_ets(self, data: dict, throw: bool = True) -> int:
        """
        Creates a new energy transfer station instance ad adds it to the list of components.

        :param data:
        :param throw:
        :return:
        """
        name = str(data['name']).strip().upper()
        if self.check_for_existing_component(name, ComponentType.ENERGYTRANSFERSTATION, throw) != 0:
            return 1

        props = data["properties"]
        hp_name = props["heat_pump"]
        load_pump_name = props["load_side_pump"]
        source_pump_name = props["source_side_pump"]
        fan_name = props["fan"]
        space_loads = props["space_loads"]

        new_ets = ETS(name, hp_name, load_pump_name, source_pump_name, fan_name, space_loads)
        self.components.append(new_ets)
        return 0

    def set_fan(self, data: dict, throw: bool = True) -> int:
        """
        Creates a new fan instance and adds it to the list of components.

        :param data:
        :param throw:
        :return:
        """
        name = str(data['name']).strip().upper()
        if self.check_for_existing_component(name, ComponentType.FAN, throw) != 0:
            return 1

        props = data["properties"]
        flow = props["design_flow_rate"]
        head = props["design_head"]
        motor_effic = props["motor_efficiency"]
        new_fan = Fan(name, flow, head, motor_effic)
        self.components.append(new_fan)
        return 0

    def set_ground_heat_exchanger(self, data: dict, throw: bool = True):
        """
        Creates a new ground heat exchanger instance and adds it to the list of components.

        :param data: dictionary of ghe data
        :param throw:
        """

        name = str(data['name']).strip().upper()
        if self.check_for_existing_component(name, ComponentType.GROUNDHEATEXCHANGER, throw) != 0:
            return 1

        props = data["properties"]
        length = props['length']
        width = props['width']
        new_ghe = GHE(name, length, width)
        self.components.append(new_ghe)
        return 0

    def set_heat_pump(self, data: dict, throw: bool = True) -> int:
        """
        Creates a new heat pump instance and adds it to the list of components.

        :param data: dictionary of heat pump data
        :param throw:
        """

        name = str(data['name']).strip().upper()
        if self.check_for_existing_component(name, ComponentType.HEATPUMP, throw) != 0:
            return 1

        props = data["properties"]
        cop_c = props['cop_c']
        cop_h = props['cop_h']
        new_hp = HeatPump(name, cop_c, cop_h)
        self.components.append(new_hp)
        return 0

    def set_pump(self, data: dict, throw: bool = True) -> int:
        """
        Creates a new pump instance and adds it to the list of components.

        :param data:
        :param throw:
        :return:
        """
        name = str(data['name']).strip().upper()
        if self.check_for_existing_component(name, ComponentType.PUMP, throw) != 0:
            return 1

        props = data["properties"]
        flow = props["design_flow_rate"]
        head = props["design_head"]
        motor_effic = props["motor_efficiency"]
        ineffic_to_fluid = props["motor_inefficiency_to_fluid_stream"]
        new_pump = Pump(name, flow, head, motor_effic, ineffic_to_fluid)
        self.components.append(new_pump)
        return 0

    def add_component_to_network(self, name: str, comp_type: ComponentType, throw: bool = True) -> int:
        name = name.strip().upper()

        for comp in self.components:
            if comp.name == name and comp.comp_type == comp_type:
                self.network.append(comp)
                return 0

        if throw:
            msg = f"{comp_type.name} \"{name}\" not found."
            print(msg, file=stderr)
        return 1

    def add_ets_to_network(self, name: str, throw: bool = True) -> int:
        return self.add_component_to_network(name, ComponentType.ENERGYTRANSFERSTATION, throw)

    def add_ghe_to_network(self, name: str, throw: bool = True) -> int:
        return self.add_component_to_network(name, ComponentType.GROUNDHEATEXCHANGER, throw)

    def add_hp_to_network(self, name: str, throw: bool = True) -> int:
        return self.add_component_to_network(name, ComponentType.HEATPUMP, throw)

    def add_pump_to_network(self, name: str, throw: bool = True) -> int:
        return self.add_component_to_network(name, ComponentType.PUMP, throw)

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

        # # debugging
        # for i, device in enumerate(self.heat_pumps):
        #     print(f"Index {i}: {device}")
        # for i, device in enumerate(self.ground_heat_exchangers):
        #     print(f"Index {i}: {device}")

        ghe_indexes = []  # This will store the indexes of all GROUNDHEATEXCHANGER devices

        for i, device in enumerate(self.network):
            print(f"Network Index {i}: {device}")
            if device.comp_type == ComponentType.GROUNDHEATEXCHANGER:
                ghe_indexes.append(i)

        print("GROUNDHEATEXCHANGER indices in network:")
        print(ghe_indexes)
        # slice the self.network by ghe_indexes
        for i, ghe_index in enumerate(ghe_indexes):
            if i == 0:  # first GHE
                devices_before_ghe = self.network[:ghe_index]
            else:
                devices_before_ghe = self.network[ghe_indexes[i - 1] + 1:ghe_index]
            print(f"Devices before GHE at index {ghe_index}: {devices_before_ghe}")
            total_space_loads = 0
            for device in devices_before_ghe:
                print(f"device.space_loads: {device.space_loads}")
                device_load = sum(device.space_loads)
                print(f"Total load for device: {device_load}")
                total_space_loads += device_load
            print(f"Total space loads for devices before GHE: {total_space_loads}")
            # call size_ghe() with total load
            self.size_ghe(total_space_loads)

    def size_ghe(self, total_space_loads):
        """
        Wrapper for GHEDesigner for GHE sizing calls.
        """
        print(f"SIZE_GHE with total_space_loads: {total_space_loads}")
        # make call to GHE Sizer for realz

    def size(self, throw: bool = True):
        """
        High-level sizing call that handles any lower-level calls or iterations.
        """
        print("size")
        if self.des_method == DesignType.AREAPROPORTIONAL:
            self.size_area_proportional()
        elif self.des_method == DesignType.UPSTREAM:
            self.size_to_upstream_equipment()
        else:
            if throw:
                msg = f"Unsupported design method {self.des_method}"
                print(msg, file=stderr)
            return 1
        return 0

    def write_outputs(self, output_path: Path):
        """
        Write all outputs.

        :param output_path: path to write outputs
        """

        # TODO: create output directory if it doesn't exist and we have made it this far.

        pass


def run_sizer_from_cli_worker(input_path: Path, output_path: Path) -> int:
    """
    Sizing worker function. Worker is called by tests, and thus not wrapped by `click`.

    :param input_path: path to input file
    :param output_path: path to write outputs
    """

    # load input file
    if not input_path.exists():
        print(f"No input file found at {input_path}, aborting.", file=stderr)
        return 1

    data = json.loads(input_path.read_text())

    if validate_input_file(input_path) != 0:
        return 1

    # load all input data
    version: int = data["version"]
    design_data: dict = data["design"]
    components_data: list[dict] = data["components"]
    network_data: list[dict] = data["network"]

    if version != VERSION:
        print("Mismatched versions, could be a problem", file=stderr)
        return 1

    # instantiate a new Network object
    network = Network()

    # begin populating structures in preparation for sizing
    errors = 0
    errors += network.set_design(des_method_str=design_data["method"], throw=True)

    for comp_data in components_data:
        errors += network.set_component(comp_data)

    for component in network_data:
        comp_name = component["name"]
        comp_type_str = str(component["type"]).strip().upper()
        if comp_type_str == ComponentType.ENERGYTRANSFERSTATION.name:
            errors += network.add_ets_to_network(comp_name)
        elif comp_type_str == ComponentType.GROUNDHEATEXCHANGER.name:
            errors += network.add_ghe_to_network(comp_name)
        elif comp_type_str == ComponentType.HEATPUMP.name:
            errors += network.add_hp_to_network(comp_name)
        elif comp_type_str == ComponentType.PUMP.name:
            errors += network.add_pump_to_network(comp_name)
        else:
            msg = f"Unsupported component type, {comp_type_str}"
            print(msg, file=stderr)
            errors += 1

    if errors != 0:
        return 1

    network.size()
    network.write_outputs(output_path)

    return 0


@click.command(name="ThermalNetworkCommandLine")
@click.argument("input-path", type=click.Path(exists=True))
@click.argument("output-path", type=click.Path(exists=True), required=False)
@click.version_option(VERSION)
@click.option(
    "--validate",
    default=False,
    is_flag=True,
    show_default=False,
    help="Validate input and exit."
)
def run_sizer_from_cli(input_path, output_path, validate):
    """
    CLI entrypoint for sizing runner.

    :param input_path: path to input file
    :param output_path: path to write outputs
    :param validate: flag for input schema validation
    """

    input_path = Path(input_path).resolve()

    if validate:
        try:
            validate_input_file(input_path)
            print("Valid input file.")
            return 0
        except ValidationError:
            print("Schema validation error. See previous error message(s) for details.", file=stderr)
            return 1

    # calling the worker function here
    output_path = Path(output_path).resolve()
    return run_sizer_from_cli_worker(input_path, output_path)


if __name__ == "__main__":
    exit(run_sizer_from_cli())
