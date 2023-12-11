import pandas as pd

from instrat_demand_model.config import data_dir
from instrat_demand_model.instrat_demand_model import (
    preprocess_baseline_demand,
    create_sectoral_demand_timeseries,
)


def create_demand_timeseries(
    demand_change_rates,
    target_elec,
    target_hydro,
    elec_rates,
    hydro_rates,
    elec_conv,
    hydro_conv,
    scenario="baseline",
):
    initial_year = 2020
    final_year = 2050

    df_baseline = pd.read_csv(data_dir("clean", "baseline_demand_2019-2021.csv"))
    df_baseline = preprocess_baseline_demand(df_baseline)

    sectors = df_baseline.columns

    for sector in sectors:
        df = create_sectoral_demand_timeseries(
            sector,
            df_baseline,
            demand_change_rates,
            target_elec,
            target_hydro,
            elec_rates,
            hydro_rates,
            elec_conv,
            hydro_conv,
            initial_year=initial_year,
            final_year=final_year,
        )
        df = df[(df > 0).any(axis=1)].round(3)
        df.to_csv(
            data_dir(
                "clean", f"demand_timeseries;scenario={scenario};sector={sector}.csv"
            )
        )

    # Aggregate
    dfs = []
    for sector in sectors:
        df = pd.read_csv(
            data_dir(
                "clean", f"demand_timeseries;scenario={scenario};sector={sector}.csv"
            ),
            index_col=0,
        )
        dfs.append(df)
    df = pd.concat(dfs)
    df = df.rename(
        index=lambda x: x.replace(" - electrifiable", "").replace(
            " - hydrogenizable", ""
        )
    )
    df = df.groupby(df.index).sum()

    # Save aggregated
    df.round(1).to_csv(
        data_dir("clean", f"demand_timeseries;scenario={scenario};unit=PJ.csv")
    )
    (df / 3.6).round(1).to_csv(
        data_dir("clean", f"demand_timeseries;scenario={scenario};unit=TWh.csv")
    )


def demand_change_rates(scenario):
    if scenario == "instrat_ambitious":
        return {
            "Industry": {
                2020: 0.0050,
                2030: 0.0025,
                2040: 0.0025,
            },
            "Transport": {
                2020: 0.010,
                2030: -0.010,
                2040: -0.020,
            },
            "Buildings": {
                "Other": {
                    2020: 0.0050,
                    2030: 0.0025,
                    2040: 0.0025,
                },
                "Heat - space": {
                    2020: -0.005,
                    2030: -0.04,
                    2040: -0.04,
                },
            },
            "Agriculture": {
                2020: 0.0,
                2030: 0.0,
                2040: 0.0,
            },
        }
    if scenario == "baseline":
        return {
            "Industry": {
                2020: 0.0050,
                2030: 0.0025,
                2040: 0.0025,
            },
            "Transport": {
                2020: 0.010,
                2030: 0.00,
                2040: -0.010,
            },
            "Buildings": {
                "Other": {
                    2020: 0.0050,
                    2030: 0.0025,
                    2040: 0.0025,
                },
                "Heat - space": {
                    2020: -0.005,
                    2030: -0.025,
                    2040: -0.025,
                },
            },
            "Agriculture": {
                2020: 0.0,
                2030: 0.0,
                2040: 0.0,
            },
        }
    if scenario == "slow_transformation":
        return {
            "Industry": {
                2020: 0.0050,
                2030: 0.0025,
                2040: 0.0025,
            },
            "Transport": {
                2020: 0.010,
                2030: 0.005,
                2040: 0.000,
            },
            "Buildings": {
                "Other": {
                    2020: 0.0050,
                    2030: 0.0025,
                    2040: 0.0025,
                },
                "Heat - space": {
                    2020: -0.005,
                    2030: -0.005,
                    2040: -0.005,
                },
            },
            "Agriculture": {
                2020: 0.0,
                2030: 0.0,
                2040: 0.0,
            },
        }
    else:
        raise ValueError(f"Invalid scenario: {scenario}")


def elec_rates(scenario):
    if scenario == "instrat_ambitious":
        return {
            "Industry": {
                2020: 0.01,
                2030: 0.03,
                2040: 0.03,
            },
            "Transport": {
                2020: 0.02,
                2030: 0.04,
                2040: 0.04,
            },
            "Buildings": {
                2020: 0.02,
                2030: 0.04,
                2040: 0.04,
            },
            "Agriculture": {
                2020: 0.01,
                2030: 0.025,
                2040: 0.025,
            },
        }
    if scenario == "baseline":
        return {
            "Industry": {
                2020: 0.01,
                2030: 0.02,
                2040: 0.02,
            },
            "Transport": {
                2020: 0.02,
                2030: 0.03,
                2040: 0.03,
            },
            "Buildings": {
                2020: 0.02,
                2030: 0.03,
                2040: 0.03,
            },
            "Agriculture": {
                2020: 0.01,
                2030: 0.025,
                2040: 0.025,
            },
        }
    if scenario == "slow_transformation":
        return {
            "Industry": {
                2020: 0.01,
                2030: 0.01,
                2040: 0.01,
            },
            "Transport": {
                2020: 0.02,
                2030: 0.02,
                2040: 0.02,
            },
            "Buildings": {
                2020: 0.02,
                2030: 0.02,
                2040: 0.02,
            },
            "Agriculture": {
                2020: 0.01,
                2030: 0.025,
                2040: 0.025,
            },
        }
    else:
        raise ValueError(f"Invalid scenario: {scenario}")


def hydro_rates(scenario):
    if scenario == "instrat_ambitious":
        return {
            "Industry": {
                2020: 0.000,
                2030: 0.015,
                2040: 0.030,
            },
            "Transport": {
                2020: 0.000,
                2030: 0.015,
                2040: 0.030,
            },
            "Buildings": {
                2020: 0.0,
                2030: 0.0,
                2040: 0.0,
            },
            "Agriculture": {
                2020: 0.000,
                2030: 0.015,
                2040: 0.030,
            },
        }
    if scenario == "baseline":
        return {
            "Industry": {
                2020: 0.000,
                2030: 0.005,
                2040: 0.020,
            },
            "Transport": {
                2020: 0.000,
                2030: 0.005,
                2040: 0.020,
            },
            "Buildings": {
                2020: 0.0,
                2030: 0.0,
                2040: 0.0,
            },
            "Agriculture": {
                2020: 0.000,
                2030: 0.005,
                2040: 0.020,
            },
        }
    if scenario == "slow_transformation":
        return {
            "Industry": {
                2020: 0.000,
                2030: 0.0025,
                2040: 0.0100,
            },
            "Transport": {
                2020: 0.000,
                2030: 0.0025,
                2040: 0.0100,
            },
            "Buildings": {
                2020: 0.000,
                2030: 0.0025,
                2040: 0.0100,
            },
            "Agriculture": {
                2020: 0.000,
                2030: 0.0025,
                2040: 0.0100,
            },
        }
    else:
        raise ValueError(f"Invalid scenario: {scenario}")


target_elec = {
    "Industry": 0.75,
    "Transport": 0.2,
    "Buildings": 1.0,
    "Agriculture": 0.5,
}
target_hydro = {key: 1 - value for key, value in target_elec.items()}


elec_conv = {
    "Industry": 0.9,
    "Transport": 0.3,
    "Buildings": 0.5,
    "Agriculture": 0.3,
}
hydro_conv = {
    "Industry": 1,
    "Transport": 1,
    "Buildings": 0,
    "Agriculture": 0,
}

if __name__ == "__main__":
    for scenario in ["instrat_ambitious", "baseline", "slow_transformation"]:
        create_demand_timeseries(
            demand_change_rates(scenario),
            target_elec,
            target_hydro,
            elec_rates(scenario),
            hydro_rates(scenario),
            elec_conv,
            hydro_conv,
            scenario=scenario,
        )
