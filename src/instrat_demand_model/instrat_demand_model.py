import pandas as pd
import numpy as np

from instrat_demand_model.config import data_dir


def preprocess_baseline_demand(df):
    # Aggregate heat demand
    df.loc[df["Carrier"].str.startswith("Heat"), "Carrier"] = "Heat"
    df = df.groupby("Carrier").sum().reset_index()
    # Split heat demand into space and water
    space_share = 0.8
    water_share = 0.2
    df = df.set_index("Carrier")
    df.loc["Heat - space"] = space_share * df.loc["Heat"]
    df.loc["Heat - water"] = water_share * df.loc["Heat"]
    df = df.drop(index="Heat")
    return df


def initialize(init_vector, target_elec, target_hydro, initial_year=2020):
    df = pd.DataFrame(
        data=init_vector.values, index=init_vector.index, columns=[initial_year]
    )

    is_fossil_fuel = df.index.str.startswith(("Coal", "Natural gas", "Oil"))
    df_fossil_fuels_electrifiable = (df.loc[is_fossil_fuel] * target_elec).rename(
        index=lambda x: f"{x} - electrifiable"
    )
    df_fossil_fuels_hydrogenizable = (df.loc[is_fossil_fuel] * target_hydro).rename(
        index=lambda x: f"{x} - hydrogenizable"
    )

    df = pd.concat(
        [
            df[~is_fossil_fuel],
            df_fossil_fuels_electrifiable,
            df_fossil_fuels_hydrogenizable,
        ]
    )

    return df


def create_conversion_matrix(
    year,
    carriers,
    elec_rates,
    hydro_rates,
    elec_conv,
    hydro_conv,
):
    period = (year // 10) * 10

    m = pd.DataFrame(data=np.identity(len(carriers)), index=carriers, columns=carriers)

    electrifiable_carriers = carriers[carriers.str.endswith("electrifiable")]
    m.loc["Electricity", electrifiable_carriers] = elec_conv * elec_rates[period]
    for carrier in electrifiable_carriers:
        m.loc[carrier, carrier] = 1 - elec_rates[period]

    hydrogenizable_carriers = carriers[carriers.str.endswith("hydrogenizable")]
    m.loc["Hydrogen", hydrogenizable_carriers] = hydro_conv * hydro_rates[period]
    for carrier in hydrogenizable_carriers:
        m.loc[carrier, carrier] = 1 - hydro_rates[period]

    return m


def create_growth_vector(
    year,
    carriers,
    sector,
    demand_change_rates,
):
    period = (year // 10) * 10

    g = pd.Series(data=np.ones(len(carriers)), index=carriers)

    if sector != "Buildings":
        g += demand_change_rates[period]
    else:
        g.loc[g.index != "Heat - space"] += demand_change_rates["Other"][period]
        g.loc["Heat - space"] += demand_change_rates["Heat - space"][period]

    return g


def create_sectoral_demand_timeseries(
    sector,
    df_baseline,
    demand_change_rates,
    target_elec,
    target_hydro,
    elec_rates,
    hydro_rates,
    elec_conv,
    hydro_conv,
    initial_year=2020,
    final_year=2050,
):
    df = initialize(
        df_baseline[sector],
        target_elec[sector],
        target_hydro[sector],
        initial_year=initial_year,
    )
    carriers = df.index

    for year in range(initial_year, final_year):
        growth_vector = create_growth_vector(
            year,
            carriers,
            sector,
            demand_change_rates[sector],
        )
        conversion_matrix = create_conversion_matrix(
            year,
            carriers,
            elec_rates[sector],
            hydro_rates[sector],
            elec_conv[sector],
            hydro_conv[sector],
        )
        df[year + 1] = growth_vector * (conversion_matrix @ df[year])

    return df



