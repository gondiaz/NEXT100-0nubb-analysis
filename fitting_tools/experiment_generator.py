import os
import glob
import numpy  as np
import pandas as pd

from invisible_cities.io.dst_io import load_dst


get_file_number = lambda filename: int(filename.split("/")[-1].split("_")[1].split(".")[0])

def get_pdata(filenames: list, nevents: int, /, background: str=None, region: str=None):

    np.random.shuffle(filenames)

    dsts = []
    selected = 0
    for filename in filenames:
        dst = load_dst(filename, "tracks", "events")
        in_file = dst.event.nunique()

        dst.loc[:, "nfile"]      = get_file_number(filename)

        if background:
            dst.loc[:, "background"] = background
        if region:
            dst.loc[:, "region"]     = region

        if (selected + in_file) < nevents:
            dsts.append(dst)
            selected += in_file
        elif (selected + in_file) >= nevents:
            n = nevents - selected
            events = np.random.choice(dst["event"].unique(), size=n, replace=False)
            dsts.append(dst.set_index("event").loc[events].reset_index())
            break

    return pd.concat(dsts)


def generate_background_experiment(time, table_filename, background_path_structure, /, backgrounds=["214Bi", "208Tl"]):

    """generates an experiment for a given time in seconds, using the efficiency from table_filename"""

    table_filename            = os.path.expandvars(table_filename)
    background_path_structure = os.path.expandvars(background_path_structure)

    tables = pd.read_excel(table_filename, sheet_name=None)

    pdata = []
    for background in backgrounds:
        table = tables[background]

        for (component, region), info in table.groupby(["Component", "Region"]):
            act = info["Activity (mBq)"]  .values[0] * 1e-3
            eff = info["Total efficiency"].values[0]

            nevents = np.random.poisson(act * eff * time)
            if (nevents == 0): continue

            path = background_path_structure.format(background=background, region=region)
            filenames = glob.glob(path + "*")
            dst = get_pdata(filenames, nevents, background, region)
            dst.loc[:, "component"] = component
            pdata.append(dst)

    return pd.concat(pdata)


def create_unique_event_number(df, /, index_name="pevent"):

    df = df.set_index(["event", "background", "region"])

    index = df.index
    counts = index.value_counts()

    ids = np.arange(index.nunique())
    ids = np.repeat(ids, counts)

    df.loc[counts.index, index_name] = ids

    return df.reset_index()
