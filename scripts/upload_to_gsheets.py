import pandas as pd


from instrat_demand_model.config import data_dir
from instrat_demand_model.download import upload_to_gsheet


if __name__ == "__main__":
    scenario_urls = {
        "instrat_ambitious": "https://docs.google.com/spreadsheets/d/1bkkxYwRgVaCSDu8Sq_zASojBUJS2wavMOLlpJhExfm0",
        "baseline": "https://docs.google.com/spreadsheets/d/1egpWHjUHdnGI5ZpKrCfxI4MBxfxjWVzoOYbXb4IY0a0",
        "slow_transformation": "https://docs.google.com/spreadsheets/d/1AelU6KUr0qXWQa7-foduvTgbkgY_pfShJTYd74K6iPA",
    }

    for scenario, url in scenario_urls.items():
        dfs = []
        for sector in ["Buildings", "Industry", "Transport", "Agriculture"]:
            df = pd.read_csv(
                data_dir(
                    "clean",
                    f"demand_timeseries;scenario={scenario};sector={sector}.csv",
                )
            )
            df["Sector"] = sector
            df["Carrier"] = (
                df["Carrier"]
                .str.replace(" - electrifiable", "")
                .str.replace(" - hydrogenizable", "")
            )
            df = df.set_index(["Sector", "Carrier"]).reset_index()
            df = df.groupby(["Sector", "Carrier"]).sum().round(2).reset_index()
            dfs.append(df)
        df = pd.concat(dfs)

        upload_to_gsheet(df, url, sheet_name="# Demand per sector and carrier")
