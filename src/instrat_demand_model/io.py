import itertools
import pandas as pd


def read_excel(file, sheet_var=None, sheet_name=0, ignore_sheets=False):
    if sheet_var is None:
        return pd.read_excel(file, sheet_name=sheet_name)
    else:
        dfs = pd.read_excel(file, sheet_name=None)
        if ignore_sheets:
            dfs = {key: df for key, df in dfs.items() if not key.startswith("#")}
        df_full = pd.concat([df.assign(**{sheet_var: val}) for val, df in dfs.items()])
        df_full[sheet_var] = pd.to_numeric(df_full[sheet_var], errors="ignore")
        return df_full


def product_dict(**kwargs):
    keys = kwargs.keys()
    vals = kwargs.values()
    return [dict(zip(keys, instance)) for instance in itertools.product(*vals)]


def dict_to_str(d):
    return ";".join(f"{key}={value}" for key, value in d.items())
