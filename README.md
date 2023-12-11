# Instrat demand model

This repository contains a simple model of demand trajectories for energy carriers in Poland. First, the Eurostat data from 2019-2021 is analysed and processed to create a starting 2020 set of final use demands per carrier. Then, those demands are projected to 2050 using a simple model assuming a piecewise constant rate of growth (or decline) of demand for a given carrier and a possibly non-zero rate of substitution between different carriers. The results of the model can be used as input to PyPSA-PL (https://github.com/instrat-pl/pypsa-pl).

## License

The code is released under the [MIT license](LICENSE). The output data are released under the [CC BY 4.0 license](https://creativecommons.org/licenses/by/4.0/).

&copy; Instrat Foundation 2023

<a href="https://instrat.pl/en/"><img src="docs/instrat.png" width="200"></a>