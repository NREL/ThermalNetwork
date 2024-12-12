import logging
import os
import shutil
from pathlib import Path

import pandas as pd
from ghedesigner.manager import GHEManager
from rich.logging import RichHandler

from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType
from thermalnetwork.geometry import polygon_area

logging.basicConfig(level=logging.DEBUG, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
logger = logging.getLogger(__name__)


class GHE(BaseComponent):
    def __init__(self, data: dict) -> None:
        super().__init__(data["name"], ComponentType.GROUNDHEATEXCHANGER)
        # design_file = data['design_file']
        self.json_data = data["properties"]
        # with open(design_file) as f:
        #    self.json_data = json.load(f)
        # compute Area
        self.id = data["id"]
        if "polygons" in self.json_data["geometric_constraints"]:
            bound_area = polygon_area(self.json_data["geometric_constraints"]["polygons"][0])
            if bound_area < 0:  # clockwise polygon; reverse for GHE Designer
                self.json_data["geometric_constraints"]["polygons"][0].reverse()
            self.area = abs(bound_area)
            for i, hole_poly in enumerate(self.json_data["geometric_constraints"]["polygons"][1:]):
                hole_area = polygon_area(hole_poly)
                if hole_area < 0:  # clockwise polygon; reverse for GHE Designer
                    self.json_data["geometric_constraints"]["polygons"][i + 1].reverse()
                self.area -= abs(hole_area)
        else:
            length = self.json_data["geometric_constraints"]["length"]
            width = self.json_data["geometric_constraints"]["width"]
            self.area = length * width

    def ghe_size(self, total_space_loads, output_path: Path) -> float:
        logger.info(f"GHE_SIZE with total_space_loads: {total_space_loads}")
        ghe = GHEManager()
        ghe.set_single_u_tube_pipe(
            inner_diameter=self.json_data["pipe"]["inner_diameter"],
            outer_diameter=self.json_data["pipe"]["outer_diameter"],
            shank_spacing=self.json_data["pipe"]["shank_spacing"],
            roughness=self.json_data["pipe"]["roughness"],
            conductivity=self.json_data["pipe"]["conductivity"],
            rho_cp=self.json_data["pipe"]["rho_cp"],
        )
        ghe.set_soil(
            conductivity=self.json_data["soil"]["conductivity"],
            rho_cp=self.json_data["soil"]["rho_cp"],
            undisturbed_temp=self.json_data["soil"]["undisturbed_temp"],
        )
        ghe.set_grout(conductivity=self.json_data["grout"]["conductivity"], rho_cp=self.json_data["grout"]["rho_cp"])
        ghe.set_fluid()
        ghe.set_borehole(
            height=self.json_data["geometric_constraints"]["max_height"],
            # Assuming max height is the height of the borehole
            buried_depth=self.json_data["borehole"]["buried_depth"],
            diameter=self.json_data["borehole"]["diameter"],
        )
        ghe.set_simulation_parameters(
            num_months=self.json_data["simulation"]["num_months"],
            max_eft=self.json_data["design"]["max_eft"],
            min_eft=self.json_data["design"]["min_eft"],
            max_height=self.json_data["geometric_constraints"]["max_height"],
            min_height=self.json_data["geometric_constraints"]["min_height"],
            continue_if_design_unmet=True,
            max_boreholes=2500,
        )
        ghe.set_ground_loads_from_hourly_list(self.json_data["loads"]["ground_loads"])
        if "polygons" in self.json_data["geometric_constraints"]:
            ghe.set_geometry_constraints_bi_rectangle_constrained(
                property_boundary=self.json_data["geometric_constraints"]["polygons"][0],
                no_go_boundaries=self.json_data["geometric_constraints"]["polygons"][1:],
                b_min=self.json_data["geometric_constraints"]["b_min"],
                b_max_x=self.json_data["geometric_constraints"]["b_max"],
                b_max_y=self.json_data["geometric_constraints"]["b_max"],
            )
        else:
            ghe.set_geometry_constraints_rectangle(
                length=self.json_data["geometric_constraints"]["length"],
                width=self.json_data["geometric_constraints"]["width"],
                b_min=self.json_data["geometric_constraints"]["b_min"],
                b_max=self.json_data["geometric_constraints"]["b_max"],
            )
        ghe.set_design(
            flow_rate=self.json_data["design"]["flow_rate"], flow_type_str=self.json_data["design"]["flow_type"]
        )

        output_file_directory = output_path / self.id

        # Check if the directory exists and delete it if so
        if output_file_directory.is_dir():
            logger.debug(f"deleting directory: {output_file_directory}")
            shutil.rmtree(output_file_directory)

        # Create the subdirectory
        logger.debug(f"creating directory: {output_file_directory}")
        output_file_directory.mkdir(parents=True)

        ground_loads_df = pd.DataFrame(self.json_data["loads"]["ground_loads"])
        file_name = output_file_directory / "ground_loads.csv"
        logger.info(f"saving loads to: {file_name}")
        ground_loads_df.to_csv(file_name, index=False)
        logger.debug("loads saved to csv file")

        ghe.find_design()
        logger.debug("design found")
        ghe.prepare_results("Project Name", "Notes", "Author", "Iteration Name")
        logger.debug("results prepared for writing to output directory")

        ghe.write_output_files(output_file_directory, "")
        logger.debug("output written to output directory")
        u_tube_height = ghe.results.output_dict["ghe_system"]["active_borehole_length"]["value"]
        # selected_coordinates = ghe.results.borehole_location_data_rows  # includes a header row
        logger.debug("Done writing output")
        return u_tube_height

    def get_atlanta_loads(self) -> list[float]:
        # read in the csv file and convert the loads to a list of length 8760
        current_file_directory = Path(os.path.dirname(os.path.abspath(__file__)))
        glhe_json_data = current_file_directory / "test_data" / "Atlanta_Office_Building_Loads.csv"
        raw_lines = glhe_json_data.read_text().split("\n")
        return [float(x) for x in raw_lines[1:] if x.strip() != ""]
