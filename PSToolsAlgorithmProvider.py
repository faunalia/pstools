# -*- coding: utf-8 -*-

"""
***************************************************************************
    PSToolsAlgorithmProvider.py
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

import os
from PyQt4 import QtGui

from processing.core.AlgorithmProvider import AlgorithmProvider
from processing.algs.AddTableField import AddTableField

#
from PSEWSpeed import PSEWSpeedGeoAlg
from PSHSpeed import PSHSpeedGeoAlg
#from PSCRIndex import PSCRIndexGeoAlg

class PSToolsAlgorithmProvider(AlgorithmProvider):

    def __init__(self):
        AlgorithmProvider.__init__(self)
        self.alglist = [
            PSEWSpeedGeoAlg(),
            PSHSpeedGeoAlg(),
            #PSCRIndexGeoAlg(),
            #PSRIndexGeoAlg(),
        ]

    def initializeSettings(self):
        AlgorithmProvider.initializeSettings(self)


    def unload(self):
        AlgorithmProvider.unload(self)


    def getName(self):
        return "pstools"

    def getDescription(self):
        return "PS Tools"

    def _loadAlgorithms(self):
        self.algs = self.alglist

    def supportsNonFileBasedOutput(self):
        return True
