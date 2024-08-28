import os
import sys
from osgeo import ogr
import logging as logger

#workingFolder = "D:\Code\WWM\Temp\"
#fullRiverDataset = "D:\subset.shp"
#global pnt2


def getUSCatchments(USCells, outRiverlyr, outCentrelinelyr ):
	#set up logger
	logFormatter = logger.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
	rootLogger = logger.getLogger()
	rootLogger.setLevel(logger.DEBUG)

	consoleHandler = logger.StreamHandler()
	consoleHandler.setFormatter(logFormatter)
	rootLogger.addHandler(consoleHandler)
	logger.info("Starting getUSCatchment....")


	global pnt2
	global USCells2
	# get connecting lines:
	# create an output datasource in memory
	MEMdriver = ogr.GetDriverByName('MEMORY')
	MEMsource = MEMdriver.CreateDataSource('memData')

	# open the memory datasource with write access
	MEMtmp = MEMdriver.Open('memData', 1)
	#MEMLayer = MEMsource.CreateLayer('mem', geom_type=ogr.wkbLineString)
	MEMLayer = MEMsource.CopyLayer(outCentrelinelyr, 'mem', ['OVERWRITE=YES'])

	# Get the output Layer's Feature Definition
	outRiverlyrDefn = outRiverlyr.GetLayerDefn()
	outFeature = ogr.Feature(outRiverlyrDefn)

	outRiverlyr.SetAttributeFilter("")

	lastfeature = len(outCentrelinelyr)-1
	UP_Cell_List = []
	ID_List = []
	dsp_list = []
	usp_list = []

	#outRiverlyr.Intersection(outCentrelinelyr, MEMLayer)
	for i in range(0, len(outRiverlyr)):
		d = outRiverlyr[i]
		e = d.GetGeometryRef()
		f = outCentrelinelyr[lastfeature]
		g = f.GetGeometryRef()
		if e.Touches(g):
			# Set geometry
			logger.info("Found joining river")
			logger.info("cells:" + str(d.GetField(1)) + " cells to compare to:" + str(USCells))
			if d.GetField(1) < USCells:
				# add to list/array:
				UP_Cell_List.append(d.GetField(1))
				ID_List.append(d.GetField(0))
				usp_list.append(e.GetPoints()[len(e.GetPoints()) - 1])  # most downstream point of geometry being checked (the itteration)
				dsp_list.append(g.GetPoints()[0])  # first point/most u/s point of query layer
			# Add field values from input Layer
			# for j in range(0, outRiverlyrDefn.GetFieldCount()):
			# 	outFeature.SetField(outRiverlyrDefn.GetFieldDefn(j).GetNameRef(), d.GetField(j))
			#
			# geom = e
			# outFeature.SetGeometry(geom.Clone())
			# # Add new feature to output Layer
			# outCentrelinelyr.CreateFeature(outFeature)
	logger.info("feature count:" + str(len(UP_Cell_List)))

	# if not empty then find most upstream one


		#for inFeature in outCentrelinelyr:
			# cycle through the us river segments and findthe one with the most upstream cells (i.e. the biggest)

	if len(UP_Cell_List) != 0:
		# get the biggest + add to a list/feature layer
		count = 0
		for i in UP_Cell_List:
			USCells2 = max(UP_Cell_List) # also makes assumption that there are not multiple with same max
			count = count + 1
			logger.info("uscells2 = " + str(USCells2))
			logger.info("max = " + str(max(UP_Cell_List)) + " compared to :" + str(i))
			logger.info("id list = " + str(ID_List))
			if i == max(UP_Cell_List) and i != USCells and dsp_list[count-1] == usp_list[count-1]: # add and d/s points do not match
				USCells = max(UP_Cell_List)
				# select the new upstream feature
				outRiverlyr.SetAttributeFilter('"ARCID" = ' + str(ID_List[count-1]))

				# append it
				for f in range(len(outRiverlyr)):
					inFeature = outRiverlyr.GetNextFeature()
					# Set geometry
					geom = inFeature.GetGeometryRef()
					outFeature.SetGeometry(geom.Clone())
					# set fields
					for j in range(0, outRiverlyrDefn.GetFieldCount()):
						outFeature.SetField(outRiverlyrDefn.GetFieldDefn(j).GetNameRef(), inFeature.GetField(j))
					outCentrelinelyr.CreateFeature(outFeature)
					# last point for height calc - this will be overridden in global var until the laster interration
					pnt2 = geom.GetPoints()[0]   # first point for height calc
					logger.info("written pnt 2 " + str(geom.GetPoints()[0]))
				# next itteration
				getUSCatchments(USCells, outRiverlyr, outCentrelinelyr)  # again assumes USCells is unique....its not


def getRiver(fullRiverDataset, wDir, catchment, first_catchment_fn, is_us_catchment_boolean):
	# params
	# catchment = # this is the whole catchment shapefile from previous script (get catchment)
	# StartRiverID = the ARCID from hydrosheds
	global pnt2

	#set up logger
	logFormatter = logger.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
	rootLogger = logger.getLogger()
	rootLogger.setLevel(logger.DEBUG)

	consoleHandler = logger.StreamHandler()
	consoleHandler.setFormatter(logFormatter)
	rootLogger.addHandler(consoleHandler)

	count = 1
	outRiver = os.path.join(wDir,"full_river.shp") #arcpy.GetParameterAsText(2)
	dsRiver = os.path.join(wDir, "DS_river.shp")
	croppedRiver = os.path.join(wDir, "catchment_river.shp")  # arcpy.GetParameterAsText(4)


	logger.info("Starting getRiver....")
	logger.info("clipping to US catchment")

	#should have catchment polygon by this point, use it to create a chopped down river layer in the wider catchment - selection time will be quicker.
	#GDAL layer.Clip ..... or spatialfilter
	outDriver = ogr.GetDriverByName("ESRI Shapefile")
	fullRiverDatasetds = ogr.Open(fullRiverDataset)
	fullRiverDatasetlyr = fullRiverDatasetds.GetLayer()
	catchmentds = ogr.Open(catchment)
	first_catchmentds = ogr.Open(first_catchment_fn)
	if os.path.exists(outRiver):
		outDriver.DeleteDataSource(outRiver)
	if os.path.exists(dsRiver):
		outDriver.DeleteDataSource(dsRiver)
	outRiverds = outDriver.CreateDataSource(outRiver)
	dsRiverds = outDriver.CreateDataSource(dsRiver)
	outRiverlyr = outRiverds.CreateLayer('full_river', geom_type=ogr.wkbLineString)
	dsRiverlyr = dsRiverds.CreateLayer('ds_river', geom_type=ogr.wkbLineString)
	if not is_us_catchment_boolean:  #only clip to full disolved catchment if there is one (dont do for single catchments that will be RR models only)
		ogr.Layer.Clip(fullRiverDatasetlyr, first_catchmentds.GetLayer(), dsRiverlyr)
		return 0, "", "", "", "", 0 # returns not needed if only the rainfall runoff catchment exists...ie. not u/s catchemnts
	ogr.Layer.Clip(fullRiverDatasetlyr, catchmentds.GetLayer(), outRiverlyr)


	if os.path.exists(croppedRiver):
		outDriver.DeleteDataSource(croppedRiver)
	croppedRiverds = outDriver.CreateDataSource(croppedRiver)
	outCentrelinelyr = croppedRiverds.CreateLayer('centreline_river', geom_type=ogr.wkbLineString)

	#get first line:....or one with highest u/s cells, this alows the imediate catchment to be separated from the lumped flow catchment
	field = "UP_CELLS"
	values = []
	for inFeature in outRiverlyr:
		values.append(inFeature.GetField(1))  # "UP_CELLS"

	top = sorted(values)[-1:]
	logger.info("finding start branch of longest path, US Cells: " + str(top[0]))
	outRiverlyr.SetAttributeFilter('"UP_CELLS" = ' + str(top[0]))  # assumes no 2 U/S catchments have the same UP_CELLS count

	# Get the output Layer's Feature Definition
	outRiverlyrDefn = outRiverlyr.GetLayerDefn()
	outCentrelinelyrDefn  = outCentrelinelyr.GetLayerDefn()

	#create fields
	for i in range(0, outRiverlyrDefn.GetFieldCount()):
		fieldDefn = outRiverlyrDefn.GetFieldDefn(i)
		outCentrelinelyr.CreateField(fieldDefn)

	# Add features to the croppedRiver layer that will hold the longest path centreline
	for inFeature in outRiverlyr:  # should only contain 1 feature
		# Create output Feature
		outFeature = ogr.Feature(outCentrelinelyrDefn)

		# Add field values from input Layer
		for i in range(0, outRiverlyrDefn.GetFieldCount()):
			outFeature.SetField(outRiverlyrDefn.GetFieldDefn(i).GetNameRef(), inFeature.GetField(i))
		ID = inFeature.GetField(0)
		USCells = inFeature.GetField(1)

		# Set geometry
		geom = inFeature.GetGeometryRef()
		logger.info("getting first point")
		pnt1 = geom.GetPoints()[len(geom.GetPoints())-1]  # first point for height calc
		outFeature.SetGeometry(geom.Clone())
		# Add new feature to output Layer
		outCentrelinelyr.CreateFeature(outFeature)
		outFeature = None

	#outRiverds = None

	#search US:
	#outRiverlyr = all rivers in catchment
	#outCentrelinelyr = centreline only
	getUSCatchments(USCells, outRiverlyr, outCentrelinelyr)

	#get length
	logger.info("finding longest path length")
	length = 0
	for inFeature in outCentrelinelyr:
		geom = inFeature.GetGeometryRef()
		length += geom.Length()

	logger.info("outputting u/s and d/s points to shapefiles")
	#get last point for height calc
	if os.path.exists(os.path.join(wDir, "p1.shp")):
		outDriver.DeleteDataSource(os.path.join(wDir, "p1.shp"))
	if os.path.exists(os.path.join(wDir, "p2.shp")):
		outDriver.DeleteDataSource(os.path.join(wDir, "p2.shp"))
	USPath = os.path.join(wDir, "p1.shp")
	outUSds = outDriver.CreateDataSource(USPath)
	outUSlyr = outUSds.CreateLayer('USPoint', geom_type=ogr.wkbPoint)
	DSPath = os.path.join(wDir, "p2.shp")
	outDSds = outDriver.CreateDataSource(DSPath)
	outDSlyr = outDSds.CreateLayer('DSPoint', geom_type=ogr.wkbPoint)

	outFeature = ogr.Feature(outRiverlyrDefn)
	point = ogr.Geometry(ogr.wkbPoint)
	point.AddPoint(pnt1[0], pnt1[1])
	outFeature.SetGeometry(point)
	point = None
	point = ogr.Geometry(ogr.wkbPoint)
	point.AddPoint(pnt2[0], pnt2[1])
	outUSlyr.CreateFeature(outFeature)
	outFeature.SetGeometry(point)
	outDSlyr.CreateFeature(outFeature)

	return USCells, croppedRiver, outRiver, USPath, DSPath, length




#outputs
#1 USCells
#2 centreline river
#3 all rivers in catchment
#4 pnt 1
#5 pnt 2
#6 length

#START RIVER ID NOT USED HERE
#z=1
