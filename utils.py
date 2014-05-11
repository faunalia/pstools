# utils

import os
import random

from osgeo import gdal, ogr
from gdalconst import *

import numpy


def ogr_extent(shape_input_path):
    # Open the data source
    orig_data_source = ogr.Open(shape_input_path) # a shape file: .shp

    if orig_data_source is None:
        raise Exception('No suitable type')

    source_ds = ogr.GetDriverByName("Memory").CopyDataSource(orig_data_source, "")
    source_layer = source_ds.GetLayer(0)
    source_srs = source_layer.GetSpatialRef()
    x_min, x_max, y_min, y_max = source_layer.GetExtent()
    return x_min, x_max, y_min, y_max


# Rasterization
RASTERIZE_COLOR_FIELD = "__color__"

def rasterize(shape_input_path, raster_output_path, pixel_size=25):
    # Open the data source
    orig_data_source = ogr.Open(shape_input_path) # a shape file: .shp

    if orig_data_source is None:
        raise Exception('No suitable type')

    # Make a copy of the layer's data source because we'll need to
    # modify its attributes table
    source_ds = ogr.GetDriverByName("Memory").CopyDataSource(
                                                  orig_data_source, "")
    source_layer = source_ds.GetLayer(0)
    source_srs = source_layer.GetSpatialRef()
    x_min, x_max, y_min, y_max = source_layer.GetExtent()
    print "rasterize extent:", x_min, x_max, y_min, y_max

    # Create a field in the source layer to hold the features colors
    field_def = ogr.FieldDefn(RASTERIZE_COLOR_FIELD, ogr.OFTReal)
    source_layer.CreateField(field_def)
    source_layer_def = source_layer.GetLayerDefn()
    field_index = source_layer_def.GetFieldIndex(RASTERIZE_COLOR_FIELD)

    # Generate random values for the color field (it's here that the value
    # of the attribute should be used, but you get the idea)
    for feature in source_layer:
        feature.SetField(field_index, random.randint(0, 255))
        source_layer.SetFeature(feature)

    # Create the destination data source
    x_res = int((x_max - x_min) / pixel_size)
    y_res = int((y_max - y_min) / pixel_size)
    print 'x_res y_res - ', x_res, y_res

    target_ds = gdal.GetDriverByName('GTiff').Create(
                                                raster_output_path,
                                                x_res,
                                                y_res,
                                                3,
                                                gdal.GDT_Byte)
    target_ds.SetGeoTransform((
            x_min, pixel_size, 0,
            y_max, 0, -pixel_size,
        ))

    if source_srs:
        # Make the target raster have the same projection as the source
        target_ds.SetProjection(source_srs.ExportToWkt())
    else:
        # Source has no projection (needs GDAL >= 1.7.0 to work)
        target_ds.SetProjection('LOCAL_CS["arbitrary"]')

    # Rasterize
    err = gdal.RasterizeLayer(
                  target_ds,
                  (3, 2, 1),
                  source_layer,
                  burn_values=(0, 0, 0),
                  options=["ATTRIBUTE=%s" % RASTERIZE_COLOR_FIELD])
    if err != 0:
        raise Exception("error rasterizing layer: %s" % err)

# Image clipping
def clip_from_extent_as_array(src_path, extent):
    # Clip the raster image and return the matrix as numpy array
    # FIXME => review the convertions to make ReadAsArray work correctly
    
    src_img = gdal.Open(src_path)
    src_band = src_img.GetRasterBand(1)
    [src_ulx, src_x_size, src_x_rotation, src_uly, src_y_rotation, src_y_size] = src_img.GetGeoTransform()    

    new_ulx, new_uly, new_lrx, new_lry = extent

    # convert to matrix coordinates
    xo = abs(int(round((new_ulx - src_ulx) / src_x_size)))    # cols origin
    yo = abs(int(round((new_uly - src_uly) / src_y_size)))    # rows origin

    new_width = abs(int(round((new_lrx - new_ulx) / src_x_size)))    # number of cols
    new_height = abs(int(round((new_lry - new_uly) / src_y_size)))   # number of rows

    # logs
    print 'clip:', src_path
    print "ulx:%s x_size:%s x_rotation:%s uly:%s y_rotation:%s y_size:%s"%(src_ulx, src_x_size, src_x_rotation, src_uly, src_y_rotation, src_y_size)
    print 'o: %s,%s size: %s,%s  '%(xo, yo, new_width, new_height)
    
    return src_band.ReadAsArray(xo, yo, new_width, new_height)


def convert_parameter(extent):
    # The extent returned from 'processing' widget is a string in the form "xmin, xmax, ymin, ymax"
    # shape_extent = ulx, uly, lrx, lry
    # ul: upper left
    # lr: lower right
    xmin, xmax, ymin, ymax = [float(v) for v in extent.split(',')]
    return [xmin, ymin, xmax, ymax]


if __name__ == '__main__':
    import sys
    print clip_from_extent_as_array(
              sys.argv[1],
              [373880.161999, 5033158.31312, 374757.398705, 5032431.85147])
