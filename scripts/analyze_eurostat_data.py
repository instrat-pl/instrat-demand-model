import os
import pandas as pd
import numpy as np

from instrat_demand_model.config import data_dir
from instrat_demand_model.download import upload_to_gsheet


def aggregate_carriers(df):
    carriers = {
        "Coal and coal products": ["Solid fossil fuels", "Manufactured gases"],
        "Natural gas": ["Natural gas"],
        "Oil and petroleum products": [
            "Oil and petroleum products (excluding biofuel portion)"
        ],
        "Biofuels": ["Renewables and biofuels"],  # Renewables need to be subtracted
        "Renewables": ["Solar thermal", "Geothermal", "Ambient heat (heat pumps)"],
        "Electricity": ["Electricity"],
        "Heat": ["Heat"],
        "Non-renewable waste": ["Non-renewable waste"],
    }

    df_carrier = pd.DataFrame(
        [(carrier, key) for key, values in carriers.items() for carrier in values],
        columns=["Carrier", "Group"],
    )
    df = (
        df.merge(df_carrier, on="Carrier", how="left")
        .drop(columns=["Carrier"])
        .rename(columns={"Group": "Carrier"})
    )
    df = df.groupby("Carrier").sum()

    df.loc["Biofuels"] -= df.loc["Renewables"]

    df = df.round(1).reset_index()

    df["Carrier"] = pd.Categorical(df["Carrier"], categories=carriers.keys())
    df = df.sort_values("Carrier")
    return df


def aggregate_sectors(df):
    sectors = {
        "Industry": [
            "Final consumption - industry sector - energy use",
        ],
        "Industry - non-energy use": [
            "Transformation input, energy sector and final consumption in industry sector - non-energy use"
        ],
        "Transport - road": [
            "Final consumption - transport sector - road - energy use"
        ],
        "Transport - international aviation and navigation": [
            "International aviation",
            "International maritime bunkers",
        ],
        "Transport - other": [
            "Final consumption - transport sector - rail - energy use",
            "Final consumption - transport sector - domestic aviation - energy use",
            "Final consumption - transport sector - pipeline transport - energy use",
            # "Final consumption - transport sector - non-energy use",
        ],
        "Buildings": [
            "Final consumption - other sectors - households - energy use",
            "Final consumption - other sectors - commercial and public services - energy use",
        ],
        "Agriculture": [
            "Final consumption - other sectors - agriculture and forestry - energy use",
        ],
        # "Buildings and agriculture - non-energy use": [
        #     "Final consumption - other sectors - non-energy use"
        # ],
        "Energy sector - energy use": [
            "Energy sector - energy use",
        ],
        "Electricity - self-consumption": [
            "Energy sector - electricity and heat generation - energy use"
        ],
        "Heat - self-consumption": [
            "Energy sector - electricity and heat generation - energy use"
        ],
        "Natural gas - self-consumption": [
            "Energy sector - oil and natural gas extraction plants - energy use"
        ],
        "Coal and coal products - self-consumption": [
            "Energy sector - coal mines - energy use"
        ],
        "Oil and petroleum products - self-consumption": [
            "Energy sector - oil and natural gas extraction plants - energy use",
            "Energy sector - petroleum refineries (oil refineries) - energy use",
        ],
        "Losses": ["Distribution losses"],
        "Residual": ["Statistical differences"],
    }

    df_sector = pd.DataFrame(
        [(sector, key) for key, values in sectors.items() for sector in values],
        columns=["Sector", "Group"],
    )

    df.columns.name = "Sector"
    df = df.set_index("Carrier").transpose().reset_index()
    print(
        "Removed columns:",
        set(df["Sector"].unique()) - set(df_sector["Sector"].unique()),
    )

    df = (
        df.merge(df_sector, on="Sector", how="left")
        .drop(columns=["Sector"])
        .rename(columns={"Group": "Sector"})
    )

    df = df[df["Sector"].notna()]
    df = df.groupby("Sector").sum().round(1).reset_index()

    df["Sector"] = pd.Categorical(df["Sector"], categories=sectors.keys())
    df = df.sort_values("Sector")

    df = df.set_index("Sector").transpose().reset_index(names=["Carrier"])

    df = df.set_index("Carrier")

    # Consider non-energy use for natural gas only 
    df.loc["Natural gas", "Industry"] += df.loc[
        "Natural gas", "Industry - non-energy use"
    ]
    df = df.drop(columns=["Industry - non-energy use"])

    df["Carrier production - self-consumption"] = 0
    for carrier in [
        "Coal and coal products",
        "Natural gas",
        "Oil and petroleum products",
        "Electricity",
        "Heat",
    ]:
        df.loc[carrier, "Carrier production - self-consumption"] = df.loc[
            carrier, f"{carrier} - self-consumption"
        ]
        df = df.drop(columns=[f"{carrier} - self-consumption"])
    df["Energy sector - energy use"] -= df["Carrier production - self-consumption"] 

    # Only for electricity include losses in demand
    non_losses_residual = [
        col for col in df.columns if col not in ["Losses", "Residual"]
    ]
    for sector in non_losses_residual:
        df.loc["Electricity", sector] += (
            df.loc["Electricity", "Losses"]
            * df.loc["Electricity", sector]
            / df.loc["Electricity", non_losses_residual].sum()
        )
    df = df.drop(columns=["Losses"])

    # Distribute residuals
    non_residual = [col for col in df.columns if col != "Residual"]
    for sector in non_residual:
        df[sector] += df["Residual"] * df[sector] / df[non_residual].sum(axis=1)
    df = df.drop(columns=["Residual"])

    df["Gross total"] = df.sum(axis=1)
    df["Net total"] = df["Gross total"] - df["Carrier production - self-consumption"]

    df = df.round(1).reset_index()
    return df


if __name__ == "__main__":
    years = [2019, 2020, 2021]

    # Direct consumption
    dfs = []
    for year in years:
        df = pd.read_csv(data_dir("clean", "eurostat", f"energy_balance_{year}.csv"))
        df = aggregate_carriers(df)
        df = aggregate_sectors(df)

        df.to_csv(
            data_dir("clean", "eurostat", f"direct_consumption_{year}.csv"),
            index=False,
        )
        dfs.append(df)

    df = pd.concat(dfs)
    df = df.groupby("Carrier", sort=False).mean().round(1).reset_index()
    df.to_csv(
        data_dir("clean", "eurostat", "direct_consumption_2019-2021.csv"),
        index=False,
    )

    # Primary energy
    dfs = []
    for year in years:
        df = pd.read_csv(data_dir("clean", "eurostat", f"energy_balance_{year}.csv"))
        df = aggregate_carriers(df)
        df = df.rename(columns={"Gross available energy": "Primary energy supply [PJ]"})
        df = df[["Carrier", "Primary energy supply [PJ]"]]

        df.to_csv(
            data_dir("clean", "eurostat", f"primary_energy_{year}.csv"),
            index=False,
        )
        dfs.append(df)

    df = pd.concat(dfs)
    df = df.groupby("Carrier", sort=False).mean().round(1).reset_index()
    df.to_csv(
        data_dir("clean", "eurostat", "primary_energy_2019-2021.csv"),
        index=False,
    )
