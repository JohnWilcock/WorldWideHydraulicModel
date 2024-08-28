import glob

from osgeo import gdal, ogr, osr
from osgeo.gdalconst import *
import numpy as np
import numpy
import sys
gdal.PushErrorHandler('CPLQuietErrorHandler')


def zonal_stats(feat, input_zone_polygon, input_value_raster):

    # Open data
    raster = gdal.Open(input_value_raster)
    shp = ogr.Open(input_zone_polygon)
    lyr = shp.GetLayer()

    # Get raster georeference info
    transform = raster.GetGeoTransform()
    xOrigin = transform[0]
    yOrigin = transform[3]
    pixelWidth = transform[1]
    pixelHeight = transform[5]

    # Reproject vector geometry to same projection as raster
    sourceSR = lyr.GetSpatialRef()
    targetSR = osr.SpatialReference()
    targetSR.ImportFromWkt(raster.GetProjectionRef())
    coordTrans = osr.CoordinateTransformation(sourceSR,targetSR)
    feat = lyr.GetNextFeature()
    geom = feat.GetGeometryRef()
    geom.Transform(coordTrans)

    # Get extent of feat
    geom = feat.GetGeometryRef()
    if (geom.GetGeometryName() == 'MULTIPOLYGON'):
        count = 0
        pointsX = []; pointsY = []
        for polygon in geom:
            geomInner = geom.GetGeometryRef(count)
            ring = geomInner.GetGeometryRef(0)
            numpoints = ring.GetPointCount()
            for p in range(numpoints):
                    lon, lat, z = ring.GetPoint(p)
                    pointsX.append(lon)
                    pointsY.append(lat)
            count += 1
    elif (geom.GetGeometryName() == 'POLYGON'):
        ring = geom.GetGeometryRef(0)
        numpoints = ring.GetPointCount()
        pointsX = []; pointsY = []
        for p in range(numpoints):
                lon, lat, z = ring.GetPoint(p)
                pointsX.append(lon)
                pointsY.append(lat)

    else:
        sys.exit("ERROR: Geometry needs to be either Polygon or Multipolygon")

    ymin = min(pointsX)
    ymax = max(pointsX)
    xmin = min(pointsY)
    xmax = max(pointsY)

    # Specify offset and rows and columns to read.  Needs to account for other hemispherss
    xoff = abs(int((xmin - xOrigin)/pixelWidth))
    yoff = abs(int((yOrigin - ymax)/pixelWidth))
    xcount = int((xmax - xmin)/pixelWidth)+1
    ycount = int((ymax - ymin)/pixelWidth)+1

    # Create memory target raster
    target_ds = gdal.GetDriverByName('MEM').Create('', xcount, ycount, 1, gdal.GDT_Byte)
    #target_ds = gdal.GetDriverByName('GTiff').Create(r'C:\Temp\W\out\test.tif', xcount, ycount, 1, gdal.GDT_Byte)
    target_ds.SetGeoTransform((
        xmin, pixelWidth, 0,
        ymax, 0, pixelHeight,
    ))

    # Create for target raster the same projection as for the value raster
    raster_srs = osr.SpatialReference()
    raster_srs.ImportFromWkt(raster.GetProjectionRef())
    target_ds.SetProjection(raster_srs.ExportToWkt())

    # Rasterize zone polygon to raster
    gdal.RasterizeLayer(target_ds, [1], lyr, burn_values=[1])

    # Read raster as arrays
    banddataraster = raster.GetRasterBand(1)
    dataraster = banddataraster.ReadAsArray(xoff, yoff, xcount, ycount).astype(float)

    bandmask = target_ds.GetRasterBand(1)
    datamask = bandmask.ReadAsArray(0, 0, xcount, ycount).astype(float)

    # Mask zone of raster
    zoneraster = numpy.ma.masked_array(dataraster,  datamask)

    # Calculate statistics of zonal raster
    return zoneraster.max() #numpy.average(zoneraster),numpy.mean(zoneraster),numpy.median(zoneraster),numpy.std(zoneraster),numpy.var(zoneraster)


def loop_zonal_stats(input_zone_polygon, input_value_raster):

    shp = ogr.Open(input_zone_polygon)
    lyr = shp.GetLayer()
    featList = range(lyr.GetFeatureCount())
    statDict = {}

    for FID in featList:
        feat = lyr.GetFeature(FID)
        maxValue = zonal_stats(feat, input_zone_polygon, input_value_raster)
        statDict[FID] = maxValue
    return statDict

def main(input_zone_polygon, input_value_raster):
    return loop_zonal_stats(input_zone_polygon, input_value_raster)


def getAMAX(AMAX_folder, disolved_catchment_UTM):
    filelist = [f for f in glob.glob(glob.escape(AMAX_folder) + "/*.tif") if ".tif" in f]
    AMAX_List = []
    for t in filelist:
        AMAX_List.append(main(disolved_catchment_UTM, t)[0])

    return AMAX_List

#a = getAMAX(r"C:\Users\johnwilcock\OneDrive - JBA Group\Documents\WWM\gdal\AMAX\1dAMAX", r"C:\Temp\W\out\UTM_full_catchment_disolved_buffer_12500.shp")
z=1