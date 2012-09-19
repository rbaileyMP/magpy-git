#!/usr/bin/env python
"""
MagPy - WIK analysis
"""
# Non-corrected Variometer and Scalar Data
# ----------------------------------------
from core.magpy_stream import *

basispath = r'/home/leon/Dropbox/Daten/Magnetism/'

stDIDD = pmRead(path_or_url=os.path.join(basispath,'DIDD-WIK','*'),starttime='2009-12-01', endtime='2010-01-01')
stDIDD.pmplot(['x','y','z','f'])

