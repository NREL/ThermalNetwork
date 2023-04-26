from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType
from ghedesigner.manager import GHEManager
import os
from pathlib import Path
from typing import List
import shutil 

class GHE(BaseComponent):
    def __init__(self, data: dict) -> None:
        super().__init__(data['name'], ComponentType.GROUNDHEATEXCHANGER)
        props = data['properties']
        self.length = props['length']
        self.width = props['width']
        self.area = self.length * self.width

    def ghe_size(self, total_space_loads) -> float:
        print(f"GHE_SIZE with total_space_loads: {total_space_loads}")
        ghe = GHEManager()
        ghe.set_single_u_tube_pipe(
            inner_diameter=0.0216, outer_diameter=0.02667, shank_spacing=0.0323,
            roughness=1.0e-6, conductivity=0.4, rho_cp=1542000.0)
        ghe.set_soil(conductivity=2.0, rho_cp=2343493.0, undisturbed_temp=18.3)
        ghe.set_grout(conductivity=1.0, rho_cp=3901000.0)
        ghe.set_fluid()
        ghe.set_borehole(height=96.0, buried_depth=2.0, diameter=0.150)
        ghe.set_simulation_parameters(num_months=240, max_eft=35, min_eft=5, max_height=135, min_height=60)
        ghe.set_ground_loads_from_hourly_list(self.get_atlanta_loads())
        ghe.set_geometry_constraints_rectangle(length=85.0, width=36.5, b_min=3.0, b_max=10.0)
        ghe.set_design(flow_rate=0.2, flow_type_str="borehole")
        ghe.find_design()
        ghe.prepare_results("Project Name", "Notes", "Author", "Iteration Name")

        # Construct the path to the new subdirectory
        current_file_directory = Path(os.path.dirname(os.path.abspath(__file__)))
        output_file_directory = current_file_directory / self.name

        # Check if the directory exists and delete it if so
        if output_file_directory.is_dir():
            print(f"deleting directory: {output_file_directory}")
            shutil.rmtree(output_file_directory)

        # Create the subdirectory
        print(f"creating directory: {output_file_directory}")
        output_file_directory.mkdir(parents=True)

        ghe.write_output_files(output_file_directory, "")
        u_tube_height = ghe.results.output_dict['ghe_system']['active_borehole_length']['value']
        selected_coordinates = ghe.results.borehole_location_data_rows  # includes a header row
        return u_tube_height

    def get_atlanta_loads(self) -> List[float]:
        # read in the csv file and convert the loads to a list of length 8760
        current_file_directory = Path(os.path.dirname(os.path.abspath(__file__)))
        glhe_json_data = current_file_directory / 'Atlanta_loads/Atlanta_Office_Building_Loads.csv'
        raw_lines = glhe_json_data.read_text().split('\n')
        return [float(x) for x in raw_lines[1:] if x.strip() != '']
