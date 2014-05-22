Introduction
------------

  The package add the following algorithms to 'processing' (was 'sexante'):

  - Point Scatterers East-West Speed  (ex PS VelEo)
    
    Model for the computation of the horizontal speed of PS in 
    respect of the satellite.

  - Point Scatterers Horizontal Speed (ex PS Velh)

    Model for the computation of the horizontal speed of PS in
    respect of the satellite. (?)

  - Point Scatterers CR Index

    Model for the computation of the CR Index of satellite visibility

  - Point Scatterers R Index

    Model for the computation of the R Index of satellite visibility
    
  - ...

Install
-------

  PSTools is installed as standard qgis plugin. The algoritms will be
  available in 'processing'.

  - extract the repository in <home>/.qgis2/python/plugins:

        $ git clone git://github.com/faunalia/pstools.git <home>/.qgis/python/plugins/

  - install numpy and gdal python libraries.

  - enable 'processing' plugin from the qgis interface

  - enable 'pstools' plugin from the qgis interface


Models
------

  With the plugin are provides the following models:

  - "?" ...

  The models must be copied in <home>/.qgis2/processing/models/ directory.


Testing
-------

  To run the unit tests:

        $ export PYTHONPATH=~/.qgis2/python/plugins:/usr/share/qgis/python/plugins
        $ cd ~/.qgis2/python/plugins/pstools
        $ python tests.py


Credits
-------

  Developed for ARPA Piemonte (Dipartimento Tematico Geologia e Dissesto)
  within the project PERMANET.
