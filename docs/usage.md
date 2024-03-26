# Usage

The expected usage of this package is via [URBANopt](https://docs.urbanopt.net/). An example command from URBANopt is:

` uo ghe_size --sys-param <path/to/sys_param.json> --feature <path/to/FEATUREFILE.json> --scenario <path/to/SCENARIOFILE.csv>`

Full documnentation of the URBANopt commands to work with a Ground Heat Exchanger (GHE) can be found in the [URBANopt documentation](https://docs.urbanopt.net/workflows/ghp/ghp.html).

It is possible to use ThermalNetwork directly, and can be done so with a similar (though not identical) command:

 `thermalnetwork --system-parameter-file <path/to/sys_param.json> --geojson-file <path/to/FEATUREFILE.json> --scenario-directory <path/to/SCENARIO_dir>`
