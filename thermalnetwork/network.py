import json
import logging
from importlib.metadata import version
from pathlib import Path
from sys import exit

import click
import numpy as np
import pandas as pd
from rich.logging import RichHandler

from thermalnetwork.base_component import BaseComponent
from thermalnetwork.energy_transfer_station import ETS
from thermalnetwork.enums import ComponentType, DesignType
from thermalnetwork.ground_heat_exchanger import GHE
from thermalnetwork.pump import Pump

logging.basicConfig(level=logging.DEBUG, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
logger = logging.getLogger(__name__)


class Network:
    def __init__(
        self, system_parameters_data: dict, geojson_data: dict, ghe_parameters_data: dict, scenario_directory_path: Path
    ) -> None:
        """A thermal network.

        :param des_method: Design method (upstream or proportional).
        :param components_data: List of component data.
        :param network: List of components.
        :param ghe_parameters: Parameters for the ground heat exchanger.
        :param geojson_data: GeoJSON data object containing features.
        :param scenario_directory_path: Path to the URBANopt scenario directory.
        """
        self.des_method = None
        self.components_data: list[dict] = []
        self.network: list[BaseComponent] = []
        self.system_parameters_data = system_parameters_data
        self.ghe_parameters = ghe_parameters_data
        self.geojson_data = geojson_data
        self.scenario_directory_path = scenario_directory_path

    def find_startloop_feature_id(self):
        """
        Finds the feature ID of a feature with the 'is_ghe_start_loop' property set to True in a list of features.

        :param features: List of features to search for the start loop feature.
        :return: The feature ID of the start loop feature, or None if not found.
        """
        for feature in self.geojson_data["features"]:
            if feature["properties"].get("is_ghe_start_loop"):
                start_feature_id = feature["properties"].get("buildingId") or feature["properties"].get("DSId")
                return start_feature_id
        return None

    def get_connected_features(self):
        """
        Retrieves a list of connected features from a GeoJSON data object.

        :return: List of connected features with additional information.
        """
        startloop_feature_id = self.find_startloop_feature_id()
        # List thermal connections
        connectors = [
            feature for feature in self.geojson_data["features"] if feature["properties"]["type"] == "ThermalConnector"
        ]

        if len(connectors) == 0:
            raise ValueError(
                "No thermal connectors (pipes) were found in the GeoJSON data which are required for a thermal network."
            )

        # Find the feature that has been labelled as the start of the loop
        # TODO: Update the UI to allow the user to select the start loop feature.
        connected_features = [
            feature["properties"].get("buildingId") or feature["properties"].get("DSId")
            for feature in self.geojson_data["features"]
            if feature["properties"].get("is_ghe_start_loop")
        ]
        # Warn that starting from something that isn't a building makes UPSTREAM results undesirable.
        for feature in self.geojson_data["features"]:
            if feature["properties"]["id"] == [connected_features[0]] and feature["properties"]["type"] != "Building":
                logger.warning(
                    f"Feature {feature[connected_features[0]]} is not a building which may have undesirable results "
                    "when using the UPSTREAM sizing method."
                )
        # complete the list of feature ids that have thermal connections (building or district system)
        while True:
            next_feature_id = None
            for connector in connectors:
                if connector["properties"]["startFeatureId"] == connected_features[-1]:
                    next_feature_id = connector["properties"]["endFeatureId"]
                    break
            if next_feature_id:
                if next_feature_id == connected_features[0]:
                    break
                connected_features.append(next_feature_id)
            else:
                break

        # Filter and return the building and district system features
        connected_objects = []
        for con_feature in connected_features:
            for feature in self.geojson_data["features"]:
                feature_id = feature["properties"]["id"]
                if (feature_id == con_feature) and (feature["properties"]["type"] in ["Building", "District System"]):
                    connected_objects.append(
                        {
                            "id": feature_id,
                            "type": feature["properties"]["type"],
                            "name": feature["properties"].get("name", ""),
                            "district_system_type": feature["properties"].get("district_system_type"),
                            "properties": {
                                k: v
                                for k, v in feature["properties"].items()
                                if k not in ["type", "name", "id", "district_system_type"]
                            },
                            "is_ghe_start_loop": feature_id == startloop_feature_id,
                        }
                    )

        return connected_objects

    @staticmethod
    def reorder_connected_features(features):
        """
        Reorders a list of connected features so that the feature with
        'is_ghe_start_loop' set to True is at the beginning.

        :param features: List of connected features.
        :return: Reordered list of connected features.
        :raises ValueError: If no feature with 'is_ghe_start_loop' set to True is found.
        """
        start_loop_index = None

        for i, feature in enumerate(features):
            if feature.get("is_ghe_start_loop"):
                start_loop_index = i
                break

        if start_loop_index is None:
            raise ValueError("No feature with 'is_ghe_start_loop' set to True was found in the list.")

        # Reorder the features list to start with the feature having 'startloop' set to 'true'
        reordered_features = features[start_loop_index:] + features[:start_loop_index]

        return reordered_features

    def find_matching_ghe_id(self, feature_id):
        """
        Find the GHE parameters for a specific GHE ID

        :param feature_id: The ID of the feature to search for.
        :return: The feature ID of the start loop feature, or None if not found.
        """

        for ghe in self.ghe_parameters["ghe_specific_params"]:
            if ghe["ghe_id"] == feature_id:
                return ghe
        return None  # if no match found, return None

    def convert_features(self, json_data):
        """
        Converts the features from geojson list into a format that can be used by the thermal network.

        :param json_data: A list of geojson features.
        :return: A list of converted features, each containing an id, name, type, and properties.
        :rtype: list
        """

        converted_features = []

        # Add pump as the first element
        obj = {
            "id": "0",
            "name": "primary pump",
            "type": "PUMP",
            "properties": {
                "design_flow_rate": 0.01,
                "design_head": 0,
                "motor_efficiency": 0.9,
                "motor_inefficiency_to_fluid_stream": 1.0,
            },
        }
        converted_features.append(obj)

        # Convert the features from geojson list
        for feature in json_data:
            if feature["type"] == "Building":
                feature_type = "ENERGYTRANSFERSTATION"
                # add building directory ID to scenario path; look for dir named
                # '_export_modelica_loads' for the building_loads.csv
                new_path = self.scenario_directory_path / feature["id"]
                for directory in new_path.iterdir():
                    if directory.is_dir() and "_export_modelica_loads" in directory.name:
                        new_path = new_path / directory.name / "building_loads.csv"
                        logger.debug(f"building_loads.csv path: {new_path}")
                        break
                if not new_path.is_file():
                    logger.error(f"BUILDING_LOADS.CSV NOT FOUND! {new_path}")
                    return 1
                properties = {
                    "heat_pump": "small wahp",
                    "load_side_pump": "ets pump",
                    "source_side_pump": "ets pump",
                    "fan": "simple fan",
                    "space_loads_file": new_path,
                }
            elif feature["type"] == "District System" and feature["district_system_type"] == "Ground Heat Exchanger":
                feature_type = "GROUNDHEATEXCHANGER"
                # get ghe parameters for 'ghe_specific_params' key of system_parameters.json
                matching_ghe = self.find_matching_ghe_id(feature["id"])
                # matching_ghe.pop('ground_loads', None)
                logger.debug(f"matching_ghe: {matching_ghe}\n")
                length = matching_ghe["ghe_geometric_params"]["length_of_ghe"]
                width = matching_ghe["ghe_geometric_params"]["width_of_ghe"]
                geometric_constraints = self.ghe_parameters["geometric_constraints"]
                geometric_constraints["length"] = length
                geometric_constraints["width"] = width
                properties = {
                    "fluid": self.ghe_parameters["fluid"],
                    "grout": self.ghe_parameters["grout"],
                    # soil properties are not exclusive to ghe, they are up one level in the system_parameters.json
                    "soil": self.system_parameters_data["district_system"]["fifth_generation"]["soil"],
                    "pipe": self.ghe_parameters["pipe"],
                    "borehole": matching_ghe["borehole"],
                    "simulation": self.ghe_parameters["simulation"],
                    "geometric_constraints": geometric_constraints,
                    "design": self.ghe_parameters["design"],
                    "loads": {"ground_loads": []},
                }
            converted_features.append(
                {"id": feature["id"], "name": feature["name"], "type": feature_type, "properties": properties}
            )

        return converted_features

    def set_design(self, des_method_str: str, throw: bool = True) -> int:
        """
        Designate the network design method.

        :param des_method_str: design method string
        :param throw: by default, function will raise an exception on error.
                      override to "False" to not raise exception
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
                logger.error(f"Design method '{des_method_str}' not supported.")
            return 1
        return 0

    def check_for_existing_component(self, name: str, comp_type_str: str, throw: bool = True):
        """
        Checks if a component with the given name and type already exists in the network.

        :param name: The name of the component to check for.
        :param comp_type_str: The type of the component to check for.
        :param throw: A boolean indicating whether an error should be thrown if the component already exists.
            Defaults to True.
        :return: Zero if the component does not exist, nonzero if it does.
        """

        for comp in self.components_data:
            if comp["name"] == name and comp["type"] == comp_type_str:
                if throw:
                    logger.error(f'Duplicate {comp_type_str} name "{name}" encountered.')
                return 1
        return 0

    def set_components(self, comp_data_list: list[dict], throw: bool = True):
        """
        Sets up the components of the thermal network.

        :param comp_data_list: list of dictionaries containing component data.
        :param throw: by default, function will raise an exception on error.
                        override to "False" to not raise exception
        :returns: zero if successful, nonzero if failure
        """

        # TODO: replace all hard-coded values with sys-param data
        # Add ets pump
        obj = {
            "id": "",
            "name": "ets pump",
            "type": "PUMP",
            "properties": {
                "design_flow_rate": 0.0005,
                "design_head": 0,
                "motor_efficiency": 0.9,
                "motor_inefficiency_to_fluid_stream": 1.0,
            },
        }
        obj["name"] = str(obj["name"]).strip().upper()
        self.components_data.append(obj)

        # Add fan
        obj = {
            "id": "",
            "name": "simple fan",
            "type": "FAN",
            "properties": {"design_flow_rate": 0.25, "design_head": 0, "motor_efficiency": 0.6},
        }
        obj["name"] = str(obj["name"]).strip().upper()
        self.components_data.append(obj)

        # Add WAHP
        obj = {
            "id": "",
            "name": "small wahp",
            "type": "HEATPUMP",
            "properties": {},
        }
        obj["name"] = str(obj["name"]).strip().upper()
        self.components_data.append(obj)

        for comp in comp_data_list:
            if self.check_for_existing_component(comp["name"], comp["type"], throw) != 0:
                return 1
            comp["name"] = str(comp["name"]).strip().upper()
            self.components_data.append(comp)
        return 0

    def get_component(self, name: str, comp_type: ComponentType):
        """
        Retrieves a component by name and type from a list of component_data dicts.

        :param name: The name of the component to search for.
        :param comp_type: The type of the component to search for.
        :return: A dictionary containing the properties of the component if found, otherwise None.
        """

        for comp in self.components_data:
            # print(f"comp: {comp}\n")
            if comp["name"] == name and comp_type.name == comp["type"]:
                return comp

    def add_ets_to_network(self, name: str, component_id: str):
        """
        Adds an Energy Transfer Station (ETS) to the network.

        :param name: The name of the ETS to be added.
        :param component_id: The component ID which is the geojson feature (building) associated with the ETS.
        :return: Zero if successful, nonzero if failure.

        This function first retrieves the ETS data by its name and type.
        It then modifies the ETS data to include the appropriate heat pump, load pump, source pump, and fan components.
        After updating the ETS data, it creates a new ETS object and adds it to the network.

        Returns zero if the ETS is successfully added to the network, or a nonzero value if there is an error.
        """

        name_uc = name.strip().upper()
        ets_data = self.get_component(name_uc, ComponentType.ENERGYTRANSFERSTATION)
        logger.debug(f"ets_data: {ets_data}")
        props = ets_data["properties"]
        logger.debug(f"props: {props}")

        # Read sys param for user-defined values
        sys_param_buildings_data = self.system_parameters_data["buildings"]
        for building in sys_param_buildings_data:
            if building["geojson_id"] == component_id:
                hp_name = str(props["heat_pump"]).strip().upper()
                hp_data = self.get_component(hp_name, ComponentType.HEATPUMP)
                props["heat_pump"] = hp_data
                props["heat_pump"]["properties"]["cop_c"] = building["fifth_gen_ets_parameters"][
                    "cop_heat_pump_cooling"
                ]
                props["heat_pump"]["properties"]["cop_h"] = building["fifth_gen_ets_parameters"][
                    "cop_heat_pump_heating"
                ]

                load_pump_name = str(props["load_side_pump"]).strip().upper()
                load_pump_data = self.get_component(load_pump_name, ComponentType.PUMP)
                props["load_side_pump"] = load_pump_data

                src_pump_name = str(props["source_side_pump"]).strip().upper()
                src_pump_data = self.get_component(src_pump_name, ComponentType.PUMP)
                props["source_side_pump"] = src_pump_data

                fan_name = str(props["fan"]).strip().upper()
                fan_data = self.get_component(fan_name, ComponentType.FAN)
                props["fan"] = fan_data

                break

        ets_data["properties"] = props
        logger.debug(f"final ets_data: {ets_data}")
        ets = ETS(ets_data)
        logger.info("made ETS")
        # check size of space loads
        logger.debug(f"length of spaceloads: {len(ets.space_loads)}")
        logger.debug(f"space_loads_file: {props['space_loads_file']}")
        if len(ets.space_loads) != 8760:
            self.make_loads_hourly(ets_data["properties"], ets)
        self.network.append(ets)
        return 0

    def make_loads_hourly(self, properties: dict, ets: ETS):
        # TODO: test this method
        """
        This method interpolates the space loads to hourly values.

        :param properties: A dictionary containing the properties of the ETS, including the space loads file path.
        :param ets: An Energy Transfer Station object.
        :return: ETS object with updated space loads.
        """

        space_loads_df = pd.read_csv(properties["space_loads_file"])
        space_loads_df["Date Time"] = pd.to_datetime(space_loads_df["Date Time"])
        space_loads_df = space_loads_df.set_index("Date Time")
        # Find the last date in the DataFrame and add one day so interpolation will get the last day
        new_date = space_loads_df.index[-1] + pd.Timedelta(days=1)
        # add duplicate entry at end of dataframe
        new_data = pd.DataFrame(
            space_loads_df.iloc[-1].to_numpy().reshape(1, -1), index=[new_date], columns=space_loads_df.columns
        )
        space_loads_df = pd.concat([space_loads_df, new_data])
        # interpolate data to hourly
        space_loads_df = space_loads_df.resample("H").interpolate(method="linear")
        # keep only 8760
        space_loads_df = space_loads_df.iloc[:8760]
        ets.space_loads = space_loads_df["TotalSensibleLoad"]
        logger.warning(f"NEW length of spaceloads: {len(ets.space_loads)}")
        return ets

    def add_ghe_to_network(self, name: str):
        """
        Adds a Ground Heat Exchanger (GHE) to the network.

        :param name: The name of the GHE to be added.
        :return: Zero if successful, nonzero if failure.

        This function first retrieves the GHE data by its name and type from the list of components in the network.
        It then creates a new GHE object and adds it to the network.
        """

        name_uc = name.strip().upper()
        ghe_data = self.get_component(name_uc, ComponentType.GROUNDHEATEXCHANGER)
        # print(f"ghe_data: {ghe_data}\n")
        ghe = GHE(ghe_data)
        self.network.append(ghe)
        return 0

    def add_pump_to_network(self, name: str):
        """
        Adds a Pump to the network.

        :param name: The name of the Pump to be added.
        :return: Zero if successful, nonzero if failure.

        This function first retrieves the Pump data by its name and type from the list of components in the network.
        It then creates a new Pump object and adds it to the network.
        """

        name_uc = name.strip().upper()
        pump_data = self.get_component(name_uc, ComponentType.PUMP)
        pump = Pump(pump_data)
        self.network.append(pump)
        return 0

    def set_component_network_loads(self):
        """
        This method sets the network loads for each component in the network.

        For each component in the network, this method checks if the component type is an Energy Transfer Station (ETS).
        If it is, the method calls the set_network_loads method of the component.
        If the component type is a Pump, the method sets the network loads to 8760 (the number of hours in a year).

        If a component does not have network loads set, it will not affect the overall sizing process.
        """

        # len_loads = []

        # for comp in self.network:
        #    if comp.comp_type == ComponentType.ENERGYTRANSFERSTATION:
        #        len_loads.append(len(comp.space_loads))
        # print(f"len_loads: {len_loads}")
        # check if all ets space loads have the same length
        # if not all([x == len_loads[0] for x in len_loads]):
        #    raise ValueError("Not all loads are of equal length")

        for comp in self.network:
            if comp.comp_type == ComponentType.ENERGYTRANSFERSTATION:
                comp.set_network_loads()
            elif comp.comp_type == ComponentType.PUMP:
                comp.set_network_loads(8760)

    def size_area_proportional(self, output_path: Path):
        """
        Sizing method for area proportional approach.

        This method sizes the network components based on the area proportional approach.
        It first finds all objects between each groundheatexchanger, sums the loads,
        finds all GHE and their sizes, and then divides the loads by the GHE sizes.
        Finally, it re-sizes each GHE based on the load per area.

        :param output_path: The path to the output directory where the sized GHEs will be saved.

        :return: None
        """

        logger.info("Sizing with: size_area_proportional")
        # find all objects between each groundheatexchanger
        #  sum loads
        # find all GHE and their sizes
        #  divide loads by GHE sizes
        ghe_indexes = []  # This will store the indexes of all GROUNDHEATEXCHANGER devices
        other_indexes = []  # This will store the indexes of all other devices

        for i, device in enumerate(self.network):
            logger.debug(f"Network Index {i}: {device}")
            if device.comp_type == ComponentType.GROUNDHEATEXCHANGER:
                ghe_indexes.append(i)
            else:
                other_indexes.append(i)

        logger.info("GROUNDHEATEXCHANGER indices in network:")
        logger.info(ghe_indexes)
        logger.info("Other equipment indices in network:")
        logger.info(other_indexes)

        total_ghe_area = 0
        for i in ghe_indexes:
            ghe_area = self.network[i].area
            logger.info(f"{self.network[i]}.area: {ghe_area}")
            total_ghe_area += ghe_area
        logger.info(f"total_ghe_area: {total_ghe_area}")

        # Initialize an array to store the summed loads for each hour of the year
        total_network_loads = [0] * 8760

        for i in other_indexes:
            # ETS .get_loads() doesnt take num_loads arg
            device = self.network[i]
            if device.comp_type != ComponentType.ENERGYTRANSFERSTATION:
                logger.debug(f"{device.comp_type}.get_loads: {device.get_loads(1)}")
                device_load = device.get_loads(1)
                # Add the scalar load to the total space loads for each hour of the year
                total_network_loads = np.array(total_network_loads) + device_load[0]
            else:
                logger.debug(f"{device.comp_type}.get_loads len: {len(device.get_loads())}")
                device_loads = device.get_loads()
                # Add the array of loads for each hour to the total space loads array
                total_network_loads = np.array(total_network_loads) + np.array(device_loads)

        logger.info(f"Total network loads for devices: {sum(total_network_loads)}")

        network_load_per_area = np.array(total_network_loads) / total_ghe_area

        # loop over GHEs and size per area
        for i in ghe_indexes:
            ghe_area = self.network[i].area
            self.network[i].json_data["loads"]["ground_loads"] = np.array(network_load_per_area) * ghe_area
            self.network[i].ghe_size(sum(network_load_per_area) * ghe_area, output_path)

    def size_to_upstream_equipment(self, output_path: Path):
        """
        Sizing method for upstream equipment approach.

        This method sizes the network components based on the upstream equipment approach.
        It first finds all loads between each groundheatexchanger, then re-sizes each GHE
        based on the building loads each GHE is required to serve.

        :param output_path: The path to the output directory where the sized GHEs will be saved.

        :return: None
        """

        logger.info("Sizing with: size_to_upstream_equipment")
        # find all objects between each groundheatexchanger
        # size to those buildings

        ghe_indexes = []  # This will store the indexes of all GROUNDHEATEXCHANGER devices

        for i, device in enumerate(self.network):
            logger.debug(f"Network Index {i}: {device}")
            if device.comp_type == ComponentType.GROUNDHEATEXCHANGER:
                ghe_indexes.append(i)

        logger.info("GROUNDHEATEXCHANGER indices in network:")
        logger.info(ghe_indexes)
        # slice the self.network by ghe_indexes
        for i, ghe_index in enumerate(ghe_indexes):
            if i == 0:  # first GHE
                devices_before_ghe = self.network[:ghe_index]
            else:
                devices_before_ghe = self.network[ghe_indexes[i - 1] + 1 : ghe_index]
            logger.info(f"Devices before GHE at index {ghe_index}: {devices_before_ghe}")

            # Initialize an array to store the summed network loads for each hour of the year
            network_loads = [0] * 8760
            for device in devices_before_ghe:
                # ETS .get_loads() doesnt take num_loads arg
                if device.comp_type != ComponentType.ENERGYTRANSFERSTATION:
                    logger.debug(f"{device.comp_type}.get_loads: {device.get_loads(1)}")
                    device_load = device.get_loads(1)
                    # Add the scalar load to the total space loads for each hour of the year
                    network_loads = np.array(network_loads) + device_load[0]

                else:
                    logger.debug(f"{device.comp_type}.get_loads len: {len(device.get_loads())}")
                    device_loads = device.get_loads()
                    # Add the array of loads for each hour to the total space loads array
                    network_loads = np.array(network_loads) + np.array(device_loads)

            logger.info(f"Total network loads for devices before GHE: {sum(network_loads)}")
            self.network[ghe_index].json_data["loads"]["ground_loads"] = network_loads
            # call ghe_size() with total load
            self.network[ghe_index].ghe_size(sum(network_loads), output_path)

    def size(self, output_path: Path, throw: bool = True):
        """
        High-level sizing call that handles any lower-level calls or iterations.
        """
        logger.debug("Choosing sizing method...")
        if self.des_method == DesignType.AREAPROPORTIONAL:
            self.size_area_proportional(output_path)
        elif self.des_method == DesignType.UPSTREAM:
            self.size_to_upstream_equipment(output_path)
        else:
            if throw:
                logger.error(f"Unsupported design method {self.des_method}")
            return 1
        return 0

    def update_sys_params(self, system_parameter_path: Path, output_directory_path: Path) -> None:
        """
        Update the existing system parameters with the new GHEDesigner output data.

        :param system_parameter_path: Path to the existing System Parameter file.
        :param output_directory_path: Path to the output directory containing the GHEDesigner output files.

        This function loads the existing system parameters from the specified file,
        updates the GHE-specific parameters with the new data from the GHEDesigner output,
        and saves the updated system parameters back to the same file.
        The GHE-specific parameters include the length of the boreholes and the number of boreholes.

        The function does not return any value, as it updates the system parameters file in place.

        :return: None
        """

        # Load the existing system parameters
        sys_params: dict = json.loads(system_parameter_path.read_text())
        ghe_params: list = sys_params["district_system"]["fifth_generation"]["ghe_parameters"]["ghe_specific_params"]
        for ghe_id in output_directory_path.iterdir():
            # each ghe_id is a directory
            if not ghe_id.is_dir():
                continue
            summary_data_path = ghe_id / "SimulationSummary.json"
            # Get the new data from the GHEDesigner output
            ghe_data: dict = json.loads(summary_data_path.read_text())["ghe_system"]
            for ghe_sys_params in ghe_params:
                if ghe_sys_params["ghe_id"] == ghe_id.stem:
                    # Update system parameters dict with the new values
                    ghe_sys_params["borehole"]["length_of_boreholes"] = ghe_data["active_borehole_length"]["value"]
                    ghe_sys_params["borehole"]["number_of_boreholes"] = ghe_data["number_of_boreholes"]
        with open(system_parameter_path, "w") as sys_param_file:
            json.dump(sys_params, sys_param_file, indent=2)
            # Restore the trailing newline
            sys_param_file.write("\n")


def run_sizer_from_cli_worker(
    system_parameter_path: Path, scenario_directory_path: Path, geojson_file_path: Path, output_directory_path: Path
) -> int:
    """
    Sizing worker function. Worker is called by tests, and thus not wrapped by `click`.

    :param geojson_file_path: path to GeoJSON file
    :param system_parameter_path: path to System Parameter File
    :param scenario_directory_path: path to scenario directory
    :param output_directory_path: path to output directory
    """

    # load geojson_file file
    if not geojson_file_path.exists():
        logger.warning(f"No input file found at {geojson_file_path}, aborting.")
        return 1

    geojson_data: dict = json.loads(geojson_file_path.read_text())
    # logger.debug(f"{geojson_data=}")

    # Check if the file exists
    if not system_parameter_path.exists():
        logger.warning(f"No system_parameter.json file found at {system_parameter_path}, aborting.")
        return 1

    system_parameters_data = json.loads(system_parameter_path.read_text())
    ghe_parameters_data: dict = system_parameters_data["district_system"]["fifth_generation"]["ghe_parameters"]

    # Downselect the buildings in the geojson that are in the system parameters file

    # List the building ids from the system parameters file
    building_id_list = []
    for building in system_parameters_data["buildings"]:
        building_id_list.append(building["geojson_id"])

    # logger.debug(f"{building_id_list=}")

    # Select the buildings in the geojson that are in the system parameters file
    building_features = [
        feature
        for feature in geojson_data["features"]
        if feature["properties"]["type"] == "Building" and feature["properties"]["id"] in building_id_list
    ]

    # Rebuild the geojson data using only the buildings in the system parameters file
    # Put in everything that isn't a building
    geojson_data["features"] = [
        feature for feature in geojson_data["features"] if feature["properties"]["type"] != "Building"
    ]
    # Only add the buildings in the system parameters file back to the geojson data
    # This has the effect of removing buildings that are not in the system parameters file
    geojson_data["features"].extend(building_features)

    # print("Building features:")
    # for feature in geojson_data["features"]:
    #     if feature["properties"]["type"] == "Building":
    #         print(feature["properties"])
    #         print("")
    # logger.debug(f"Feature :: {feature['properties']['type']}: {feature['properties']['id']}")

    # load all input data
    sys_param_version: str = ghe_parameters_data["version"]
    if version("thermalnetwork")[:3] != sys_param_version[:3]:  # Just major & minor, ignore patch version
        logger.warning(
            "Mismatched ThermalNetwork versions. Could be a problem. "
            f"The system_parameter.json version is {sys_param_version}, but the ThermalNetwork version is "
            f"{version('thermalnetwork')}."
        )

    ghe_design_data: dict = ghe_parameters_data["design"]
    logger.debug(f"{ghe_design_data=}")
    # instantiate a new Network object
    network = Network(system_parameters_data, geojson_data, ghe_parameters_data, scenario_directory_path)

    # get network list from geojson
    connected_features = network.get_connected_features()
    logger.debug(f"Features in district loop: {connected_features}\n")

    reordered_features = network.reorder_connected_features(connected_features)
    logger.debug(f"Features in loop order: {reordered_features}\n")

    num_ghes = len([x for x in reordered_features if x["district_system_type"]])
    bldg_groups_per_ghe = []

    # populate bldg_groups_per_ghe list with info for GMT diagramming
    seen_id_list = []
    for _ in range(num_ghes):
        loop_info = {"list_bldg_ids_in_group": [], "list_ghe_ids_in_group": []}
        for feature in reordered_features:
            if feature["id"] in seen_id_list:
                continue
            elif feature["district_system_type"]:
                loop_info["list_ghe_ids_in_group"].append(feature["id"])
                seen_id_list.append(feature["id"])
                break
            loop_info["list_bldg_ids_in_group"].append(feature["id"])
            seen_id_list.append(feature["id"])  # Add ID to seen list (so we don't add it again)
        bldg_groups_per_ghe.append(loop_info)

    # save loop order to file next to sys-params for temporary use by the GMT
    # Prepending an underscore to emphasize these as temporary files
    loop_order_filepath = system_parameter_path.parent.resolve() / "_loop_order.json"
    with open(loop_order_filepath, "w") as loop_order_file:
        json.dump(bldg_groups_per_ghe, loop_order_file, indent=2)
        # Add a trailing newline to the file
        loop_order_file.write("\n")

    # convert geojson type "Building","District System" to "ENERGYTRANSFERSTATION",
    # "GROUNDHEATEXCHANGER" and add properties
    network_data: list[dict] = network.convert_features(connected_features)
    # logger.debug(f"{network_data=}\n")
    # network_data: list[dict] = data["network"]
    # component_data: list[dict] = data["components"]

    # begin populating structures in preparation for sizing
    errors = 0
    errors += network.set_design(des_method_str=ghe_design_data["method"], throw=True)
    errors += network.set_components(network_data, throw=True)
    # print(f"components_data: {network.components_data}\n")
    # pprint(network.components_data)

    for component in network_data:
        comp_name = str(component["name"]).strip().upper()
        comp_type_str = str(component["type"]).strip().upper()
        component_id = str(component["id"]).strip()
        if comp_type_str == ComponentType.ENERGYTRANSFERSTATION.name:
            errors += network.add_ets_to_network(comp_name, component_id)
        elif comp_type_str == ComponentType.GROUNDHEATEXCHANGER.name:
            errors += network.add_ghe_to_network(comp_name)
        elif comp_type_str == ComponentType.PUMP.name:
            errors += network.add_pump_to_network(comp_name)
        else:
            logger.error(f"Unsupported component type, {comp_type_str}")
            errors += 1

    if errors != 0:
        return 1

    network.set_component_network_loads()
    network.size(output_directory_path)
    network.update_sys_params(system_parameter_path, output_directory_path)

    return 0


@click.command(name="ThermalNetworkCommandLine")
@click.option(
    "-y", "--system-parameter-file", type=click.Path(exists=True, path_type=Path), help="Path to System Parameter file"
)
@click.option(
    "-s", "--scenario-directory", type=click.Path(exists=True, path_type=Path), help="Path to scenario directory"
)
@click.option("-f", "--geojson-file", type=click.Path(exists=True, path_type=Path), help="Path to GeoJSON file")
@click.option("-o", "--output-directory", type=click.Path(path_type=Path), help="Path to output directory")
@click.version_option(version("thermalnetwork"))
def run_sizer_from_cli(system_parameter_file, scenario_directory, geojson_file, output_directory):
    """
    CLI entrypoint for sizing runner.

    :param system_parameter_file: path to system parameter file

    :param scenario_directory: path to scenario directory

    :param geojson_file: path to GeoJSON file

    :param output_directory: path to output directory
    """

    # if validate:
    #    try:
    #        validate_input_file(input_path)
    #        print("Valid input file.")
    #        return 0
    #    except ValidationError:
    #        print("Schema validation error. See previous error message(s) for details.", file=stderr)
    #        return 1
    # calling the worker function here

    logger.debug(f"{system_parameter_file=}")
    logger.debug(f"{scenario_directory=}")
    logger.debug(f"{geojson_file=}")
    logger.debug(f"{output_directory=}")

    if not output_directory.exists():
        logger.info("Output path does not exist. attempting to create")
        output_directory.mkdir(parents=True, exist_ok=True)

    return run_sizer_from_cli_worker(system_parameter_file, scenario_directory, geojson_file, output_directory)


if __name__ == "__main__":
    exit(run_sizer_from_cli())
