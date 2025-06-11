import logging
import shutil
from pathlib import Path

from ghedesigner.main import run
from rich.logging import RichHandler

from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType, GHEDesignType
from thermalnetwork.utilities import load_json, write_json

logging.basicConfig(level=logging.DEBUG, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
logger = logging.getLogger(__name__)


class GHE(BaseComponent):
    def __init__(self, data: dict) -> None:
        super().__init__(data["name"], ComponentType.GROUNDHEATEXCHANGER)
        self.id = data["id"]
        self.json_data = data["properties"]
        self.design_method = GHEDesignType[self.json_data["borefield"]["design_method"].upper()]
        self.area = self.compute_area()

        # # compute Area
        # self.id = data["id"]
        # if "polygons" in self.json_data["geometric_constraints"]:
        #     bound_area = polygon_area(self.json_data["geometric_constraints"]["polygons"][0])
        #     if bound_area < 0:  # clockwise polygon; reverse for GHE Designer
        #         self.json_data["geometric_constraints"]["polygons"][0].reverse()
        #     self.area = abs(bound_area)
        #     for i, hole_poly in enumerate(self.json_data["geometric_constraints"]["polygons"][1:]):
        #         hole_area = polygon_area(hole_poly)
        #         if hole_area < 0:  # clockwise polygon; reverse for GHE Designer
        #             self.json_data["geometric_constraints"]["polygons"][i + 1].reverse()
        #         self.area -= abs(hole_area)
        # else:
        #     length = self.json_data["geometric_constraints"]["length"]
        #     width = self.json_data["geometric_constraints"]["width"]
        #     self.area = length * width
        #
        # borehole_data = self.json_data["borehole"]
        #
        # if (
        #     borehole_data["length_of_boreholes_autosized"] is True
        #     or borehole_data["number_of_boreholes_autosized"] is True
        # ):
        #     self.autosize = True
        # else:
        #     self.autosize = False

        self.nbh = None
        self.bh_length = None

    def compute_area(self) -> float:
        if (
            self.design_method == GHEDesignType.AUTOSIZED_BIRECTANGLE_CONSTRAINED_BOREFIELD
            or GHEDesignType.AUTOSIZED_BIZONED_RECTANGLE_BOREFIELD
            or GHEDesignType.AUTOSIZED_NEAR_SQUARE_BOREFIELD
            or GHEDesignType.AUTOSIZED_RECTANGLE_BOREFIELD
            or GHEDesignType.AUTOSIZED_RECTANGLE_CONSTRAINED_BOREFIELD
            or GHEDesignType.AUTOSIZED_ROWWISE_BOREFIELD
        ):
            length = self.json_data["borefield"]["length_of_ghe"]
            width = self.json_data["borefield"]["width_of_ghe"]
            area = length * width

        elif self.design_method == GHEDesignType.PREDESIGNED_BOREFIELD:
            area = None
        else:
            raise ValueError("design_type method not supported")

        return area

    def get_common_inputs(self) -> dict:
        d = {
            "version": 2,
            "topology": [{"type": "ground-heat-exchanger", "name": f"{self.id}"}],
            "fluid": {
                "fluid_name": str(self.json_data["fluid"]["fluid_name"]).upper(),
                "concentration_percent": self.json_data["fluid"]["concentration_percent"],
                "temperature": self.json_data["soil"]["undisturbed_temp"],
            },
            "ground-heat-exchanger": {
                f"{self.id}": {
                    "flow_rate": self.json_data["design"]["flow_rate"],
                    "flow_type": str(self.json_data["design"]["flow_type"]).upper(),
                    "grout": {**self.json_data["grout"]},
                    "soil": {**self.json_data["soil"]},
                    "pipe": {
                        key: val.upper() if type(val) is str else val for key, val in self.json_data["pipe"].items()
                    },
                    "borehole": {
                        "buried_depth": self.json_data["borehole"]["buried_depth"],
                        "diameter": self.json_data["borehole"]["diameter"],
                    },
                }
            },
            "simulation-control": {"simulation-months": self.json_data["simulation"]["num_months"]},
        }

        return d

    def get_input_file_data(self) -> dict:
        d = self.get_common_inputs()

        # if (
        #     self.design_method == GHEDesignType.AUTOSIZED_BIRECTANGLE_CONSTRAINED_BOREFIELD
        #     or self.design_method == GHEDesignType.AUTOSIZED_BIZONED_RECTANGLE_BOREFIELD
        #     or self.design_method == GHEDesignType.AUTOSIZED_NEAR_SQUARE_BOREFIELD
        # ):
        #     pass
        if self.design_method == GHEDesignType.AUTOSIZED_RECTANGLE_BOREFIELD:
            # if "polygons" in self.json_data["geometric_constraints"]:
            #     geo_constraints = {
            #         "property_boundary": self.json_data["geometric_constraints"]["polygons"][0],
            #         "no_go_boundaries": self.json_data["geometric_constraints"]["polygons"][1:],
            #         "b_min": self.json_data["geometric_constraints"]["b_min"],
            #         "b_max_x": self.json_data["geometric_constraints"]["b_max"],
            #         "b_max_y": self.json_data["geometric_constraints"]["b_max"],
            #         "method": "BIRECTANGLECONSTRAINED",
            #     }
            # else:

            geo_constraints = {
                "length": self.json_data["borefield"]["length_of_ghe"],
                "width": self.json_data["borefield"]["width_of_ghe"],
                "b_min": self.json_data["borefield"]["b_min"],
                "b_max": self.json_data["borefield"]["b_max"],
                "method": "RECTANGLE",
            }

            d_ghe = {
                **d["ground-heat-exchanger"][f"{self.id}"],
                "geometric_constraints": geo_constraints,
                "design": {
                    "max_eft": self.json_data["design"]["max_eft"],
                    "min_eft": self.json_data["design"]["min_eft"],
                    "max_height": self.json_data["borefield"]["max_height"],
                    "min_height": self.json_data["borefield"]["min_height"],
                    "max_boreholes": 2500,
                    "continue_if_design_unmet": True,
                },
                "loads": self.json_data["loads"]["ground_loads"].tolist(),
            }

            d_full = d
            d_full["ground-heat-exchanger"][f"{self.id}"] = d_ghe

            return d_full

        # elif (
        #     self.design_method == GHEDesignType.AUTOSIZED_RECTANGLE_CONSTRAINED_BOREFIELD
        #     or self.design_method == GHEDesignType.AUTOSIZED_ROWWISE_BOREFIELD
        # ):
        #     pass
        elif self.design_method == GHEDesignType.PREDESIGNED_BOREFIELD:
            nbh = self.json_data["borehole"]["number_of_boreholes"]
            nbh_x = len(self.json_data["pre_designed_borefield"]["borehole_x_coordinates"])
            nbh_y = len(self.json_data["pre_designed_borefield"]["borehole_y_coordinates"])

            # check if all equal
            if len({nbh, nbh_x, nbh_y}) != 1:
                raise ValueError(
                    "number of boreholes not consistent. check 'number_of_boreholes', 'borehole_x_coordinates', "
                    "and 'borehole_y_coordinates' are not equal"
                )

            d_ghe = {
                **d["ground-heat-exchanger"][f"{self.id}"],
                "pre_designed": {
                    "arrangement": "MANUAL",
                    "H": self.json_data["borehole"]["length_of_boreholes"],
                    "x": self.json_data["pre_designed_borefield"]["borehole_x_coordinates"],
                    "y": self.json_data["pre_designed_borefield"]["borehole_y_coordinates"],
                },
            }

            d_full = d
            d_full["ground-heat-exchanger"][f"{self.id}"] = d_ghe
            return d_full

        else:
            raise ValueError("design_type not supported")

    def write_input_file(self, output_path: Path):
        d = self.get_input_file_data()

        # ghe output directory
        ghe_dir = output_path / self.id

        # Check if the directory exists and delete it if so
        if ghe_dir.is_dir():
            logger.debug(f"deleting directory: {ghe_dir}")
            shutil.rmtree(ghe_dir)

        # Create the subdirectory, write ghedesigner input file
        logger.debug(f"creating directory: {ghe_dir}")
        ghe_dir.mkdir(parents=True)
        ghe_input_file = ghe_dir / "in.json"
        write_json(ghe_input_file, d, sort_keys=True)

        return ghe_input_file

    def update_config(self, results_dir: Path):
        if (
            self.design_method == GHEDesignType.AUTOSIZED_BIRECTANGLE_CONSTRAINED_BOREFIELD
            or GHEDesignType.AUTOSIZED_BIZONED_RECTANGLE_BOREFIELD
            or GHEDesignType.AUTOSIZED_NEAR_SQUARE_BOREFIELD
            or GHEDesignType.AUTOSIZED_RECTANGLE_BOREFIELD
            or GHEDesignType.AUTOSIZED_RECTANGLE_CONSTRAINED_BOREFIELD
            or GHEDesignType.AUTOSIZED_ROWWISE_BOREFIELD
        ):
            d = load_json(results_dir / "SimulationSummary.json")
            self.nbh = d["ghe_system"]["number_of_boreholes"]
            self.bh_length = d["ghe_system"]["active_borehole_length"]["value"]

        elif self.design_method == GHEDesignType.PREDESIGNED_BOREFIELD:
            self.nbh = self.json_data["borehole"]["number_of_boreholes"]
            self.bh_length = self.json_data["borehole"]["length_of_boreholes"]
        else:
            raise ValueError("design_type method not supported")

    def size(self, output_path: Path) -> None:
        # write input file for ghedesigner
        ghe_input_file = self.write_input_file(output_path)
        ghe_dir = ghe_input_file.parent

        # size ghe
        logger.debug("running ghe sizing")
        run(ghe_input_file, ghe_dir)
        logger.debug(f"ghe sizing data written to {ghe_dir.resolve()}")

        self.update_config(ghe_dir)
