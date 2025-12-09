import numpy as np
import pandas as pd
from loguru import logger
from modelica_builder.modelica_mos_file import ModelicaMOS

from thermalnetwork import HOURS_IN_YEAR
from thermalnetwork.base_component import BaseComponent
from thermalnetwork.enums import ComponentType


class WasteHeatSource(BaseComponent):
    def __init__(self, whs_name: str, data: dict):
        super().__init__(whs_name, ComponentType.WASTEHEATSOURCE)
        self.heat_source_rate = data["heat_source_rate"]
        self.system_parameter_path = data.get("system_parameter_path")
        self.network_loads = np.zeros(HOURS_IN_YEAR)

        # calculate loads on init
        self.calculate_loads()

    def calculate_loads(self) -> None:
        # there are 2 ways of specifying waste heat. One is constant value, the other is a Modelica Schedule file.
        # handle both cases. All values assumed to be in Watts

        # TODO: review how the waste heat gets subtracted...

        # determine if rate is a number or a file.
        # the path is expected to be related to the system parameter file location
        if self.heat_source_rate.endswith(".mos"):
            logger.debug("heat source rate parameter is a MOS file; loading values from file")

            # Check if system_parameter_path is available for file resolution
            if self.system_parameter_path is None:
                logger.error(
                    "Cannot load MOS file for waste heat: system_parameter_path not provided to Network constructor."
                    "System parameter path is required to resolve relative file paths."
                )
                return

            heat_source_rate_filepath = self.system_parameter_path.parent / self.heat_source_rate

            # Check if the file exists
            if not heat_source_rate_filepath.exists():
                logger.error(
                    f"Waste heat MOS file not found at {heat_source_rate_filepath}. "
                    f"Please check the path in your system parameters file."
                )
                return

            try:
                # load the mos file and get the waste heat data
                # don't assume that the loads in this file are hourly (may need interpolation).
                mos_file = ModelicaMOS(heat_source_rate_filepath)

                # Check if the MOS file actually contains data
                if mos_file.data is None or len(mos_file.data) == 0:
                    logger.error(f"MOS file {heat_source_rate_filepath} exists but contains no data.")
                    return

            except Exception as e:  # noqa: BLE001
                logger.error(f"Error reading MOS file {heat_source_rate_filepath}: {e!s}")
                return

            try:
                # Data is in mos_file.data. Expecting first column to be timestamps in seconds
                # and second column being heat in Watts
                waste_heat_df = pd.DataFrame(mos_file.data)
                waste_heat_df.columns = ["Time_s", "Waste_Heat_W"]
            except Exception as e:  # noqa: BLE001
                logger.error(
                    f"Error processing data from MOS file {heat_source_rate_filepath}: {e!s}. "
                    f"Expected 2 columns (time in seconds, heat in Watts)."
                )
                return

            waste_heat_df["Date Time"] = pd.to_datetime(waste_heat_df["Time_s"], unit="s")
            waste_heat_df = waste_heat_df.set_index("Date Time")

            # Make sure that last timestamp (in seconds) goes to end of year (31536000 seconds)
            # if not, copy last Watts value to a new timestamp representing end of year
            if waste_heat_df["Time_s"].iloc[-1] < 31536000:
                new_date = pd.to_datetime(31536000, unit="s")
                new_data = pd.DataFrame(
                    {
                        "Time_s": [31536000],
                        "Waste_Heat_W": [waste_heat_df["Waste_Heat_W"].iloc[-1]],
                    },
                    index=[new_date],
                    columns=["Time_s", "Waste_Heat_W"],
                )
                waste_heat_df = pd.concat([waste_heat_df, new_data])

            # Interpolate data to hourly
            waste_heat_df = waste_heat_df.resample("h").interpolate(method="linear")
            # keep only HOURS_IN_YEAR
            waste_heat_df = waste_heat_df.iloc[:HOURS_IN_YEAR]
            waste_heat_values = waste_heat_df["Waste_Heat_W"].to_numpy()

            self.network_loads = self.network_loads - waste_heat_values

        else:
            try:
                logger.debug("heat source rate parameter is a number; applying constant to heating loads")
                waste_heat_val = float(self.heat_source_rate)
                # subtract (make negative) from network loads
                self.network_loads = self.network_loads - waste_heat_val

            except ValueError:
                # heat_source_rate is not a valid number, make loads zero and log error
                logger.error(
                    "Waste heat source rate is not a valid number. Please provide a valid value or schedule file."
                )
                self.network_loads = np.zeros(HOURS_IN_YEAR)

    def get_loads(self):
        # return the loads previously calculated
        return self.network_loads
