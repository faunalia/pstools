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

# image clipping
def clip(src_path, sub_img_path, origin, size):

    image = gdal.Open(src_path)
    band = image.GetRasterBand(1)
    [upper_left_x, x_size, x_rotation, upper_left_y, y_rotation, y_size] = image.GetGeoTransform()

    # raster size in pixel
    cols = image.RasterXSize    # width or band.XSize
    rows = image.RasterYSize    # height or band.YSize

    # new origin in pixel
    xo, yo = origin
    width, height = size

    sub_image_array = band.ReadAsArray(xo, yo, width, height)

    ## save
    driver = gdal.GetDriverByName('GTiff')
    dst = driver.Create(
                  sub_img_path,
                  width,                    # in pixel
                  height,                   # in pixel
                  1,                        # number of bands
                  gdal.GDT_Float32)         # data type

    # set transform and projection
    # new origin
    new_ox = upper_left_x + xo * x_size
    new_oy = upper_left_y + yo * y_size

    dst.SetGeoTransform([new_ox, x_size, x_rotation, new_oy, y_rotation, y_size])
    dst.SetProjection( image.GetProjection() )

    # write on file
    bandOut = dst.GetRasterBand(1)
    bandOut.WriteArray(sub_image_array)


def clip_from_extent(src_path, sub_img_path, extent):
    #import pdb; pdb.set_trace()

    src_img = gdal.Open(src_path)
    src_band = src_img.GetRasterBand(1)
    [src_ulx, src_x_size, src_x_rotation, src_uly, src_y_rotation, src_y_size] = src_img.GetGeoTransform()

    new_ulx, new_uly, new_lrx, new_lry = extent

    xo = int(round((new_ulx - src_ulx) / src_x_size))
    yo = int(round((new_uly - src_uly) / src_y_size))

    print 'new:', xo, yo

    #src_width = src_img.RasterXSize * src_x_size
    #src_height = src_img.RasterYSize * src_y_size

    new_width = int(round((new_lrx - new_ulx) / src_x_size))
    new_height = int(round((new_lry - new_uly) / src_y_size))

    print "size:",  new_width, new_height

    sub_image_array = src_band.ReadAsArray(xo, yo, new_width, new_height)

    # save...
    driver = gdal.GetDriverByName('GTiff')
    dst = driver.Create(
                  sub_img_path,
                  new_width,                    # in pixel
                  new_height,                   # in pixel
                  1,                        # number of bands
                  gdal.GDT_Float32)         # data type

    dst.SetGeoTransform([new_ulx, src_x_size, src_x_rotation, new_uly, src_y_rotation, src_y_size])
    dst.SetProjection( src_img.GetProjection() )

    # write on file
    bandOut = dst.GetRasterBand(1)
    bandOut.WriteArray(sub_image_array)

    # pezzo giusto ma in posizione leggermente errata
    # provato a sistemare la conversione con int(round())
    # viene comunque un pochino spostata


def clip_from_extent_as_array(src_path, extent):
    # as clip_from_extent but return only the array

    src_img = gdal.Open(src_path)
    src_band = src_img.GetRasterBand(1)
    [src_ulx, src_x_size, src_x_rotation, src_uly, src_y_rotation, src_y_size] = src_img.GetGeoTransform()

    new_ulx, new_uly, new_lrx, new_lry = extent

    xo = int(round((new_ulx - src_ulx) / src_x_size))
    yo = int(round((new_uly - src_uly) / src_y_size))

    new_width = int(round((new_lrx - new_ulx) / src_x_size))
    new_height = int(round((new_lry - new_uly) / src_y_size))

    print 'clip:', src_path
    print '  ', xo, yo, new_width, new_height
    return src_band.ReadAsArray(xo, yo, new_width, new_height)


def convert_parameter(extent):
    # The value is a string in the form "xmin, xmax, ymin, ymax"
    xmin, xmax, ymin, ymax = [float(v) for v in extent.split(',')]
    return [xmin, ymax, xmax, ymin]


if __name__ == '__main__':
    import sys

    #clip(sys.argv[1], sys.argv[2], (10,10), (20,20))
    # python utils.py /home/axa/Projects/languages/python/gdal/to_raster.tiff /tmp/sub_img.tiff
    clip_from_extent(
        sys.argv[1],
        sys.argv[2],
        [373880.161999, 5033158.31312, 374757.398705, 5032431.85147])
