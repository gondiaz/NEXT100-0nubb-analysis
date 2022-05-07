import os
import sys
import glob
import pandas as pd
import numpy  as np
import tables as tb
from collections import namedtuple

from invisible_cities.core     import system_of_units as units

from invisible_cities.types.ic_types   import xy
from invisible_cities.evm              import event_model       as evm
from invisible_cities.reco             import paolina_functions as plf
from invisible_cities.cities.esmeralda import types_dict_tracks

from invisible_cities.io.dst_io  import df_writer
from invisible_cities.io.hits_io import hits_from_df

from invisible_cities.cities.components import index_tables

import argparse
parser = argparse.ArgumentParser(description="")
parser.add_argument("in_filename", type=str)
parser.add_argument("out_filename"  , type=str)
args = parser.parse_args()


in_filename  = os.path.expandvars(args.in_filename)
out_filename = os.path.expandvars(args.out_filename)
paolina_params = dict( vox_size         = [10 * units.mm, 10 * units.mm, 10 * units.mm]
                     , strict_vox_size  = False
                     , energy_threshold = 10 * units.keV
                     , min_voxels       = 3
                     , blob_radius      = 21 * units.mm
                     , max_num_hits     = 30000)


def track_blob_info_creator_extractor(vox_size         : [float, float, float],
                                      strict_vox_size  : bool                 ,
                                      energy_threshold : float                ,
                                      min_voxels       : int                  ,
                                      blob_radius      : float                ,
                                      max_num_hits     : int):
    def create_extract_track_blob_info(hitc):
        df = pd.DataFrame(columns=list(types_dict_tracks.keys()))
        if len(hitc.hits) > max_num_hits:
            return df, hitc, True
        #track_hits is a new Hitcollection object that contains hits belonging to tracks, and hits that couldnt be corrected
        track_hitc = evm.HitCollection(hitc.event, hitc.time)
        out_of_map = np.any(np.isnan([h.Ep for h in hitc.hits]))
        if out_of_map:
            #add nan hits to track_hits, the track_id will be -1
            track_hitc.hits.extend  ([h for h in hitc.hits if np.isnan   (h.Ep)])
            hits_without_nan       = [h for h in hitc.hits if np.isfinite(h.Ep)]
            #create new Hitcollection object but keep the name hitc
            hitc      = evm.HitCollection(hitc.event, hitc.time)
            hitc.hits = hits_without_nan

        if len(hitc.hits) > 0:
            voxels           = plf.voxelize_hits(hitc.hits, vox_size, strict_vox_size, evm.HitEnergy.Ep)
            (    mod_voxels,
             dropped_voxels) = plf.drop_end_point_voxels(voxels, energy_threshold, min_voxels)
            tracks           = plf.make_track_graphs(mod_voxels)

            for v in dropped_voxels:
                track_hitc.hits.extend(v.hits)

            vox_size_x = voxels[0].size[0]
            vox_size_y = voxels[0].size[1]
            vox_size_z = voxels[0].size[2]
            del(voxels)
            #sort tracks in energy
            tracks     = sorted(tracks, key=plf.get_track_energy, reverse=True)

            track_hits = []
            for c, t in enumerate(tracks, 0):
                tID = c
                energy = plf.get_track_energy(t)
                length = plf.length(t)
                numb_of_hits   = len([h for vox in t.nodes() for h in vox.hits])
                numb_of_voxels = len(t.nodes())
                numb_of_tracks = len(tracks   )
                pos   = [h.pos for v in t.nodes() for h in v.hits]
                x, y, z = map(np.array, zip(*pos))
                r = np.sqrt(x**2 + y**2)

                e     = [h.Ep for v in t.nodes() for h in v.hits]
                ave_pos = np.average(pos, weights=e, axis=0)
                ave_r   = np.average(r  , weights=e, axis=0)
                extr1, extr2 = plf.find_extrema(t)
                extr1_pos = extr1.XYZ
                extr2_pos = extr2.XYZ

                blob_pos1, blob_pos2 = plf.blob_centres(t, blob_radius)

                e_blob1, e_blob2, hits_blob1, hits_blob2 = plf.blob_energies_and_hits(t, blob_radius)
                overlap = float(sum(h.Ep for h in set(hits_blob1).intersection(set(hits_blob2))))
                list_of_vars = [hitc.event, tID, energy, length, numb_of_voxels,
                                numb_of_hits, numb_of_tracks,
                                min(x), min(y), min(z), min(r), max(x), max(y), max(z), max(r),
                                *ave_pos, ave_r, *extr1_pos,
                                *extr2_pos, *blob_pos1, *blob_pos2,
                                e_blob1, e_blob2, overlap,
                                vox_size_x, vox_size_y, vox_size_z]

                df.loc[c] = list_of_vars

                for vox in t.nodes():
                    for hit in vox.hits:
                        hit.track_id = tID
                        track_hits.append(hit)

            #change dtype of columns to match type of variables
            df = df.apply(lambda x : x.astype(types_dict_tracks[x.name]))
            track_hitc.hits.extend(track_hits)
        return df, mod_voxels, track_hitc, out_of_map

    return create_extract_track_blob_info



if __name__ == "__main__":

    columns = ["event", "peak", "track", "ntracks", "out_of_map",
               "nvoxels", "nhits", "length",
               "x", "y", "z", "r", "energy",
               "xmin", "ymin", "zmin", "rmin",
               "xmax", "ymax", "zmax", "rmax",
               "xb1", "yb1", "zb1", "eb1",
               "xb2", "yb2", "zb2", "eb2", "ovlp_e"]

    data   = namedtuple("data", columns) # auxiliar namedtuple

    paolina_algorithm = track_blob_info_creator_extractor(**paolina_params)

    out_df = pd.DataFrame(columns=columns)

    try:
        DECO = pd.read_hdf(in_filename, "DECO/Events")
    except KeyError:
        # save empty file
        with tb.open_file(out_filename, "w") as h5out:
            df_writer(h5out, out_df, group_name="tracks", table_name="events")
        index_tables(out_filename)
        sys.exit()

    for (event, peak), deco in DECO.groupby(["event", "npeak"]):

        # pre-proccess
        deco.loc[:, "time"] = 0
        deco.loc[:, "Ec"]   = deco["E"]
        deco.loc[:, "Ep"]   = deco["E"]
        deco.loc[:, ("Q", "Xrms", "Yrms", "nsipm")] = np.nan

        # Paolina
        hitc = hits_from_df(deco)[event]
        df, voxels, track_hitc, out_of_map = paolina_algorithm(hitc)

        for tid, track in df.groupby("trackID"):
            track = track.iloc[0]

            info = data(event=event, peak=peak, track=tid, ntracks=int(track.numb_of_tracks), out_of_map=out_of_map,
                        nvoxels=int(track.numb_of_voxels), nhits=int(track.numb_of_hits), length=track.length,
                        x=track.x_ave, y=track.y_ave, z=track.z_ave, r=track.r_ave, energy=track.energy,
                        xmin=track.x_min, ymin=track.y_min, zmin=track.z_min, rmin=track.r_min,
                        xmax=track.x_max, ymax=track.y_max, zmax=track.z_max, rmax=track.r_max,
                        xb1=track.blob1_x, yb1=track.blob1_y, zb1=track.blob1_z, eb1=track.eblob1,
                        xb2=track.blob2_x, yb2=track.blob2_y, zb2=track.blob2_z, eb2=track.eblob2,
                        ovlp_e=track.ovlp_blob_energy)

            out_df = out_df.append(info._asdict(), ignore_index=True)

    # write output per file
    with tb.open_file(out_filename, "w") as h5out:
        df_writer(h5out, out_df.apply(pd.to_numeric), group_name="tracks", table_name="events")
    index_tables(out_filename)
