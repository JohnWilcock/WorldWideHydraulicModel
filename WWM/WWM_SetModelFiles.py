import os
import sys
from osgeo import ogr
import WWM_GetInflowAlignment, WWM_GetModelRasters

def erase(baseFile, eraseFile, outFile): #this class performs the erase tool from ARCGIS//     erasefile must be polygon
  driver = ogr.GetDriverByName('ESRI Shapefile')

  feat1 = driver.Open(baseFile, 0)
  feat2 = driver.Open(eraseFile, 0)

  feat1Layer = feat1.GetLayer()
  feat2Layer = feat2.GetLayer()

  feature2 = feat2Layer.GetFeature(0)
  geomfeat2 = feature2.GetGeometryRef()

  feat1Layer.ResetReading()

  # spatial ref system
  proj = feat1Layer.GetSpatialRef()

  # create a new data source and layer
  fn = outFile
  if os.path.exists(fn):
    driver.DeleteDataSource(fn)
  outDS = driver.CreateDataSource(fn)
  outLayer = outDS.CreateLayer('output',proj, geom_type=ogr.wkbLineString)

  # fields
  typeField = ogr.FieldDefn("Type", ogr.OFTString)
  flagsField = ogr.FieldDefn("Flags", ogr.OFTString)
  nameField = ogr.FieldDefn("Name", ogr.OFTString)
  fField = ogr.FieldDefn("f", ogr.OFTString)
  dField = ogr.FieldDefn("d", ogr.OFTString)
  tdField = ogr.FieldDefn("td", ogr.OFTString)
  bField = ogr.FieldDefn("b", ogr.OFTString)
  aField = ogr.FieldDefn("a", ogr.OFTString)

  outLayer.CreateField(typeField)
  outLayer.CreateField(flagsField)
  outLayer.CreateField(nameField)
  outLayer.CreateField(fField)
  outLayer.CreateField(dField)
  outLayer.CreateField(tdField)
  outLayer.CreateField(bField)
  outLayer.CreateField(aField)

  # get the FeatureDefn for the output shapefile
  featureDefn = outLayer.GetLayerDefn()

  #loop through input layer
  for inFeature in feat1Layer:

    # create a new feature
    outFeature = ogr.Feature(featureDefn)

    outFeature.SetField("Type", "HQ")
    outFeature.SetField("Flags", "")
    outFeature.SetField("Name", "Qout")
    outFeature.SetField("f", 0)
    outFeature.SetField("d", 0)
    outFeature.SetField("td", 0)
    outFeature.SetField("b", 0.001)
    outFeature.SetField("a", 0)

    #get Geometry of feature and apply the difference method on that feature
    inGeom = inFeature.GetGeometryRef()
    GeomDiff = inGeom.Difference(geomfeat2)
    #Set geometry of the outfeature
    outFeature.SetGeometry(GeomDiff)

    # add the feature to the output layer
    outLayer.CreateFeature(outFeature)

def setInflowBC(d_is_us_catchment_boolean, b1, b2, b4, b5, wDir, mDir):
    if d_is_us_catchment_boolean:
        refBearing, intersectbearing, outfrontlinefn = WWM_GetInflowAlignment.createInflowClips(b4,b5, b2, b1, wDir)
        inflow_BC_fn = WWM_GetInflowAlignment.fixInflowAlignment(refBearing, intersectbearing, outfrontlinefn , mDir)

        #add fields
        driver = ogr.GetDriverByName('ESRI Shapefile')
        inflow_BC_ds = driver.Open(inflow_BC_fn, 1)
        inflow_BC_lyr = inflow_BC_ds.GetLayer()
        ldef = inflow_BC_lyr.GetLayerDefn()

        # fields
        typeField = ogr.FieldDefn("Type", ogr.OFTString)
        flagsField = ogr.FieldDefn("Flags", ogr.OFTString)
        nameField = ogr.FieldDefn("Name", ogr.OFTString)
        fField = ogr.FieldDefn("f", ogr.OFTReal)
        dField = ogr.FieldDefn("d", ogr.OFTReal)
        tdField = ogr.FieldDefn("td", ogr.OFTReal)
        bField = ogr.FieldDefn("b", ogr.OFTReal)
        aField = ogr.FieldDefn("a", ogr.OFTReal)

        inflow_BC_lyr.CreateField(typeField)
        inflow_BC_lyr.CreateField(flagsField)
        inflow_BC_lyr.CreateField(nameField)
        inflow_BC_lyr.CreateField(fField)
        inflow_BC_lyr.CreateField(dField)
        inflow_BC_lyr.CreateField(tdField)
        inflow_BC_lyr.CreateField(bField)
        inflow_BC_lyr.CreateField(aField)

        for inFeature in inflow_BC_lyr:
          # create a new feature
          inFeature.SetField("Type", "QT")
          inFeature.SetField("Flags", "")
          inFeature.SetField("Name", "Qin")
          inFeature.SetField("f", 0)
          inFeature.SetField("d", 0)
          inFeature.SetField("td", 0)
          inFeature.SetField("b", 0)
          inFeature.SetField("a", 0)
          inflow_BC_lyr.SetFeature(inFeature)

        inflow_BC_lyr.DeleteField(0)

        return inflow_BC_fn
    return ""


def set2DCode(UTM_first_catchment_fn, wDir):

    #check for current inflow output
    newFile = os.path.join(wDir, "2D_BC_code.shp")
    driver = ogr.GetDriverByName("ESRI Shapefile")
    if os.path.exists(newFile):
        driver.DeleteDataSource(newFile)

    # open current file
    driver = ogr.GetDriverByName('ESRI Shapefile')
    _2DCode_ds = driver.Open(UTM_first_catchment_fn, 1)
    _2DCode_lyr = _2DCode_ds.GetLayer()
    proj = _2DCode_lyr.GetSpatialRef()

    #create new file
    new_2DCodeds = driver.CreateDataSource(newFile)
    new_2DCodelyr = new_2DCodeds.CreateLayer('_2D_code', proj, geom_type=ogr.wkbPolygon)

    # fields
    idField = ogr.FieldDefn("id", ogr.OFTInteger)
    new_2DCodelyr.CreateField(idField)
    ldef = new_2DCodelyr.GetLayerDefn()

    for inFeature in _2DCode_lyr:
        # create a new feature
        outFeature = ogr.Feature(ldef)
        outFeature.SetGeometry(inFeature.GetGeometryRef().Clone())
        outFeature.SetField("id", 1)
        new_2DCodelyr.CreateFeature(outFeature)

    return

def setModelFiles(UTM_fn, wDir, d_is_us_catchment_boolean):
    #input
    # 1 = UTM_fn[] #list of UTM proj files from getstudyarea
    # 2 = wDir
    # 3 = d_is_us_catchment_boolean

    #set model directory
    mDir = os.path.join(wDir,"Model", "model", "shp")

    # Check whether the specified path exists or not
    if not os.path.exists(mDir):
        # Create a new directory because it does not exist
        os.makedirs(mDir)

    # EDGE BC
    erase(UTM_fn[7], UTM_fn[11], os.path.join(mDir, "2D_Edge_BC.shp"))

    # INFLOW BC - if needed
    inflow_BC_fn = setInflowBC(d_is_us_catchment_boolean, UTM_fn[7], UTM_fn[8], UTM_fn[10], UTM_fn[11], wDir, mDir)

    # 2D Code - based on catchment boundary in UTM (first catchment)
    set2DCode(UTM_fn[2], mDir)

    # Rasters - DTM and landuse
    #rasters = unclipped_rasters
    #WWM_GetModelRasters.clipRasters(rasters, mDir, UTM_fn[9])

    return inflow_BC_fn

#a = ['C:\\Temp\\W\\out\\UTM_full_catchment.shp', 'C:\\Temp\\W\\out\\UTM_full_catchment_disolved.shp', 'C:\\Temp\\W\\out\\UTM_first_catchment.shp', 'C:\\Temp\\W\\out\\UTM_catchment_river.shp', 'C:\\Temp\\W\\out\\UTM_full_river.shp', 'C:\\Temp\\W\\out\\UTM_p1.shp', 'C:\\Temp\\W\\out\\UTM_p2.shp', 'C:\\Temp\\W\\out\\UTM_first_catchment_buffer_M200.shp', 'C:\\Temp\\W\\out\\UTM_first_catchment_buffer_200.shp', 'C:\\Temp\\W\\out\\UTM_full_catchment_disolved_buffer_12500.shp', 'C:\\Temp\\W\\out\\UTM_p1_buffer_600.shp', 'C:\\Temp\\W\\out\\UTM_p1_buffer_1000.shp']
#setModelFiles(a, r"C:\Temp\W\out", True )


