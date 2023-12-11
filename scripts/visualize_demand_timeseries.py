import pandas as pd
import plotly.express as px


from instrat_demand_model.config import data_dir, project_dir

if __name__ == "__main__":
    dfs = []
    for scenario in ["instrat_ambitious", "baseline", "slow_transformation"]:
        df = pd.read_csv(
            data_dir("clean", f"demand_timeseries;scenario={scenario};unit=TWh.csv")
        )
        df["Scenario"] = scenario
        dfs.append(df)

    df = pd.concat(dfs)

    df["Carrier"] = df["Carrier"].apply(
        lambda x: x if not x.startswith("Heat") else "Heat"
    )

    df = df.groupby(["Carrier", "Scenario"]).sum().round(1).reset_index()

    df = df[
        df["Carrier"].isin(["Electricity", "Heat", "Hydrogen", "Light vehicle energy"])
    ]

    df = df.melt(
        id_vars=["Carrier", "Scenario"], var_name="Year", value_name="Value [TWh]"
    )

    for carrier, subdf in df.groupby("Carrier"):
        fig = px.line(
            subdf,
            x="Year",
            y="Value [TWh]",
            color="Scenario",
            template="simple_white+gridon",
            range_y=(0, subdf["Value [TWh]"].max() * 1.1),
            title=carrier,
        )
        fig.write_image(project_dir("figures", f"demand_timeseries;carrier={carrier}.png"))
