import os
from math import floor
from osgeo import gdal, ogr, osr
import struct


def createBuffer(inputfn, outputBufferfn, bufferDist, geomtype=ogr.wkbPolygon):
    inputds = ogr.Open(inputfn)
    inputlyr = inputds.GetLayer()

    # spatial ref system
    proj = inputlyr.GetSpatialRef()

    shpdriver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(outputBufferfn):
        shpdriver.DeleteDataSource(outputBufferfn)
    outputBufferds = shpdriver.CreateDataSource(outputBufferfn)
    bufferlyr = outputBufferds.CreateLayer(outputBufferfn, proj, geom_type=geomtype)
    featureDefn = bufferlyr.GetLayerDefn()


    for feature in inputlyr:
        ingeom = feature.GetGeometryRef()
        geomBuffer = ingeom.Buffer(bufferDist)

        outFeature = ogr.Feature(featureDefn)
        outFeature.SetGeometry(geomBuffer)
        bufferlyr.CreateFeature(outFeature)
        outFeature = None

    return outputBufferfn

