
import sys
import os.path
import numpy


def writeControlFiles(d_is_us_catchment_boolean, wDir, UH_timestep_series, UH_total_fraction_series, Total_rain, bbox, rasterNames, inflow_BC_fn = None, discharge_hydrograph = None):
    # inputs
    bcinflow = inflow_BC_fn

    rainfallValues = numpy.array(UH_total_fraction_series) * Total_rain
    rainfallTime = UH_timestep_series
    inflowValues = discharge_hydrograph
    inflowTime = UH_timestep_series

    minX = bbox[0]
    maxX = bbox[1]
    minY = bbox[2]
    maxY = bbox[3]

    hasInflow = d_is_us_catchment_boolean


    #setup model folders
    bcDir = os.path.join(wDir,"Model", "bc")
    runsDir = os.path.join(wDir, "Model", "runs")
    mDir = os.path.join(wDir, "Model", "model")

    # Check whether the specified path exists or not
    if not os.path.exists(bcDir):
        # Create a new directory because it does not exist
        os.makedirs(bcDir)
    if not os.path.exists(runsDir):
        # Create a new directory because it does not exist
        os.makedirs(runsDir)
    if not os.path.exists(mDir):
        # Create a new directory because it does not exist
        os.makedirs(mDir)



    #rasterNames - both include file ext.
    # 0 = dtm
    # 1 = landuse

    # bc files
    file = open(os.path.join(bcDir, "bc_dbase.csv"), "w")
    file.write("Name,Source,Column1_or_Time,Column2_or_Value_or_ID,TimeAdd,ValueMult,ValueAdd,IMultF,IAddF,ITimeAddF\n")
    if hasInflow:
        file.write("Qin,bc.csv,Time,Flow\n")
    file.write("Qout,,,\n")
    file.write("rainfall,rainfall.csv,Time,rainfall\n")
    file.close()

    file = open(os.path.join(bcDir, "rainfall.csv"), "w")
    file.write("Time,rainfall\n")
    count = 0
    lastRainfallTime = 0
    for t in rainfallValues:
        if count == 0:
            file.write(str(rainfallTime[count]) + ", " + str(0) + "\n")
        else:
            file.write(str(rainfallTime[count]) + ", " + str(rainfallValues[count]) + "\n")
        lastRainfallTime = rainfallTime[count]
        count = count + 1
    file.close()

    lastInflowTime = 0
    if hasInflow:  #
        ts = inflowTime[1]
        file = open(os.path.join(bcDir, "bc.csv"), "w")
        file.write("Time,Flow\n")
        count = 0
        lastInflowTime = 0
        for t in inflowValues:
            file.write(str(ts * count) + ", " + str(inflowValues[count]) + "\n")
            lastInflowTime = (ts * count)
            count = count + 1
        file.close()

    # get last time values
    lastTime = max(lastRainfallTime, lastInflowTime)

    # create tcf
    file = open(os.path.join(runsDir, "model.tcf"), "w")

    file.write(r"SHP Projection == ..\model\shp\2d_bc_code.prj" + "\n")
    file.write("GIS Projection Check == WARNING\n")
    file.write("Start Time == 0 ! simulation start time (hours)\n")
    file.write("End Time == " + str(lastTime) + "   ! simulation end time (hours)\n")
    file.write("Timestep == 8   ! timestep (seconds)\n")

    file.write(r"Geometry Control File == ..\model\model.tgc ! reference to the geometry control file for this simulation" + "\n")
    file.write(r"BC Control File == ..\model\model.tbc ! reference to the boundary control file for this simulation" + "\n")
    file.write(
        r"BC Database == ..\bc\bc_dbase.csv ! database that relates the names of boundary conditions within MapInfo tables" + "\n")

    file.write(
        r"Read Materials File == ..\model\model.tmf ! looks for the file relating the materials values in the MapInfo file to a roughness coefficient" + "\n")

    file.write("Map Output Data Types == d v h \n")
    file.write("Map Output Format == XMDF ASC \n")
    file.write("Store Maximums and Minimums == ON MAXIMUMS ONLY \n")
    file.write("Start Map Output == 0! start map output time (hours)\n")
    file.write("Map Output Interval == 300  ! frequency the map output data is written to file (seconds)\n")
    file.write("ASC Map Output Interval == 0 \n")
    file.write("Map Cutoff Depth ==  0.03 \n")
    file.write("CSV Time == Hours\n")
    file.write("Output Folder == results" + chr(92) + "2d \n")
    file.write("!Write Check Files == checks" + chr(92) + "2d \n")
    file.write("Log Folder == Log\n")
    file.close()

    # create tgc
    cellSize = 30

    file = open(os.path.join(mDir, "model.tgc"), "w")
    # bottom left corner of catchment
    file.write("Origin == " + str(minX) + ", " + str(
        minY) + "\n")  # file.write("Origin == " + str(math.floor(minX)) + ", " + str(math.floor(minY)) + "\n")
    file.write(
        "Grid Size (X,Y) == " + str((maxX - minX) + 10) + "," + str((maxY - minY) + 10) + "! grid dimensions in meters\n")
    file.write("Cell Size == " + str(cellSize) + " ! cell size in meters\n")

    file.write("Set Code == 0 \n")
    file.write(r"Read GIS Code == shp\2d_bc_code.shp" + "\n")
    file.write("Set Zpt == 0\n")
    file.write("Read Grid Zpts == " + rasterNames[0] + " ! read in the base zpts that have been defined by the DTM\n")
    file.write("Set Mat == 1 \n")
    file.write("Read GRID Mat == " + rasterNames[1] + "\n")
    file.close()

    # create tbc
    file = open(os.path.join(mDir, "model.tbc"), "w")
    file.write(r"Read GIS BC == shp\2d_edge_bc.shp" + "\n")

    file.write("Global Rainfall BC == rainfall\n")
    if hasInflow:  # len(arcpy.GetParameterAsText(0)) > 0:
        file.write(r"Read GIS BC == shp\2d_bc_inflow.shp" + "\n")
    file.close()

    # create tmf - GlobCover 2009
    file = open(os.path.join(mDir, "model.tmf"), "w")
    file.write(" 1, 0.05\n")
    file.write(" 11,0.03!Post-flooding or irrigated croplands (or aquatic)\n")
    file.write(" 14,0.06!Rainfed croplands\n")
    file.write(" 20,0.06!Mosaic cropland (50-70%) / vegetation (grassland/shrubland/forest) (20-50%)\n")
    file.write(" 30,0.05!Mosaic vegetation (grassland/shrubland/forest) (50-70%) / cropland (20-50%) \n")
    file.write(" 40,0.06!Closed to open (>15%) broadleaved evergreen or semi-deciduous forest (>5m)\n")
    file.write(" 50,0.1!Closed (>40%) broadleaved deciduous forest (>5m)\n")
    file.write(" 60,0.08!Open (15-40%) broadleaved deciduous forest/woodland (>5m)\n")
    file.write(" 70,0.1!Closed (>40%) needleleaved evergreen forest (>5m)\n")
    file.write(" 90,0.08!Open (15-40%) needleleaved deciduous or evergreen forest (>5m)\n")
    file.write(" 100,0.08!Closed to open (>15%) mixed broadleaved and needleleaved forest (>5m)\n")
    file.write(" 110,0.1!Mosaic forest or shrubland (50-70%) / grassland (20-50%)\n")
    file.write(" 120,0.05!Mosaic grassland (50-70%) / forest or shrubland (20-50%) \n")
    file.write(" 130,0.06!Closed to open (>15%) (broadleaved or needleleaved, evergreen or deciduous) shrubland (<5m)\n")
    file.write(" 140,0.045!Closed to open (>15%) herbaceous vegetation (grassland, savannas or lichens/mosses)\n")
    file.write(" 150,0.04!Sparse (<15%) vegetation\n")
    file.write(
        " 160,0.06!Closed to open (>15%) broadleaved forest regularly flooded (semi-permanently or temporarily) - Fresh or brackish water\n")
    file.write(" 170,0.03!Closed (>40%) broadleaved forest or shrubland permanently flooded - Saline or brackish water\n")
    file.write(
        " 180,0.05!Closed to open (>15%) grassland or woody vegetation on regularly flooded or waterlogged soil - Fresh, brackish or saline water\n")
    file.write(" 190,0.50!Artificial surfaces and associated areas (Urban areas >50%)\n")
    file.write(" 200,0.03!Bare areas\n")
    file.write(" 210,0.03!Water bodies\n")
    file.write(" 220,0.03!Permanent snow and ice\n")
    file.write(" 230,0.04!No data (burnt areas, clouds,…)\n")
    file.close()


    # Now write a run file to easyly launch the model
    SP = os.path.dirname(os.path.realpath(sys.argv[0]))
    file = open(os.path.join(wDir, "Model", "model.bat"), "w")
    file.write(chr(34) + SP + chr(92) + "\Scripts\Tuflow" + chr(92) + "TUFLOW_iDP_w64.exe" + chr(34) + " -b " + chr(
        34) + runsDir + chr(92) + "model.tcf" + chr(34) + "\n")
    file.write("" + "\n")
    file.close()






