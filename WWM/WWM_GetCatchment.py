# Import arcpy module
# import arcpy
import os
import sys
from osgeo import ogr
import logging as logger
global count
global isUSCatchment # should be "HAS" US catchment


def getFirstCatchment(MasterCatchmentID, tf, DSCatchment, Catchments, FirstCatchment):
    # Script arguments
    ID = MasterCatchmentID
    USCatchments = tf + "/US"

    logger.info("Start GetFirstCatchment...")
    logger.info("GetCatchment: " + DSCatchment)
    # logger.info("GetCatchment: " + Catchments)
    logger.info("GetCatchment: " + USCatchments)


    #get first catchment and output as the model boundary
    driver = ogr.GetDriverByName("ESRI Shapefile")
    ###dataSource = driver.Open(Catchments, 0)
    ###layer = dataSource.GetLayer()
    layer = Catchments
    layer.SetAttributeFilter("")
    layer.SetAttributeFilter('"HYBAS_ID" = ' + str(ID)) # filter layer to just master catchment ID

    outDriver = ogr.GetDriverByName("ESRI Shapefile")
    if os.path.exists(FirstCatchment):
        outDriver.DeleteDataSource(FirstCatchment)

    # Create the output shapefile
    outDataSource = outDriver.CreateDataSource(FirstCatchment)
    out_lyr_name = os.path.splitext(os.path.split(FirstCatchment)[1])[0]
    outLayer = outDataSource.CreateLayer(out_lyr_name, geom_type=ogr.wkbPolygon)

    # Add input Layer Fields to the output Layer if it is the one we want
    inLayerDefn = layer.GetLayerDefn()
    for i in range(0, inLayerDefn.GetFieldCount()):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        outLayer.CreateField(fieldDefn)

    # Get the output Layer's Feature Definition
    outLayerDefn = outLayer.GetLayerDefn()

    # Add features to the ouput Layer
    for inFeature in layer:
        # Create output Feature
        outFeature = ogr.Feature(outLayerDefn)

        # Add field values from input Layer
        for i in range(0, outLayerDefn.GetFieldCount()):
            outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(),
                                inFeature.GetField(i))

        # Set geometry as centroid
        geom = inFeature.GetGeometryRef()
        outFeature.SetGeometry(geom.Clone())
        # Add new feature to output Layer
        outLayer.CreateFeature(outFeature)
        outFeature = None

    # Save and close DataSources
    inDataSource = None
    outDataSource = None
    logger.info("GetCatchment: created first catchment")

    logger.info("GetCatchment: created blank shapefile full_catchment for US catchments")
    if os.path.exists(DSCatchment):
        outDriver.DeleteDataSource(DSCatchment)

    # Create the output shapefile
    outDataSource = outDriver.CreateDataSource(DSCatchment)
    out_lyr_name = os.path.splitext(os.path.split(DSCatchment)[1])[0]
    outLayer = outDataSource.CreateLayer(out_lyr_name, geom_type=ogr.wkbPolygon)

    # Add input Layer Fields to the output Layer if it is the one we want
    inLayerDefn = layer.GetLayerDefn()
    for i in range(0, inLayerDefn.GetFieldCount()):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        outLayer.CreateField(fieldDefn)
    inDataSource = None
    outDataSource = None

    logger.info("GetCatchment: detecting upstream catchments")
    #now find any upstream catchments (if they exist)
    getUSCatchments(Catchments, DSCatchment, ID)





def getUSCatchments(Catchments, USCatchments, ID):
    logger.info("start GetUSCatchment...")
    logger.info("GetUSCatchment: opening pre made layer: " + str(USCatchments))
    driver = ogr.GetDriverByName("ESRI Shapefile")
    global count
    global isUSCatchment

    #new us catchments in here
    dataSourceNewFile = driver.Open(USCatchments, 1)  # 1 for write

    USCatchmentslayer = dataSourceNewFile.GetLayer()
    USCatchmentsLayerDefn = USCatchmentslayer.GetLayerDefn()

    # full catchment layer
    ###dataSource = driver.Open(Catchments, 0)
    ###Catchmentslayer = dataSource.GetLayer()
    Catchmentslayer = Catchments
    CatchmentsLayerDefn = Catchmentslayer.GetLayerDefn()

    logger.info("GetUSCatchment: filtering based on NEXT_DOWN: " + str(ID))
    Catchmentslayer.SetAttributeFilter('"NEXT_DOWN" = ' + str(ID))  # filter to only show US catchment(s)

    ID_List = []

    #add us catchments to shapefile output
    logger.info("GetUSCatchment: add us catchments to shapefile output")
    # Append features to the USCatchmentslayer Layer
    for f in range(len(Catchmentslayer)): #   inFeature in Catchmentslayer:
        # Create output Feature
        inFeature = Catchmentslayer.GetNextFeature()
        outFeature = ogr.Feature(USCatchmentsLayerDefn)
        logger.info("Found geom of US catchment")

        # Add field values from input Layer
        for i in range(0, USCatchmentsLayerDefn.GetFieldCount()):
            outFeature.SetField(USCatchmentsLayerDefn.GetFieldDefn(i).GetNameRef(), inFeature.GetField(i))
            # logger.info("field: " + str(CatchmentsLayerDefn.GetFieldDefn(i).GetNameRef()))
            if str(USCatchmentsLayerDefn.GetFieldDefn(i).GetNameRef()) == "HYBAS_ID":
                logger.info("found US ID: " + str(inFeature.GetField(i)))
                ID_List.append(inFeature.GetField(i))
                continue

        # Set geometry as centroid
        geom = inFeature.GetGeometryRef()
        outFeature.SetGeometry(geom.Clone())
        # Add new feature to output Layer
        USCatchmentslayer.CreateFeature(outFeature)
        outFeature = None
        infeature = None
        isUSCatchment = True # flag to say there is at least 1 US catchment...so inflow can be calculated

    # Save and close DataSources
    dataSource = None
    dataSourceNewFile = None


    #cycle through the us catchemtns and see if they have any u/s
    logger.info("GetUSCatchment: detecting other US catchments ")
    for us_id in ID_List:
        logger.info("GetUSCatchment: found:" + str(us_id))
        getUSCatchments(Catchments, USCatchments, us_id) # this is reseting the curser so it cannot continue to cycle through other branches


def createDS(ds_name, ds_format, geom_type, srs, overwrite=True):
    drv = ogr.GetDriverByName(ds_format)
    if os.path.exists(ds_name) and overwrite is True:
        drv.DeleteDataSource(ds_name)

    ds = drv.CreateDataSource(ds_name)
    lyr_name = os.path.splitext(os.path.basename(ds_name))[0]
    lyr = ds.CreateLayer(lyr_name, srs, geom_type)
    return ds, lyr


def dissolve(input, output, multipoly=True, overwrite=True):
    ds = ogr.Open(input)
    lyr = ds.GetLayer()
    out_ds, out_lyr = createDS(output, ds.GetDriver().GetName(), lyr.GetGeomType(), lyr.GetSpatialRef(), overwrite)
    defn = out_lyr.GetLayerDefn()
    multi = ogr.Geometry(ogr.wkbMultiPolygon)
    for feat in lyr:
        if feat.geometry():
            feat.geometry().CloseRings() # this copies the first point to the end
            wkt = feat.geometry().ExportToWkt()
            multi.AddGeometryDirectly(ogr.CreateGeometryFromWkt(wkt))
    union = multi.UnionCascaded()
    if multipoly is False:
        for geom in union:
            poly = ogr.CreateGeometryFromWkb(geom.ExportToWkb())
            feat = ogr.Feature(defn)
            feat.SetGeometry(poly)
            out_lyr.CreateFeature(feat)
    else:
        out_feat = ogr.Feature(defn)
        out_feat.SetGeometry(union)
        out_lyr.CreateFeature(out_feat)
        out_ds.Destroy()
    ds.Destroy()
    return True


def getCatchment(MasterCatchmentID, MEMLayer, WorkingDir, MEMsource): # MEMLayer = hydosheds catchments level 12
    global count
    global isUSCatchment
    area = 0
    logFormatter = logger.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logger.getLogger()
    rootLogger.setLevel(logger.DEBUG)

    consoleHandler = logger.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)
    # inputs
    # 0 = ID of selected catchment
    # 1 = shapefile of the level 12 hydrosheds catchment layer for the correct contient
    # 2 = working directory for temp files/outputs

    # outputs
    # 0 = DSCatchment #upstream catchmentd
    # 1 = DSCatchmentDisolved
    # 2 = area
    # 4 = FirstCatchment

    # Script setup
    logger.info("Start GetCatchment...")
    count = 1
    isUSCatchment = False
    #Catchments = hydroshedsCatchmentShapefileLev12
    wDir = WorkingDir
    DSCatchment = os.path.join(wDir,"full_catchment.shp")
    FirstCatchment = os.path.join(wDir,"first_catchment.shp") #arcpy.GetParameterAsText(2)
    DSCatchmentDisolved = os.path.join(wDir,"full_catchment_disolved.shp")


    #open all catchments file to mem for speed
    driver = ogr.GetDriverByName("ESRI Shapefile")
    # dataSource = driver.Open(Catchments, 0)
    # Catchmentslayer = MEMsource.GetLayer()

    # # create an output datasource in memory
    # MEMdriver = ogr.GetDriverByName('MEMORY')
    # MEMsource = MEMdriver.CreateDataSource('memData')
    # # open the memory datasource with write access
    # MEMtmp = MEMdriver.Open('memData', 1)
    # MEMLayer = MEMsource.CopyLayer(Catchmentslayer, 'mem', ['OVERWRITE=YES'])


    tf = wDir
    getFirstCatchment(MasterCatchmentID, tf, DSCatchment,MEMLayer, FirstCatchment )

    if isUSCatchment:
        logger.info("GetCatchment: dissolving")
        dissolve(DSCatchment, DSCatchmentDisolved)

        #get area
        logger.info("GetCatchment: assessing area")
        area = 1
        driver = ogr.GetDriverByName("ESRI Shapefile")
        dataSource = driver.Open(DSCatchmentDisolved, 1)
        layer = dataSource.GetLayer()
        new_field = ogr.FieldDefn("Area", ogr.OFTReal)
        new_field.SetWidth(32)
        new_field.SetPrecision(2) #added line to set precision
        layer.CreateField(new_field)

        for feature in layer:
            geom = feature.GetGeometryRef()
            area = geom.GetArea()

        dataSource = None

    return DSCatchment, DSCatchmentDisolved, area, isUSCatchment,  FirstCatchment

# hsheds = "C:\Temp\W\hybas_eu_lev12_v1c.shp"
# out = "C:\Temp\W\out"
# a,b,c,d,e = getCatchment(2120696410, hsheds, out)
# z = 1+1
