#!/usr/bin/env python

# inst: university of bristol
# auth: jeison sosa
# mail: j.sosa@bristol.ac.uk / sosa.jeison@gmail.com

import subprocess
import numpy as np
import gdalutils as gu

void_demf = 'lidar_clip.tif'
fill_demf = 'OS_terrain_50_clip.tif'
nodata    = -9999 # non data value in both datasets

# Calculate delta surface with voids
def step_01():

    geo        = gu.get_geo(void_demf)
    void_dem   = gu.get_data(void_demf)
    fill_dem   = gu.get_data(fill_demf)
    delta_surf = void_dem - fill_dem

    delta_surf[(delta_surf>=8000) | (delta_surf<=-8000)] = nodata
    delta_surf[delta_surf==0] = nodata

    gu.write_raster(delta_surf,'delta_surf_wt_voids.tif',geo,'Float64',nodata)

# Create list of source points to interpolate
def step_02():

    subprocess.call(['gdal_translate','-of','XYZ','delta_surf_wt_voids.tif','delta_surf_wt_voids.xyz'])
    subprocess.call(['sed','s/ /,/g','delta_surf_wt_voids.xyz'],stdout=open('delta_surf_wt_voids.csv','w'))
    subprocess.call(['sed','-i','','/-9999/d','delta_surf_wt_voids.csv'])

    f = open('delta_surf_wt_voids.vrt','w')
    f.write('<OGRVRTDataSource>'+'\n')
    f.write('    <OGRVRTLayer name="delta_surf_wt_voids">'+'\n')
    f.write('        <SrcDataSource>delta_surf_wt_voids.csv</SrcDataSource>'+'\n')
    f.write('        <GeometryType>wkbPoint</GeometryType>'+'\n')
    f.write('        <GeometryField encoding="PointFromColumns" x="field_1" y="field_2" z="field_3"/>'+'\n')
    f.write('    </OGRVRTLayer>'+'\n')
    f.write('</OGRVRTDataSource>'+'\n')
    f.close()

# Interpolation
def step_03():

    geo  = gu.get_geo(void_demf)
    nx   = geo[4]
    ny   = geo[5]
    xmin = geo[0]
    xmax = geo[2]
    ymin = geo[1]
    ymax = geo[3]

    subprocess.call(['gdal_grid','--config','GDAL_NUM_THREADS','ALL_CPUS',
                    '-a','invdist',
                    '-of','GTiff',
                    '-ot','Float64',
                    '-txe', str(xmin), str(xmax),
                    '-tye', str(ymin), str(ymax),
                    '-outsize', str(nx), str(ny),
                    '-l','delta_surf_wt_voids',
                    'delta_surf_wt_voids.vrt','delta_surf_interp.tif'])

# Get final raster
def step_04():

    A = gu.get_data('delta_surf_interp.tif')
    B = gu.get_data(fill_demf)
    C = gu.get_data(void_demf)
    geo = gu.get_geo(void_demf)
    mysum = A+B
    final = np.where(C==nodata,mysum,C)
    
    final[(final>=8000) | (final<=-8000)] = nodata
    gu.write_raster(final,'dem.tif',geo,'Float64',nodata)

# Running the program
def main():
    step_01()
    step_02()
    step_03()
    step_04()
main()
