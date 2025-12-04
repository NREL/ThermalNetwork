import sys
from collections import OrderedDict, defaultdict
from importlib.metadata import version
from pathlib import Path

import click
import numpy as np
import pandas as pd
from loguru import logger
from modelica_builder.modelica_mos_file import ModelicaMOS

from thermalnetwork import HOURS_IN_YEAR
from thermalnetwork.base_component import BaseComponent
from thermalnetwork.energy_transfer_station import ETS
from thermalnetwork.enums import ComponentType, DesignType, GHEDesignType
from thermalnetwork.geometry import lower_left_point, rotate_polygon_to_axes
from thermalnetwork.ground_heat_exchanger import GHE
from thermalnetwork.pipe import Pipe
from thermalnetwork.projection import lon_lat_to_polygon, meters_to_long_lat_factors
from thermalnetwork.pump import Pump
from thermalnetwork.utilities import load_json, lps_to_cms, write_json


class Network:
    def __init__(
        self,
        system_parameters_data: dict,
        geojson_data: dict,
        ghe_parameters_data: dict,
        scenario_directory_path: Path,
        system_parameter_path: Path,
    ) -> None:
        """
        A thermal network.

        :param system_parameters_data: System parameters data.
        :param geojson_data: GeoJSON data object containing features.
        :param ghe_parameters_data: Parameters for the ground heat exchanger.
        :param scenario_directory_path: Path to the URBANopt scenario directory.
        :param system_parameter_path: Path to the system parameters file.
        """

        self.des_method = None
        self.components_data: list[dict] = []
        self.network: list[BaseComponent] = []
        self.system_parameters_data = system_parameters_data
        self.ghe_parameters = ghe_parameters_data
        self.geojson_data = geojson_data
        self.scenario_directory_path = scenario_directory_path
        self.system_parameter_path = system_parameter_path

        # placeholders
        self.total_network_pipe_length = 0
        self.autosized_hydraulic_dia = 0
        self.autosized_design_pump_head = 0
        self.autosized_design_flow_rate = 0

    def get_connected_features(self):
        """
        Retrieves a list of connected features from a GeoJSON data object.

        :return: List of connected features with additional information.
        """
        # List thermal connections
        connectors = [
            feature for feature in self.geojson_data["features"] if feature["properties"]["type"] == "ThermalConnector"
        ]

        logger.debug(f"Number of thermal connectors (horizontal pipes): {len(connectors)}")

        if len(connectors) == 0:
            raise ValueError(
                "No thermal connectors (pipes) were found in the GeoJSON data which are required for a thermal network."
            )

        connected_features = [
            feature["properties"].get("endFeatureId")
            for feature in self.geojson_data["features"]
            if feature["properties"].get("endFeatureId") is not None
        ]
        logger.debug(f"Number of features (buildings & GHEs) connected to pipes: {len(connected_features)}")
        # de-dupe connected features, if any
        de_duped_connected_features = list(set(connected_features))
        if len(connected_features) != len(de_duped_connected_features):
            logger.error(f"Number of features connected after de-duplication: {len(de_duped_connected_features)}")
            raise ValueError("Duplicate connections made between buildings. Fix geoJSON file before continuing")

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
                            "geometry": feature["geometry"],
                        }
                    )

        return connected_objects

    @staticmethod
    def reorder_connected_features(features):
        """
        Reorders a list of connected features so that a feature with
        "district_system_type": "Ground Heat Exchanger" is at the beginning.

        :param features: List of connected features.
        :return: Reordered list of connected features.
        :raises ValueError: If no Ground Heat Exchanger feature is found.
        """
        start_loop_index = None

        for i, feature in enumerate(features):
            if feature.get("district_system_type") == "Ground Heat Exchanger":
                start_loop_index = i
                break

        if start_loop_index is None:
            raise ValueError("No Ground Heat Exchanger was found in the list.")

        # Reorder the features list to start with the feature having 'startloop' set to 'true'
        reordered_features = features[start_loop_index:] + features[:start_loop_index]

        return reordered_features

    def find_matching_ghe_id(self, feature_id):
        """
        Find the GHE parameters for a specific GHE ID

        :param feature_id: The ID of the feature to search for.
        :return: The feature ID of the start loop feature, or None if not found.
        """

        for ghe in self.ghe_parameters["borefields"]:
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
            "properties": {"design_flow_rate": 0.01, "design_head": 0},
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
                    "heat_pump": "wahp",
                    "load_side_pump": "ets load-side pump",
                    "source_side_pump": "ets source-side pump",
                    "fan": "fan",
                    "dhw": "dhw",
                    "space_loads_file": new_path,
                }
            elif feature["type"] == "District System" and feature["district_system_type"] == "Ground Heat Exchanger":
                feature_type = "GROUNDHEATEXCHANGER"
                # get ghe parameters for 'borefields' key of system_parameters.json
                matching_ghe = self.find_matching_ghe_id(feature["id"])
                logger.debug(f"matching_ghe: {matching_ghe}\n")

                properties = {
                    "fluid": self.ghe_parameters["fluid"],
                    "grout": self.ghe_parameters["grout"],
                    # soil properties are not exclusive to ghe, they are up one level in the system_parameters.json
                    "soil": self.system_parameters_data["district_system"]["fifth_generation"]["soil"],
                    "pipe": self.ghe_parameters["pipe"],
                    "borehole": self.ghe_parameters["borehole"],
                    "simulation": self.ghe_parameters["simulation"],
                    "design": self.ghe_parameters["design"],
                    "loads": {"ground_loads": []},
                }

                needs_geojson_polygons = False
                if "autosized_birectangle_borefield" in matching_ghe:
                    properties["borefield"] = {
                        **matching_ghe["autosized_birectangle_borefield"],
                        "design_method": "autosized_birectangle_borefield",
                    }
                elif "autosized_birectangle_constrained_borefield" in matching_ghe:
                    properties["borefield"] = {
                        **matching_ghe["autosized_birectangle_constrained_borefield"],
                        "design_method": "autosized_birectangle_constrained_borefield",
                    }
                    needs_geojson_polygons = True
                elif "autosized_rectangle_constrained_borefield" in matching_ghe:
                    properties["borefield"] = {
                        **matching_ghe["autosized_rectangle_constrained_borefield"],
                        "design_method": "autosized_rectangle_constrained_borefield",
                    }
                    needs_geojson_polygons = True
                elif "autosized_bizoned_rectangle_borefield" in matching_ghe:
                    properties["borefield"] = {
                        **matching_ghe["autosized_bizoned_rectangle_borefield"],
                        "design_method": "autosized_bizoned_rectangle_borefield",
                    }
                elif "autosized_near_square_borefield" in matching_ghe:
                    properties["borefield"] = {
                        **matching_ghe["autosized_near_square_borefield"],
                        "design_method": "autosized_near_square_borefield",
                    }
                elif "autosized_rectangle_borefield" in matching_ghe:
                    properties["borefield"] = {
                        **matching_ghe["autosized_rectangle_borefield"],
                        "design_method": "autosized_rectangle_borefield",
                    }
                elif "autosized_rowwise_borefield" in matching_ghe:
                    properties["borefield"] = {
                        **matching_ghe["autosized_rowwise_borefield"],
                        "design_method": "autosized_rowwise_borefield",
                    }
                    needs_geojson_polygons = True
                elif "pre_designed_borefield" in matching_ghe:
                    properties["borefield"] = {
                        **matching_ghe["pre_designed_borefield"],
                        "design_method": "pre_designed_borefield",
                    }
                else:
                    raise ValueError("borefield design method not supported")

                if needs_geojson_polygons:
                    # convert detailed geometry coordinates to meters
                    lat_long_polys = feature["geometry"]["coordinates"]
                    origin_lon_lat = lower_left_point(lat_long_polys[0])
                    convert_factors = meters_to_long_lat_factors(origin_lon_lat)
                    ghe_polygons = []
                    for poly in lat_long_polys:
                        coords = lon_lat_to_polygon(poly, origin_lon_lat, convert_factors)
                        ghe_polygons.append(coords)
                    ghe_polygons = rotate_polygon_to_axes(ghe_polygons)
                    # set geometric constraints to be dictated by the polygons
                    properties["borefield"]["polygons"] = ghe_polygons
            elif feature["type"] == "District System" and (
                any("waste heat source" in s.lower() for s in feature["properties"].get("equipment", []))
            ):
                # This makes waste heat features available in the _loop_order file.
                # TODO: Adjust GHE size due to a waste heat source impacts on loop loads.
                continue
            else:
                raise ValueError(f"feature {feature['type']} not supported")

            converted_features.append(
                {"id": feature["id"], "name": feature["name"], "type": feature_type, "properties": properties}
            )

        return converted_features

    def set_ghe_design_method(self, des_method_str: str) -> None:
        """
        Designate the ghe design method.

        :param des_method_str: design method string
        :returns: zero if successful, nonzero if failure
        :rtype: int
        """

        des_method_str = des_method_str.strip().upper()

        if des_method_str == DesignType.AREAPROPORTIONAL.name:
            self.des_method = DesignType.AREAPROPORTIONAL
        elif des_method_str == DesignType.UPSTREAM.name:
            self.des_method = DesignType.UPSTREAM
        else:
            logger.error(f"Design method '{des_method_str}' not supported.")

    def check_for_existing_component(self, name: str, comp_type_str: str) -> None:
        """
        Checks if a component with the given name and type already exists in the network.

        :param name: The name of the component to check for.
        :param comp_type_str: The type of the component to check for.
        :return: Zero if the component does not exist, nonzero if it does.
        """

        for comp in self.components_data:
            if comp["name"] == name and comp["type"] == comp_type_str:
                logger.error(f'Duplicate {comp_type_str} name "{name}" encountered.')

    def get_component(self, name: str, comp_type: ComponentType):
        """
        Retrieves a component by name and type from a list of component_data dicts.

        :param name: The name of the component to search for.
        :param comp_type: The type of the component to search for.
        :return: A dictionary containing the properties of the component if found, otherwise None.
        """

        for comp in self.components_data:
            if comp["name"] == name and comp_type.name == comp["type"]:
                return comp

        raise ValueError(f'Component not found. Name: "{name}"; Type: "{comp_type.name}".')

    def add_ets_to_network(self, ets_data: dict):
        """
        Adds an Energy Transfer Station (ETS) to the network.

        :param ets_data: information about the ETS
        :return: Zero if successful, nonzero if failure.

        This function modifies the ETS data to include the appropriate
        heat pump, load pump, source pump, and fan components.
        After updating the ETS data, it creates a new ETS object and adds it to the network.

        Returns zero if the ETS is successfully added to the network, or a nonzero value if there is an error.
        """

        logger.debug(f"ETS data: {ets_data}")
        props = ets_data["properties"]
        logger.debug(f"ETS properties: {props}")

        # Read sys param for user-defined values
        sys_param_buildings_data = self.system_parameters_data["buildings"]
        for building in sys_param_buildings_data:
            if building["geojson_id"] == ets_data["id"]:
                props["heat_pump"] = {
                    "id": "",
                    "name": "WAHP",
                    "type": "HEATPUMP",
                    "properties": {
                        "cop_c": building["fifth_gen_ets_parameters"]["cop_heat_pump_cooling"],
                        "cop_h": building["fifth_gen_ets_parameters"]["cop_heat_pump_heating"],
                    },
                }

                props["load_side_pump"] = {
                    "id": "",
                    "name": "ETS LOAD-SIDE PUMP",
                    "type": "PUMP",
                    "properties": {
                        "design_flow_rate": building["fifth_gen_ets_parameters"]["ets_pump_flow_rate"],
                        "design_head": building["fifth_gen_ets_parameters"]["ets_pump_head"],
                    },
                }

                props["source_side_pump"] = {
                    "id": "",
                    "name": "ETS SOURCE-SIDE PUMP",
                    "type": "PUMP",
                    "properties": {
                        "design_flow_rate": building["fifth_gen_ets_parameters"]["ets_pump_flow_rate"],
                        "design_head": building["fifth_gen_ets_parameters"]["ets_pump_head"],
                    },
                }

                props["fan"] = {
                    "id": "",
                    "name": "FAN",
                    "type": "FAN",
                    "properties": {
                        "design_flow_rate": building["fifth_gen_ets_parameters"]["fan_design_flow_rate"],
                        "design_head": building["fifth_gen_ets_parameters"]["fan_design_head"],
                    },
                }

                props["dhw"] = {
                    "id": "",
                    "name": "DHW",
                    "type": "HEATPUMP",
                    "properties": {"cop_dhw": building["fifth_gen_ets_parameters"]["cop_heat_pump_hot_water"]},
                }

                break

        ets_data["properties"] = props
        logger.debug(f"final ets_data: {ets_data}")
        ets = ETS(ets_data)
        logger.info(f"made ETS for: {ets.name.capitalize()}")
        # check size of space loads
        logger.debug(f"length of heating loads: {len(ets.heating_loads)}")
        logger.debug(f"space_loads_file: {props['space_loads_file']}")

        # If any loads aren't hourly for a year, make them so
        if any(len(lst) != HOURS_IN_YEAR for lst in [ets.heating_loads, ets.cooling_loads, ets.dhw_loads]):
            self.make_loads_hourly(ets_data["properties"], ets)

        # Append to network
        self.network.append(ets)

    @staticmethod
    def make_loads_hourly(properties: dict, ets: ETS):
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
        space_loads_df = space_loads_df.resample("h").interpolate(method="linear")
        # keep only HOURS_IN_YEAR
        space_loads_df = space_loads_df.iloc[:HOURS_IN_YEAR]
        ets.heating_loads = space_loads_df["TotalHeatingSensibleLoad"]
        ets.cooling_loads = space_loads_df["TotalCoolingSensibleLoad"]
        ets.dhw_loads = space_loads_df["TotalWaterHeating"]
        logger.warning(f"NEW length of heating loads: {len(ets.heating_loads)}")
        return ets

    def add_ghe_to_network(self, ghe_data: dict) -> None:
        """
        Adds a Ground Heat Exchanger (GHE) to the network.

        :param ghe_data: information about the GHE
        :return: Zero if successful, nonzero if failure.

        This function creates a new GHE object and adds it to the network.
        """

        ghe = GHE(ghe_data)
        self.network.append(ghe)

    def add_pump_to_network(self, pump_data: dict) -> None:
        """
        Adds a Pump to the network.

        :param pump_data: information about the pump
        :return: Zero if successful, nonzero if failure.

        This function creates a new Pump object and adds it to the network.
        """

        pump = Pump(pump_data)
        self.network.append(pump)

    def add_waste_heat_sources(self, total_network_loads):
        """
        Adjusts the total loads to account for any waste heat sources.

        :param total_network_loads: The total network loads before accounting for waste heat.
        :return: Adjusted total network loads accounting for waste heat.
        """
        # there are 2 ways of specifying waste heat. One is constant value, the other is a timeseries file
        # handle both cases. All values assumed to be in Watts

        # find data in the system parameters file
        sys_param_heat_params = (
            self.system_parameters_data.get("district_system", {})
            .get("fifth_generation", {})
            .get("heat_source_parameters", [])
        )

        if sys_param_heat_params is None or len(sys_param_heat_params) == 0:
            # nothing to do
            logger.info("No heat source parameters found in the system parameters; proceeding without waste heat sources.")
            return total_network_loads

        # find heat_source_rate in sys_params_heat_params
        # TODO: is it correct to look in first element only? could there be more elements here?
        heat_source_rate = sys_param_heat_params[0].get("heat_source_rate", None)
        if heat_source_rate is None:
            logger.warning(
                "Waste heat source rate is not provided. Please provide a value or schedule "
                "for the waste heat source if you want to consider it in the sizing."
            )
            return total_network_loads

        logger.info(f"Found waste heat source rate: {heat_source_rate}")
        # determine if rate is a number or a file.
        # the path is expected to be related to the system parameter file location
        if heat_source_rate.endswith(".mos"):
            logger.debug("heat source rate parameter is a path; loading values from file")
            heat_source_rate_filepath = self.system_parameter_path.parent / heat_source_rate

            # load the mos file and get the waste heat data
            # don't assume that the loads in this file are hourly (may need interpolation).
            mos_file = ModelicaMOS(heat_source_rate_filepath)
            print(f"mos_file.data :\n{mos_file.data}")
            # Data is in mos_file.data. Expecting first column to be timestamps in seconds
            # and second column being heat in Watts
            waste_heat_df = pd.DataFrame(mos_file.data)
            waste_heat_df.columns = ["Time_s", "Waste_Heat_W"]
            waste_heat_df["Date Time"] = pd.to_datetime(waste_heat_df["Time_s"], unit="s")
            waste_heat_df = waste_heat_df.set_index("Date Time")

            # Make sure that last timestamp (in seconds) goes to end of year (31536000 seconds)
            # if not, copy last Watts value to a new timestamp representing end of year
            if waste_heat_df["Time_s"].iloc[-1] < 31536000:
                new_date = pd.to_datetime(31536000, unit="s")
                new_data = pd.DataFrame(
                    {"Waste_Heat_W": [waste_heat_df["Waste_Heat_W"].iloc[-1]]},
                    index=[new_date],
                    columns=["Waste_Heat_W"],
                )
                waste_heat_df = pd.concat([waste_heat_df, new_data])

            # Interpolate data to hourly
            waste_heat_df = waste_heat_df.resample("h").interpolate(method="linear")
            # keep only HOURS_IN_YEAR
            waste_heat_df = waste_heat_df.iloc[:HOURS_IN_YEAR]
            logger.debug(f"length of waste heat: {len(waste_heat_df)}")
            waste_heat_addition = waste_heat_df["Waste_Heat_W"].to_numpy()

            # Store original loads for comparison
            original_heating_loads = total_network_loads.copy()

            # Adjust the heating loads by subtracting the waste heat addition
            total_network_loads = np.maximum(total_network_loads - waste_heat_addition, 0)

            # Log comparison statistics (temporary)
            total_reduction = np.sum(original_heating_loads) - np.sum(total_network_loads)
            max_reduction = np.max(original_heating_loads - total_network_loads)
            avg_reduction = np.mean(original_heating_loads - total_network_loads)
            logger.info(
                f"Waste heat impact: Total reduction={total_reduction:.2f} W, "
                f"Max hourly reduction={max_reduction:.2f} W, Avg hourly reduction={avg_reduction:.2f} W"
            )
        else:
            try:
                logger.debug("heat source rate parameter is a number; applying constant to heating loads")
                waste_heat_addition = float(heat_source_rate)

                # Store original loads for comparison
                original_heating_loads = total_network_loads.copy()

                # Adjust the heating loads by subtracting the waste heat addition
                total_network_loads = np.maximum(total_network_loads - waste_heat_addition, 0)

                # Log comparison statistics
                total_reduction = np.sum(original_heating_loads) - np.sum(total_network_loads)
                hours_affected = np.sum(original_heating_loads > waste_heat_addition)
                logger.info(
                    f"Constant waste heat impact: Total reduction={total_reduction:.2f} W-hr, "
                    f"Constant reduction={waste_heat_addition} W, Hours with heating "
                    f"needed={hours_affected}/{len(total_network_loads)}"
                )
            except ValueError:
                # heat_source_rate is not a valid number, do nothing and return
                logger.error(
                    "Waste heat source rate is not a valid number.Please provide a valid value or schedule file."
                )
                return total_network_loads

        logger.info("Adjusted total loads to account for waste heat sources.")
        return total_network_loads

    def size_area_proportional(self, output_path: Path) -> None:
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
            if device.comp_type == ComponentType.GROUNDHEATEXCHANGER:
                ghe_indexes.append(i)
            else:
                other_indexes.append(i)

        total_ghe_area = 0
        for i in ghe_indexes:
            ghe_area = self.network[i].area
            total_ghe_area += ghe_area

        # Initialize an array to store the summed loads for each hour of the year
        total_network_loads = np.zeros(HOURS_IN_YEAR)

        for comp in self.network:
            if comp.comp_type is not ComponentType.GROUNDHEATEXCHANGER:
                total_network_loads += comp.get_loads()

        # add waste heat source impacts on loads here
        total_network_loads = self.add_waste_heat_sources(total_network_loads)

        network_load_per_area = total_network_loads / total_ghe_area

        # loop over GHEs and size per area
        for i in ghe_indexes:
            ghe_area = self.network[i].area
            self.network[i].json_data["loads"]["ground_loads"] = np.array(network_load_per_area) * ghe_area
            self.network[i].size(output_path)

    def size_to_upstream_equipment(self, output_path: Path) -> None:
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

        ghe_indexes = []

        for i, device in enumerate(self.network):
            if device.comp_type == ComponentType.GROUNDHEATEXCHANGER:
                ghe_indexes.append(i)

        # slice the self.network by ghe_indexes
        for i, ghe_index in enumerate(ghe_indexes):
            if i == 0:  # first GHE
                devices_before_ghe = self.network[:ghe_index]
            else:
                devices_before_ghe = self.network[ghe_indexes[i - 1] + 1 : ghe_index]

            # Initialize an array to store the summed network loads for each hour of the year
            ghe_load = np.zeros(HOURS_IN_YEAR)
            for device in devices_before_ghe:
                ghe_load += device.get_loads()
            # TODO: do we need to add the waste heat source impacts on loads for this method?
            self.network[ghe_index].json_data["loads"]["ground_loads"] = ghe_load

            # call size() with total load
            self.network[ghe_index].size(output_path)

    def size_ghe(self, output_path: Path) -> None:
        """
        High-level sizing call that handles any lower-level calls or iterations.
        """
        logger.debug("Choosing sizing method...")
        if self.des_method == DesignType.AREAPROPORTIONAL:
            self.size_area_proportional(output_path)
        elif self.des_method == DesignType.UPSTREAM:
            self.size_to_upstream_equipment(output_path)
        else:
            msg = f"Unsupported design method {self.des_method}"
            logger.error(msg)
            raise ValueError(msg)

    def size_network(self, system_parameter_path: Path):
        sys_params = load_json(system_parameter_path)
        dist_sys_params = sys_params["district_system"]["fifth_generation"]
        ghe_params = dist_sys_params["ghe_parameters"]
        pipe_params = dist_sys_params["horizontal_piping_parameters"]

        max_num_boreholes = 0

        for i, device in enumerate(self.network):
            if device.comp_type == ComponentType.GROUNDHEATEXCHANGER:
                max_num_boreholes = max(device.nbh, max_num_boreholes)

        bh_vol_flow_lps = ghe_params["design"]["flow_rate"]
        network_design_vol_flow = lps_to_cms(bh_vol_flow_lps) * max_num_boreholes
        network_pipe = Pipe(
            dimension_ratio=pipe_params["diameter_ratio"],
            length=self.total_network_pipe_length,
            fluid_type_str=ghe_params["fluid"]["fluid_name"],
            fluid_concentration=ghe_params["fluid"]["concentration_percent"],
            fluid_temperature=ghe_params["fluid"]["temperature"],
        )

        # Pa/m, defaults to 300 if not in sys_params
        design_pressure_loss_per_length = dist_sys_params["horizontal_piping_parameters"].get(
            "pressure_drop_per_meter", 300
        )

        self.autosized_hydraulic_dia = network_pipe.size_hydraulic_diameter(
            network_design_vol_flow, design_pressure_loss_per_length
        )
        self.autosized_design_pump_head = network_pipe.pressure_loss(network_design_vol_flow)
        self.autosized_design_flow_rate = network_design_vol_flow

    def update_sys_params(self, system_parameter_path: Path, output_directory_path: Path) -> None:
        """
        Update the existing system parameters file with sizing data.

        :param system_parameter_path: Path to the existing System Parameter file.
        :param output_directory_path: Path to the output directory containing the GHEDesigner output files.

        This function loads the existing system parameters from the specified file,
        updates the GHE-specific parameters, with the new data from the GHEDesigner output, updates the pipe
        and pump parameters with autosized flow and pressures, and saves the updated
        system parameters back to the same file.

        - The GHE-specific parameters include the length of the boreholes and the number of boreholes.
        - Pump parameters include the design head and design flow rate
        - Pipe parameters include the hydraulic diameter

        The function does not return any value, as it updates the system parameters file in place.

        :return: None
        """

        # Load the existing system parameters
        sys_params = load_json(system_parameter_path)
        dist_sys_params = sys_params["district_system"]["fifth_generation"]
        pipe_params = dist_sys_params["horizontal_piping_parameters"]
        pump_params = dist_sys_params["central_pump_parameters"]

        for i, device in enumerate(self.network):
            if (
                device.comp_type == ComponentType.GROUNDHEATEXCHANGER
                and device.design_method != GHEDesignType.PRE_DESIGNED_BOREFIELD
            ):
                for idx_ghe, ghe in enumerate(
                    sys_params["district_system"]["fifth_generation"]["ghe_parameters"]["borefields"]
                ):
                    if ghe["ghe_id"] == device.id:
                        design_key = device.design_method.name.lower()
                        sys_params["district_system"]["fifth_generation"]["ghe_parameters"]["borefields"][idx_ghe][
                            design_key
                        ]["borehole_length"] = device.bh_length
                        sys_params["district_system"]["fifth_generation"]["ghe_parameters"]["borefields"][idx_ghe][
                            design_key
                        ]["number_of_boreholes"] = device.nbh

        if pipe_params.get("hydraulic_diameter_autosized"):
            sys_params["district_system"]["fifth_generation"]["horizontal_piping_parameters"]["hydraulic_diameter"] = (
                self.autosized_hydraulic_dia
            )

        if pump_params.get("pump_design_head_autosized"):
            pump_params["pump_design_head"] = sys_params["district_system"]["fifth_generation"][
                "central_pump_parameters"
            ]["pump_design_head"] = self.autosized_design_pump_head

        if pump_params.get("pump_flow_rate_autosized"):
            pump_params["pump_flow_rate"] = sys_params["district_system"]["fifth_generation"][
                "central_pump_parameters"
            ]["pump_flow_rate"] = self.autosized_design_flow_rate

        write_json(system_parameter_path, sys_params)


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

    geojson_data = load_json(geojson_file_path)

    # Check if the file exists
    if not system_parameter_path.exists():
        logger.warning(f"No system_parameter.json file found at {system_parameter_path}, aborting.")
        return 1

    system_parameters_data = load_json(system_parameter_path)
    ghe_parameters_data: dict = system_parameters_data["district_system"]["fifth_generation"]["ghe_parameters"]

    # Downselect the buildings in the geojson that are in the system parameters file

    # List the building ids from the system parameters file
    sys_param_building_ids = []
    for building in system_parameters_data["buildings"]:
        sys_param_building_ids.append(building["geojson_id"])

    # Select the buildings in the geojson that are in the system parameters file
    building_features = [feature for feature in geojson_data["features"] if feature["properties"]["type"] == "Building"]

    geojson_feature_ids = [feature["properties"]["id"] for feature in building_features]

    if len(building_features) == 0:
        logger.error(
            'No buildings found. Ensure the GeoJSON "Feature" "id" keys match the system \n'
            'parameter file "geojson_id" key values for the respective buildings.'
        )

    if set(sys_param_building_ids) != set(geojson_feature_ids):
        logger.error(
            'Building entries in the GeoJSON "Feature" "id" keys do not match the system \n'
            'parameter file "geojson_id" key values for the respective buildings.'
        )

    # Rebuild the geojson data using only the buildings in the system parameters file
    # Put in everything that isn't a building
    geojson_data["features"] = [
        feature for feature in geojson_data["features"] if feature["properties"]["type"] != "Building"
    ]
    # Only add the buildings in the system parameters file back to the geojson data
    # This has the effect of removing buildings that are not in the system parameters file
    geojson_data["features"].extend(building_features)

    # load all input data
    sys_param_version: str = ghe_parameters_data["version"]
    if version("thermalnetwork")[:3] != sys_param_version[:3]:  # Just major & minor, ignore patch version
        logger.warning(
            f"The system_parameter.json version is {sys_param_version}, but the ThermalNetwork version is "
            f"{version('thermalnetwork')}. Could be a problem."
        )

    ghe_design_data: dict = ghe_parameters_data["design"]
    logger.debug(f"{ghe_design_data=}")
    # instantiate a new Network object
    network = Network(
        system_parameters_data, geojson_data, ghe_parameters_data, scenario_directory_path, system_parameter_path
    )

    # get network list from geojson
    connected_features = network.get_connected_features()
    logger.debug(f"Features in district loop: {connected_features}\n")

    reordered_features = network.reorder_connected_features(connected_features)
    logger.debug(f"Features in loop order: {reordered_features}\n")

    total_network_length = 0
    for idx_f, f in enumerate(geojson_data["features"]):
        if "total_length" in f["properties"]:
            total_network_length += f["properties"]["total_length"]

    network.total_network_pipe_length = total_network_length

    loop_order_list = []
    feature_group = defaultdict(list)

    # Source type to field name
    source_types = {
        "Ground Heat Exchanger": "list_ghe_ids_in_group",
        "Central Ambient Water": "list_source_ids_in_group",
    }

    def strip_and_order(group_dict):
        """Only include non-empty lists, with list_bldg_ids_in_group as the first key if present"""
        keys = []
        if group_dict.get("list_bldg_ids_in_group"):
            keys.append("list_bldg_ids_in_group")
        if group_dict.get("list_ghe_ids_in_group"):
            keys.append("list_ghe_ids_in_group")
        if group_dict.get("list_source_ids_in_group"):
            keys.append("list_source_ids_in_group")
        return OrderedDict((k, group_dict[k]) for k in keys)

    def group_has_required_data(group):
        """Check if the group has at least one source and one building."""
        has_buildings = bool(group["list_bldg_ids_in_group"])
        has_any_source = bool(group["list_ghe_ids_in_group"] or group["list_source_ids_in_group"])
        return has_buildings and has_any_source

    for feature in reordered_features:
        district_type = feature["district_system_type"]

        if district_type in source_types:
            # If this starts a new group (previous group had buildings), close it
            if group_has_required_data(feature_group):
                loop_order_list.append(strip_and_order(feature_group))
                feature_group = defaultdict(list)
            feature_group[source_types[district_type]].append(feature["id"])
        else:
            # buildings are always added to the current group
            feature_group["list_bldg_ids_in_group"].append(feature["id"])

    # Finish last group if valid
    if group_has_required_data(feature_group):
        loop_order_list.append(strip_and_order(feature_group))

    # save loop order to file next to sys-params for temporary use by the GMT
    # Prepending an underscore to emphasize these as temporary files not for human use
    loop_order_filepath = system_parameter_path.parent.resolve() / "_loop_order.json"
    write_json(loop_order_filepath, loop_order_list)

    # convert geojson type "Building","District System" to "ENERGYTRANSFERSTATION",
    network_data: list[dict] = network.convert_features(connected_features)

    # begin populating structures in preparation for sizing
    network.set_ghe_design_method(des_method_str=ghe_design_data["method"])

    for component in network_data:
        comp_type_str = str(component["type"]).strip().upper()
        if comp_type_str == ComponentType.ENERGYTRANSFERSTATION.name:
            network.add_ets_to_network(component)
        elif comp_type_str == ComponentType.GROUNDHEATEXCHANGER.name:
            network.add_ghe_to_network(component)
        elif comp_type_str == ComponentType.PUMP.name:
            network.add_pump_to_network(component)
        else:
            logger.error(f"Unsupported component type, {comp_type_str}")

    # This is the call to GHED, which takes the most time.
    network.size_ghe(output_directory_path)
    network.size_network(system_parameter_path)
    network.update_sys_params(system_parameter_path, output_directory_path)

    logger.info("\nSizing completed successfully.")

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

    logger.debug(f"{system_parameter_file=}")
    logger.debug(f"{scenario_directory=}")
    logger.debug(f"{geojson_file=}")
    logger.debug(f"{output_directory=}")

    if not output_directory.exists():
        logger.info("Output path does not exist. attempting to create")
        output_directory.mkdir(parents=True, exist_ok=True)

    return run_sizer_from_cli_worker(system_parameter_file, scenario_directory, geojson_file, output_directory)


if __name__ == "__main__":
    sys.exit(run_sizer_from_cli())
