import sys, os, time
acol_folder = '/mnt/0_ARCTUS_Projects/19_SAGE-Port/src/python/'
sys.path.append(acol_folder+"/acolite_gee")
import acolite as ac

l1c="/mnt/0_ARCTUS_Projects/19_SAGE-Port/dataset/L1/Pleiades/WO_000224478_1_3_SAL24206904-3_ACQ_PNEO3_04803413386209+(2)/000224478_1_2_STD_A/"
settings = {
        'inputfile': l1c,
        'output': "/mnt/0_ARCTUS_Projects/19_SAGE-Port/dataset/L2/",
        'l2w_parameters': ['rhorc_*', 'rhos_*','Rrs_*','spm_nechad2010','tur_nechad2010'],
        'output_rhorc': False,
        'l1r_export_geotiff': True,
        'l2r_export_geotiff': False,
        'l2w_export_geotiff': True,
        'dsf_aot_estimate': 'fixed',
        'atmospheric_correction': True,
        'ancillary_data': False,
        's2_target_res': 10,
        'l1r_export_geotiff_rgb': False,
        'l2r_export_geotiff_rgb': False,
        'use_gdal_merge_import': False,
        'reproject_inputfile': True
    }

ac.acolite.acolite_run(settings=settings, inputfile=l1c)
