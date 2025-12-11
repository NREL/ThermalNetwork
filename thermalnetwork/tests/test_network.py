import pytest

from thermalnetwork.enums import GHEDesignType
from thermalnetwork.network import run_sizer_from_cli, run_sizer_from_cli_worker
from thermalnetwork.tests.test_base import BaseCase
from thermalnetwork.utilities import load_json


class TestNetwork(BaseCase):
    def check_horiz_pipe_params(self, sys_param: dict, expected_hydraulic_dia: float):
        self.assertAlmostEqual(
            sys_param["district_system"]["fifth_generation"]["horizontal_piping_parameters"]["hydraulic_diameter"],
            expected_hydraulic_dia,
            delta=0.0001,
        )

    def check_pump_params(self, sys_param: dict, expected_pump_head: float, expected_flow_rate: float):
        self.assertAlmostEqual(
            sys_param["district_system"]["fifth_generation"]["central_pump_parameters"]["pump_design_head"],
            expected_pump_head,
            delta=1,
        )

        self.assertAlmostEqual(
            sys_param["district_system"]["fifth_generation"]["central_pump_parameters"]["pump_flow_rate"],
            expected_flow_rate,
            delta=0.01,
        )

    @staticmethod
    def get_ghe_design_key(ghe_data):
        possible_methods = [x.name.lower() for x in GHEDesignType]
        for k in possible_methods:
            if k in ghe_data:
                return k

        raise ValueError("ghe design key not found")

    def check_ghe_data(self, sys_param: dict, expected_ghe_data: dict):
        ghe_data = sys_param["district_system"]["fifth_generation"]["ghe_parameters"]["borefields"]
        for ghe in ghe_data:
            for k_expected, v_expected in expected_ghe_data.items():
                if ghe["ghe_id"] == k_expected:
                    design_key = self.get_ghe_design_key(ghe)
                    self.assertAlmostEqual(ghe[design_key]["borehole_length"], v_expected["length"], delta=0.1)

                    if "number_of_boreholes" in ghe[design_key]:
                        self.assertEqual(ghe[design_key]["number_of_boreholes"], v_expected["num_bh"])
                    else:
                        self.assertEqual(len(ghe[design_key]["borehole_x_coordinates"]), v_expected["num_bh"])

    def test_cli(self):
        output_path = self.test_outputs_path.resolve() / "cli_test"

        # -- Act
        # run subprocess as if we're an end-user
        res = self.runner.invoke(
            run_sizer_from_cli,
            [
                "-y",
                self.sys_param_path_1_ghe_detailed_geometry,
                "-s",
                self.scenario_directory_path_1_ghe,
                "-f",
                self.geojson_path_1_ghe,
                "-o",
                output_path,
            ],
        )

        # -- Assert
        assert res.exit_code == 0

        updated_sys_param = load_json(self.sys_param_path_1_ghe_detailed_geometry)

        expected_hydraulic_dia = 0.1156
        expected_pump_head = 164_720
        expected_flow_rate = 0.018

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {"8c369df2-18e9-439a-8c25-875851c5aaf0": {"num_bh": 36, "length": 128.2}}
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

        # -- Clean up
        # If any assertion fails, this will not run. Useful for debugging, as long as you don't get confused.
        self.reset_sys_param(self.sys_param_path_1_ghe_detailed_geometry)

    def test_waste_heat(self):
        # Check if waste heat demo files are available and log detailed error if not
        if not self.waste_heat_demo_available:
            missing_files = []
            if not self.waste_heat_geojson_path.exists():
                missing_files.append(str(self.waste_heat_geojson_path))
            if not self.waste_heat_sys_params_path.exists():
                missing_files.append(str(self.waste_heat_sys_params_path))
            if not self.waste_heat_scenario_path.exists():
                missing_files.append(str(self.waste_heat_scenario_path))

            error_msg = "Waste heat test cannot run: Missing required demo files:\n" + "\n".join(
                f"  - {file}" for file in missing_files
            )
            print(error_msg)
            self.fail(error_msg)

        output_path = self.test_outputs_path.resolve() / "waste_heat_test"

        # -- Act
        # run subprocess as if we're an end-user
        res = self.runner.invoke(
            run_sizer_from_cli,
            [
                "-y",
                self.waste_heat_sys_params_path,
                "-s",
                self.waste_heat_scenario_path,
                "-f",
                self.waste_heat_geojson_path,
                "-o",
                output_path,
            ],
        )
        print(res.output)
        # -- Assert
        assert res.exit_code == 0, f"CLI failed with exit code {res.exit_code}, output: {res.output}"

        # assert there is a loop order file saved next to the sys-param file
        loop_order_file = self.waste_heat_sys_params_path.parent / "_loop_order.json"
        assert loop_order_file.exists()

        # same path as the original path
        updated_sys_param = load_json(self.waste_heat_sys_params_path)

        expected_ghe_data = {"0b575a8f-97d1-47e6-b329-7ef7566d26f2": {"num_bh": 180, "length": 127.1}}
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

        # -- Clean up
        # If any assertion fails, this will not run. Useful for debugging, as long as you don't get confused.
        self.reset_sys_param(self.waste_heat_sys_params_path)
        # remove loop order file
        if loop_order_file.exists():
            loop_order_file.unlink()

    @pytest.mark.skip(reason="Skip until GHED improves ROWWISE autosizing technique")
    def test_network_one_ghe(self):
        # -- Set up
        output_path = self.test_outputs_path / "one_ghe"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        res = run_sizer_from_cli_worker(
            self.sys_param_path_1_ghe,
            self.scenario_directory_path_1_ghe,
            self.geojson_path_1_ghe,
            output_path,
        )

        assert res == 0

        updated_sys_param = load_json(self.sys_param_path_1_ghe)

        expected_hydraulic_dia = 0.13767
        expected_pump_head = 128704
        expected_flow_rate = 0.025

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {"8c369df2-18e9-439a-8c25-875851c5aaf0": {"num_bh": 50, "length": 89.8}}
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

        # -- Clean up
        self.reset_sys_param(self.sys_param_path_1_ghe)

    def test_network_one_ghe_detailed_geometry(self):
        # -- Set up
        output_path = self.test_outputs_path / "one_ghe_detailed_geo"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        res = run_sizer_from_cli_worker(
            self.sys_param_path_1_ghe_detailed_geometry,
            self.scenario_directory_path_1_ghe,
            self.geojson_path_1_ghe,
            output_path,
        )

        assert res == 0
        updated_sys_param = load_json(self.sys_param_path_1_ghe_detailed_geometry)

        expected_hydraulic_dia = 0.1156
        expected_pump_head = 164720
        expected_flow_rate = 0.018

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {"8c369df2-18e9-439a-8c25-875851c5aaf0": {"num_bh": 36, "length": 128.23}}
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

        # -- Clean up
        self.reset_sys_param(self.sys_param_path_1_ghe_detailed_geometry)

    def test_network_two_ghe_sequential(self):
        # -- Set up
        output_path = self.test_outputs_path / "two_ghe_sequential"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        res = run_sizer_from_cli_worker(
            self.sys_param_path_2_ghe_sequential,
            self.scenario_dir_2_ghe,
            self.geojson_path_2_ghe_sequential,
            output_path,
        )

        assert res == 0

        updated_sys_param = load_json(self.sys_param_path_2_ghe_sequential)

        expected_hydraulic_dia = 0.09351
        expected_pump_head = 160804
        expected_flow_rate = 0.008

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {
            "dd69549c-ecfc-4245-96dc-5b6127f34f46": {"num_bh": 16, "length": 127.5},
            "47fd01d3-3d72-46c0-85f2-a12854783764": {"num_bh": 13, "length": 128.0},
        }
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

        # -- Clean up
        self.reset_sys_param(self.sys_param_path_2_ghe_sequential)

    def test_network_two_ghe_staggered(self):
        # -- Set up
        output_path = self.test_outputs_path / "two_ghe_staggered"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        res = run_sizer_from_cli_worker(
            self.sys_params_path_2_ghe_staggered,
            self.scenario_dir_2_ghe,
            self.geojson_path_2_ghe_staggered,
            output_path,
        )

        assert res == 0

        updated_sys_param = load_json(self.sys_params_path_2_ghe_staggered)

        expected_hydraulic_dia = 0.09351
        expected_pump_head = 188970
        expected_flow_rate = 0.01

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {
            "dd69549c-ecfc-4245-96dc-5b6127f34f46": {"num_bh": 16, "length": 127.5},
            "47fd01d3-3d72-46c0-85f2-a12854783764": {"num_bh": 13, "length": 127.8},
        }
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

        # -- Clean up
        self.reset_sys_param(self.sys_params_path_2_ghe_staggered)

    def test_network_two_ghe_birectangles(self):
        # -- Set up
        output_path = self.test_outputs_path / "two_ghe_birectangles"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        res = run_sizer_from_cli_worker(
            self.sys_params_path_2_ghe_birectangles,
            self.scenario_dir_2_ghe,
            self.geojson_path_2_ghe_staggered,
            output_path,
        )

        assert res == 0

        updated_sys_param = load_json(self.sys_params_path_2_ghe_birectangles)

        expected_hydraulic_dia = 0.09351
        expected_pump_head = 334515
        expected_flow_rate = 0.01

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {
            "dd69549c-ecfc-4245-96dc-5b6127f34f46": {"num_bh": 22, "length": 90.3},
            "47fd01d3-3d72-46c0-85f2-a12854783764": {"num_bh": 14, "length": 130},
        }
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

        # -- Clean up
        self.reset_sys_param(self.sys_params_path_2_ghe_birectangles)

    def test_network_two_ghe_bizones_and_near_square(self):
        # -- Set up
        output_path = self.test_outputs_path / "two_ghe_bizoned_and_near_square"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        res = run_sizer_from_cli_worker(
            self.sys_params_path_2_ghe_bizoned_and_near_square,
            self.scenario_dir_2_ghe,
            self.geojson_path_2_ghe_staggered,
            output_path,
        )

        assert res == 0

        updated_sys_param = load_json(self.sys_params_path_2_ghe_bizoned_and_near_square)

        expected_hydraulic_dia = 0.09351
        expected_pump_head = 281895
        expected_flow_rate = 0.01

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {
            "dd69549c-ecfc-4245-96dc-5b6127f34f46": {"num_bh": 14, "length": 132},
            "47fd01d3-3d72-46c0-85f2-a12854783764": {"num_bh": 20, "length": 120},
        }
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

        # -- Clean up
        self.reset_sys_param(self.sys_params_path_2_ghe_bizoned_and_near_square)

    def test_network_three_ghe_upstream(self):
        # -- Set up
        output_path = self.test_outputs_path / "three_ghe_upstream"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        res = run_sizer_from_cli_worker(
            self.sys_param_13_buildings_upstream_ghe,
            self.scenario_dir_13_buildings,
            self.geojson_path_13_buildings,
            output_path,
        )

        assert res == 0

        updated_sys_param = load_json(self.sys_param_13_buildings_upstream_ghe)

        expected_hydraulic_dia = 0.54032
        expected_pump_head = 782301
        expected_flow_rate = 1.2255

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {
            "344421ab-b416-403e-bd22-7b8af7b581a2": {"num_bh": 2380, "length": 135.0},
            "8410c9a9-d52e-4c68-b7bc-4affae974481": {"num_bh": 72, "length": 93.3},
            "3eb26af6-a1f7-4daa-8372-ec016ca185a4": {"num_bh": 2451, "length": 135.0},
        }
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

        # -- Clean up
        self.reset_sys_param(self.sys_param_13_buildings_upstream_ghe)

    def test_network_three_ghe_area_proportional(self):
        # -- Set up
        output_path = self.test_outputs_path / "three_ghe_area_proportional"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        res = run_sizer_from_cli_worker(
            self.sys_param_path_13_buildings_proportional_ghe,
            self.scenario_dir_13_buildings,
            self.geojson_path_13_buildings,
            output_path,
        )

        assert res == 0

        updated_sys_param = load_json(self.sys_param_path_13_buildings_proportional_ghe)

        expected_hydraulic_dia = 0.54032
        expected_pump_head = 796483
        expected_flow_rate = 1.2375

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {
            "344421ab-b416-403e-bd22-7b8af7b581a2": {"num_bh": 2380, "length": 135.0},
            "8410c9a9-d52e-4c68-b7bc-4affae974481": {"num_bh": 2475, "length": 135.0},
            "3eb26af6-a1f7-4daa-8372-ec016ca185a4": {"num_bh": 1036, "length": 133.5},
        }
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

        # -- Clean up
        self.reset_sys_param(self.sys_param_path_13_buildings_proportional_ghe)

    def test_one_ghe_pre_designed(self):
        # -- Set up
        output_path = self.test_outputs_path / "one_ghe_pre_designed"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        res = run_sizer_from_cli_worker(
            self.sys_param_path_1_ghe_pre_designed,
            self.scenario_directory_path_1_ghe,
            self.geojson_path_1_ghe,
            output_path,
        )

        assert res == 0

        updated_sys_param = load_json(self.sys_param_path_1_ghe_pre_designed)

        expected_hydraulic_dia = 0.09351
        expected_pump_head = 158326
        expected_flow_rate = 0.01

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {"8c369df2-18e9-439a-8c25-875851c5aaf0": {"num_bh": 20, "length": 152}}
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

    def test_network_two_ghe_pre_designed(self):
        # -- Set up
        output_path = self.test_outputs_path / "two_ghe_pre_designed"
        output_path.mkdir(parents=True, exist_ok=True)

        # -- Run
        res = run_sizer_from_cli_worker(
            self.sys_param_path_2_ghe_pre_designed,
            self.scenario_dir_2_ghe,
            self.geojson_path_2_ghe_pre_designed,
            output_path,
        )

        assert res == 0

        updated_sys_param = load_json(self.sys_param_path_2_ghe_pre_designed)

        expected_hydraulic_dia = 0.11560
        expected_pump_head = 186568
        expected_flow_rate = 0.01

        self.check_horiz_pipe_params(updated_sys_param, expected_hydraulic_dia)
        self.check_pump_params(updated_sys_param, expected_pump_head, expected_flow_rate)

        expected_ghe_data = {
            "dd69549c-ecfc-4245-96dc-5b6127f34f46": {"num_bh": 28, "length": 131.8},
            "47fd01d3-3d72-46c0-85f2-a12854783764": {"num_bh": 20, "length": 152},
        }
        self.check_ghe_data(updated_sys_param, expected_ghe_data)

        # -- Clean up
        # clean up code only resets autosized values, leaves pre-designed untouched
        self.reset_sys_param(self.sys_param_path_2_ghe_pre_designed)
