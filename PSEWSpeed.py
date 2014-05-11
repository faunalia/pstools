# -*- coding: utf-8 -*-

"""
***************************************************************************
    PSWESpeed.py
    ---------------------
    Date                 : October 2013
    Copyright            : (C) 2013 by Riccardo Lemmi
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
__date__ = 'October 2013'
__copyright__ = '(C) 2013, Riccardo Lemmi'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'


from osgeo import gdal
import numpy

import utils

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.outputs.OutputRaster import OutputRaster

from processing.parameters.ParameterVector import ParameterVector
from processing.parameters.ParameterNumber import ParameterNumber
#from processing.parameters.ParameterRaster import ParameterRaster
from processing.parameters.ParameterExtent import ParameterExtent


class PSEWSpeedAlg:
    # Computation of the horizontal speed of PS East-West 
    
    def __init__(
            self,
            asc_input_path, 
            desc_input_path,
            extent,
            point_size,
            cd_e_asc,
            cd_h_asc,
            cd_e_desc,
            cd_h_desc,
            output_path):
              
        self.asc_input_path = asc_input_path
        self.desc_input_path = desc_input_path
        self.extent = extent
        self.point_size = point_size
        self.cd_e_asc = cd_e_asc
        self.cd_h_asc = cd_h_asc
        self.cd_e_desc = cd_e_desc
        self.cd_h_desc = cd_h_desc
        
        self.output_path = output_path

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

    def compute(self):
        #
        
        # Feature to Raster
        ras_asc_path = "/tmp/ascending_raster.tiff"    # tmp file, Ras -> Raster
        utils.rasterize(self.asc_input_path, ras_asc_path, self.point_size)     
        clipped_asc_array = utils.clip_from_extent_as_array(ras_asc_path, self.extent)
        
        ras_desc_path = "/tmp/descending_raster.tiff"  # tmp file
        utils.rasterize(self.desc_input_path, ras_desc_path, self.point_size)   
        clipped_desc_array = utils.clip_from_extent_as_array(ras_desc_path, self.extent)

        # Constant images
        self.rows, self.cols = clipped_asc_array.shape
        CosDir1_array = self.cd_e_desc * numpy.ones((self.rows, self.cols), dtype=numpy.byte)
        CosDir2_array = self.cd_h_desc * numpy.ones((self.rows, self.cols), dtype=numpy.byte)
        CosDir3_array = self.cd_e_asc * numpy.ones((self.rows, self.cols), dtype=numpy.byte)
        CosDir4_array = self.cd_h_asc * numpy.ones((self.rows, self.cols), dtype=numpy.byte)

        # 
        num = ((clipped_desc_array / CosDir2_array) - (clipped_asc_array / CosDir4_array))
        den = ((CosDir1_array / CosDir2_array) - (CosDir3_array / CosDir4_array))           # for den == [0...] -> wrong image
        ew_speed_array = num / den
      
        from PyQt4.QtCore import *
        import pdb
        pyqtRemoveInputHook()
        pdb.set_trace()
        
        self._save(ew_speed_array)

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


class PSEWSpeedGeoAlg(GeoAlgorithm):
    """ was PSVelEo """
    
    ASC_INPUT = "ASC_INPUT"                 # Ascending -> SHP
    DESC_INPUT = "DISC_INPUT"               # Descending -> SHP
    
    EXTENT = "EXTENT"                     
    POINT_SIZE = "POINT_SIZE"            
    
    COSENO_DIRETTORE_E_ASCENDENTE = "CD_E_ASC"
    COSENO_DIRETTORE_H_ASCENDENTE = "CD_H_ASC"
    COSENO_DIRETTORE_E_DISCENDENTE = "CD_E_DISC"  # Cosine Director East Descending
    COSENO_DIRETTORE_H_DISCENDENTE = "CD_H_DISC"  # ... H?

    OUTPUT_PATH = "OUTPUT_PATH"           # Raster
 
    def defineCharacteristics(self):
        self.name = "Model to compute East-West horizontal component of speed for PS points"
        self.group = "[pstools]"
        
        self.addParameter(ParameterVector(PSEWSpeedGeoAlg.ASC_INPUT, 
                                          "Ascending Vector"))   
        self.addParameter(ParameterVector(PSEWSpeedGeoAlg.DESC_INPUT, 
                                          "Descending Vector"))  
        
        self.addParameter(ParameterExtent(PSEWSpeedGeoAlg.EXTENT, 
                                             "Extent"))     
        self.addParameter(ParameterNumber(PSEWSpeedGeoAlg.POINT_SIZE, 
                                          "Point Size", 
                                          minValue=1,
                                          default=25))
        
        self.addParameter(ParameterNumber(PSEWSpeedGeoAlg.COSENO_DIRETTORE_E_ASCENDENTE, 
                                          "Cosine Director East Ascending",
                                          minValue=0.0, 
                                          maxValue=1.0,
                                          default=0.6))
        self.addParameter(ParameterNumber(PSEWSpeedGeoAlg.COSENO_DIRETTORE_H_ASCENDENTE, 
                                          "Cosine Director Horizontal Ascending", 
                                          minValue=0.0, 
                                          maxValue=1.0,
                                          default=0.5))
        self.addParameter(ParameterNumber(PSEWSpeedGeoAlg.COSENO_DIRETTORE_E_DISCENDENTE, 
                                          "Cosine Director East Descending", 
                                          minValue=0.0, 
                                          maxValue=1.0,
                                          default=0.8))
        self.addParameter(ParameterNumber(PSEWSpeedGeoAlg.COSENO_DIRETTORE_H_DISCENDENTE,
                                          "Cosine Director Horizontal Descending",
                                          minValue=0.0, 
                                          maxValue=1.0,
                                          default=0.5))
        

        self.addOutput(OutputRaster(PSEWSpeedGeoAlg.OUTPUT_PATH, 
                                    "East-West Speed Image"))

    def processAlgorithm(self, progress):
        asc_input_path = str(self.getParameterValue(PSEWSpeedGeoAlg.ASC_INPUT))
        desc_input_path = str(self.getParameterValue(PSEWSpeedGeoAlg.DESC_INPUT))
        extent = utils.convert_parameter(self.getParameterValue(PSEWSpeedGeoAlg.EXTENT))
        point_size = self.getParameterValue(PSEWSpeedGeoAlg.POINT_SIZE)
        cd_e_asc = self.getParameterValue(PSEWSpeedGeoAlg.COSENO_DIRETTORE_E_ASCENDENTE)
        cd_h_asc = self.getParameterValue(PSEWSpeedGeoAlg.COSENO_DIRETTORE_H_ASCENDENTE)
        cd_e_desc = self.getParameterValue(PSEWSpeedGeoAlg.COSENO_DIRETTORE_E_DISCENDENTE)
        cd_h_desc = self.getParameterValue(PSEWSpeedGeoAlg.COSENO_DIRETTORE_H_DISCENDENTE)
        
        #...
        output_path = str(self.getOutputValue(PSEWSpeedGeoAlg.OUTPUT_PATH))
        
        with PSEWSpeedAlg(
                asc_input_path, 
                desc_input_path,
                extent,
                point_size,
                cd_e_asc,
                cd_h_asc,
                cd_e_desc,
                cd_h_desc,
                output_path) as vel:
            vel.compute()
