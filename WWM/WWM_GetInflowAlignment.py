import os
from math import floor
from osgeo import gdal, ogr, osr
from math import atan2, degrees, radians
from WWM_GetBuffers import createBuffer


def get_angle(point_1, point_2):  # These can also be four parameters instead of two arrays
    angle = atan2(point_1[1] - point_2[1], point_1[0] - point_2[0])

    # Optional
    angle = degrees(angle)

    # OR
    #angle = radians(angle)

    return angle

def createInflowClips(pntBuffSmall, pntBuffLarge, firstCatchmentBuffSmall, firstCatchmentBuffLarge, wDir):


    outDriver = ogr.GetDriverByName("ESRI Shapefile")
    pntBuffSmallds = ogr.Open(pntBuffSmall)
    pntBuffLargeds = ogr.Open(pntBuffLarge)
    firstCatchmentBuffSmallds = ogr.Open(firstCatchmentBuffSmall)
    firstCatchmentBuffLargeds = ogr.Open(firstCatchmentBuffLarge)

    outbackline = os.path.join(wDir, "backline.shp")
    outfrontline = os.path.join(wDir, "frontline.shp")

    if os.path.exists(outbackline):
        outDriver.DeleteDataSource(outbackline)
    if os.path.exists(outfrontline):
        outDriver.DeleteDataSource(outfrontline)

    #outputs
    outbacklineds = outDriver.CreateDataSource(outbackline)
    outfrontlineds = outDriver.CreateDataSource(outfrontline)
    prj = firstCatchmentBuffSmallds.GetLayer().GetSpatialRef()

    outbacklinelyr = outbacklineds.CreateLayer('backline', prj, geom_type=ogr.wkbLineString)
    outfrontlinelyr = outfrontlineds.CreateLayer('frontline', prj, geom_type=ogr.wkbLineString)



    ogr.Layer.Clip(firstCatchmentBuffSmallds.GetLayer(), pntBuffSmallds.GetLayer(), outbacklinelyr)
    ogr.Layer.Clip(firstCatchmentBuffLargeds.GetLayer(), pntBuffSmallds.GetLayer(), outfrontlinelyr)

    FrontBackbearing, intersection_bearing = getstartXYFrontBackLines(outbacklinelyr, outfrontlinelyr, wDir)

    return FrontBackbearing, intersection_bearing, os.path.join(wDir, "frontline.shp")

def getstartXYFrontBackLines(outbacklinelyr, outfrontlinelyr, wDir):

    prj = outbacklinelyr.GetSpatialRef()
    inFeaturefront = outfrontlinelyr[0]
    inFeatureback = outbacklinelyr[0]# should only contain 1 feature
    # geometry
    geomFront = ogr.ForceToLineString(inFeaturefront.GetGeometryRef())
    geomBack = ogr.ForceToLineString(inFeatureback.GetGeometryRef())

    pntFront = geomFront.GetPoints()[0]
    pntBack = geomBack.GetPoints()[0]

    line = ogr.Geometry(ogr.wkbLineString)
    line.AddPoint(pntBack[0], pntBack[1])
    line.AddPoint(pntFront[0], pntFront[1])
    FrontBackbearing = get_angle(pntBack, pntFront)

    outDriver = ogr.GetDriverByName("ESRI Shapefile")
    FrontBackLinefn = os.path.join(wDir, "FrontBackLine.shp")
    if os.path.exists(FrontBackLinefn):
        outDriver.DeleteDataSource(FrontBackLinefn)

    FrontBackLineds = outDriver.CreateDataSource(FrontBackLinefn)
    FrontBackLinelyr = FrontBackLineds.CreateLayer('FrontBackConnectingLine', prj, geom_type=ogr.wkbLineString)
    FrontBackLinelyrDefn = FrontBackLinelyr.GetLayerDefn()
    outFeature = ogr.Feature(FrontBackLinelyrDefn)

    outFeature.SetGeometry(line.Clone())
    # Add new feature to output Layer
    FrontBackLinelyr.CreateFeature(outFeature)
    outFeature = None
    FrontBackLineds = None

    intersection_bearing = createInflowIntersections(FrontBackLinefn, wDir, outfrontlinelyr)

    return FrontBackbearing, intersection_bearing

def createInflowIntersections(FrontBackLinefn, wDir, outfrontlinelyr):
    #buffer frontbackAlignment and clip it to small catchment buffer
    prj = outfrontlinelyr.GetSpatialRef()
    outBufferfn = os.path.join(wDir, "FrontBackLine_buffer.shp")
    outFrontBackIntersectionfn = os.path.join(wDir, "FrontBackLine_intersection.shp")

    createBuffer(FrontBackLinefn, outBufferfn, 50)

    outDriver = ogr.GetDriverByName("ESRI Shapefile")
    outFrontBackIntersectionds = outDriver.CreateDataSource(outFrontBackIntersectionfn)
    outFrontBackIntersectionlyr = outFrontBackIntersectionds.CreateLayer('frontbacklineintersection', prj,  geom_type=ogr.wkbLineString)
    outBufferfnds = ogr.Open(outBufferfn)

    ogr.Layer.Clip(outfrontlinelyr, outBufferfnds.GetLayer(), outFrontBackIntersectionlyr)

    #get bearing
    inFeature = outFrontBackIntersectionlyr[0]


    if str(inFeature.GetGeometryRef()).find("ULTI") > 0: # if still multi geometry, only use first part, this will be the part connected to the end of the line
        geom = inFeature.GetGeometryRef().GetGeometryRef(0)
    else:
        geom = ogr.ForceToLineString(inFeature.GetGeometryRef())

    pntFront = geom.GetPoints()[0]
    pntBack = geom.GetPoints()[len(geom.GetPoints()) - 1]
    bearing = get_angle(pntFront, pntBack)

    return bearing


def fixInflowAlignment(refBearing, intersectbearing, inflow_BC_fn, wDir):
    step = 0
    start = 0
    stop = 0

    #check for current inflow output
    newFile = os.path.join(wDir, "2D_BC_Inflow.shp")
    driver = ogr.GetDriverByName("ESRI Shapefile")
    if os.path.exists(newFile):
        driver.DeleteDataSource(newFile)

    #open current file
    dataSource = driver.Open(inflow_BC_fn, 0)
    inflowlayer = dataSource.GetLayer()
    proj = inflowlayer.GetSpatialRef()

    #get line string (first only if multi)
    inFeature = inflowlayer[0]
    outLine = ogr.Geometry(ogr.wkbLineString)
    geom = None
    if str(inFeature.GetGeometryRef()).find("ULTI") > 0: # if still multi geometry, only use first part, this will be the part connected to the end of the line
        geom = inFeature.GetGeometryRef().GetGeometryRef(0)
    else:
        geom = ogr.ForceToLineString(inFeature.GetGeometryRef())


    #create new file
    fixedInflowds = driver.CreateDataSource(newFile)
    fixedInflowlyr = fixedInflowds.CreateLayer("_2D_BC_Inflow", proj, geom_type=ogr.wkbLineString)

    #whats the difference in line bearing ? this will determine if the inflow line is LB to RB(correct) or RB to LB(wrong)
    bearingDiff = refBearing - intersectbearing
    if bearingDiff > 0 and bearingDiff < 180 or bearingDiff > -360 and bearingDiff < -180:
        #its in the correct alignment, save to new file
        step = 1
        start = 0
        stop = len(geom.GetPoints())
    else:
        #its in the wrong alignment, flip the line, then save to new file
        step = -1
        start = len(geom.GetPoints()) - 1
        stop = -1
    for n in range(start, stop, step):
        outLine.AddPoint_2D(geom.GetPoints()[n][0], geom.GetPoints()[n][1])

    outFeature = ogr.Feature(fixedInflowlyr.GetLayerDefn())
    outFeature.SetGeometry(outLine.Clone())
    fixedInflowlyr.CreateFeature(outFeature)
    return newFile

# a,b = createInflowClips(r"C:\Temp\W\out\UTM_pnt1_buffer_0_01.shp",r"C:\Temp\W\out\UTM_pnt1_buffer_0_02.shp", r"C:\Temp\W\out\UTM_first_catchment_buffer_0_005.shp",r"C:\Temp\W\out\UTM_first_catchment_buffer_M0_005.shp", r"C:\Temp\W\out")
# c = get_angle([8000,5000], [8500,5000])
#fixInflowAlignment(-144,-8, r"C:\Temp\W\out\FrontLine.shp" , r"C:\Temp\W\out")
z=1
