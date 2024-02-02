import os,pathlib
import numpy as np
import rasterio


class LevelTOA(object):

    def __init__(self, l1tif, water_vapor=1.5, ozone=0.3,windspeed=5.0, pressure = 1013.25,**kwargs):
        '''
        @l1tif: l1 toa reflectance downloaded from gee
        '''
        basename = os.path.splitext(pathlib.Path(l1tif).name)[0]
        self.l1tif = l1tif
        # self.satellite = basename.split('_')[0][:2]
        # self.sensor = basename.split('_')[0][2:]
        self.aoi_name = basename.split('-')[-1]

        with rasterio.open(l1tif,'r') as dst:
            self.meta = dst.meta
            info = dst.tags()['info']
            descriptions = dst.descriptions

            self.dimension = dst.shape
        _temp = info.split(':')
        self.composite_scenes = [_.split(',')[0] for _ in _temp]
        self.composite_tiles = ['_'.join(_.split('_')[3:6])  for _ in self.composite_scenes]
        self.sensor = 'S2A_MSI'
        if self.composite_scenes[0][:3] == 'S2B':
            self.sensor = 'S2B_MSI'
        elif self.composite_scenes[0].startswith('LC08') or self.composite_scenes[0].startswith('L8'):
            self.sensor = 'L8_OLI'


        self.theta_v = np.asarray([float(_.split(',')[1]) for _ in _temp]).mean()
        self.theta_s = np.asarray([float(_.split(',')[2]) for _ in _temp]).mean()
        self.azimuth_v = np.asarray([float(_.split(',')[3]) for _ in _temp]).mean()
        self.azimuth_s = np.asarray([float(_.split(',')[4]) for _ in _temp]).mean()
        self.phi = abs(self.azimuth_v - self.azimuth_s)  if abs(self.azimuth_v - self.azimuth_s)<180 else 360-abs(self.azimuth_v - self.azimuth_s)

        self.water_vapor  = water_vapor
        self.ozone = ozone
        self.pressure = pressure
        self.windspeed = windspeed

        self.band_names = descriptions
        self.band_names_sim = [_[1:] for _ in self.band_names]
        sensing_date = basename.split('_')[1]
        self.sensing_time = f'{sensing_date} 15:40:00'

        self.if_download_auxiliary_data = kwargs['if_download_auxiliary_data'] if 'if_download_auxiliary_data' in kwargs else False
        self.auxiliary_data_source = kwargs['auxiliary_data_source'] if 'auxiliary_data_source' in kwargs else 'gee'



    def read_to_dic(self):
        '''
        read the data into a dictionary
        '''
        dic = {}
        with rasterio.open(self.l1tif) as dst:
            for i, band_name in enumerate(self.band_names):
                dic[band_name] = dst.read(i+1)


        # uoz_default = 0.3
        # uwv_default = 1.5
        # pressure = 1013.25

        dic['water_vapor'] = self.water_vapor
        dic['ozone'] = self.ozone
        dic['pressure'] = self.pressure

        if self.if_download_auxiliary_data:
            pass

        return dic

    def __download_auxiliary_data(self,do):
        '''
        surface pressure, windspeed,ozone,water vapor
        '''

        pass



def get_projection(meta, s2_target_res=10, return_grids=False):
    from pyproj import Proj

    is_utm = True
    is_ps = False

    proj = 'UTM'
    ellipsoid = 'WGS84'
    datum = 'WGS84'
    # cs_code = meta["HORIZONTAL_CS_CODE"]
    # cs_name = meta["HORIZONTAL_CS_NAME"]
    epsg =  meta['crs'].to_epsg()

    datum = 'WGS84'
    if 32600 < epsg <= 32660:
        zone = epsg - 32600
        proj4_list = ['+proj=utm',
                      '+zone={}'.format(zone),
                      '+datum={}'.format(datum),
                      '+units=m',
                      '+no_defs ']

    if 32700 < epsg <= 32760:
        zone = epsg - 32700
        proj4_list = ['+proj=utm',
                      '+zone={}'.format(zone),
                      '+south',
                      '+datum={}'.format(datum),
                      '+units=m',
                      '+no_defs ']

    zone_name = f'{zone}N'
    proj4_string = ' '.join(proj4_list)
    p = Proj(proj4_string)

    dimensions = meta['width'], meta['height']
    pixel_size = meta['transform'].a, abs(meta['transform'].e)
    x_lu,y_lu = meta['transform'].c, meta['transform'].f

    x_rb,y_rb = meta['transform']*dimensions

    dct = {'p': p, 'epsg': p.crs.to_epsg(),
           'xrange': [x_lu, x_rb],
           'yrange': [y_rb,y_lu],
           'proj4_string':proj4_string, 'dimensions':dimensions,
           'pixel_size': pixel_size, 'utm': is_utm, 'ps': is_ps}
    if is_utm: dct['zone'] : zone_name

    ## offset end of range by one pixel to make correct lat/lon x/y datasets
    #dct['xrange'][1]-=dct['pixel_size'][0]
    #dct['yrange'][1]-=dct['pixel_size'][1]
    #dct['xdim'] = int((dct['xrange'][1]-dct['xrange'][0])/dct['pixel_size'][0])+1
    #dct['ydim'] = int((dct['yrange'][1]-dct['yrange'][0])/dct['pixel_size'][1])+1

    # dct['xdim'] = int((dct['xrange'][1]-dct['xrange'][0])/dct['pixel_size'][0])
    # dct['ydim'] = int((dct['yrange'][1]-dct['yrange'][0])/dct['pixel_size'][1])

    # dct['xdim'] = int(np.ceil( (dct['xrange'][1] - dct['xrange'][0]) / dct['pixel_size'][0]))
    # dct['ydim'] = int(np.ceil( (dct['yrange'][1] - dct['yrange'][0]) / dct['pixel_size'][1]))

    dct['xdim'], dct['ydim'] = dimensions

    return(dct)




