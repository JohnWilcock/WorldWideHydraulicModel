import os
from math import floor
from osgeo import gdal, ogr
import struct

def getHeight(pnt1path, dtmpath):
    src_ds = gdal.Open(dtmpath)
    gt_forward = src_ds.GetGeoTransform()
    gt_reverse = gdal.InvGeoTransform(gt_forward)
    rb = src_ds.GetRasterBand(1)

    ds = ogr.Open(pnt1path)
    lyr = ds.GetLayer()
    for feat in lyr:
        geom = feat.GetGeometryRef()
        mx, my = geom.GetX(), geom.GetY()  # coord in map units

        # Convert from map to pixel coordinates.
        px, py = gdal.ApplyGeoTransform(gt_reverse, mx, my)
        px = floor(px)  # x pixel
        py = floor(py)  # y pixel

        structval = rb.ReadRaster(px, py, 1, 1, buf_type=gdal.GDT_UInt16)  # Assumes 16 bit int aka 'short' suitabke a only integer grid
        intval = struct.unpack('h', structval)  # use the 'short' format code (2 bytes) not int (4 bytes)

       # print(intval[0])  # intval is a tuple, length=1 as we only asked for 1 pixel value

    return intval[0]

def getHeights(p1,p2,DTM):
    p1dtm = getHeight(p1, DTM)
    p2dtm = getHeight(p2, DTM)
    return p1dtm, p2dtm




