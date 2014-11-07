# -*- coding: utf-8 -*-

"""
***************************************************************************
    PSRIndex.py
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
from processing.core.outputs import OutputRaster

from processing.core.parameters import ParameterRaster
from processing.core.parameters import ParameterNumber
from processing.core.parameters import ParameterExtent


class PSRIndexAlg:
    # Computation of the R Index

    def __init__(
            self,
            extent,
            aspect_input_path,
            slope_input_path,
            west_angle,
            incidence_angle,
            cell_size,
            r_index_path):

        self.extent = extent

        self.aspect_input_path = aspect_input_path
        self.slope_input_path = slope_input_path
        self.west_angle = west_angle
        self.incidence_angle = incidence_angle
        self.cell_size = cell_size

        self.r_index_path = r_index_path

        #
        self.aspect = gdal.Open(str(self.aspect_input_path))
        self.slope = gdal.Open(str(self.slope_input_path))

    def compute(self):
        #
        self.cols, self.rows = utils.extent_size(self.extent, self.cell_size)  

        slope_array = self.slope.GetRasterBand(1).ReadAsArray(0, 0, self.cols, self.rows) 
        aspect_array = self.slope.GetRasterBand(1).ReadAsArray(0, 0, self.cols, self.rows)

        west_angle_array = self.west_angle * numpy.ones((self.rows, self.cols), dtype=numpy.byte)
        incidence_angle_array = self.incidence_angle * numpy.ones((self.rows, self.cols), dtype=numpy.byte)

        # "(Sin (([slope] * (Sin (([aspect] + [WA]) div 57.925)) - [IA]) div 57.295)) * -1"
        r_index_array = - numpy.sin(slope_array * (numpy.sin((aspect_array + west_angle_array) / 57.925) - incidence_angle_array) / 57.295)
        
        self._save(r_index_array)


    def _save(self, array):
        # create the output image
        driver = gdal.GetDriverByName('GTiff')
        dst = driver.Create(
              self.r_index_path,
              self.cols,
              self.rows,
              1,                        # number of bands
              gdal.GDT_Float32)         # data type

        new_ulx, new_uly, new_lrx, new_lry = self.extent
        dst.SetGeoTransform([new_ulx, self.cell_size, 0, new_uly, 0, self.cell_size])

        self.bandOut = dst.GetRasterBand(1)
        self.bandOut.SetNoDataValue(-3.4e+38)
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
        pass


class PSRIndexGeoAlg(GeoAlgorithm):
    """ was PS_R_Index.py """

    EXTENT = "EXTENT"  # was SHAPE_EXTENT

    ASPECT_INPUT = "ASPECT_INPUT"       # raster
    SLOPE_INPUT = "SLOPE_INPUT"         # raster

    WEST_ANGLE = "WEST_ANGLE"
    INCIDENCE_ANGLE = "INCIDENCE_ANGLE"
    CELL_SIZE = "CELL_SIZE"

    R_INDEX_OUTPUT = "R_INDEX_OUTPUT"          # raster

    def defineCharacteristics(self):
        self.name = "Model to compute R Index for PS points"
        self.group = "[pstools]"


        self.addParameter(ParameterExtent(PSRIndexGeoAlg.EXTENT,
                                          "Extent"))

        self.addParameter(ParameterRaster(PSRIndexGeoAlg.ASPECT_INPUT,
                                          "Aspect Grid"))
        self.addParameter(ParameterRaster(PSRIndexGeoAlg.SLOPE_INPUT,
                                          "Slope Grid"))

        self.addParameter(ParameterNumber(PSRIndexGeoAlg.WEST_ANGLE,
                                          "West Angle",
                                          minValue=0.0,
                                          maxValue=90.0, #180?
                                          default=0.0))
        self.addParameter(ParameterNumber(PSRIndexGeoAlg.INCIDENCE_ANGLE,
                                          "Incidence Angle",
                                          minValue=0.0,
                                          maxValue=90.0, #180?
                                          default=0.0))
        self.addParameter(ParameterNumber(PSRIndexGeoAlg.CELL_SIZE,
                                          "Cell Size",
                                          minValue=1,
                                          default=25))


        self.addOutput(OutputRaster(PSRIndexGeoAlg.R_INDEX_OUTPUT,
                                    "R Index Image"))

    def processAlgorithm(self, progress):
        extent = utils.convert_parameter(self.getParameterValue(PSRIndexGeoAlg.EXTENT))

        aspect_input_path = str(self.getParameterValue(PSRIndexGeoAlg.ASPECT_INPUT))
        slope_input_path = str(self.getParameterValue(PSRIndexGeoAlg.SLOPE_INPUT))

        west_angle = self.getParameterValue(PSRIndexGeoAlg.WEST_ANGLE)
        incidence_angle = self.getParameterValue(PSRIndexGeoAlg.INCIDENCE_ANGLE)
        cell_size = self.getParameterValue(PSRIndexGeoAlg.CELL_SIZE)

        r_index_path = str(self.getOutputValue(PSRIndexGeoAlg.R_INDEX_OUTPUT))

        with PSRIndexAlg(
                extent,
                aspect_input_path,
                slope_input_path,
                west_angle,
                incidence_angle,
                cell_size,
                r_index_path) as rindex:
            rindex.compute()
