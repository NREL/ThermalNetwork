import os
import shutil
from pathlib import Path
from typing import List

from ghedesigner.manager import GHEManager

from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType


class GHE(BaseComponent):
    def __init__(self, data: dict) -> None:
        super().__init__(data['name'], ComponentType.GROUNDHEATEXCHANGER)
        # design_file = data['design_file']
        self.json_data = data['properties']
        # with open(design_file) as f:
        #    self.json_data = json.load(f)
        # compute Area
        self.area = self.json_data['geometric_constraints']['length'] * self.json_data['geometric_constraints']['width']

    def ghe_size(self, total_space_loads, output_path: Path) -> float:
        print(f"GHE_SIZE with total_space_loads: {total_space_loads}")
        ghe = GHEManager()
        ghe.set_single_u_tube_pipe(
            inner_diameter=self.json_data['pipe']['inner_diameter'],
            outer_diameter=self.json_data['pipe']['outer_diameter'],
            shank_spacing=self.json_data['pipe']['shank_spacing'],
            roughness=self.json_data['pipe']['roughness'],
            conductivity=self.json_data['pipe']['conductivity'],
            rho_cp=self.json_data['pipe']['rho_cp'])
        ghe.set_soil(
            conductivity=self.json_data['soil']['conductivity'],
            rho_cp=self.json_data['soil']['rho_cp'],
            undisturbed_temp=self.json_data['soil']['undisturbed_temp'])
        ghe.set_grout(
            conductivity=self.json_data['grout']['conductivity'],
            rho_cp=self.json_data['grout']['rho_cp'])
        ghe.set_fluid()
        ghe.set_borehole(
            height=self.json_data['geometric_constraints']['max_height'],
            # Assuming max height is the height of the borehole
            buried_depth=self.json_data['borehole']['buried_depth'],
            diameter=self.json_data['borehole']['diameter'])
        ghe.set_simulation_parameters(
            num_months=self.json_data['simulation']['num_months'],
            max_eft=self.json_data['design']['max_eft'],
            min_eft=self.json_data['design']['min_eft'],
            max_height=self.json_data['geometric_constraints']['max_height'],
            min_height=self.json_data['geometric_constraints']['min_height'])
        ghe.set_ground_loads_from_hourly_list(self.json_data['loads']['ground_loads'])
        ghe.set_geometry_constraints_rectangle(
            length=self.json_data['geometric_constraints']['length'],
            width=self.json_data['geometric_constraints']['width'],
            b_min=self.json_data['geometric_constraints']['b_min'],
            b_max=self.json_data['geometric_constraints']['b_max'])
        ghe.set_design(
            flow_rate=self.json_data['design']['flow_rate'],
            flow_type_str=self.json_data['design']['flow_type'])

        ghe.find_design()
        ghe.prepare_results("Project Name", "Notes", "Author", "Iteration Name")

        # Construct the path to the new subdirectory
        # current_file_directory = Path(os.path.dirname(os.path.abspath(__file__)))
        # output_file_directory = current_file_directory / self.name
        output_file_directory = output_path / self.name

        # Check if the directory exists and delete it if so
        if output_file_directory.is_dir():
            print(f"deleting directory: {output_file_directory}")
            shutil.rmtree(output_file_directory)

        # Create the subdirectory
        print(f"creating directory: {output_file_directory}")
        output_file_directory.mkdir(parents=True)

        ghe.write_output_files(output_file_directory, "")
        u_tube_height = ghe.results.output_dict['ghe_system']['active_borehole_length']['value']
        # selected_coordinates = ghe.results.borehole_location_data_rows  # includes a header row
        return u_tube_height

    def get_atlanta_loads(self) -> List[float]:
        # read in the csv file and convert the loads to a list of length 8760
        current_file_directory = Path(os.path.dirname(os.path.abspath(__file__)))
        glhe_json_data = current_file_directory / 'Atlanta_loads/Atlanta_Office_Building_Loads.csv'
        raw_lines = glhe_json_data.read_text().split('\n')
        return [float(x) for x in raw_lines[1:] if x.strip() != '']
