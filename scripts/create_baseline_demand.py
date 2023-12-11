import os
import pandas as pd
import numpy as np

from instrat_demand_model.config import data_dir


def add_energy_sector_to_industry(df):
    # Add energy sector demand to industry demand
    df["Industry"] += df["Energy sector - energy use"]
    df.drop(columns=["Energy sector - energy use"], inplace=True)


def add_hydrogen_demand(df):
    hydrogen_consumption_in_tonnes = 1.04e6
    # https://www.gov.pl/attachment/1b590d54-fa1e-49fe-9096-b2d0c6a4fe59
    # assumed 80% capacity utilization

    mj_per_kg = 120
    # lower heating value of hydrogen

    hydrogen_consumption_in_pj = hydrogen_consumption_in_tonnes * mj_per_kg / 1e6

    natural_gas_reforming_efficiency = 0.7
    # NETL 2023 https://doi.org/10.2172/1862910
    # assumed all hydrogen in Poland is produced through steam methane reforming

    natural_gas_consumption_in_pj = (
        hydrogen_consumption_in_pj / natural_gas_reforming_efficiency
    )

    df.loc["Natural gas", "Industry"] -= natural_gas_consumption_in_pj
    df.loc["Hydrogen", "Industry"] = hydrogen_consumption_in_pj


def add_decentralized_heat_demand(df):
    energy_share_used_for_heating = {
        "Coal and coal products": 1.0,
        "Natural gas": 0.8,
        "Oil and petroleum products": 1.0,
        "Biofuels": 1.0,
        "Renewables": 1.0,
    }
    # https://stat.gov.pl/obszary-tematyczne/srodowisko-energia/energia/zuzycie-energii-w-gospodarstwach-domowych-w-2021-roku,2,5.html

    thermal_efficiency = {
        "Coal and coal products": 0.75,
        "Natural gas": 0.85,
        "Oil and petroleum products": 0.85,
        "Biofuels": 0.75,
        "Renewables": 1.0,
    }
    # https://www.vaillant.pl/klienci-indywidualni/porady-i-wiedza/poradnik/urzadzenia-gazowe-i-olejowe/sprawnosc-kotlow-na-paliwo-stale-w-porownaniu-z-innymi-urzadzeniami-grzewczymi/

    carriers = [
        "Coal and coal products",
        "Natural gas",
        "Oil and petroleum products",
        "Biofuels",
        "Renewables",
    ]
    df_heat = df.loc[carriers, ["Buildings"]].rename(
        columns={"Buildings": "Primary energy"}
    )
    df_heat["Energy used for heating"] = df_heat["Primary energy"] * df_heat.index.map(
        energy_share_used_for_heating
    )
    df_heat["Heat"] = df_heat["Energy used for heating"] * df_heat.index.map(
        thermal_efficiency
    )
    print("\nDecentralized heating estimate:")
    print(df_heat)

    df.loc[carriers, "Buildings"] -= df_heat["Energy used for heating"]
    df.loc["Heat - decentralized", "Buildings"] = df_heat["Heat"].sum()

    # Remove heat pump electricity demand from electricity demand
    scop = 3.0
    df.loc["Electricity", "Buildings"] -= df_heat.loc["Renewables", "Heat"] / scop


def add_light_vehicle_energy_demand(df):
    road_transport_oil_consumption = df.loc[
        "Oil and petroleum products", "Transport - road"
    ]
    # PJ

    light_vehicle_oil_consumption_as_fraction_of_road = 0.63
    # KOBIZE National Inventory Report 2023
    # https://cdr.eionet.europa.eu/pl/eu/mmr/art07_inventory/ghg_inventory/envzckvq/NIR_2023_POL.pdf
    # fuels: gasoline, diesel, and LPG consumption
    # road: passenger cars, light duty trucks, heavy duty trucks and buses, motorcycles and mopeds
    # light vehicles: passenger cars, light duty trucks

    light_vehicle_oil_consumption = (
        light_vehicle_oil_consumption_as_fraction_of_road
        * road_transport_oil_consumption
    )

    tank_to_wheel_efficiency = 0.25
    # typical gasoline/diesel engine
    # NREL https://www.nrel.gov/docs/fy23osti/84631.pdf
    # US DoE (https://www.fueleconomy.gov/feg/evtech.shtml

    light_vehicle_wheel_energy_consumption = (
        tank_to_wheel_efficiency * light_vehicle_oil_consumption
    )

    light_vehicle_kilometers = 214e9
    # https://stat.gov.pl/obszary-tematyczne/transport-i-lacznosc/transport/transport-drogowy-w-polsce-w-latach-2020-i-2021GUS,6,7.html

    wheel_mj_per_vkm = (
        light_vehicle_wheel_energy_consumption / light_vehicle_kilometers * 1e9
    )

    number_of_light_vehicles = 1.1 * 20e6
    # SAMAR https://www.samar.pl/__/3/3.a/117083/3.sc/11/Park-2022---Ile-jest-w-Polsce-samochod%C3%B3w-i-jaki-jest-ich-wiek-.html
    # multiply by 1.1 to account for light duty vehicles
    km_per_vehicle = light_vehicle_kilometers / number_of_light_vehicles

    print("\nLight vehicle estimates:")
    print(f"  wheel energy consumption: {wheel_mj_per_vkm:.3f} MJ/vkm")
    print(f"  kilometers per vehicle: {km_per_vehicle:.1f}")

    df.loc[
        "Oil and petroleum products", "Transport - road"
    ] -= light_vehicle_oil_consumption
    df.loc[
        "Light vehicle energy", "Transport - road"
    ] = light_vehicle_wheel_energy_consumption


if __name__ == "__main__":
    df = pd.read_csv(
        data_dir("clean", "eurostat", "direct_consumption_2019-2021.csv"),
    )
    df = df.set_index("Carrier")

    df = df.drop(columns=["Gross total", "Net total"], index=["Non-renewable waste"])
    df = df.rename(index={"Heat": "Heat - centralized"})

    add_energy_sector_to_industry(df)
    add_hydrogen_demand(df)
    add_decentralized_heat_demand(df)
    add_light_vehicle_energy_demand(df)

    transport_columns = [
        "Transport - road",
        "Transport - other",
        "Transport - international aviation and navigation",
    ]
    df["Transport"] = df[transport_columns].sum(axis=1)
    df.drop(columns=transport_columns, inplace=True)

    df = df.round(1).fillna(0)

    sectors = [
        "Industry",
        "Buildings",
        "Transport",
        "Agriculture",
    ]
    carriers = [
        "Coal and coal products",
        "Natural gas",
        "Oil and petroleum products",
        "Biofuels",
        "Renewables",
        "Electricity",
        "Heat - centralized",
        "Heat - decentralized",
        "Hydrogen",
        "Light vehicle energy",
    ]

    df = df.loc[carriers, sectors].reset_index()

    df.to_csv(
        data_dir("clean", "baseline_demand_2019-2021.csv"),
        index=False,
    )
