# -*- coding: utf-8 -*-

"""
***************************************************************************
    PSCRIndex.py
    ---------------------
    Date                 : May 2014
    Copyright            : (C) 2014 by Riccardo Lemmi
    Email                : riccardo at reflab dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Riccardo Lemmi'
__date__ = 'May 2014'
__copyright__ = '(C) 2014, Riccardo Lemmi'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'


from osgeo import gdal
import numpy

import utils

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.outputs.OutputRaster import OutputRaster

from processing.parameters.ParameterVector import ParameterVector
from processing.parameters.ParameterNumber import ParameterNumber
from processing.parameters.ParameterExtent import ParameterExtent


class PSCRIndexAlg:
    # Computation of the CR Index

    def __init__(
            self,
            extent,
            aspect_input_path,
            slope_input_path,
            land_use_index_input_path,
            west_angle,
            incidence_angle,
            cell_size,
            cr_index_path):

        self.extent = extent
        
        self.aspect_input_path = aspect_input_path
        self.slope_input_path = slope_input_path
        self.land_use_index_input_path = land_use_index_input_path
        self.west_angle = west_angle
        self.incidence_angle = incidence_angle
        self.cell_size = cell_size
        
        self.cr_index_path = cr_index_path

        #
        self.aspect = gdal.Open(str(self.aspect_input_path))
        self.slope = gdal.Open(str(self.slope_input_path))
        self.land_use_index = gdal.Open(str(self.land_use_index_input_path))
        
    def compute(self):
        #
        self.rows, self.cols = utils.extent_size(self.extent, self.cell_size)  # todo

        slope_array = self.slope.GetRasterBand(1).ReadAsArray(0, 0, self.cols, self.rows) #fixme
        aspect_array = self.slope.GetRasterBand(1).ReadAsArray(0, 0, self.cols, self.rows)      #fixme
        land_use_index_array = self.slope.GetRasterBand(1).ReadAsArray(0, 0, self.cols, self.rows)    #fixme
        
        west_angle_array = self.west_angle * numpy.ones((self.rows, self.cols), dtype=numpy.byte)
        incidence_angle_array = self.incidence_angle * numpy.ones((self.rows, self.cols), dtype=numpy.byte)

        # "(Sin (([slope] * (Sin (([aspect] + [WA]) div 57.925)) - [IA]) div 57.295)) * -1"
        r_index_array = - sin(slope_array * (sin((aspect_array + west_angle_array) / 57.925) - incidence_angle_array) / 57.295)
        # "([R_index] - 0.3) * 2.857 + 1"
        lu_weight_array = (r_index_array - 0.3) * 2.857 + 1
        # "[R_index] > 0 AND Land_Use_Index > 0
        zero_mask_array = r_index_array > 0 and land_use_index_array > 0

        # "(([Land_Use_Index] * [Peso_LU]) + ([R_index] * 100)) / (1 + [Peso_LU]) * [Zero_Mask]"
        cr_index_array = ((land_use_index_array * lu_weight_array) + (r_index_array * 100)) / (1 + lu_weight_array) * zero_mask_array

        self._save(cr_index_array)


    def _save(self, array):
        # create the output image
        driver = gdal.GetDriverByName('GTiff')
        print "out path:", self.output_path
        dst = driver.Create(
              self.output_path,
              self.cols,
              self.rows,
              1,                        # number of bands
              gdal.GDT_Float32)         # data type

        # set geotrasform and projection
        #   to refactor
        src_x_size = self.point_size
        src_y_size = self.point_size
        new_ulx, new_uly, new_lrx, new_lry = self.extent
        new_width = int(round((new_lrx - new_ulx) / src_x_size))
        new_height = int(round((new_lry - new_uly) / src_y_size))
        dst.SetGeoTransform([new_ulx, src_x_size, 0, new_uly, 0, src_y_size])
        dst.SetProjection( gdal.Open("/tmp/ascending_raster.tiff").GetProjection() )
        #

        self.bandOut = dst.GetRasterBand(1)
        #bandOut.SetNoDataValue(-3.4e+38)
        #bandOut.SetStatistics(
        #          self.min,
        #          self.max,
        #          numpy.mean([self.max, self.min]),
        #          self.std)

        self.bandOut.WriteArray(array)
        self.bandOut.FlushCache()

    def __enter__(self):
        return  self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # set the geotransform and projection on the output
        #self.imageOut.SetGeoTransform(self.imageIn.GetGeoTransform())
        #self.imageOut.SetProjection(self.imageIn.GetProjection())

        ## build pyramids for the output
        #gdal.SetConfigOption('HFA_USE_RRD', 'YES')
        #self.imageOut.BuildOverviews(overviewlist=[2,4,8,16])
        # del dst???
        pass


class PSCRIndexGeoAlg(GeoAlgorithm):
    """ was PS_CR_Index.py """

    
    EXTENT = "EXTENT"  # was SHAPE_EXTENT

    # raster?
    ASPECT = "ASPECT_INPUT"
    SLOPE = "SLOPE_INPUT"
    LAND_USE_INDEX  = "LAND_USE_INDEX_INPUT"

    WEST_ANGLE = "WEST_ANGLE"
    INCIDENCE_ANGLE = "INCIDENCE_ANGLE"
    CELL_SIZE = "CELL_SIZE"

    CR_INDEX = "CR_INDEX_OUTPUT"  #Raster

    def defineCharacteristics(self):
        self.name = "Model to compute CR Index for PS points"
        self.group = "[pstools]"


        self.addParameter(ParameterExtent(PSCRIndexGeoAlg.EXTENT,
                                      "Extent"))

        self.addParameter(ParameterVector(PSCRIndexGeoAlg.ASPECT_INPUT,
                                          "Aspect Grid"))
        self.addParameter(ParameterVector(PSCRIndexGeoAlg.SLOPE_INPUT,
                                          "Slope Grid"))
        self.addParameter(ParameterVector(PSCRIndexGeoAlg.LAND_USE_INDEX_INPUT,
                                          "Quality Index of land use"))
                                          
        self.addParameter(ParameterNumber(PSEWSpeedGeoAlg.WEST_ANGLE),
                                          "West Angle",
                                          minValue=0.0,
                                          maxValue=90.0, #180?
                                          default=0.0))
        self.addParameter(ParameterNumber(PSEWSpeedGeoAlg.INCIDENCE_ANGLE,
                                          "Incidence Angle",
                                          minValue=0.0,
                                          maxValue=90.0, #180?
                                          default=0.0))
        self.addParameter(ParameterNumber(PSEWSpeedGeoAlg.CELL_SIZE,
                                          "Cell Size",
                                          minValue=1,
                                          default=25))


        self.addOutput(OutputRaster(PSEWSpeedGeoAlg.CR_INDEX),
                                    "CR Index Image"))

    def processAlgorithm(self, progress):
        extent = utils.convert_parameter(self.getParameterValue(PSEWSpeedGeoAlg.EXTENT))

        aspect_input_path = str(self.getParameterValue(PSCRIndexGeoAlg.ASPECT_INPUT))
        slope_input_path = str(self.getParameterValue(PSCRIndexGeoAlg.SLOPE_INPUT))
        land_use_index_input_path = str(self.getParameterValue(PSCRIndexGeoAlg.LAND_USE_INDEX_INPUT))
                
        west_angle = self.getParameterValue(PSCRIndexGeoAlg.WEST_ANGLE)
        incidence_angle = self.getParameterValue(PSCRIndexGeoAlg.INCIDENCE_ANGLE)
        cell_size = self.getParameterValue(PSCRIndexGeoAlg.CELL_SIZE)
        
        cr_index_path = str(self.getOutputValue(PSCRIndexGeoAlg.CR_INDEX_OUTPUT))

        with PSCRIndexAlg(
                extent,
                aspect_input_path,
                slope_input_path,
                land_use_index_input_path,
                west_angle,
                incidence_angle,
                cell_size,
                cr_index_path) as crindex:
            crindex.compute()
