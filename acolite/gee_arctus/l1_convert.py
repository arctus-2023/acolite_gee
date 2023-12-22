import sys, os, glob, dateutil.parser, time
from osgeo import ogr, osr, gdal
import acolite as ac
import scipy.ndimage
import numpy as np

from .reader import LevelTOA, get_projection

def l1_convert(inputfile, output = None, settings = {},
                percentiles_compute = True,
                percentiles = (0,1,5,10,25,50,75,90,95,99,100),
                check_sensor = True,
                check_time = True,
                max_merge_time = 600, # seconds
                geometry_format='GeoTIFF', ## for gpt geometry
                verbosity = 5):

    import sys, os, glob, dateutil.parser, time
    from osgeo import ogr,osr,gdal
    import acolite as ac
    import scipy.ndimage
    import numpy as np
    t0 = time.time()

    if 'verbosity' in settings: verbosity = settings['verbosity']

    ## parse inputfile
    if type(inputfile) != list:
        if type(inputfile) == str:
            inputfile = inputfile.split(',')
        else:
            inputfile = list(inputfile)
    nscenes = len(inputfile)
    if verbosity > 1: print('Starting conversion of {} scenes'.format(nscenes))

    new = True
    warp_to = None

    setu = {}
    ofile = None
    ofiles = []
    for bundle in inputfile:
        l1toa = LevelTOA(l1tif=bundle)


        bundle_name = os.path.split(bundle)[-1]

        #if output is None: output = os.path.dirname(bundle)
        if verbosity > 1: print('Starting conversion of {}'.format(bundle))



        if verbosity > 1: print('Importing metadata from {}'.format(bundle))


        ## determine sensor
        sensor = l1toa.sensor

        ## merge sensor specific settings
        if new:
            setu = ac.acolite.settings.parse(sensor, settings=settings)
            verbosity = setu['verbosity']
            if output is None: output = setu['output']

            gains = setu['gains']
            gains_toa = setu['gains_toa']
            offsets = setu['offsets']
            offsets_toa = setu['offsets_toa']

            s2_target_res=setu['s2_target_res']

            geometry_type=setu['geometry_type']
            geometry_res=setu['geometry_res']
            geometry_override=setu['geometry_override']
            geometry_per_band=setu['geometry_per_band']
            geometry_fixed_footprint=setu['geometry_fixed_footprint']

            s2_include_auxillary = setu['s2_include_auxillary']
            s2_project_auxillary = setu['s2_project_auxillary']
            netcdf_projection = setu['netcdf_projection']

            dilate = setu['s2_dilate_blackfill']
            dilate_iterations = setu['s2_dilate_blackfill_iterations']

            output_geolocation=setu['output_geolocation']
            output_xy=setu['output_xy']
            output_geometry=setu['output_geometry']
            vname = setu['region_name']

            limit=setu['limit']
            ## check if ROI polygon is given
            if setu['polylakes']:
                poly = ac.shared.polylakes(setu['polylakes_database'])
                setu['polygon_limit'] = False
            else:
                poly = setu['polygon']


            ## check if merging settings make sense
            merge_tiles = setu['merge_tiles']
            merge_zones = setu['merge_zones']
            extend_region = setu['extend_region']
        sub = None

        dtime = dateutil.parser.parse(l1toa.sensing_time)

        doy = dtime.strftime('%j')
        se_distance = ac.shared.distance_se(doy)
        isodate = dtime.isoformat()

        grmeta = None

        dct = get_projection(l1toa.meta)
        global_dims = dct['dimensions']

        #mgrs_tile = meta['PRODUCT_URI'].split('_')[-2]
        mgrs_tile = l1toa.composite_tiles

        ## scene average geometry
        sza = l1toa.theta_s
        saa = l1toa.azimuth_s
        vza = l1toa.theta_v
        vaa = l1toa.azimuth_v
        raa = np.abs(saa-vaa)
        while raa > 180: raa = abs(raa-360)

        ## read rsr
        rsrf = ac.path+'/data/RSR/{}.txt'.format(sensor)
        rsr, rsr_bands = ac.shared.rsr_read(rsrf)
        waves = np.arange(250, 2500)/1000
        waves_mu = ac.shared.rsr_convolute_dict(waves, waves, rsr)
        waves_names = {'{}'.format(b):'{:.0f}'.format(waves_mu[b]*1000) for b in waves_mu}

        ## get F0 - not stricty necessary if using USGS reflectance
        f0 = ac.shared.f0_get(f0_dataset=setu['solar_irradiance_reference'])
        f0_b = ac.shared.rsr_convolute_dict(np.asarray(f0['wave'])/1000, np.asarray(f0['data'])*10, rsr)

        granule = ''

        ## make global attributes for L1R NetCDF
        gatts = {'sensor':sensor, 'isodate':isodate, 'global_dims':global_dims,
                 'sza':sza, 'vza':vza, 'raa':raa, 'vaa': vaa, 'saa': saa, 'se_distance': se_distance,
                 'mus': np.cos(sza*(np.pi/180.)), 'granule': granule, 'mgrs_tile': mgrs_tile,
                 'acolite_file_type': 'L1R'}

        gatts['tile_code'] = '-'.join(l1toa.composite_tiles)
        stime = dateutil.parser.parse(gatts['isodate'])

        oname = '{}_{}_{}'.format(gatts['sensor'], stime.strftime('%Y_%m_%d_%H_%M_%S'), gatts['tile_code'])
        if vname != '': oname+='_{}'.format(vname)

        ## output file information
        if (merge_tiles is False) | (ofile is None):
            ofile = '{}/{}_L1R.nc'.format(output, oname)
            gatts['oname'] = oname
            gatts['ofile'] = ofile
        elif (merge_tiles) & (ofile is None):
            ofile = '{}/{}_L1R.nc'.format(output, oname)
            gatts['oname'] = oname
            gatts['ofile'] = ofile

        ## add band info to gatts
        for b in rsr_bands:
            gatts['{}_wave'.format(b)] = waves_mu[b]*1000
            gatts['{}_name'.format(b)] = waves_names[b]
            gatts['{}_f0'.format(b)] = f0_b[b]
            #if b in fmeta:
            #    fmeta[b]['f0'] = f0_b[b]
            #    fmeta[b]['se_distance'] = gatts['se_distance']

        ## get scene projection and extent
        # dct = get_projection(l1toa.meta)

        ## full scene
        gatts['scene_xrange'] = dct['xrange']
        gatts['scene_yrange'] = dct['yrange']
        gatts['scene_proj4_string'] = dct['proj4_string']
        gatts['scene_pixel_size'] = dct['pixel_size']
        gatts['scene_dims'] = dct['dimensions']
        if 'zone' in dct: gatts['scene_zone'] = dct['zone']


        ##
        if ((merge_tiles is False) & (merge_zones is False)): warp_to = None

        dct_prj = {k:dct[k] for k in dct}

        ## get projection info for netcdf
        if netcdf_projection:
            nc_projection = ac.shared.projection_netcdf(dct_prj, add_half_pixel=True)
        else:
            nc_projection = None

        ## save projection keys in gatts
        pkeys = ['xrange', 'yrange', 'proj4_string', 'pixel_size', 'zone']
        for k in pkeys:
            if k in dct_prj: gatts[k] = dct_prj[k]

        ## with subsetting fix the offsets should not be required 2021-10-28
        xyr = [min(dct_prj['xrange']),
               min(dct_prj['yrange']),
               max(dct_prj['xrange']),
               max(dct_prj['yrange']),
               dct_prj['proj4_string']]

        ## warp settings for read_band
        res_method = 'average'
        warp_to = (dct_prj['proj4_string'], xyr, dct_prj['pixel_size'][0],dct_prj['pixel_size'][1], res_method)

        ## store scene and output dimensions
        gatts['scene_dims'] = dct['ydim'], dct['xdim']
        gatts['global_dims'] = dct_prj['dimensions']

        ## new file for every bundle if not merging
        if (merge_tiles is False):
            new = True
            new_pan = True


        ## start the conversion
        ## write geometry
        vaa_arr = np.full(l1toa.dimension, vaa, dtype=np.float32)
        saa_arr = np.full(l1toa.dimension, saa, dtype=np.float32)
        if (output_geometry):
            if verbosity > 1: print('Reading per pixel geometry')

            if setu['s2_write_vaa']:
                ac.output.nc_write(ofile, 'vaa', vaa_arr, replace_nan=True,
                                        attributes=gatts, new=new, nc_projection=nc_projection,
                                                netcdf_compression=setu['netcdf_compression'],
                                                netcdf_compression_level=setu['netcdf_compression_level'])
                new = False
                if verbosity > 1: print('Wrote vaa {}'.format(vaa_arr.shape))

            if setu['s2_write_saa']:
                ac.output.nc_write(ofile, 'saa', saa_arr, replace_nan=True,
                                        attributes=gatts, new=new, nc_projection=nc_projection,
                                                netcdf_compression=setu['netcdf_compression'],
                                                netcdf_compression_level=setu['netcdf_compression_level'])
                new = False
                if verbosity > 1: print('Wrote saa {}'.format(saa_arr.shape))

            ## compute relative azimuth angle
            raa = np.abs(saa_arr-vaa_arr)
            ## raa along 180 degree symmetry
            tmp = np.where(raa>180)
            raa[tmp]=np.abs(raa[tmp] - 360)
            # raa[mask] = np.nan
            vaa_arr, saa_arr = None,  None

            ac.output.nc_write(ofile, 'raa', raa, replace_nan=True,
                                    attributes=gatts, new=new, nc_projection=nc_projection,
                                                netcdf_compression=setu['netcdf_compression'],
                                                netcdf_compression_level=setu['netcdf_compression_level'])
            if verbosity > 1: print('Wrote raa {}'.format(raa.shape))
            raa = None
            new = False
            vza_arr = np.full(l1toa.dimension,vza,dtype=np.float32)
            ac.output.nc_write(ofile, 'vza', vza_arr, replace_nan=True,
                                netcdf_compression=setu['netcdf_compression'],
                                netcdf_compression_level=setu['netcdf_compression_level'])
            if verbosity > 1: print('Wrote vza {}'.format(vza_arr.shape))

            sza_arr = np.full(l1toa.dimension, sza, dtype=np.float32)
            ac.output.nc_write(ofile, 'sza', sza_arr, replace_nan=True,
                                netcdf_compression=setu['netcdf_compression'],
                                netcdf_compression_level=setu['netcdf_compression_level'])

            if verbosity > 1: print('Wrote sza {}'.format(sza_arr.shape))
            sza_arr = None
            vza_arr = None

            ## write per band geometry
            ## delete sun azimuth & mask
            saa = None
            mask = None

        ## write lat/lon
        if (output_geolocation):
            if (os.path.exists(ofile) & (not new)):
                datasets = ac.shared.nc_datasets(ofile)
            else:
                datasets = []
            if ('lat' not in datasets) or ('lon' not in datasets):
                if verbosity > 1: print('Writing geolocation lon/lat')
                lon, lat = ac.shared.projection_geo(dct_prj, add_half_pixel=True)
                print(lon.shape)
                ac.output.nc_write(ofile, 'lon', lon, attributes=gatts, new=new, double=True,
                                    nc_projection=nc_projection,
                                    netcdf_compression=setu['netcdf_compression'],
                                    netcdf_compression_level=setu['netcdf_compression_level'])
                lon = None
                if verbosity > 1: print('Wrote lon')
                print(lat.shape)
                ac.output.nc_write(ofile, 'lat', lat, double=True,
                                    netcdf_compression=setu['netcdf_compression'],
                                    netcdf_compression_level=setu['netcdf_compression_level'])
                lat = None
                if verbosity > 1: print('Wrote lat')
                new=False

        ## auxillary data

        ## write TOA bands
        quant = 1e4
        nodata = 0

        if verbosity > 1: print('Converting bands')

        l1toa_data_dic = l1toa.read_to_dic()
        for bi, b in enumerate(rsr_bands):
            Bn = 'B{}'.format(b)
            if Bn not in l1toa.band_names: continue

            if b in waves_names:
                data = l1toa_data_dic[f'B{b}']
                data_mask = data == nodata

                data = data.astype(np.float32)

                data /= quant
                data[data_mask] = np.nan

                ds = 'rhot_{}'.format(waves_names[b])
                ds_att = {'wavelength':waves_mu[b]*1000}

                #for k in band_data: ds_att[k] = band_data[k][b]
                if percentiles_compute:
                    ds_att['percentiles'] = percentiles
                    ds_att['percentiles_data'] = np.nanpercentile(data, percentiles)

                ## write to ms file
                ac.output.nc_write(ofile, ds, data, replace_nan=True, attributes=gatts, new=new,
                                    dataset_attributes = ds_att, nc_projection=nc_projection,
                                    netcdf_compression=setu['netcdf_compression'],
                                    netcdf_compression_level=setu['netcdf_compression_level'],
                                    netcdf_compression_least_significant_digit=setu['netcdf_compression_least_significant_digit'])
                new = False
                if verbosity > 1: print('Converting bands: Wrote {} ({})'.format(ds, data.shape))
            else:
                continue

        if verbosity > 1:
            print('Conversion took {:.1f} seconds'.format(time.time()-t0))
            print('Created {}'.format(ofile))

        if limit is not None: sub = None
        if ofile not in ofiles: ofiles.append(ofile)

    return(ofiles, setu)

