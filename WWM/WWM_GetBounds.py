
import osgeo.ogr as ogr

def getBounds(first_catchment_buffered_fn):
    catchmentfile = ogr.Open(first_catchment_buffered_fn)
    catchmentfilelyr = catchmentfile.GetLayer()

    #assumes only 1 polgon
    feat = catchmentfilelyr[0]
    geom = feat.GetGeometryRef()
    bbox = geom.GetEnvelope()
    area = geom.GetArea()

    return bbox, area

#a = getBounds(r"C:\Temp\W\out\UTM_first_catchment_buffer_200.shp")
#z=1