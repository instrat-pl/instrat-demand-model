import os
import pandas as pd
import numpy as np

from instrat_demand_model.config import data_dir
from instrat_demand_model.download import download_and_unzip

if __name__ == "__main__":
    # Before running the script download the following custom dataset from Eurostat as csv
    # https://ec.europa.eu/eurostat/databrowser/bookmark/cf9e32ad-dd93-4c84-95d3-79288194718a
    filename_eurostat = "nrg_bal_c__custom_7064775_linear.csv"

    os.makedirs(data_dir("raw", "eurostat"), exist_ok=True)
    os.makedirs(data_dir("clean", "eurostat"), exist_ok=True)

    dfs_codes = {}
    for variable_short, variable_long, name in [
        ("siec", "Carrier", "ESTAT_SIEC_en"),
        ("nrg_bal", "Variable", "ESTAT_NRG_BAL_en"),
    ]:
        dfs_codes[variable_short] = pd.read_csv(
            data_dir("raw", "eurostat", f"{name}.tsv"),
            sep="\t",
            header=None,
            names=[variable_short, variable_long],
        )

    # Energy balance
    raw_file = data_dir("raw", "eurostat", filename_eurostat)
    df = pd.read_csv(raw_file)

    columns_balance = [
        "GAE",  # Gross available energy
        "INTMARB",  # International maritime bunkers
        "INTAVI",  # International aviation
        "TO",  # Transformation output
        "TI_E",  # Transformation input - energy use
        "NRG_E",  # Energy sector - energy use
        "NRG_EHG_E", 
        "NRG_CM_E",
        "NRG_OIL_NG_E",
        "NRG_PR_E",
        "DL",  # Distribution losses
        "AFC",  # Available for final consumption
    ]

    columns_consumption = [
        # Non-energy use
        # "FC_IND_NE",
        "TI_NRG_FC_IND_NE",
        "FC_TRA_NE",
        "FC_OTH_NE",
        # Industry
        "FC_IND_E",
        # Transport
        "FC_TRA_RAIL_E",
        "FC_TRA_ROAD_E",
        "FC_TRA_DAVI_E",
        # "FC_TRA_DNAVI_E",
        "FC_TRA_PIPE_E",
        # Commercial & public services
        "FC_OTH_CP_E",
        # Households
        "FC_OTH_HH_E",
        # Agriculture, forestry and fishing
        "FC_OTH_AF_E",
        # "FC_OTH_FISH_E",
        # Residue
        "STATDIFF",
    ]

    df = pd.merge(df, dfs_codes["siec"], on="siec", how="left")
    df = df.rename(columns={"TIME_PERIOD": "Year"})

    df["Value [PJ]"] = (df["OBS_VALUE"].astype(float) / 1000).round(1)
    df = df[df["Value [PJ]"] > 0]

    df = df.pivot(
        index=["Year", "Carrier"], columns="nrg_bal", values="Value [PJ]"
    ).fillna(0)

    df = df[columns_balance + columns_consumption].rename(
        columns=dfs_codes["nrg_bal"].set_index("nrg_bal")["Variable"]
    )
    df = df.reset_index()

    df["Residual balance"] = (
        df[
            [
                "Gross available energy",
                "Transformation output",
            ]
        ].sum(axis=1)
        - df[
            [
                "Transformation input - energy use",
                "Energy sector - energy use",
                "Distribution losses",
                "International aviation",
                "International maritime bunkers",
                "Available for final consumption",
            ]
        ].sum(axis=1)
    ).round(1)

    df["Residual consumption"] = (
        df["Available for final consumption"]
        - df[
            [
                col
                for col in df.columns
                if col.startswith("Final consumption")
                or col
                == "Transformation input, energy sector and final consumption in industry sector - non-energy use"
            ]
        ].sum(axis=1)
        - df["Statistical differences"]
    ).round(1)

    for year, df_year in df.groupby("Year"):
        df_year = df_year.drop(columns=["Year"])
        df_year.to_csv(
            data_dir("clean", "eurostat", f"energy_balance_{year}.csv"), index=False
        )
