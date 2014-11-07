# -*- coding: utf-8 -*-

"""
***************************************************************************
    PSWESpeed.py
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


from osgeo import gdal, ogr
import numpy

import utils

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.outputs import OutputVector


from processing.core.parameters import ParameterRaster
from processing.core.parameters import ParameterVector
from processing.core.parameters import ParameterNumber


class PSProjectionToolAlg:
    # Computation of the horizontal speed

    def __init__(
            self,
            ps_input_path,
            exp_alos,
            exp_blos,
            exp_clos,
            exp_dip,
            exp_dipdir,
            ps_proj_path):

        self.ps_input_path = ps_input_path

        self.exp_alos = exp_alos
        self.exp_blos = exp_blos
        self.exp_clos = exp_clos

        self.exp_dip = exp_dip
        self.exp_dipdir = exp_dipdir
        
        self.ps_proj_path= ps_proj_path


    def compute(self):
        #

        ps_ds = ogr.Open(self.ps_input_path)
        output_proj_ds = ogr.GetDriverByName("ESRI Shapefile").CopyDataSource(ps_ds, self.ps_proj_path)

        utils.addFieldManagement(output_proj_ds, "ALOS", ogr.OFTReal)
        utils.addFieldManagement(output_proj_ds, "BLOS", ogr.OFTReal)
        utils.addFieldManagement(output_proj_ds, "CLOS", ogr.OFTReal)
        utils.addFieldManagement(output_proj_ds, "dip", ogr.OFTReal)
        utils.addFieldManagement(output_proj_ds, "dipdir", ogr.OFTReal)

        utils.calculateFieldManagement(output_proj_ds, "ALOS", self.exp_alos)
        utils.calculateFieldManagement(output_proj_ds, "BLOS", self.exp_blos)
        utils.calculateFieldManagement(output_proj_ds, "CLOS", self.exp_clos)
        utils.calculateFieldManagement(output_proj_ds, "dip", self.exp_dip)
        utils.calculateFieldManagement(output_proj_ds, "dipdir", self.exp_dipdir)

        formula = "[VEL]*(1/(((cos(([dip]/57.29)))*(sin((([dipdir]-90)/57.29)))*[ALOS])+((-1)*(cos(([dip]/57.29)))*(cos((([dipdir]-90)/57.29)))*[BLOS])+((sin(([dip]/57.29)))*[CLOS])))"
        utils.addFieldManagement(output_proj_ds, "VEL_PRJ", ogr.OFTReal)
        utils.real_CalculateField_management(
                output_proj_ds,
                "VEL_PRJ",
                formula,
                ['VEL', 'ALOS', 'BLOS', 'CLOS', 'dip', 'dipdir'])

        self._save(output_proj_ds)


    #
    def _save(self, output_proj_ds):
        output_proj_ds = None            # close the file

    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class PSProjectionToolDDIRGeoAlg(GeoAlgorithm):
    """ was PS_projection_tools_DDIR.py """

    PS_INPUT = "PS_INPUT"       # Starting dataset: VEL

    EXP_ALOS = "EXP_ALOS"
    EXP_BLOS = "EXP_BLOS"
    EXP_CLOS = "EXP_CLOS"

    EXP_DIP = "EXP_DIP"
    EXP_DIPDIR = "EXP_DIPDIR"
    
    PS_PROJ_PATH = "PS_PROJ_PATH"

    def defineCharacteristics(self):
        self.name = "Model to compute speed projection DDIR for PS points"
        self.group = "[pstools]"

        self.addParameter(ParameterVector(PSProjectionToolDDIRGeoAlg.PS_INPUT,
                                          "Starting Dataset"))

        self.addParameter(ParameterNumber(PSProjectionToolDDIRGeoAlg.EXP_ALOS,
                                          "Cosine Director in x",
                                          minValue=0.0,
                                          maxValue=1.0,
                                          default=0.6))
        self.addParameter(ParameterNumber(PSProjectionToolDDIRGeoAlg.EXP_BLOS,
                                          "Cosine Director in y",
                                          minValue=0.0,
                                          maxValue=1.0,
                                          default=0.5))
        self.addParameter(ParameterNumber(PSProjectionToolDDIRGeoAlg.EXP_CLOS,
                                          "Cosine Director in h",
                                          minValue=0.0,
                                          maxValue=1.0,
                                          default=0.8))

        self.addParameter(ParameterNumber(PSProjectionToolDDIRGeoAlg.EXP_DIP,
                                          "Layer Dip",
                                          minValue=0.0,
                                          maxValue=90.0,
                                          default=45.0))
        self.addParameter(ParameterNumber(PSProjectionToolDDIRGeoAlg.EXP_DIPDIR,
                                          "Layer Dip Direction",
                                          minValue=0.0,
                                          maxValue=360.0,
                                          default=180.0))

                                          
        self.addOutput(OutputVector(PSProjectionToolDDIRGeoAlg.PS_PROJ_PATH,
                                    "Speed Projection using dip and dipdir"))

    def processAlgorithm(self, progress):
        """ """

        ps_input_path = str(self.getParameterValue(PSProjectionToolDDIRGeoAlg.PS_INPUT))

        exp_alos = self.getParameterValue(PSProjectionToolDDIRGeoAlg.EXP_ALOS)
        exp_blos = self.getParameterValue(PSProjectionToolDDIRGeoAlg.EXP_BLOS)
        exp_clos = self.getParameterValue(PSProjectionToolDDIRGeoAlg.EXP_CLOS)

        exp_dip = self.getParameterValue(PSProjectionToolDDIRGeoAlg.EXP_DIP)
        exp_dipdir = self.getParameterValue(PSProjectionToolDDIRGeoAlg.EXP_DIPDIR)
        
        ps_proj_path = str(self.getOutputValue(PSProjectionToolDDIRGeoAlg.PS_PROJ_PATH))

        with PSProjectionToolAlg(
                ps_input_path,
                exp_alos,
                exp_blos,
                exp_clos,
                exp_dip,
                exp_dipdir,
                ps_proj_path) as ps_proj_alg:
            ps_proj_alg.compute()
