import json
from pathlib import Path
from sys import exit, stderr

import click
from jsonschema import ValidationError

from thermalnetwork import VERSION
from thermalnetwork.base_component import BaseComponent
from thermalnetwork.energy_transfer_station import ETS
from thermalnetwork.enums import ComponentType, DesignType
from thermalnetwork.ground_heat_exchanger import GHE
from thermalnetwork.pump import Pump
from thermalnetwork.validate import validate_input_file


class Network:
    def __init__(self) -> None:
        self.des_method = None
        self.components_data: list[dict] = []
        self.network: list[BaseComponent] = []

    def find_startloop_feature_id(features):
        """
        Finds the feature ID of a feature with the 'startLoop' property set to 'true' in a list of features.

        :param features: List of features to search for the start loop feature.
        :return: The feature ID of the start loop feature, or None if not found.
        """
        for feature in features:
            if feature['properties'].get('start_loop') == 'true':
                start_feature_id = feature['properties'].get('buildingId') or feature['properties'].get('DSId')
                return start_feature_id
        return None

    def get_connected_features(geojson_data):
        """
        Retrieves a list of connected features from a GeoJSON data object.

        :param geojson_data: GeoJSON data object containing features.
        :return: List of connected features with additional information.
        """
        features = geojson_data['features']
        connectors = [feature for feature in features if feature['properties']['type'] == 'ThermalConnector']
        connected_features = []

        #get the id of the building or ds from the thermaljunction that has start_loop: true
        startloop_feature_id = find_startloop_feature_id(features)
        
        # Start with the first connector
        start_feature_id = connectors[0]['properties']['startFeatureId']
        connected_features.append(start_feature_id)

        while True:
            next_feature_id = None
            for connector in connectors:
                if connector['properties']['startFeatureId'] == connected_features[-1]:
                    next_feature_id = connector['properties']['endFeatureId']
                    break

            if next_feature_id:
                connected_features.append(next_feature_id)
                if next_feature_id == start_feature_id:
                    break
            else:
                break

        # Filter and return the building and district system features
        connected_objects = []
        for feature in features:
            feature_id = feature['properties']['id']
            if feature_id in connected_features and feature['properties']['type'] in ['Building', 'District System']:
                connected_objects.append({
                    'id': feature_id,
                    'type': feature['properties']['type'],
                    'name': feature['properties'].get('name', ''),
                    'start_loop': 'true' if feature_id == startloop_feature_id else None
                })

        return connected_objects

    def reorder_connected_features(features):
        """
        Reorders a list of connected features so that the feature with 'startloop' set to 'true' is at the beginning.

        :param features: List of connected features.
        :return: Reordered list of connected features.
        """
        while features[0].get('start_loop') != 'true':
            features.append(features.pop(0))
        return features    

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

    def check_for_existing_component(self, name: str, comp_type_str: str, throw: bool = True):
        for comp in self.components_data:
            if comp['name'] == name and comp['type'] == comp_type_str:
                if throw:
                    msg = f"Duplicate {comp_type_str} name \"{name}\" encountered."
                    print(msg, file=stderr)
                return 1
        return 0

    def set_components(self, comp_data_list: list[dict], throw: bool = True):
        for comp in comp_data_list:
            if self.check_for_existing_component(comp['name'], comp['type'], throw) != 0:
                return 1
            comp["name"] = str(comp["name"]).strip().upper()
            self.components_data.append(comp)
        return 0

    def get_component(self, name: str, comp_type: ComponentType):
        for comp in self.components_data:
            if comp['name'] == name and comp_type.name == comp['type']:
                return comp

    def add_ets_to_network(self, name: str):
        name_uc = name.strip().upper()
        ets_data = self.get_component(name_uc, ComponentType.ENERGYTRANSFERSTATION)

        props = ets_data['properties']

        hp_name = str(props['heat_pump']).strip().upper()
        hp_data = self.get_component(hp_name, ComponentType.HEATPUMP)
        props['heat_pump'] = hp_data

        load_pump_name = str(props['load_side_pump']).strip().upper()
        load_pump_data = self.get_component(load_pump_name, ComponentType.PUMP)
        props['load_side_pump'] = load_pump_data

        src_pump_name = str(props['source_side_pump']).strip().upper()
        src_pump_data = self.get_component(src_pump_name, ComponentType.PUMP)
        props['source_side_pump'] = src_pump_data

        fan_name = str(props['fan']).strip().upper()
        fan_data = self.get_component(fan_name, ComponentType.FAN)
        props['fan'] = fan_data

        ets_data['properties'] = props
        ets = ETS(ets_data)
        self.network.append(ets)
        return 0

    def add_ghe_to_network(self, name: str):
        name_uc = name.strip().upper()
        ghe_data = self.get_component(name_uc, ComponentType.GROUNDHEATEXCHANGER)
        ghe = GHE(ghe_data)
        self.network.append(ghe)
        return 0

    def add_pump_to_network(self, name: str):
        name_uc = name.strip().upper()
        pump_data = self.get_component(name_uc, ComponentType.PUMP)
        pump = Pump(pump_data)
        self.network.append(pump)
        return 0

    def set_component_network_loads(self):

        len_loads = []

        for comp in self.network:
            if comp.comp_type == ComponentType.ENERGYTRANSFERSTATION:
                len_loads.append(len(comp.space_loads))

        # check if all ets space loads have the same length
        if not all([x == len_loads[0] for x in len_loads]):
            raise ValueError("Not all loads are of equal length")

        for comp in self.network:
            if comp.comp_type == ComponentType.ENERGYTRANSFERSTATION:
                comp.set_network_loads()
            elif comp.comp_type == ComponentType.PUMP:
                comp.set_network_loads(len_loads[0])

    def size_area_proportional(self, output_path: Path):
        """
        Sizing method for area proportional approach.
        """
        print("size_area_proportional")
        # find all objects between each groundheatexchanger
        #  sum loads
        # find all GHE and their sizes
        #  divide loads by GHE sizes
        ghe_indexes = []  # This will store the indexes of all GROUNDHEATEXCHANGER devices
        other_indexes = [] # This will store the indexes of all other devices

        for i, device in enumerate(self.network):
            print(f"Network Index {i}: {device}")
            if device.comp_type == ComponentType.GROUNDHEATEXCHANGER:
                ghe_indexes.append(i)
            else:
                other_indexes.append(i)    

        print("GROUNDHEATEXCHANGER indices in network:")
        print(ghe_indexes)
        print("Other equip indices in network:")
        print(other_indexes)

        total_ghe_area = 0
        for i in ghe_indexes:
            ghe_area = self.network[i].area
            print(f"{self.network[i]}.area: {ghe_area}")
            total_ghe_area += ghe_area
        print(f"total_ghe_area: {total_ghe_area}")

        total_space_loads = 0
        for i in other_indexes:
            #ETS .get_loads() doesnt take num_loads arg
            device = self.network[i]
            if device.comp_type != ComponentType.ENERGYTRANSFERSTATION:
                print(f"{device.comp_type}.get_loads: {device.get_loads(1)}")
                device_load = sum(device.get_loads(1))
            else:
                print(f"{device.comp_type}.get_loads len: {len(device.get_loads())}")
                device_load = sum(device.get_loads())
            print(f"Total load for {device.comp_type}: {device_load}")
            total_space_loads += device_load
        print(f"Total space loads for devices before GHE: {total_space_loads}")
        
        load_per_area = total_space_loads / total_ghe_area
        print(f"Load per Area: {load_per_area}")

        #loop over GHEs and size per area
        for i in ghe_indexes:
            ghe_area = self.network[i].area
            self.network[i].ghe_size(load_per_area * ghe_area, output_path)

    def size_to_upstream_equipment(self, output_path: Path):
        """
        Sizing method for upstream equipment approach.
        """
        print("size_to_upstream")
        # find all objects between each groundheatexchanger
        # size to those buildings

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
                #ETS .get_loads() doesnt take num_loads arg
                if device.comp_type != ComponentType.ENERGYTRANSFERSTATION:
                    print(f"{device.comp_type}.get_loads: {device.get_loads(1)}")
                    device_load = sum(device.get_loads(1))
                else:
                    print(f"{device.comp_type}.get_loads len: {len(device.get_loads())}")
                    device_load = sum(device.get_loads())
                print(f"Total load for {device.comp_type}: {device_load}")
                total_space_loads += device_load
                
            print(f"Total space loads for devices before GHE: {total_space_loads}")
            # call ghe_size() with total load
            self.network[ghe_index].ghe_size(total_space_loads, output_path)

    def size(self, output_path: Path, throw: bool = True):
        """
        High-level sizing call that handles any lower-level calls or iterations.
        """
        print("size")
        if self.des_method == DesignType.AREAPROPORTIONAL:
            self.size_area_proportional(output_path)
        elif self.des_method == DesignType.UPSTREAM:
            self.size_to_upstream_equipment(output_path)
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

        # This is being done in the GHE sizer call.  Should those dirs get moved somewhere else?

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
    component_data: list[dict] = data["components"]
    network_data: list[dict] = data["network"]

    if version != VERSION:
        print("Mismatched versions, could be a problem", file=stderr)
        return 1

    # instantiate a new Network object
    network = Network()

    # begin populating structures in preparation for sizing
    errors = 0
    errors += network.set_design(des_method_str=design_data["method"], throw=True)
    errors += network.set_components(component_data, throw=True)

    for component in network_data:
        comp_name = str(component["name"]).strip().upper()
        comp_type_str = str(component["type"]).strip().upper()
        if comp_type_str == ComponentType.ENERGYTRANSFERSTATION.name:
            errors += network.add_ets_to_network(comp_name)
        elif comp_type_str == ComponentType.GROUNDHEATEXCHANGER.name:
            errors += network.add_ghe_to_network(comp_name)
        elif comp_type_str == ComponentType.PUMP.name:
            errors += network.add_pump_to_network(comp_name)
        else:
            msg = f"Unsupported component type, {comp_type_str}"
            print(msg, file=stderr)
            errors += 1

    if errors != 0:
        return 1

    network.set_component_network_loads()
    network.size(output_path)
    #network.write_outputs(output_path)

    return 0


@click.command(name="ThermalNetworkCommandLine")
@click.argument("input-path", type=click.Path(exists=True))
@click.argument("output-path", type=click.Path(exists=False))
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
    print(f"Input path: {input_path.resolve()}") 
    if validate:
        try:
            validate_input_file(input_path)
            print("Valid input file.")
            return 0
        except ValidationError:
            print("Schema validation error. See previous error message(s) for details.", file=stderr)
            return 1
    # calling the worker function here
    output_path = Path(output_path)
    print(f"Output path: {output_path.resolve()}") 
    if not output_path.exists():
        print("Output path does not exist.")  # Add this line
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Failed to create directory: {e}")
    
    output_path = output_path.resolve()
    return run_sizer_from_cli_worker(input_path, output_path)


if __name__ == "__main__":
    exit(run_sizer_from_cli())
