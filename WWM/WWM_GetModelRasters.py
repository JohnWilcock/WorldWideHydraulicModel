from osgeo import gdal, ogr
import os
import math
import logging as logger

def clipRasters(inputRasterList,wDir,first_catchment_fn, out_srid):
    #set model directory
    mDir = os.path.join(wDir,"Model", "model", "shp")

    # Check whether the specified path exists or not
    if not os.path.exists(mDir):
        # Create a new directory because it does not exist
        os.makedirs(mDir)

    outfns = []
    outfnsASCII = []
    for x in inputRasterList:
        filename = os.path.splitext(os.path.basename(x))[0]
        logger.info("Creating raster " + filename)
        newFilename = os.path.splitext(os.path.basename(x))[0] + "clipped.tif"
        newFilenameASCII = os.path.splitext(os.path.basename(x))[0] + "clipped.asc"
        newFile = os.path.join(mDir, newFilename)
        newFileASCII = os.path.join(mDir, newFilenameASCII)
        outfns.append(newFile)
        outfnsASCII.append(newFileASCII)

        #get cell size in order to force this and prevent asciis with dx/dy
        raster = gdal.Open(x)
        gt = raster.GetGeoTransform()
        pX = gt[1]
        pY = -gt[5]
        #convert to metres using haversine formula assuming input is always in degrees (wgs84)
        # or use simple: Multiply the degrees of separation of longitude and latitude by 111,139
        pX = pX * 111139
        pY = pY * 111139

        #remember coord transform ! gdal.Warp(output_raster,input_raster,dstSRS='EPSG:4326')
        Output = gdal.Warp(newFile, x, cutlineDSName=first_catchment_fn, cropToCutline=True, dstNodata = 0, dstSRS= 'EPSG:'+ str(out_srid),  xRes=pX, yRes=pY)
        Output = None

        #convert to asc
        ds = gdal.Open(outfns[len(outfns)-1])
        ds = gdal.Translate(outfnsASCII[len(outfns)-1], ds)
        ds = None

    return outfnsASCII

