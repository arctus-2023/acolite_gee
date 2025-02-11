import os, sys
import glob
from concurrent.futures import ProcessPoolExecutor
sys.path.append("/mnt/0_ARCTUS_Projects/19_SAGE-Port/src/python/acolite_gee")
os.environ['PROJ_LIB'] = '/home/tj/miniconda3/envs/intelliport/share/proj/'
import acolite as ac
from pathlib import Path

#s2_f = '*composite.tif'
#s2_f = "IMG_PHR1A_MS_201512201607389_ORT_fc7c5c90-501a-42b9-c2c8-c8a7ca25844c-1.TIF"
#l1d = "/mnt/0_ARCTUS_Projects/19_SAGE-Port/dataset/L1/Pleaides/*/"
#l1d = '/mnt/0_ARCTUS_Projects/19_SAGE-Port/dataset/L1/Pleaides/'
#l1d = '/mnt/0_ARCTUS_Projects/19_SAGE-Port/dataset/L1/Pleaides/dimapV2_PHR1B_acq20160906_del34f1b93e/'
#l1d = '/mnt/0_ARCTUS_Projects/19_SAGE-Port/dataset/L1/Planet/archives/Hatfield+Consultants+_+AECOM-+R15-+10_29_2021+-14_57_34+and+14_57_36_psscene_analytic_8b_udm2/'
#l2_dir = "/mnt/0_ARCTUS_Projects/19_SAGE-Port/dataset/L1/Planet/archives/Hatfield+Consultants+_+AECOM-+R15-+10_29_2021+-14_57_34+and+14_57_36_psscene_analytic_8b_udm2/"
#l2_dir = "/mnt/0_ARCTUS_Projects/19_SAGE-Port/dataset/L1/Pleaides/dimapV2_PHR1B_acq20190815_delb5c408e9/"
#l1d = '/mnt/0_ARCTUS_Projects/19_SAGE-Port/dataset/L1/Planet/last_version/Hatfield+Consultants+_+AECOM-+R15-+4_28_2023+-15_13_37+and+15_13_39_psscene_analytic_8b_udm2/'
#l1d = '/mnt/0_ARCTUS_Projects/19_SAGE-Port/dataset/L1/Planet/last_version/'
#l1d = '/mnt/0_ARCTUS_Projects/19_SAGE-Port/dataset/L1/Pleiades/WO_000243456_1_3_SAL24224502-3_ACQ_PNEO3_04734513309191+(2)/000243456_1_2_STD_A/'
#l1d = '/mnt/0_ARCTUS_Projects/19_SAGE-Port/dataset/L1/Pleiades/WO_000194483_1_4_SAL24178158-4_ACQ_PNEO4_04304911719484+(2)/000194483_1_4_STD_A/'
#l1d = '/mnt/0_ARCTUS_Projects/19_SAGE-Port/dataset/L1/Pleiades/WO_000194483_1_4_SAL24178158-4_ACQ_PNEO4_04304911719484+(2)/000194483_1_3_STD_A/'
#l1d = '/mnt/0_ARCTUS_Projects/19_SAGE-Port/dataset/L1/Pleiades/dimapV2_PHR1A_acq20180917_del518899ee/'
#l2_dir = os.path.join('/mnt/0_ARCTUS_Projects/19_SAGE-Port/dataset/L2/', os.path.basename(os.path.normpath(l1d)))

def process(l1c):
    out_name = 'Acolite_out'
    #p= Path(l1c)
    #l2_dir= str(p.parent)
    settings = {
        'inputfile': l1c,
        'output': os.path.join(l2_dir, out_name),
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

#def main():
#        data_files = glob.glob(os.path.join(l1d+'*psscene_analytic*'))
#        #dirname = os.listdir(data_files[0])
#        print(data_files)
#        #fnames = glob.glob(data_files[0] + '*/*/*R*C*.TIF')
#        with ProcessPoolExecutor(max_workers=2) as executor:
#                executor.map(process, data_files)

#if __name__ == '__main__':
#   main()
planet_dir = '/mnt/0_ARCTUS_Projects/19_SAGE-Port/dataset/L1/Planet/'
l2_base_dir = '/mnt/0_ARCTUS_Projects/19_SAGE-Port/dataset/L2/Planet_Aco/'

for fname in  glob.glob(os.path.join(planet_dir,'**','composite.tif'), recursive=True):
    l2_dir = os.path.join(l2_base_dir, os.path.basename(os.path.dirname(os.path.normpath(fname))))
    l1d=os.path.dirname(os.path.normpath(fname))+'/'
    if os.path.exists(l2_dir):
        #print(f"Skipping {l1d} as {l2_dir} already exists.")
        continue
    print('THIS is the process to do', l1d)
    process(l1c=l1d)
#process(l1c=l1d)



