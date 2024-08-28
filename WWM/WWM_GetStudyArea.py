import os
import math
import sys

import osgeo.ogr as ogr
import osgeo.osr as osr
import numpy as np

import WWM_GetBounds
import WWM_GetCatchment, WWM_GetRiver
import WWM_GetBuffers, WWM_SetModelFiles, WWM_GetRain, WWM_GetAMAX, WWM_GetModelRasters, WWM_GetHeight, WWM_WriteModelControlFiles
import configparser

def convert_wgs_to_utm(lon, lat):
    utm_band = str((math.floor((lon + 180) / 6) % 60) + 1)
    if len(utm_band) == 1:
        utm_band = '0' + utm_band
    if lat >= 0:
        epsg_code = '326' + utm_band
    else:
        epsg_code = '327' + utm_band
    return int(epsg_code)


def transformShp(inshp, outshp,out_epsg, in_epsg=4326):
    # shapefile with the from projection
    driver = ogr.GetDriverByName("ESRI Shapefile")
    if os.path.exists(outshp):
        driver.DeleteDataSource(outshp)
    dataSource = driver.Open(inshp, 1)
    layer = dataSource.GetLayer()
    layer_defn = layer.GetLayerDefn()

    # set spatial reference and transformation
    sourceprj = osr.SpatialReference()
    sourceprj.ImportFromEPSG(in_epsg)
    targetprj = osr.SpatialReference()
    targetprj.ImportFromEPSG(out_epsg)
    sourceprj.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER) #stupid thing this wgs84 should be y/x rather than x/y
    transform = osr.CoordinateTransformation(sourceprj, targetprj)

    newshp_dr = ogr.GetDriverByName("Esri Shapefile")
    newshp_ds = newshp_dr.CreateDataSource(outshp)
    newshp_outlayer = newshp_ds.CreateLayer('UTM', targetprj, layer_defn.GetGeomType())

    # set fields in new shapefile
    for i in range(0, layer_defn.GetFieldCount()):
        fieldDefn = layer_defn.GetFieldDefn(i)
        newshp_outlayer.CreateField(fieldDefn)


    # apply transformation

    defn = newshp_outlayer.GetLayerDefn()
    for feature in layer:
        transformed = feature.GetGeometryRef()
        transformed.Transform(transform)

        geom = ogr.CreateGeometryFromWkb(transformed.ExportToWkb())
        feat = ogr.Feature(defn)
        # Add field values from input Layer
        for i in range(0, defn.GetFieldCount()):
            feat.SetField(defn.GetFieldDefn(i).GetNameRef(), feature.GetField(i))

        feat.SetGeometry(geom)
        newshp_outlayer.CreateFeature(feat)
        feat = None

    ds = None
    newshp_ds = None




def getCatchmentID(studyPointFile, HydroShedsCatchments, wDir):
    #find intersecting catchment with study area point
    driver = ogr.GetDriverByName("ESRI Shapefile")
    outshp = os.path.join(wDir, "intersectedCatchments.shp")
    if os.path.exists(outshp):
        driver.DeleteDataSource(outshp)
    hydroshedsDS = driver.Open(HydroShedsCatchments, 0) # need full filepath
    outshpDS = driver.CreateDataSource(outshp)
    studyPointFileds = driver.Open(studyPointFile, 0)
    hydroshedslayer = hydroshedsDS.GetLayer()
    outshplayer = outshpDS.CreateLayer("catchmemt", geom_type=ogr.wkbPolygon)
    studyPointFilelayer = studyPointFileds.GetLayer()
    hydroshedslayer_defn = hydroshedslayer.GetLayerDefn()
    studyPointFilelayer_defn = studyPointFilelayer.GetLayerDefn()



    #open all catchments file to mem for speed
    # create an output datasource in memory
    MEMdriver = ogr.GetDriverByName('MEMORY')
    MEMsource = MEMdriver.CreateDataSource('memData')
    # open the memory datasource with write access
    MEMtmp = MEMdriver.Open('memData', 1)
    # MEMLayer = MEMsource.CreateLayer('mem', geom_type=ogr.wkbLineString)
    MEMLayer = MEMsource.CopyLayer(hydroshedslayer, 'mem', ['OVERWRITE=YES'])




    # set fields in new shapefile
    for i in range(0, hydroshedslayer_defn.GetFieldCount()):
        fieldDefn = hydroshedslayer_defn.GetFieldDefn(i)
        outshplayer.CreateField(fieldDefn)
    outshplayer_defn = outshplayer.GetLayerDefn()
    outFeature = ogr.Feature(outshplayer_defn)

    catchmentID = ""
    for i in range(0, len(MEMLayer)):
        d = MEMLayer[i]
        e = d.GetGeometryRef()
        f = studyPointFilelayer[0]
        g = f.GetGeometryRef()
        if e.Intersects(g):
            # Set geometry
            #outFeature.SetGeometry(e.Clone())
            # set fields
            for j in range(0, outshplayer_defn.GetFieldCount()):
                #outFeature.SetField(outshplayer_defn.GetFieldDefn(j).GetNameRef(), d.GetField(j))
                if outshplayer_defn.GetFieldDefn(j).GetNameRef() == "HYBAS_ID":
                    catchmentID = d.GetField(j)
            #outshplayer.CreateFeature(outFeature)

    return catchmentID, MEMLayer, MEMsource



def inputToUTM(lat,lon, wDir):
    # create shapefile in wgs84
    # set up the shapefile driver
    driver = ogr.GetDriverByName("ESRI Shapefile")

    # create the data source
    wgsshp = os.path.join(wDir,"StudyLocation4326.shp")
    utmshp = os.path.join(wDir, "StudyLocationUTM.shp")
    if os.path.exists(wgsshp):
        driver.DeleteDataSource(wgsshp)
    if os.path.exists(utmshp):
        driver.DeleteDataSource(utmshp)
    data_source = driver.CreateDataSource(wgsshp)

    # create the spatial reference, WGS84
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)

    # create the layer
    layer = data_source.CreateLayer("StudyLocation4326", srs, ogr.wkbPoint)

    # create the WKT for the feature using Python string formatting
    feature = ogr.Feature(layer.GetLayerDefn())
    wkt = "POINT(%f %f)" % (float(lon), float(lat))
    point = ogr.CreateGeometryFromWkt(wkt)
    # Set the feature geometry using the point
    feature.SetGeometry(point)
    # Create the feature in the layer (shapefile)
    layer.CreateFeature(feature)
    # Dereference the feature
    feature = None
    data_source = None

    #get first cacthment ID
    #get closest river id



    #get correct UTM ESPG
    out_srid = convert_wgs_to_utm(lon,lat)


    #project to UTm
    # set spatial reference and transformation
    transformShp(wgsshp, utmshp, out_srid)



    return wgsshp, out_srid

def load_config(config_filename):
    """
    Load and parse global configuration values from config file.

    :return: Global configuration values.
    :rtype: configparser.ConfigParser
    """
    # Get path to config file
    current_pkg = os.path.dirname(os.path.abspath(__file__))
    parent_pkg = os.path.dirname(current_pkg)
    config_file = os.path.join(current_pkg, config_filename)

    # Check whether the config file exists
    if not os.path.exists(config_file):
        raise IOError(f"Config file does not exist: '{config_file}'")

    # Parse config file
    config = configparser.ConfigParser()
    read_ok = config.read(config_file)

    # Check whether the config file was successfully parsed
    if not read_ok:
        raise IOError(f"Unable to read config from file: '{config_file}'")

    return config

def getHydrosheds(studyPointFile):
    scriptDir = os.path.dirname(os.path.realpath(sys.argv[0]))
    hsheds = os.path.join(scriptDir,"Hydrosheds", "Level1_all.shp")

    # get continent
    # find intersecting catchment with study area point
    driver = ogr.GetDriverByName("ESRI Shapefile")
    hydroshedsDS = driver.Open(hsheds, 0)
    studyPointFileds = driver.Open(studyPointFile, 0)
    hydroshedslayer = hydroshedsDS.GetLayer()
    studyPointFilelayer = studyPointFileds.GetLayer()
    hydroshedslayer_defn = hydroshedslayer.GetLayerDefn()
    studyPointFilelayer_defn = studyPointFilelayer.GetLayerDefn()

    amax = os.path.dirname(os.path.join(scriptDir,"AMAX", "1dAMAX", ""))
    landuse = os.path.join(scriptDir,"Hydrosheds", "LandCover", "GLOBCOVER_L4_200901_200912_V2.3.tif")

    catchments = ""
    dtm = ""
    rivers = ""
    for i in range(0, len(hydroshedslayer)):
        d = hydroshedslayer[i]
        e = d.GetGeometryRef()
        f = studyPointFilelayer[0]
        g = f.GetGeometryRef()
        if e.Intersects(g):
            # Set geometry
            # set fields
            for j in range(0, hydroshedslayer_defn.GetFieldCount()):
                if hydroshedslayer_defn.GetFieldDefn(j).GetNameRef() == "Name":
                    catchments = os.path.join(scriptDir, "Hydrosheds", "Basins", "hybas_" + d.GetField(j) + "_lev12_v1c.shp")
                    rivers = os.path.join(scriptDir, "Hydrosheds", "Rivers", d.GetField(j) + "_riv_15s.shp")
                elif hydroshedslayer_defn.GetFieldDefn(j).GetNameRef() == "DTM90Name":
                    dtm = os.path.join(scriptDir, "Hydrosheds", "DTM", d.GetField(j) + ".tif")

    return catchments, dtm, rivers, amax, landuse


# load defaults
config = load_config('WWM_config.ini')
wDir = config.get('hydrosheds', 'wDir')
AEP = config.get('hydrosheds', 'AEP')
storm_duration_hrs = config.get('hydrosheds', 'storm_duration_hrs')
runoff_fraction = config.get('hydrosheds', 'runoff_fraction')

lat = 30.869
lon = 37.723

lat = -37.4933
lon = 145.4581

#CO
lat = 36.5278
lon = -117.85471


# get the study point from lat/lon
wgsshpfn, out_srid = inputToUTM(lat, lon, wDir) #lat lon

#spin up... which hsheds areas are needed
hsheds, DTM, hsheds_river, AMAX_folder, landuse  = getHydrosheds(wgsshpfn)

# get the catchment ID from point
a_catchment_id, b_mem_layer, c_mem_source = getCatchmentID(wgsshpfn, hsheds, wDir)

# get the catchment and upstream catchemnt from the ID
a_full_catchment_upstream_fn, b_full_catchment_upstream_disolved_fn, c_area_deg, d_is_us_catchment_boolean, e_first_catchment_fn = WWM_GetCatchment.getCatchment(a_catchment_id, b_mem_layer, wDir, c_mem_source)

# get the rivers/longest path
a_upstream_cells, b_centreline_river_fn, c_all_rivers_in_us_catchment_fn, d_pnt1, e_pnt2, f_length_in_x = WWM_GetRiver.getRiver(hsheds_river, wDir, b_full_catchment_upstream_disolved_fn, e_first_catchment_fn, d_is_us_catchment_boolean)

# convert all to UTM
UTM_convert_list = [a_full_catchment_upstream_fn, b_full_catchment_upstream_disolved_fn, e_first_catchment_fn, b_centreline_river_fn, c_all_rivers_in_us_catchment_fn, d_pnt1, e_pnt2 ]
driver = ogr.GetDriverByName("ESRI Shapefile")
UTM_fn = []
for t in range(len(UTM_convert_list)): #only do first if a rainfall catchment with no inflow
    if d_is_us_catchment_boolean or t == 2:
        n = UTM_convert_list[t]
        utmfile = os.path.join(os.path.dirname(n), "UTM_" + os.path.splitext(os.path.basename(n))[0] + ".shp")
        UTM_fn.append(os.path.join(os.path.dirname(n), "UTM_" + os.path.splitext(os.path.basename(n))[0] + ".shp"))
        if os.path.exists(utmfile):
            driver.DeleteDataSource(utmfile)
        transformShp(n, utmfile, out_srid)
    else:
        UTM_fn.append("")

# set buffers index 7 to 11
if d_is_us_catchment_boolean:
    UTM_fn.append(WWM_GetBuffers.createBuffer(UTM_fn[2], os.path.join(os.path.dirname(UTM_fn[2]), os.path.splitext(os.path.basename(UTM_fn[2]))[0] + "_buffer_M200.shp"), -200, ogr.wkbLineString))
    UTM_fn.append(WWM_GetBuffers.createBuffer(UTM_fn[2], os.path.join(os.path.dirname(UTM_fn[2]), os.path.splitext(os.path.basename(UTM_fn[2]))[0] + "_buffer_200.shp"), 200, ogr.wkbLineString))
    UTM_fn.append(WWM_GetBuffers.createBuffer(UTM_fn[1],  os.path.join(os.path.dirname(UTM_fn[1]), os.path.splitext(os.path.basename(UTM_fn[1]))[0] + "_buffer_12500.shp"), 12500))
    UTM_fn.append(WWM_GetBuffers.createBuffer(UTM_fn[5], os.path.join(os.path.dirname(UTM_fn[5]), os.path.splitext(os.path.basename(UTM_fn[5]))[0] + "_buffer_600.shp"), 600))
    UTM_fn.append(WWM_GetBuffers.createBuffer(UTM_fn[5], os.path.join(os.path.dirname(UTM_fn[5]), os.path.splitext(os.path.basename(UTM_fn[5]))[0] + "_buffer_1000.shp"), 1000))
else:
    UTM_fn.append(WWM_GetBuffers.createBuffer(UTM_fn[2], os.path.join(os.path.dirname(UTM_fn[2]), os.path.splitext(os.path.basename(UTM_fn[2]))[0] + "_buffer_M200.shp"), -200, ogr.wkbLineString))
    UTM_fn.append(WWM_GetBuffers.createBuffer(UTM_fn[2], os.path.join(os.path.dirname(UTM_fn[2]), os.path.splitext(os.path.basename(UTM_fn[2]))[0] + "_buffer_200.shp"), 200, ogr.wkbLineString))
    UTM_fn.append(WWM_GetBuffers.createBuffer(UTM_fn[2],  os.path.join(os.path.dirname(UTM_fn[2]), os.path.splitext(os.path.basename(UTM_fn[2]))[0] + "_buffer_12500.shp"), 25000))
    UTM_fn.append(WWM_GetBuffers.createBuffer(UTM_fn[2], os.path.join(os.path.dirname(UTM_fn[2]), os.path.splitext(os.path.basename(UTM_fn[2]))[0] + "_buffer_600.shp"), 600))
    UTM_fn.append(WWM_GetBuffers.createBuffer(UTM_fn[2], os.path.join(os.path.dirname(UTM_fn[2]), os.path.splitext(os.path.basename(UTM_fn[2]))[0] + "_buffer_1000.shp"), 1000))


bbox, c_area_m3 = WWM_GetBounds.getBounds(UTM_fn[8]) # slightly buffered

# get rasters
clipped_rasters = WWM_GetModelRasters.clipRasters([DTM, landuse], wDir, UTM_fn[9], out_srid) # use 9 to get slightly buffered and enough for pnt extraction

# set model files
inflow_BC_fn = WWM_SetModelFiles.setModelFiles(UTM_fn, wDir, d_is_us_catchment_boolean)

# set hydrology
# get AMAX
AMAX_series = WWM_GetAMAX.getAMAX(AMAX_folder, UTM_fn[9])
# get rainfall totals
total_rainfall_mm = WWM_GetRain.calculateTotalRainfall(AEP, AMAX_series)
# get heights of u/s and d/s points
if d_is_us_catchment_boolean:
    pnt1_height_m, pnt2_height_m = WWM_GetHeight.getHeights(d_pnt1, e_pnt2, DTM) #dont sent UTM
# get inflow
tp = None # set to none as may not get filled
discharge_hydrograph = None
if d_is_us_catchment_boolean:
    tp, discharge_hydrograph = WWM_GetRain.getFlowFromDescriptors(pnt1_height_m, pnt2_height_m, f_length_in_x, (c_area_m3/1000000), runoff_fraction,
                           storm_duration_hrs, total_rainfall_mm)
else:
    inflow_BC_fn = None

# get rainfall profile
a_UH_total_fraction_series, b_UH_timestep_series = WWM_GetRain.rainfall_profile(storm_duration_hrs, tp_hrs=tp)
a_UH_total_fraction_series = np.array(a_UH_total_fraction_series) * float(runoff_fraction)


# write model control files
WWM_WriteModelControlFiles.writeControlFiles(d_is_us_catchment_boolean, wDir, b_UH_timestep_series, a_UH_total_fraction_series, total_rainfall_mm, bbox, clipped_rasters, inflow_BC_fn, discharge_hydrograph)

z=1

# todo: muskingham parameters estimate based on cunge 1969 https://www.youtube.com/watch?v=qvMz46RFBjg
# todo: muskingham routing of upstream cacthments https://www.youtube.com/watch?v=0y9CNHuvnWU
# todo: https://support.goldsim.com/hc/en-us/articles/115016130888-River-Routing-Muskingum-Cunge-Model
# todo: https://ponce.sdsu.edu/muskingum_cunge_method_explained.html

