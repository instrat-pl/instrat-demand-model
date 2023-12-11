from pathlib import Path
import inspect
import logging
import plotly.graph_objs as go
import locale


def project_dir(*path):
    root = (
        Path(inspect.getframeinfo(inspect.currentframe()).filename).resolve().parents[2]
    )
    return Path(root, *path)


def data_dir(*path):
    return project_dir("data", *path)


def plots_dir(*path):
    return project_dir("plots", *path)

"""
locale.setlocale(locale.LC_COLLATE, "pl_PL.UTF-8 ")

def local_sort(val):
    if isinstance(val, str):
        return locale.strxfrm(val)
    else:
        # vectorized version
        return [locale.strxfrm(x) for x in val]
"""

def make_instrat_template():
    template = go.layout.Template()
    template.layout.title.font = dict(
        family="Work Sans Medium, sans-serif", size=18, color="black"
    )
    template.layout.font = dict(
        family="Work Sans Light, sans-serif", size=13, color="black"
    )
    # template.layout.colorway = [
    #     "#000000",
    #     "#c0843f",
    #     "#5f468f",
    #     "#1d6995",
    #     "#38a5a4",
    #     "#0f8454",
    #     "#73ae48",
    #     "#ecac08",
    #     "#e07c05",
    #     "#cb503e",
    #     "#93346e",
    #     "#6f4070",
    #     "#666666",
    # ]
    return template
