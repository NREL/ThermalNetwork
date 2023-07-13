import json
from pathlib import Path
from sys import exit, stderr

import click

from thermalnetwork import VERSION
from thermalnetwork.base_component import BaseComponent
from thermalnetwork.energy_transfer_station import ETS
from thermalnetwork.enums import ComponentType, DesignType
from thermalnetwork.ground_heat_exchanger import GHE
from thermalnetwork.pump import Pump


class Network:
    def __init__(self) -> None:
        self.des_method = None
        self.components_data: list[dict] = []
        self.network: list[BaseComponent] = []
        self.ghe_parameters: dict = {}
        self.geojson_data: dict = {}
        self.scenario_directory_path: Path = Path()

    def find_startloop_feature_id(self, features):
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

    def get_connected_features(self, geojson_data):
        """
        Retrieves a list of connected features from a GeoJSON data object.

        :param geojson_data: GeoJSON data object containing features.
        :return: List of connected features with additional information.
        """
        features = geojson_data['features']
        connectors = [feature for feature in features if feature['properties']['type'] == 'ThermalConnector']
        connected_features = []

        # get the id of the building or ds from the thermaljunction that has start_loop: true
        startloop_feature_id = self.find_startloop_feature_id(features)

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
                    'district_system_type': feature['properties'].get('district_system_type', ''),
                    'properties': {k: v for k, v in feature['properties'].items() if k not in [':type', ':name']},
                    'start_loop': 'true' if feature_id == startloop_feature_id else None
                })

        return connected_objects

    def reorder_connected_features(self, features):
        """
        Reorders a list of connected features so that the feature with 'startloop' set to 'true' is at the beginning.

        :param features: List of connected features.
        :return: Reordered list of connected features.
        """
        while features[0].get('start_loop') != 'true':
            features.append(features.pop(0))
        return features

    def find_matching_ghe_id(self, feature_id):
        for ghe in self.ghe_parameters['ghe_specific_params']:
            if ghe['ghe_id'] == feature_id:
                return ghe
        return None  # if no match found, return None

    def convert_features(self, json_data):
        converted_features = []

        # Add pump as the first element
        obj = {'id': '0',
               'name': 'primary pump',
               'type': 'PUMP',
               "properties": {
                   "design_flow_rate": 0.01,
                   "design_head": 150000,
                   "motor_efficiency": 0.9,
                   "motor_inefficiency_to_fluid_stream": 1.0
               }
               }
        converted_features.append(obj)

        # Convert the features from geojson list
        for feature in json_data:
            feature_type = feature['type']
            if feature_type == 'Building':
                feature_type = 'ENERGYTRANSFERSTATION'
                # add building directory ID to scenario path; look for dir named '_export_modelica_loads' for the building_loads.csv
                new_path = self.scenario_directory_path / feature['properties']['id']
                for directory in new_path.iterdir():
                    if directory.is_dir() and "_export_modelica_loads" in directory.name:
                        new_path = new_path / directory.name / 'building_loads.csv'
                        print(f"building_loads.csv path: {new_path}\n")
                        break
                if not Path.is_file(new_path):
                    print("BUILDING_LOADS.CSV NOT FOUND! {new_path}", file=stderr)
                    return 1
                properties = {
                    "heat_pump": "small wahp",
                    "load_side_pump": "ets pump",
                    "source_side_pump": "ets pump",
                    "fan": "simple fan",
                    "space_loads_file": new_path
                }
            elif feature_type == 'District System' and feature['district_system_type'] == 'Ground Heat Exchanger':
                feature_type = 'GROUNDHEATEXCHANGER'
                # get ghe parameters for 'ghe_specific_params' key of system_parameters.json
                matching_ghe = self.find_matching_ghe_id(feature['id'])
                # matching_ghe.pop('ground_loads', None)
                # print(f"matching_ghe: {matching_ghe}\n")
                length = matching_ghe['ghe_geometric_params']['length_of_ghe']
                width = matching_ghe['ghe_geometric_params']['width_of_ghe']
                geometric_constraints = self.ghe_parameters['geometric_constraints']
                geometric_constraints['length'] = length
                geometric_constraints['width'] = width
                properties = {
                    'fuild': self.ghe_parameters['fluid'],
                    'grout': self.ghe_parameters['grout'],
                    'soil': self.ghe_parameters['soil'],
                    'pipe': self.ghe_parameters['pipe'],
                    'borehole': matching_ghe['borehole'],
                    'simulation': self.ghe_parameters['simulation'],
                    'geometric_constraints': geometric_constraints,
                    'design': self.ghe_parameters['design'],
                    'loads': {'ground_loads': matching_ghe['ground_loads']}
                }
            converted_features.append({
                'id': feature['id'],
                'name': feature['name'],
                'type': feature_type,
                'properties': properties
            })

        return converted_features

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

        # Add ets pump
        obj = {'id': '',
               'name': 'ets pump',
               'type': 'PUMP',
               "properties": {
                   "design_flow_rate": 0.0005,
                   "design_head": 100000,
                   "motor_efficiency": 0.9,
                   "motor_inefficiency_to_fluid_stream": 1.0
               }
               }
        obj["name"] = str(obj["name"]).strip().upper()
        self.components_data.append(obj)

        # Add fan
        obj = {'id': '',
               "name": "simple fan",
               "type": "FAN",
               "properties": {
                   "design_flow_rate": 0.25,
                   "design_head": 150,
                   "motor_efficiency": 0.6
               }
               }
        obj["name"] = str(obj["name"]).strip().upper()
        self.components_data.append(obj)

        # Add WAHP
        obj = {'id': '',
               "name": "small wahp",
               "type": "HEATPUMP",
               "properties": {
                   "cop_c": 3.5,
                   "cop_h": 2.5
               }
               }
        obj["name"] = str(obj["name"]).strip().upper()
        self.components_data.append(obj)

        for comp in comp_data_list:
            if self.check_for_existing_component(comp['name'], comp['type'], throw) != 0:
                return 1
            comp["name"] = str(comp["name"]).strip().upper()
            self.components_data.append(comp)
        return 0

    def get_component(self, name: str, comp_type: ComponentType):
        for comp in self.components_data:
            # print(f"comp: {comp}\n")
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
        # print(f"ghe_data: {ghe_data}\n")
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
        other_indexes = []  # This will store the indexes of all other devices

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
            # ETS .get_loads() doesnt take num_loads arg
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

        # loop over GHEs and size per area
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
                # ETS .get_loads() doesnt take num_loads arg
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


def run_sizer_from_cli_worker(geojson_file_path: Path, scenario_directory_path: Path,
                              output_directory_path: Path) -> int:
    """
    Sizing worker function. Worker is called by tests, and thus not wrapped by `click`.

    :param geojson_file_path: path to GeoJSON file
    :param scenario_directory_path: path to scenario directory
    :param output_directory_path: path to output directory
    """

    # load geojson_file file
    if not geojson_file_path.exists():
        print(f"No input file found at {geojson_file_path}, aborting.", file=stderr)
        return 1

    geojson_data = json.loads(geojson_file_path.read_text())
    # print(f"geojson_data: {geojson_data}")

    # load system_parameters file from the scenario directory path
    system_parameters_path = scenario_directory_path.joinpath("ghe_dir", "system_parameter.json")

    # Check if the file exists
    if not system_parameters_path.exists():
        print(f"No system_parameter.json file found at {system_parameters_path}, aborting.", file=stderr)
        return 1

    system_parameters_data = json.loads(system_parameters_path.read_text())
    # print(f"system_parameters_data: {system_parameters_data}")

    # load all input data
    version: int = system_parameters_data["district_system"]["fifth_generation"]["ghe_parameters"]["version"]
    if version != VERSION:
        print("Mismatched versions, could be a problem", file=stderr)
        return 1

    design_data: dict = system_parameters_data["district_system"]["fifth_generation"]["ghe_parameters"]["design"]
    print(f"design_data: {design_data}\n")
    # instantiate a new Network object
    network = Network()
    network.geojson_data = geojson_data
    network.ghe_parameters = system_parameters_data["district_system"]["fifth_generation"]["ghe_parameters"]
    network.scenario_directory_path = scenario_directory_path

    # get network list from geojson
    connected_features = network.get_connected_features(geojson_data)
    print(f"Features in district loop: {connected_features}\n")

    reordered_features = network.reorder_connected_features(connected_features)
    print(f"Features in loop order: {reordered_features}\n")

    # convert geojson type "Building","District System" to "ENERGYTRANSFERSTATION","GROUNDHEATEXCHANGER" and add properties
    network_data: list[dict] = network.convert_features(reordered_features)
    # print(f"Network data: {network_data}\n")
    # network_data: list[dict] = data["network"]
    # component_data: list[dict] = data["components"]

    # begin populating structures in preparation for sizing
    errors = 0
    errors += network.set_design(des_method_str=design_data["method"], throw=True)
    errors += network.set_components(network_data, throw=True)
    # print(f"components_data: {network.components_data}\n")
    # pprint(network.components_data)

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
    network.size(output_directory_path)
    # network.write_outputs(output_path)

    return 0


@click.command(name="ThermalNetworkCommandLine")
@click.option("-f", "--geojson_file", type=click.Path(exists=True), metavar="GEOJSON_FILE", help="Path to GeoJSON file")
@click.option("-s", "--scenario_directory", type=click.Path(exists=True), metavar="SCENARIO_DIRECTORY",
              help="Path to scenario directory")
@click.option("-o", "--output_directory", type=click.Path(), metavar="OUTPUT_DIRECTORY",
              help="Path to output directory")
@click.version_option(VERSION)
# @click.option(
#     "--validate",
#     default=False,
#     is_flag=True,
#     show_default=False,
#     help="Validate input and exit."
# )
def run_sizer_from_cli(geojson_file, scenario_directory, output_directory):
    """
    CLI entrypoint for sizing runner.

    :param geojson_file: path to GeoJSON file
    :param scenario_directory: path to scenario directory
    :param output_directory: path to output directory    :param validate: flag for input schema validation
    """

    print("GeoJSON file:", geojson_file)
    print("Scenario directory:", scenario_directory)
    print("Output directory:", output_directory)

    geojson_file_path = Path(geojson_file).resolve()
    print(f"geojson_file path: {geojson_file_path}\n")
    # if validate:
    #    try:
    #        validate_input_file(input_path)
    #        print("Valid input file.")
    #        return 0
    #    except ValidationError:
    #        print("Schema validation error. See previous error message(s) for details.", file=stderr)
    #        return 1
    # calling the worker function here

    scenario_directory_path = Path(scenario_directory).resolve()
    print(f"scenario_directory path: {scenario_directory_path}\n")

    output_directory_path = Path(output_directory)
    print(f"Output path: {output_directory_path}\n")
    if not output_directory_path.exists():
        print("Output path does not exist. attempting to create")  # Add this line
        try:
            output_directory_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Failed to create directory: {e}")

    output_directory_path = output_directory_path.resolve()
    return run_sizer_from_cli_worker(geojson_file_path, scenario_directory_path, output_directory_path)


if __name__ == "__main__":
    exit(run_sizer_from_cli())
