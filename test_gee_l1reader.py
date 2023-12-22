import os, sys
sys.path.append("c:/Users/pany0/WorkSpace/pycharm_proj/acolite")

import acolite as ac

# s2_f = 'S2A_MSIL1C_20211221T155701_N0301_R054_T18TXR_20211221T175233.SAFE'
# l1d = "C:/Users/pany0/WorkSpace/projects/SmartHabour"
# out_dir = "C:/Users/pany0/WorkSpace/projects/SmartHabour"

s2_f = 'S2_2019-07-26_L1TOA-SecterA.tif'
l1d = "D:/SDBs/BdC/data/s2_gee/l1_toa/SecterA"
out_dir = "D:/SDBs/BdC/data/s2_gee/l2_acolite"


def process(l1c):
    out_name = 'test_merge_s2'
    # settings = {
    #     'inputfile': l1c,
    #     'output': os.path.join(out_dir, out_name),
    #     'limit': limit,
    #     'l2w_parameters': 'Rrs_*',
    #     'output_rhorc': False,
    #     'l2r_export_geotiff': False,
    #     'l2w_export_geotiff': False,
    #     'atmospheric_correction': True,
    #     'aerosol_correction': 'dark_spectrum',
    #     'adjacency_correction': False,
    #     'dsf_aot_estimate': 'fixed',
    #     'ancillary_data': False,
    #     's2_target_res': 10,
    #     'l2w_mask': False,
    #     'dsf_residual_glint_correction': False,
    #     'l2w_mask_negative_rhow': False,
    #     'map_raster': True,
    #     'l1r_export_geotiff_rgb': True,
    #     'l2r_export_geotiff_rgb': True
    # }

    settings = {
            'inputfile':l1c,
            'output': os.path.join(out_dir,out_name),
            'merge_tiles': False,
            # 'limit': limit,## south, west,north,east
            # 'polygon':os.path.join(l1d, 'aoi_small.geojson'),
            # 'polygon_limit':True,
            'l2w_parameters': 'Rrs_*',
            'output_rhorc': True,
            'l1r_export_geotiff': False,
            'l2r_export_geotiff': False,
            'l2w_export_geotiff': False,
            'dsf_aot_estimate':'fixed',
            'atmospheric_correction':True,
            'ancillary_data': True,
            'map_raster': False,
            's2_target_res': 10,
            'l1r_export_geotiff_rgb':True,
            'l2r_export_geotiff_rgb':True,
            'use_gdal_merge_import':False
            }

    print(settings)
    ac.acolite.acolite_run(settings=settings)


process(l1c = os.path.join(l1d,s2_f))