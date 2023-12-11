from io import BytesIO
import os
import requests
from zipfile import ZipFile
import gspread
import pandas as pd


def download(url, savedir, filename, params=None, force=False):
    file = savedir.joinpath(filename)
    if not force and file.exists():
        return
    os.makedirs(savedir, exist_ok=True)
    print(f"Downloading from {url}")
    r = requests.get(url, params=params, stream=True)
    with open(file, "wb") as f:
        f.write(r.content)


def download_and_unzip(url, savedir, filename="", rename=False, force=False):
    file = savedir.joinpath(filename)
    if not force and file.exists():
        return
    os.makedirs(savedir, exist_ok=True)
    print(f"Downloading and unzipping {url}")
    r = requests.get(url, stream=True)
    zip_file = ZipFile(BytesIO(r.content))
    zipped_filename = zip_file.namelist()[0]
    zip_file.extractall(path=savedir)
    if rename:
        os.rename(savedir.joinpath(zipped_filename), file)


def download_gsheet(url, savedir, filename, force=False):
    file = savedir.joinpath(filename)
    if not force and file.exists():
        return
    os.makedirs(savedir, exist_ok=True)
    print(f"Downloading from {url}")

    gc = gspread.oauth()
    gs = gc.open_by_url(url)
    dfs = {ws.title: pd.DataFrame(ws.get_all_records()) for ws in gs.worksheets()}

    if filename.endswith(".csv"):
        assert len(dfs) == 1
        df = list(dfs.values())[0]
        df.to_csv(file, index=False)
    elif filename.endswith(".xlsx"):
        with pd.ExcelWriter(file) as writer:
            for sheet_name, df in dfs.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        raise ValueError(f"Not supported file format: {filename}")


def upload_to_gsheet(df, url, sheet_name):
    print(f"Uploading to sheet {sheet_name} of {url}")

    gc = gspread.oauth()
    gs = gc.open_by_url(url)
    ws = gs.worksheet(sheet_name)

    ws.update([df.columns.values.tolist()] + df.values.tolist())
