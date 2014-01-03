#!/usr/bin/env python

# ----------------------------------------------------------------------------
# Part 1: Import routines for packages
# ----------------------------------------------------------------------------

from stream import *
from absolutes import *
from transfer import *

import MySQLdb

# ----------------------------------------------------------------------------
# Part 2: Default list definitions - defining fields of database standard tables
# ----------------------------------------------------------------------------

DATAINFOKEYLIST = ['DataID','SensorID','StationID','ColumnContents','ColumnUnits','DataFormat',
			'DataSamplingFilter','DataDigitalSampling','DataComponents','DataSamplingRate',
			'DataType','DataDeltaX','DataDeltaY','DataDeltaZ','DataDeltaF',
			'DataDeltaReferencePier','DataDeltaReferenceEpoch','DataScaleX',
			'DataScaleY','DataScaleZ','DataScaleUsed','DataCompensationX',
			'DataCompensationY','DataCompensationZ','DataSensorOrientation',
			'DataSensorAzimuth','DataSensorTilt','DataAngularUnit','DataPier',
			'DataAcquisitionLatitude','DataAcquisitionLongitude','DataLocationReference',
			'DataElevation','DataElevationRef','DataFlagModification','DataAbsFunc',
			'DataAbsDegree','DataAbsKnots','DataAbsMinTime','DataAbsMaxTime','DataAbsDate',
			'DataRating','DataComments']

SENSORSKEYLIST = ['SensorID','SensorName','SensorType','SensorSerialNum','SensorGroup','SensorDataLogger',
			'SensorDataLoggerSerNum','SensorDataLoggerRevision','SensorDataLoggerRevisionComment',
			'SensorDescription','SensorElements','SensorKeys','SensorModule','SensorDate',
			'SensorRevision','SensorRevisionComment','SensorRevisionDate']

STATIONSKEYLIST = ['StationID','StationName','StationIAGAcode','StationInstitution','StationStreet',
			'StationCity','StationPostalCode','StationCountry','StationWebInfo',
			'StationEmail','StationDescription']

FLAGSKEYLIST = ['FlagID','SensorID','FlagBeginTime','FlagEndTime','FlagComponents','FlagNum','FlagReason','ModificationDate']

BASELINEKEYLIST = ['SensorID','MinTime','MaxTime','TmpMaxTime','BaseFunction','BaseDegree','BaseKnots','BaseComment']

# Optional (if acquisition routine is used)
MOONSKEYLIST = ['Moon','MoonIP','MoonSensors','MoonType','MoonLocationLat','MoonLocationLong','MoonSystem','MoonMainUser','MoonComment']

"""
Standard tables:

SENSOR:
	SensorID: a combination of name, serialnumber and revision
	SensorName: a name defined by the observers to refer to the instrument
	SensorType: type of sensor (e.g. fluxgate, overhauzer, temperature ...)
        SensorSerialNum: its serial number
	SensorGroup: Geophysical group (e.g. Magnetism, Gravity, Environment, Meteorology, Seismology, Radiometry, ...) 
	SensorDataLogger: type of any electronics connected to the sensor 
	SensorDataLoggerSerNum: its serial number
        SensorDataLoggerRevision: 4 digit revision id '0001'
        SensorDataLoggerRevisionComment: description of revision
	SensorDescription: Description of the sensor
        SensorElements: Measured components e.g. x,y,z,t_sensor,t_electonics
        SensorKeys: the keys to be used for the elements in MagPy e.g. 'x,y,z,t1,t2', should have the same number as Elements (check MagPy Manual for this)
        SensorModule: type of sensor connection
        SensorDate: Date of Sensor construction/buy  
        SensorRevision: 4 digit number defining a revision ID
        SensorRevisionComment: Comment for current revision - changes to previous number (e.g. calibration)
        SensorRevisionDate: Date of revision - for 0001 this equals the SensorDate 
STATION:
        StationID: unique ID of the station e.g. IAGA code
        StationIAGAcode: 
        StationName: e.g. Cobenzl
        StationStreet: Stations address
        StationCity: Vienna
        StationEmail: 'ramon.egli@zamg.ac.at',
        StationPostalCode: '1190',
        StationCountry: 'Austria',
        StationInstitution: 'Zentralanstalt fuer Meteorologie und Geodynamik',
        StationWebInfo: 'http://www.zamg.ac.at',
        StationDescription: 'Running since 1951.'
DATAINFO:
	DataID:

FLAGS: (used to store flagging information)

BASELINE: (used to store baseline fit parameters)


"""

# ----------------------------------------------------------------------------
#  Part 3: Main methods for mysql database communication --
#      dbalter, dbsensorinfo, dbdatainfo, dbdict2fields, dbfields2dict and 
# ----------------------------------------------------------------------------

def dbsamplingrate(stream):
    """
    DEFINITION:
        returns a rounded value of the sampling rate
    headerdict = 
    """
    sr = stream.get_sampling_period()*24*3600
    if np.round(sr,0) == 0:
        return np.round(sr,1)
    else:
        return np.round(sr,0)


def dbupload(db, path,stationid,**kwargs):
    """
    DEFINITION:
        method to upload data to a database and to create an archive
    headerdict = 
    """
    starttime = kwargs.get('starttime')
    endtime = kwargs.get('endtime')
    headerdict = kwargs.get('headerdict')
    archivepath = kwargs.get('archivepath')
    sensorid = kwargs.get('sensorid')
    tablenum1 = kwargs.get('tablenum1')
    tablenum2 = kwargs.get('tablenum2')

    stream = read(path,starttime=starttime,endtime=endtime)
    if headerdict:
        stream.header = headerdict
    stream.header['StationID']=stationid
    stream.header['DataSamplingRate'] = str(dbsamplingrate(stream)) + ' sec'
    if sensorid:
        stream.header['SensorID']=sensorid

    try:
        if tablenum1:
            stream2db(db,stream,mode='insert',tablename=sensorid+'_'+tablenum1)
        else:
            stream2db(db,stream,mode='insert')
    except:
        if tablenum1:
            stream2db(db,stream,mode='extend',tablename=sensorid+'_'+tablenum1)
        else:
            stream2db(db,stream,mode='extend')

    if archivepath:
        datainfoid = dbdatainfo(db,stream.header['SensorID'],stream.header)
        stream.header = dbfields2dict(db,datainfoid)
        archivedir = os.path.join(archivepath,stream.header['StationID'],stream.header['SensorID'],datainfoid)
        stream.write(archivedir, filenamebegins=datainfoid+'_', format_type='PYCDF')
        datainfoorg = datainfoid

    stream = stream.filter(filter_type='gauss',filter_width=timedelta(minutes=1))

    try:
        if tablenum2:
            stream2db(db,stream,mode='insert',tableext=sensorid+'_'+tablenum2)
        else:
            stream2db(db,stream,mode='insert')
    except:
        if tablenum2:
            stream2db(db,stream,mode='extend',tableext=sensorid+'_'+tablenum2)
        else:
            stream2db(db,stream,mode='extend')

    if archivepath:
        datainfoid = dbdatainfo(db,stream.header['SensorID'],stream.header)
        archivedir = os.path.join(archivepath,stream.header['StationID'],stream.header['SensorID'],datainfoid)
        stream.write(archivedir, filenamebegins=datainfoid+'_', format_type='PYCDF')
    # Reset filter
    stream.header = dbfields2dict(db,datainfoorg)



def dbinit(db):
    """
    DEFINITION:
        set up standard tables of magpy:
        DATAINFO, SENSORS, and STATIONS (and FlAGGING).
        
    PARAMETERS:
    Variables:
        - db:   	(mysql database) defined by MySQLdb.connect().
    Kwargs:
        --
    RETURNS:
        --
    EXAMPLE:
        >>> dbinit(db)

    APPLICATION:
        Requires an existing mysql database (e.g. mydb)
        1. Connect to the database
        db = MySQLdb.connect (host = "localhost",user = "user",passwd = "secret",db = "mysqldb")
        2. use method
        dbinit(db)
    """

    # SENSORS TABLE
    # Create station table input
    headstr = ' CHAR(100), '.join(SENSORSKEYLIST) + ' CHAR(100)'
    headstr = headstr.replace('SensorID CHAR(100)', 'SensorID CHAR(50) NOT NULL PRIMARY KEY')
    headstr = headstr.replace('SensorDescription CHAR(100)', 'SensorDescription TEXT')
    createsensortablesql = "CREATE TABLE IF NOT EXISTS SENSORS (%s)" % headstr

    # STATIONS TABLE
    # Create station table input
    stationstr = ' CHAR(100), '.join(STATIONSKEYLIST) + ' CHAR(100)'
    stationstr = stationstr.replace('StationID CHAR(100)', 'StationID CHAR(50) NOT NULL PRIMARY KEY')
    stationstr = stationstr.replace('StationDescription CHAR(100)', 'StationDescription TEXT')
    stationstr = 'StationID CHAR(50) NOT NULL PRIMARY KEY, StationName CHAR(100), StationIAGAcode CHAR(10), StationInstitution CHAR(100), StationStreet CHAR(50), StationCity CHAR(50), StationPostalCode CHAR(20), StationCountry CHAR(50), StationWebInfo CHAR(100), StationEmail CHAR(100), StationDescription TEXT'
    createstationtablesql = "CREATE TABLE IF NOT EXISTS STATIONS (%s)" % stationstr

    # DATAINFO TABLE
    # Create datainfo table
    datainfostr = 'DataID CHAR(50) NOT NULL PRIMARY KEY, SensorID CHAR(50), StationID CHAR(50), ColumnContents TEXT, ColumnUnits TEXT, DataFormat CHAR(20),DataMinTime CHAR(50), DataMaxTime CHAR(50), DataSamplingFilter CHAR(100), DataDigitalSampling CHAR(100), DataComponents CHAR(10), DataSamplingRate CHAR(100), DataType CHAR(100), DataDeltaX DECIMAL(20,9), DataDeltaY DECIMAL(20,9), DataDeltaZ DECIMAL(20,9),DataDeltaF DECIMAL(20,9),DataDeltaReferencePier CHAR(20),DataDeltaReferenceEpoch CHAR(50),DataScaleX DECIMAL(20,9),DataScaleY DECIMAL(20,9),DataScaleZ DECIMAL(20,9),DataScaleUsed CHAR(2),DataSensorOrientation CHAR(10),DataSensorAzimuth DECIMAL(20,9),DataSensorTilt DECIMAL(20,9), DataAngularUnit CHAR(5),DataPier CHAR(20),DataAcquisitionLatitude DECIMAL(20,9), DataAcquisitionLongitude DECIMAL(20,9), DataLocationReference CHAR(20), DataElevation DECIMAL(20,9), DataElevationRef CHAR(10), DataFlagModification CHAR(50), DataAbsFunc CHAR(20), DataAbsDegree INT, DataAbsKnots DECIMAL(20,9), DataAbsMinTime CHAR(50), DataAbsMaxTime CHAR(50), DataAbsDate CHAR(50), DataRating CHAR(10), DataComments TEXT'
    createdatainfotablesql = "CREATE TABLE IF NOT EXISTS DATAINFO (%s)" % datainfostr

    # FLAGS TABLE
    # Create flagging table
    flagstr = ' CHAR(100), '.join(FLAGSKEYLIST) + ' CHAR(100)'
    flagstr = flagstr.replace('FlagID CHAR(100)', 'FlagID CHAR(50) NOT NULL PRIMARY KEY')
    flagstr = flagstr.replace('SensorID CHAR(100)', 'SensorID CHAR(50) NOT NULL')
    createflagtablesql = "CREATE TABLE IF NOT EXISTS FLAGS (%s)" % flagstr

    # BASELINE TABLE
    # Create baseline table
    basestr = ' CHAR(100), '.join(BASELINEKEYLIST) + ' CHAR(100)'
    basestr = basestr.replace('SensorID CHAR(100)', 'SensorID CHAR(50) NOT NULL')
    createbaselinetablesql = "CREATE TABLE IF NOT EXISTS BASELINE (%s)" % basestr

    # MOON TABLE
    # Create baseline table
    moonstr = ' CHAR(100), '.join(MOONSKEYLIST) + ' CHAR(100)'
    moonstr = moonstr.replace('MoonComment CHAR(100)', 'MoonComment TEXT')
    createbaselinetablesql = "CREATE TABLE IF NOT EXISTS MOONS (%s)" % moonstr


    cursor = db.cursor()

    cursor.execute(createsensortablesql)
    cursor.execute(createstationtablesql)
    cursor.execute(createdatainfotablesql)
    cursor.execute(createflagtablesql)
    cursor.execute(createbaselinetablesql)

    db.commit()
    cursor.close ()
    dbalter(db)


def dbdelete(db,datainfoid,**kwargs):
    """
    DEFINITION:
       Delete contents of the database
       If datainfoid is provided only this database contents are deleted
       If before is specified all data before the given date are erased
       Else before is determined according to the  samplingrateratio

    PARAMETERS:
    Variables:
        - db:   	    (mysql database) defined by MySQLdb.connect().
        - datainfoid:       (string) table and dataid    
    Kwargs:
        - samplingrateratio:(float) defines the ratio for deleting data older than (samplingperiod(sec)*samplingrateratio) DAYS
                        default = 45
        - timerange:        (int) time range to keep from now in days

    RETURNS:
        --

    EXAMPLE:
        >>> dbdelete(db,'DIDD_3121331_0002_0001')

    APPLICATION:
        Requires an existing mysql database (e.g. mydb)
        so first connect to the database
        db = MySQLdb.connect (host = "localhost",user = "user",passwd = "secret",db = "mysqldb")

    TODO:
        - If sampling rate not given in DATAINFO get it from the datastream
    """

    samplingrateratio = kwargs.get("samplingrateratio")
    timerange = kwargs.get("timerange")

    if not samplingrateratio:
        samplingrateratio = 45.0
        
    cursor = db.cursor()
    timeunit = 'DAY'

    # Do steps 1 to 2 if time interval is not given (parameter interval, before)
    if not timerange:
        # 1. Get sampling rate
        # option a - get from db
        try:
            getsr = 'SELECT DataSamplingRate FROM DATAINFO WHERE DataID = "%s"' % datainfoid
            cursor.execute(getsr)
            samplingperiod = float(cursor.fetchone()[0].strip(' sec'))
            loggerdatabase.debug("dbdelete: samplingperiod = %s" % str(samplingperiod))
        except:
            loggerdatabase.error("dbdelete: could not access DataSamplingRate in table %s" % datainfoid)
            samplingperiod = None
        # option b - get directly from stream
        if samplingperiod == None:
            # read stream and get sampling rate there
            #stream = db2stream(db,datainfoid)
            samplingperiod = 5	# TODO
        # 2. Determine time interval to delete
        # factor depends on available space...
        timerange = np.ceil(samplingperiod*samplingrateratio)

    loggerdatabase.debug("dbdelete: selected timerange of %s days" % str(timerange))

    # 3. Delete time interval
    loggerdatabase.info("dbdelete: deleting data of %s older than %s days" % (datainfoid, str(timerange)))
    #try:
    deletesql = "DELETE FROM %s WHERE time < ADDDATE(NOW(), INTERVAL -%i %s)" % (datainfoid, timerange, timeunit)
    cursor.execute(deletesql)
    #except:
    loggerdatabase.error("dbdelete: error when deleting data")

    # 4. Re-determine length for Datainfo
    try:
        newdatesql = "SELECT min(time),max(time) FROM %s" % datainfoid
        cursor.execute(newdatesql)
        value = cursor.fetchone()
        mintime = value[0]
        maxtime = value[1]
        updatedatainfosql = 'UPDATE DATAINFO SET DataMinTime="%s", DataMaxTime="%s" WHERE DataID="%s"' % (mintime,maxtime,datainfoid)
        cursor.execute(updatedatainfosql)
    except:
        loggerdatabase.error("dbdelete: error when re-determining dates for DATAINFO")

    db.commit()
    cursor.close ()


def dbdict2fields(db,header_dict,**kwargs):
    """
    DEFINITION:
        Provide a dictionary with header information according to KEYLISTS STATION, SENSOR and DATAINFO
        Creates database inputs in standard tables

    PARAMETERS:
    Variables:
        - db:   	(mysql database) defined by MySQLdb.connect().
        - header_dict:  (dict) dictionary with header information 
    Kwargs:
        - mode:         (string) can be insert (default) or replace
                          insert tries to insert dict values: if already existing, a warning is issued
                          replace will replace any alraedy present db data by dict values
    RETURNS:
        --
    EXAMPLE:
        >>> dbdict2fields(db,stream.header,mode='replace')

    APPLICATION:
        Requires an existing mysql database (e.g. mydb)
        so first connect to the database
        db = MySQLdb.connect (host = "localhost",user = "user",passwd = "secret",db = "mysqldb")
    """
    mode = kwargs.get('mode')

    if not mode:
        mode = 'insert'

    cursor = db.cursor()

    sensorfieldlst,sensorvaluelst = [],[]
    stationfieldlst,stationvaluelst = [],[]
    datainfofieldlst,datainfovaluelst = [],[]
    usestation, usesensor, usedatainfo = False,False,False

    if "StationID" in header_dict:
        usestation = True
        loggerdatabase.debug("dbdict2fields: Found StationID in dict")
    else:
        loggerdatabase.warning("dbdict2fields: No StationID in dict - skipping any other eventually given station information")
    if "SensorID" in header_dict:
        usesensor = True
        loggerdatabase.debug("dbdict2fields: found SensorID in dict")
    else:
        loggerdatabase.warning("dbdict2fields: No SensorID in dict - skipping any other eventually given sensor information")
    if "DataID" in header_dict:
        usedatainfo = True
        loggerdatabase.debug("dbdict2fields: found DataID in dict")
    else:
        loggerdatabase.warning("dbdict2fields: No DataID in dict - skipping any other eventually given datainfo information")

    # 2. Update content for the primary IDs
    for key in header_dict:
        fieldname = key
        fieldvalue = header_dict[key]
        if fieldname in STATIONSKEYLIST:
            if usestation:
                stationfieldlst.append(fieldname)
                stationvaluelst.append(fieldvalue)
        elif fieldname in SENSORSKEYLIST:
            if usesensor:
                sensorfieldlst.append(fieldname)
                sensorvaluelst.append(fieldvalue)
        elif fieldname in DATAINFOKEYLIST:
            if usedatainfo:
                datainfofieldlst.append(fieldname)
                datainfovaluelst.append(fieldvalue)
        else:
            loggerdatabase.warning("dbdict2fields: !!!!!!!! %s not existing !!!!!!!" % fieldname)

    try:
        insertsql = 'INSERT INTO STATIONS (%s) VALUE (%s)' %  (', '.join(stationfieldlst), '"'+'", "'.join(stationvaluelst)+'"')
        if mode == 'replace':
            insertsql = insertsql.replace("INSERT","REPLACE")
        if len(stationfieldlst) > 0:
            cursor.execute(insertsql)
    except:
        try:
            for key in header_dict:
                if key in STATIONSKEYLIST:
                    searchsql = "SELECT %s FROM STATIONS WHERE StationID = '%s'" % (key,header_dict['SensorID'])
                    cursor.execute(searchsql)
                    value = cursor.fetchone()[0]
                    if value <> header_dict[key]:
                        loggerdatabase.warning("dbdict2fields: StationID is already existing but field values for field %s are differing: dict (%s); db (%s)" % (key, header_dict[key], value))
        except:
            loggerdatabase.warning("dbdict2fields: STATIONS table not existing?")
    try:
        insertsql = 'INSERT INTO SENSORS (%s) VALUE (%s)' %  (', '.join(sensorfieldlst), '"'+'", "'.join(sensorvaluelst)+'"')
        if mode == 'replace':
            insertsql = insertsql.replace("INSERT","REPLACE")
        if len(sensorfieldlst) > 0:
            cursor.execute(insertsql)
    except:
        try:
            for key in header_dict:
                if key in SENSORSKEYLIST:
                    searchsql = "SELECT %s FROM SENSORS WHERE SensorID = '%s'" % (key,header_dict['SensorID'])
                    cursor.execute(searchsql)
                    value = cursor.fetchone()[0]
                    if value <> header_dict[key]:
                        loggerdatabase.warning("dbdict2fields: SensorID is already existing but field values for field %s are differing: dict (%s); db (%s)" % (key, header_dict[key], value))
        except:
            loggerdatabase.warning("dbdict2fields: SENSORS table not existing?")
    try:
        insertsql = 'INSERT INTO DATAINFO (%s) VALUE (%s)' %  (', '.join(datainfofieldlst), '"'+'", "'.join(datainfovaluelst)+'"')
        if mode == 'replace':
            insertsql = insertsql.replace("INSERT","REPLACE")
        if len(datainfofieldlst) > 0:
            cursor.execute(insertsql)
    except:
        try:
            for key in header_dict:
                if key in DATAINFOKEYLIST:
                    searchsql = "SELECT %s FROM DATAINFO WHERE DataID = '%s'" % (key,header_dict['SensorID'])
                    cursor.execute(searchsql)
                    value = cursor.fetchone()[0]
                    if value <> header_dict[key]:
                        loggerdatabase.warning("dbdict2fields: DataID is already existing but field values for field %s are differing: dict (%s); db (%s)" % (key, header_dict[key], value))
        except:
            loggerdatabase.warning("dbdict2fields: DATAINFO table not existing?")

    db.commit()
    cursor.close ()


def dbfields2dict(db,datainfoid):
    """
    DEFINITION:
        Provide datainfoid to get all informations from tables STATION, SENSORS and DATAINFO
        Use it to get metadata from database for saving cdf archive files
        Returns a dictionary

    PARAMETERS:
    Variables:
        - db:   	(mysql database) defined by MySQLdb.connect().
        - datainfoid:   (string) 
    Kwargs:
        --
    RETURNS:
        --
    EXAMPLE:
        >>> header_dict = dbfields2dict(db,'DIDD_3121331_0001_0001')

    APPLICATION:
        Requires an existing mysql database (e.g. mydb)
        so first connect to the database
        db = MySQLdb.connect (host = "localhost",user = "user",passwd = "secret",db = "mysqldb")
    """
    metadatadict = {}
    cursor = db.cursor()

    #getids = 'SELECT sensorid FROM DATAINFO WHERE DataID = "'+datainfoid+'"'
    getids = 'SELECT sensorid,stationid FROM DATAINFO WHERE DataID = "'+datainfoid+'"'
    cursor.execute(getids)
    ids = cursor.fetchone()
    if not ids:
        return {}
    loggerdatabase.debug("dbfields2dict: Selected sensorid: %s" % ids[0])

    for key in DATAINFOKEYLIST:
        if not key == 'StationID': # Remove that line when included into datainfo
            getdata = 'SELECT '+ key +' FROM DATAINFO WHERE DataID = "'+datainfoid+'"'
            cursor.execute(getdata)
            row = cursor.fetchone()
            loggerdatabase.debug("dbfields2dict: got key from DATAINFO - %s" % getdata)
            if isinstance(row[0], basestring):
                metadatadict[key] = row[0]
                if key == 'ColumnContents':
                    colsstr = row[0]
                if key == 'ColumnUnits':
                    colselstr = row[0]
            else:
                if row[0] == None:
                    #metadatadict[key] = row[0]
                    pass
                else:
                    metadatadict[key] = float(row[0])

    try:
        cols = colsstr.split('_')
        colsel = colselstr.split('_')
        print cols, colsel
        for i, elem in enumerate(cols):
            if not elem == '_':
                key = 'col-'+elem
                metadatadict[key] = colsel[i]
    except:
        loggerdatabase.warning("dbfields2dict: Could not assign column name")

    for key in SENSORSKEYLIST:
        getsens = 'SELECT '+ key +' FROM SENSORS WHERE SensorID = "'+ids[0]+'"'
        cursor.execute(getsens)
        row = cursor.fetchone()
        if isinstance(row[0], basestring):
            metadatadict[key] = row[0]
            if key == 'SensorKeys':
                colsstr = row[0]
            if key == 'SensorElements':
                colselstr = row[0]
        else:
            if row[0] == None:
                pass
                #metadatadict[key] = row[0]
            else:
                metadatadict[key] = float(row[0])
    try:
        cols = colsstr.split(',')
        colsel = colselstr.split(',')
        for i, elem in enumerate(cols):
            key = 'col-'+elem
            metadatadict[key] = colsel[i]
    except:
        loggerdatabase.warning("dbfields2dict: Could not assign column name")

    for key in STATIONSKEYLIST:
        getstat = 'SELECT '+ key +' FROM STATIONS WHERE StationID = "'+ids[1]+'"'
        cursor.execute(getstat)
        row = cursor.fetchone()
        if isinstance(row[0], basestring):
            metadatadict[key] = row[0]
        else:
            if row[0] == None:
                pass
                #metadatadict[key] = row[0]
            else:
                metadatadict[key] = float(row[0])

    return metadatadict


def dbalter(db):
    """
    DEFINITION:
        Use KEYLISTS and changes the columns of standard tables
        DATAINFO, SENSORS, and STATIONS.
        Can be used for changing (adding) contents to tables

    PARAMETERS:
    Variables:
        - db:   	(mysql database) defined by MySQLdb.connect().
    Kwargs:
        --
    RETURNS:
        --
    EXAMPLE:
        >>> dbalter(db)

    APPLICATION:
        Requires an existing mysql database (e.g. mydb)
        1. Connect to the database
        db = MySQLdb.connect (host = "localhost",user = "user",passwd = "secret",db = "mysqldb")
        2. use method
        dbalter(db)
    """
    if not db:
        loggerdatabase.error("dbalter: No database connected - aborting -- please create an empty database first")
        return
    cursor = db.cursor ()

    try:
        checksql = 'SELECT SensorID FROM SENSORS'
        cursor.execute(checksql)
        for key in SENSORSKEYLIST:
            try:
                checksql = 'SELECT ' + key+ ' FROM SENSORS'
                loggerdatabase.debug("dbalter: Checking key: %s" % key)
                cursor.execute(checksql)
                loggerdatabase.debug("dbalter: Found key: %s" % key)
            except:
                loggerdatabase.debug("dbalter: Missing key: %s" % key)
                addstr = 'ALTER TABLE SENSORS ADD ' + key + ' CHAR(100)'
                cursor.execute(addstr)
                loggerdatabase.debug("dbalter: Key added: %s" % key)
    except:
        loggerdatabase.warning("dbalter: Table SENSORS not existing")

    try:
        checksql = 'SELECT StationID FROM STATIONS'
        cursor.execute(checksql)
        for key in STATIONSKEYLIST:
            try:
                checksql = 'SELECT ' + key+ ' FROM STATIONS'
                loggerdatabase.debug("dbalter: Checking key: %s" % key)
                cursor.execute(checksql)
                loggerdatabase.debug("dbalter: Found key: %s" % key)
            except:
                loggerdatabase.debug("dbalter: Missing key: %s" % key)
                addstr = 'ALTER TABLE STATIONS ADD ' + key + ' CHAR(100)'
                cursor.execute(addstr)
                loggerdatabase.debug("dbalter: Key added: %s" % key)
    except:
        loggerdatabase.warning("dbalter: Table STATIONS not existing")

    try:
        checksql = 'SELECT DataID FROM DATAINFO'
        cursor.execute(checksql)
        for key in DATAINFOKEYLIST:
            try:
                checksql = 'SELECT ' + key+ ' FROM DATAINFO'
                loggerdatabase.debug("Checking key: %s" % key)
                cursor.execute(checksql)
                loggerdatabase.debug("Found key: %s" % key)
            except:
                loggerdatabase.debug("Missing key: %s" % key)
                addstr = 'ALTER TABLE DATAINFO ADD ' + key + ' CHAR(100)'
                cursor.execute(addstr)
                loggerdatabase.debug("Key added: %s" % key)
    except:
        loggerdatabase.warning("Table DATAINFO not existing")

    db.commit()
    cursor.close ()


def dbsensorinfo(db,sensorid,sensorkeydict=None,sensorrevision = '0001'):
    """
    DEFINITION:
        checks whether sensorinfo is already available in SENSORS tab
        if not, it creates a new line for the provided sensorid in the selected database db
        Keywords are all database fields provided as dictionary

    PARAMETERS:
    Variables:
        - db:   	  (mysql database) defined by MySQLdb.connect().
        - sensorid:   	  (string) code for sensor if.
    Optional variables:
        - sensorkeydict:  (dict) provide a dictionary with sensor information (see SENSORS) .
        - sensorrevision: (string) provide a revision number in format '0001' .
    Kwargs:
        --
    RETURNS:
       sensorid with revision number e.g. DIDD_235178_0001
    USED BY:
       stream2db
    EXAMPLE:
        >>> dbsensorinfo()

    APPLICATION:
        Requires an existing mysql database (e.g. mydb)
        1. Connect to the database
        db = MySQLdb.connect (host = "localhost",user = "user",passwd = "secret",db = "mysqldb")
        2. use method
        dbalter(db)
    """

    sensorhead,sensorvalue,numlst = [],[],[]

    cursor = db.cursor()
   
    if sensorkeydict:
        for key in sensorkeydict:
            if key in SENSORSKEYLIST: 
                sensorhead.append(key)
                sensorvalue.append(sensorkeydict[key])

    loggerdatabase.debug("dbsensorinfo: sensor: ", sensorhead, sensorvalue)

    check = 'SELECT SensorID, SensorRevision, SensorName, SensorSerialNum FROM SENSORS WHERE SensorID LIKE "'+sensorid+'%"'
    try:
        cursor.execute(check)
        rows = cursor.fetchall()
    except:
        loggerdatabase.warning("dbsensorinfo: Could not access table SENSORS in database - creating table SENSORS")
        headstr = ' CHAR(100), '.join(SENSORSKEYLIST) + ' CHAR(100)'
        headstr = headstr.replace('SensorID CHAR(100)', 'SensorID CHAR(50) NOT NULL PRIMARY KEY')
        createsensortablesql = "CREATE TABLE IF NOT EXISTS SENSORS (%s)" % headstr
        cursor.execute(createsensortablesql)

    if len(rows) > 0: 
        # SensorID is existing in Table
        loggerdatabase.info("dbsensorinfo: Sensorid already existing in SENSORS")
        loggerdatabase.info("dbsensorinfo: rows: %s" % rows)
        # Get the maximum revision number
        for i in range(len(rows)):
            rowval = rows[i][1]
            try:
                numlst.append(int(rowval))
            except:
                pass
        try:
            maxnum = max(numlst)
        except:
            maxnum = None
        if isinstance(maxnum, int):
            index = numlst.index(maxnum)
            sensorid = rows[index][0]
        else:
            loggerdatabase.warning("dbsensorinfo: SensorRevision not set - changing to %s" % sensorrevision)
            if rows[0][2] == None:
                sensoridsplit = sensorid.split('_')
                if len(sensoridsplit) == 2:
                    sensorserialnum = sensoridsplit[1]
                else:
                    sensorserialnum = sensorid
            else:
                sensorserialnum = rows[0][2]
            oldsensorid = sensorid
            sensorid = sensorid+'_'+sensorrevision
            updatesensorsql = 'UPDATE SENSORS SET SensorID = "' + sensorid + '", SensorRevision = "' + sensorrevision + '", SensorSerialNum = "' + sensorserialnum + '" WHERE SensorID = "' + oldsensorid + '"'
            cursor.execute(updatesensorsql)
    else:
        # SensorID is not existing in Table
        loggerdatabase.info("dbsensorinfo: Sensorid not yet existing in SENSORS.")
        # Check whether given sensorid is incomplete e.g. revision number is missing
        loggerdatabase.info("dbsensorinfo: Creating new sensorid %s " % sensorid)
        if not 'SensorSerialNum' in sensorhead:
            sensoridsplit = sensorid.split('_')
            if len(sensoridsplit) == 2:
                sensorserialnum = sensoridsplit[1]
            elif len(sensoridsplit) == 3:
                sensorserialnum = sensoridsplit[1]
                if not 'SensorRevision' in sensorhead:
                    sensorhead.append('SensorRevision')
                    sensorvalue.append(sensoridsplit[2])
                index = sensorhead.index('SensorID')
                sensorvalue[index] = sensorid
            else:
                sensorserialnum = sensorid
            sensorhead.append('SensorSerialNum')
            sensorvalue.append(sensorserialnum)
            loggerdatabase.debug("dbsensorinfo: sensor %s, %s" % (sensoridsplit, sensorserialnum))
        if not 'SensorRevision' in sensorhead:
            sensorhead.append('SensorRevision')
            sensorvalue.append(sensorrevision)
            if not 'SensorID' in sensorhead:
                sensorhead.append('SensorID')
                sensorvalue.append(sensorid+'_'+sensorrevision)
            else:
                index = sensorhead.index('SensorID')
                sensorvalue[index] = sensorid+'_'+sensorrevision
            sensorid = sensorid+'_'+sensorrevision
        ### create an input for the new sensor
        sensorsql = "INSERT INTO SENSORS(%s) VALUES (%s)" % (', '.join(sensorhead), '"'+'", "'.join(sensorvalue)+'"')
        #print "Adding the following info to SENSORS: ", sensorsql
        cursor.execute(sensorsql)

    db.commit()
    cursor.close ()

    return sensorid


def dbdatainfo(db,sensorid,datakeydict=None,tablenum=None,defaultstation='WIC',updatedb=True):
    """
    DEFINITION:
        provide sensorid and any relevant meta information for datainfo tab
        returns the full datainfoid

    PARAMETERS:
    Variables:
        - db:   	  (mysql database) defined by MySQLdb.connect().
        - sensorid:   	  (string) code for sensor if.
    Optional variables:
        - datakeydict:    (dict) provide a dictionary with data table information (see DATAINFO) .
        - tablenum:       (string) provide a table number in format '0001' .
               If tablenum is specified, the corresponding table is selected and DATAINFO is updated with the provided datakeydict
               If tablenum = 'new', a new number is generated e.g. 0006 if no DATAINFO matching the provided info is found 
               If no tablenum is selected all data including all Datainfo is appended to the latest numbe if no DATAINFO matching the provided info is found and no conflict with the existing DATAINFO is found 
        - defaultstation: (string) provide a default station code.
               An important keyword is the StationID. Please make sure to provide it. Otherwise the defaultvalue 'WIC' is used

        - updatedb:      (bool) if true (default) then the new infoid is added into the database
    Kwargs:
        --
    RETURNS:
       datainfoid e.g. DIDD_235178_0001_0001
    USED BY:
       stream2db
    EXAMPLE:
        >>> tablename = dbdatainfo(db,sensorid,headdict,None,stationid)

    APPLICATION:
        1. read a datastream: stream = read(file)
        2. add additional header info: stream.header['StationID'] = 'WIC'
        3. Open a mysql database
        4. write stream2db
        5. check DATAINFO table: num = dbdatainfo(db,steam.header['SensorID'],stream.header,None,None)
              case 1: new sensor - not yet existing
                      tablenum = 0001
              case 2: sensor existing
                      default: select fitting datainfo (compare only provided fields - not in DATAINFO existing) and get highest number matching the info
                      tablenum=new: add new number, disregarding any previous matching DATAINFO 
                      tablenum=0003: returns 0003 if case 1 is satisfied 

        Not changeable are:
        DataMinTime CHAR(50)
        DataMaxTime CHAR(50)
    """

    searchlst = ' '
    datainfohead,datainfovalue=[],[]
    if datakeydict:
        for key in datakeydict:
            if key in DATAINFOKEYLIST:
                datainfohead.append(key)
                datainfovalue.append(str(datakeydict[key]))
                if key == 'DataID' or key.startswith('Column'):
                    pass
                else:
                    searchlst += 'AND ' + key + ' = "'+ str(datakeydict[key]) +'" '

    datainfonum = '0001'
    numlst,intnumlst = [],[]

    cursor = db.cursor()
    
    # check for appropriate sensorid
    loggerdatabase.debug("dbdatainfo: Reselecting SensorID")
    sensorid = dbsensorinfo(db,sensorid,datakeydict)
    if 'SensorID' in datainfohead:
        index = datainfohead.index('SensorID') 
        datainfovalue[index] = sensorid
    loggerdatabase.debug("dbdatainfo:  -- SensorID is now %s" % sensorid) 

    checkinput = 'SELECT StationID FROM DATAINFO WHERE SensorID = "'+sensorid+'"'
    try:
        cursor.execute(checkinput)
        rows = cursor.fetchall()
    except:
        loggerdatabase.warning("dbdatainfo: Column StationID not yet existing in table DATAINFO (very old magpy version) - creating it ...")
        stationaddstr = 'ALTER TABLE DATAINFO ADD StationID CHAR(50) AFTER SensorID'
        cursor.execute(stationaddstr)

    checkinput = 'SELECT DataID FROM DATAINFO WHERE SensorID = "'+sensorid+'"'
    loggerdatabase.debug("dbdatainfo: %s " % checkinput) 
    try:
        print checkinput
        cursor.execute(checkinput)
        rows = cursor.fetchall()
        loggerdatabase.debug("dbdatainfo: Number of existing DATAINFO lines: %s" % str(rows))
    except:
        loggerdatabase.warning("dbdatainfo: Could not access table DATAINFO in database")
        datainfostr = 'DataID CHAR(50) NOT NULL PRIMARY KEY, SensorID CHAR(50), ColumnContents TEXT, ColumnUnits TEXT, DataFormat CHAR(20),DataMinTime CHAR(50), DataMaxTime CHAR(50), DataSamplingFilter CHAR(100), DataDigitalSampling CHAR(100), DataComponents CHAR(10), DataSamplingRate CHAR(100), DataType CHAR(100), DataDeltaX DECIMAL(20,9), DataDeltaY DECIMAL(20,9), DataDeltaZ DECIMAL(20,9),DataDeltaF DECIMAL(20,9),DataDeltaReferencePier CHAR(20),DataDeltaReferenceEpoch CHAR(50),DataScaleX DECIMAL(20,9),DataScaleY DECIMAL(20,9),DataScaleZ DECIMAL(20,9),DataScaleUsed CHAR(2),DataSensorOrientation CHAR(10),DataSensorAzimuth DECIMAL(20,9),DataSensorTilt DECIMAL(20,9), DataAngularUnit CHAR(5),DataPier CHAR(20),DataAcquisitionLatitude DECIMAL(20,9), DataAcquisitionLongitude DECIMAL(20,9), DataLocationReference CHAR(20), DataElevation DECIMAL(20,9), DataElevationRef CHAR(10), DataFlagModification CHAR(50), DataAbsFunc CHAR(20), DataAbsDegree INT, DataAbsKnots DECIMAL(20,9), DataAbsMinTime CHAR(50), DataAbsMaxTime CHAR(50), DataAbsDate CHAR(50), DataRating CHAR(10), DataComments TEXT'
        createdatainfotablesql = "CREATE TABLE IF NOT EXISTS DATAINFO (%s)" % datainfostr
        cursor.execute(createdatainfotablesql)

    # check whether input in DATAINFO with sensorid is existing already
    if len(rows) > 0:
        # Get maximum number
        for i in range(len(rows)):
            rowval = rows[i][0].replace(sensorid + '_','')
            #print len(rows), rowval, sensorid+'_', rows[i][0]
            try:
                numlst.append(int(rowval))
		#print numlst
            except:
                print "crap"
                pass
        maxnum = max(numlst)
        loggerdatabase.debug("dbdatainfo: Maxnum: %i" % maxnum)
        # Perform intensive search using any given meta info
        intensivesearch = 'SELECT DataID FROM DATAINFO WHERE SensorID = "'+sensorid+'"' + searchlst
        loggerdatabase.debug("dbdatainfo: Searchlist: %s" % intensivesearch)
        cursor.execute(intensivesearch)
        intensiverows = cursor.fetchall()
        print "Found matching table: ", intensiverows
        print "using searchlist ", intensivesearch
        loggerdatabase.debug("dbdatainfo: intensiverows: %i" % len(intensiverows))
        if len(intensiverows) > 0:
            for i in range(len(intensiverows)):
                # if more than one record is existing select the latest (highest) number
                introwval = intensiverows[i][0].replace(sensorid + '_','')
                try:
                    intnumlst.append(int(introwval))
                except:
                    pass
            intmaxnum = max(intnumlst)
            datainfonum = '{0:04}'.format(intmaxnum)
        else:
            datainfonum = '{0:04}'.format(maxnum+1)
            # select maximum number + 1
            if 'DataID' in datainfohead:
                index = datainfohead.index('DataID') 
                datainfovalue[index] = sensorid + '_' + datainfonum
            else:
                datainfohead.append('DataID')
                datainfovalue.append(sensorid + '_' + datainfonum)
            datainfosql = 'INSERT INTO DATAINFO(%s) VALUES (%s)' % (', '.join(datainfohead), '"'+'", "'.join(datainfovalue)+'"')
            loggerdatabase.debug("dbdatainfo: sql: %s" % datainfosql)
            if updatedb:
                cursor.execute(datainfosql)
        datainfoid = sensorid + '_' + datainfonum
    else:
        # return 0001
        datainfoid = sensorid + '_' + datainfonum
        datainfohead.append('DataID')
        datainfovalue.append(datainfoid)
        # and create datainfo input
        loggerdatabase.debug("dbdatainfo: %s, %s" % (datainfohead, datainfovalue))
        datainfosql = 'INSERT INTO DATAINFO(%s) VALUES (%s)' % (', '.join(datainfohead), '"'+'", "'.join(datainfovalue)+'"')
        if updatedb:
            cursor.execute(datainfosql)

    db.commit()
    cursor.close ()

    return datainfoid


def stream2db(db, datastream, noheader=None, mode=None, tablename=None):
    """
    DEFINITION:
        Method to write datastreams to a mysql database

    PARAMETERS:
    Variables:
        - db:   	(mysql database) defined by MySQLdb.connect().
        - datastream:   (magpy datastream) 
    Kwargs:
        - mode:         (string)
                            mode: replace -- replaces existing table contents with new one, also replaces informations from sensors and station table
                            mode: delete -- deletes existing tables and writes new ones -- remove (or make it extremeley difficult to use) this method after initializing of tables
                            mode: extend -- only add new data points with unique ID's (default) - table must exist already !
                            mode: insert -- create new table with unique ID

                    New Header informations are created with modes 'replace' and 'delete'.
                    If mode = 'extend' then check for the existence of sensorid and datainfo first -> if not available then request mode = 'insert'
                    Mode 'extend' requires an existing input in sensor, station and datainfo tables: tablename needs to be given.
                    Mode 'insert' checks for the existance of existing inputs in sensor, station and datainfo, and eventually adds a new datainfo tab.
                    Mode 'replace' checks for the existance of existing inputs in sensor, station and datainfo, and replaces the stored information: optional tablename can be given.
                         if tablename is given, then data from this table is replaced - otherwise only data from station and sensor are replaced
                    Mode 'delete' completely deletes all tables and creates new ones. 

    REQUIRES:
        dbdatainfo, dbsensorinfo
        
    RETURNS:
        --

    EXAMPLE:
        >>> stream2db(db,stream,mode='extend',tablename=datainfoid)

    APPLICATION:
        Requires an existing mysql database (e.g. mydb)
        so first connect to the database
        db = MySQLdb.connect (host = "localhost",user = "user",passwd = "secret",db = "mysqldb")
        stream = read('/home/leon/Dropbox/Daten/Magnetism/DIDD-WIK/raw/*', starttime='2013-01-01',endtime='2013-02-01')
        datainfoid = dbdatainfo(db,stream.header['SensorID'],stream.header)
        stream2db(db,stream,mode='extend',tablename=datainfoid)

    TODO:
        - make it possible to create spezial tables by defining an extension (e.g. _sp2013min) where sp indicates special        
    """

    if not mode:
        mode = 'insert'

    if not db:
        loggerdatabase.error("stream2DB: No database connected - aborting -- please create an empty database first")
        return
    cursor = db.cursor ()

    headdict = datastream.header
    head, line = [],[]
    sensorhead, sensorvalue = [],[]
    datainfohead, datainfovalue = [],[]
    stationhead, stationvalue = [],[]
    collst, unitlst = [],[]
    datacolumn = []
    datakeys, dataheads = [],[]
    datavals = []

    if not noheader:
        pass

    loggerdatabase.debug("stream2DB: ### Writing stream to database ###")
    loggerdatabase.debug("stream2DB: --- Starting header extraction ...")

    if len(datastream) < 1:
        loggerdatabase.error("stream2DB: Empty datastream. Aborting ...")
        return

    # check SENSORS information
    loggerdatabase.debug("stream2DB: --- Checking SENSORS table ...")
    sensorid = dbsensorinfo(db,headdict['SensorID'],headdict)
    loggerdatabase.debug("stream2DB: Working with sensor: %s" % sensorid)
    # updating dict
    headdict['SensorID'] = sensorid
    # HEADER INFO - TABLE
    # read Header information
    for key in headdict:
        if key.startswith('Sensor'):
            if key == "SensorID":
                #sensorid = headdict[key]
                sensorhead.append(key)
                sensorvalue.append(sensorid)
            else:
                sensorhead.append(key)
                sensorvalue.append(headdict[key])
        elif key.startswith('Data'):
            if not key == 'DataInterval': 
                datainfohead.append(key)
                datainfovalue.append(headdict[key])
        elif key.startswith('Station'):
            if key == "StationID":
                stationid = headdict[key]
                stationhead.append(key)
            else:
                if not key == "Station": 
                    stationhead.append(key)
            if not key == "Station": 
                stationvalue.append(headdict[key].replace('http://',''))
        elif key.startswith('col'):
            pass            
        elif key.startswith('unit'):
            pass
        else:
            #key not transferred to DB
            loggerdatabase.debug("stream2DB: --- unkown key: %s, %s" % (key, headdict[key]))

    # If no sensorid is available then report error and return:
    if not sensorid:
        loggerdatabase.error("stream2DB:  --- stream2DB: no SensorID specified in stream header. Cannot proceed ...")
        return
    if not stationid:
        loggerdatabase.error("stream2DB: --- stream2DB: no StationID specified in stream header. Cannot proceed ...")
        return

    loggerdatabase.debug("stream2DB: --- Checking column contents ...")
    # HEADER INFO - DATA TABLE
    # select only columss which contain data and get units and column contents
    for key in KEYLIST:
       #print key
       colstr = '-'
       unitstr = '-'
       if not key == 'time':
           ind = KEYLIST.index(key)
           try:
               keylst = np.asarray([row[ind] for row in datastream if not isnan(row[ind])])
               if len(keylst) > 0:
                   dataheads.append(key + ' FLOAT')
                   datakeys.append(key)
           except:
               keylst = np.asarray([row[ind] for row in datastream if not row[ind]=='-'])
               if len(keylst) > 0:
                   dataheads.append(key + ' CHAR(100)')
                   datakeys.append(key)
       for hkey in headdict:
           if key == hkey.replace('col-',''):
               colstr = headdict[hkey]            
           elif key == hkey.replace('unit-col-',''):
               unitstr = headdict[hkey]            
       collst.append(colstr)            
       unitlst.append(unitstr)            

    colstr =  '_'.join(collst)
    unitstr = '_'.join(unitlst)

    # Update the column data at the end together with time

    st = datetime.strftime(num2date(datastream[0].time).replace(tzinfo=None),'%Y-%m-%d %H:%M:%S.%f')
    et = datetime.strftime(num2date(datastream[-1].time).replace(tzinfo=None),'%Y-%m-%d %H:%M:%S.%f')

    loggerdatabase.debug("stream2DB: --- Checking/Updating existing tables ...")
    
    if mode=='extend':
        if not tablename:
            loggerdatabase.error("stream2DB: tablename must be specified for mode 'extend'" )
            return
        # Check for the existance of data base contents and sufficient header information
        searchstation = 'SELECT * FROM STATIONS WHERE StationID = "'+stationid+'"' 
        searchsensor = 'SELECT * FROM SENSORS WHERE SensorID = "'+sensorid+'"'
        searchdatainfo = 'SHOW TABLES LIKE "'+tablename+'"'

        try:
            cursor.execute(searchstation)
        except:
            loggerdatabase.error("stream2DB: Station table not existing - use mode 'insert' - aborting with error")
            raise

        rows = cursor.fetchall()
        if not len(rows) > 0:
            loggerdatabase.error("stream2DB: Station is not yet existing - use mode 'insert' - aborting with error")
            raise
            #return

        cursor.execute(searchsensor)
        rows = cursor.fetchall()
        if not len(rows) > 0:
            loggerdatabase.error("stream2DB: Sensor is not yet existing - use mode 'insert'")
            raise
        cursor.execute(searchdatainfo)
        rows = cursor.fetchall()
        if not len(rows) > 0:
            loggerdatabase.error("stream2DB: Selected data table is not yet existing - check tablename")
            raise
    else:
        # SENSOR TABLE
        # Create sensor table input
        headstr = ' CHAR(100), '.join(SENSORSKEYLIST) + ' CHAR(100)'
        headstr = headstr.replace('SensorID CHAR(100)', 'SensorID CHAR(50) NOT NULL PRIMARY KEY')
        headstr = headstr.replace('SensorDescription CHAR(100)', 'SensorDescription TEXT')
        createsensortablesql = "CREATE TABLE IF NOT EXISTS SENSORS (%s)" % headstr
        sensorsql = "INSERT INTO SENSORS(%s) VALUES (%s)" % (', '.join(sensorhead), '"'+'", "'.join(sensorvalue)+'"')

        # STATION TABLE
        # Create station table input
        stationstr = ' CHAR(100), '.join(STATIONSKEYLIST) + ' CHAR(100)'
        stationstr = stationstr.replace('StationID CHAR(100)', 'StationID CHAR(50) NOT NULL PRIMARY KEY')
        stationstr = stationstr.replace('StationDescription CHAR(100)', 'StationDescription TEXT')
        stationstr = 'StationID CHAR(50) NOT NULL PRIMARY KEY, StationName CHAR(100), StationIAGAcode CHAR(10), StationInstitution CHAR(100), StationStreet CHAR(50), StationCity CHAR(50), StationPostalCode CHAR(20), StationCountry CHAR(50), StationWebInfo CHAR(100), StationEmail CHAR(100), StationDescription TEXT'
        createstationtablesql = "CREATE TABLE IF NOT EXISTS STATIONS (%s)" % stationstr
        stationsql = "INSERT INTO STATIONS(%s) VALUES (%s)" % (', '.join(stationhead), '"'+'", "'.join(stationvalue)+'"')

        # DATAINFO TABLE
        # Create datainfo table
        datainfostr = 'DataID CHAR(50) NOT NULL PRIMARY KEY, SensorID CHAR(50), StationID CHAR(50), ColumnContents TEXT, ColumnUnits TEXT, DataFormat CHAR(20),DataMinTime CHAR(50), DataMaxTime CHAR(50), DataSamplingFilter CHAR(100), DataDigitalSampling CHAR(100), DataComponents CHAR(10), DataSamplingRate CHAR(100), DataType CHAR(100), DataDeltaX DECIMAL(20,9), DataDeltaY DECIMAL(20,9), DataDeltaZ DECIMAL(20,9),DataDeltaF DECIMAL(20,9),DataDeltaReferencePier CHAR(20),DataDeltaReferenceEpoch CHAR(50),DataScaleX DECIMAL(20,9),DataScaleY DECIMAL(20,9),DataScaleZ DECIMAL(20,9),DataScaleUsed CHAR(2),DataSensorOrientation CHAR(10),DataSensorAzimuth DECIMAL(20,9),DataSensorTilt DECIMAL(20,9), DataAngularUnit CHAR(5),DataPier CHAR(20),DataAcquisitionLatitude DECIMAL(20,9), DataAcquisitionLongitude DECIMAL(20,9), DataLocationReference CHAR(20), DataElevation DECIMAL(20,9), DataElevationRef CHAR(10), DataFlagModification CHAR(50), DataAbsFunc CHAR(20), DataAbsDegree INT, DataAbsKnots DECIMAL(20,9), DataAbsMinTime CHAR(50), DataAbsMaxTime CHAR(50), DataAbsDate CHAR(50), DataRating CHAR(10), DataComments TEXT'
        createdatainfotablesql = "CREATE TABLE IF NOT EXISTS DATAINFO (%s)" % datainfostr

        if mode == "delete":
            cursor.execute("DROP TABLE IF EXISTS SENSORS") 
            cursor.execute("DROP TABLE IF EXISTS STATIONS") 
            cursor.execute("DROP TABLE IF EXISTS DATAINFO") 

        cursor.execute(createsensortablesql)
        cursor.execute(createstationtablesql)
        cursor.execute(createdatainfotablesql)

        if mode == "replace":
            try:
                cursor.execute(sensorsql.replace("INSERT","REPLACE"))
                cursor.execute(stationsql.replace("INSERT","REPLACE"))
            except:
                loggerdatabase.warning("stream2DB: Write MySQL: Replace failed")
        else:
            try:
                loggerdatabase.debug("stream2DB: executing: %s" % sensorsql)
                cursor.execute(sensorsql)
            except:
                loggerdatabase.warning("stream2DB: Sensor data already existing: use mode 'replace' to overwrite")
                loggerdatabase.warning("stream2DB: Perhaps this field does not exist")
                pass
            try:
                cursor.execute(stationsql)
            except:
                loggerdatabase.warning("stream2DB: Station data already existing: use mode 'replace' to overwrite")
                loggerdatabase.warning("stream2DB: Perhaps this field does not exist")
                pass

        # DATAINFO TABLE
        # check whether contents exists

        tablename = dbdatainfo(db,sensorid,headdict,None,stationid)


    loggerdatabase.info("stream2DB: Creating/updating data table " + tablename)

    createdatatablesql = "CREATE TABLE IF NOT EXISTS %s (time CHAR(40) NOT NULL PRIMARY KEY, %s)" % (tablename,', '.join(dataheads))
    cursor.execute(createdatatablesql)

    for elem in datastream:
        for el in datakeys:
            if datastream._is_number(eval('elem.'+el)):
                val = str(eval('elem.'+el))
            else:
                val = '"'+str(eval('elem.'+el))+'"'
            if val=='nan':
                val = 'null'
            datavals.append(val)
        ct = datetime.strftime(num2date(elem.time).replace(tzinfo=None),'%Y-%m-%d %H:%M:%S.%f')
        insertdatasql = "INSERT INTO %s(time, %s) VALUES (%s, %s)" % (tablename, ', '.join(datakeys), '"'+ct+'"', ', '.join(datavals))
        if mode == "replace":
            try:
                cursor.execute(insertdatasql.replace("INSERT","REPLACE"))
            except:
                try:
                    cursor.execute(insertdatasql)
                except:
                    loggerdatabase.warning("stream2DB: Write MySQL: Replace failed")
        else:
            try:
                cursor.execute(insertdatasql)
            except:
                loggerdatabase.debug("stream2DB: Record at %s already existing: use mode replace to overwrite" % ct)
        datavals  = []

    # Select MinTime and MaxTime from datatable and eventually update datainfo
    getminmaxtimesql = "Select MIN(time),MAX(time) FROM " + tablename
    cursor.execute(getminmaxtimesql)
    rows = cursor.fetchall()
    loggerdatabase.info("stream2DB: Table now covering a time range from " + str(rows[0][0]) + " to " + str(rows[0][1]))
    updatedatainfotimesql = 'UPDATE DATAINFO SET DataMinTime = "' + rows[0][0] + '", DataMaxTime = "' + rows[0][1] +'", ColumnContents = "' + colstr +'", ColumnUnits = "' + unitstr +'" WHERE DataID = "'+ tablename + '"'
    #print updatedatainfotimesql
    cursor.execute(updatedatainfotimesql)
    
    db.commit()
    cursor.close ()


def db2stream(db, sensorid=None, begin=None, end=None, tableext=None, sql=None):
    """
    sql: provide any additional search criteria
        example: sql = "DataSamplingRate=60 AND DataType='variation'"
    DEFINITION:
        extract data streams from the data base

    PARAMETERS:
    Variables:
        - db:   	    (mysql database) defined by MySQLdb.connect().
        - sensorid:       (string) table and dataid    
        - sql:      (string) provide any additional search criteria
                             example: sql = "DataSamplingRate=60 AND DataType='variation'"
        - datainfoid:       (string) table and dataid    
    Kwargs:

    RETURNS:
        data stream

    EXAMPLE:
        >>> db2stream(db,None,'DIDD_3121331_0002_0001')

    APPLICATION:
        Requires an existing mysql database (e.g. mydb)
        so first connect to the database
        db = MySQLdb.connect (host = "localhost",user = "user",passwd = "secret",db = "mysqldb")

    TODO:
        - If sampling rate not given in DATAINFO get it from the datastream
        - begin needs to be string - generalize that 
    """
    wherelist = []
    stream = DataStream()

    if not db:
        loggerdatabase.error("DB2stream: No database connected - aborting")
        return stream

    cursor = db.cursor ()
    
    if not tableext and not sensorid:
        loggerdatabase.error("DB2stream: Aborting ... either sensorid or table must be specified")
        return
    if begin:
        wherelist.append('time >= "' + begin + '"')
    if end:
        wherelist.append('time <= "' + end + '"')
    if len(wherelist) > 0:
        whereclause = ' AND '.join(wherelist)
    else:
        whereclause = ''
    if sql:
        if len(whereclause) > 0:
            whereclause = whereclause + ' AND ' + sql
        else:
            whereclause = sql

    #print whereclause

    if not tableext:
        getdatainfo = 'SELECT DataID FROM DATAINFO WHERE SensorID = "' + sensorid + '"'
        cursor.execute(getdatainfo)
        rows = cursor.fetchall()
        for table in rows:
            loggerdatabase.debug("DB2stream: Extracting field values from table %s" % str(table[0]))
            if len(whereclause) > 0:
                getdatasql = 'SELECT * FROM ' + table[0] + ' WHERE ' + whereclause
            else:
                getdatasql = 'SELECT * FROM ' + table[0]
            getcolumnnames = 'SHOW COLUMNS FROM ' + table[0]
            # sqlquery to get column names of table - store that in keylst
            keylst = []
            cursor.execute(getcolumnnames)
            rows = cursor.fetchall()
            for line in rows:
                keylst.append(line[0])
            # sqlquery to extract data
            cursor.execute(getdatasql)
            rows = cursor.fetchall()
            for line in rows:
                row = LineStruct()
                for i, elem in enumerate(line):
                    if keylst[i]=='time':
                        exec('row.'+keylst[i]+' = date2num(stream._testtime(elem))')
                    else:
                        exec('row.'+keylst[i]+' = elem')
                    #print elem
                stream.add(row)
    else:
        if len(whereclause) > 0:
            getdatasql = 'SELECT * FROM ' + tableext + ' WHERE ' + whereclause
        else:
            getdatasql = 'SELECT * FROM ' + tableext
        getcolumnnames = 'SHOW COLUMNS FROM ' + tableext
        # sqlquery to get column names of table - store that in keylst
        keylst = []
        cursor.execute(getcolumnnames)
        rows = cursor.fetchall()
        for line in rows:
            keylst.append(line[0])
        # sqlquery to extract data
        cursor.execute(getdatasql)
        rows = cursor.fetchall()
        for line in rows:
            row = LineStruct()
            for i, elem in enumerate(line):
                if keylst[i]=='time':
                    exec('row.'+keylst[i]+' = date2num(stream._testtime(elem))')
                else:
                    if elem == None:
                        elem = float(NaN)
                        #print "found"
                        #if keylst[i]=='x':
                        #    elem = float(NaN)
                    exec('row.'+keylst[i]+' = elem')
            stream.add(row)

    if tableext:
        stream.header = dbfields2dict(db,tableext)

    cursor.close ()
    return stream

def diline2db(db, dilinestruct, mode=None, **kwargs):
    """
    DEFINITION:
        Method to write dilinestruct to a mysql database

    PARAMETERS:
    Variables:
        - db:   	(mysql database) defined by MySQLdb.connect().
        - dilinestruct: (magpy diline) 
    Optional:
        - mode:         (string) - default is insert
                            mode: replace -- replaces existing table contents with new one, also replaces informations from sensors and station table
                            mode: insert -- create new table with unique ID
                            mode: delete -- like insert but drops the existing DIDATA table
    kwargs:
        - tablename:    (string) - specify tablename of the DI table (default is DIDATA)

    EXAMPLE:
        >>> diline2db(db,...)

    APPLICATION:
        Requires an existing mysql database (e.g. mydb)
        so first connect to the database
        db = MySQLdb.connect (host = "localhost",user = "user",passwd = "secret",db = "mysqldb")
    """

    tablename = kwargs.get('tablename')

    loggerdatabase.debug("diline2DB: ### Writing DI values to database ###")

    if len(dilinestruct) < 1:
        loggerdatabase.error("diline2DB: Empty diline. Aborting ...")
        return

    # 1. Create the diline table if not existing
    # - DIDATA
    DIDATAKEYLIST = ['DIID','StartTime','TimeArray','HcArray','VcArray','ResArray','OptArray','LaserArray','FTimeArray',
                                 'FArray','Temperature','ScalevalueFluxgate','ScaleAngle','Azimuth','Pier','Observer','DIInst',
                                 'FInst','FluxInst','InputDate','DIComment']

    # DIDATA TABLE
    if not tablename:
        tablename = 'DIDATA'

    cursor = db.cursor ()

    headstr = ' CHAR(100), '.join(DIDATAKEYLIST) + ' CHAR(100)'
    headstr = headstr.replace('DIID CHAR(100)', 'DIID CHAR(100) NOT NULL PRIMARY KEY')
    headstr = headstr.replace('DIComment CHAR(100)', 'DIComment TEXT')
    headstr = headstr.replace('Array CHAR(100)', 'Array TEXT')    
    createDItablesql = "CREATE TABLE IF NOT EXISTS %s (%s)" % (tablename,headstr)

    if mode == 'delete':
        try:
            cursor.execute("DROP TABLE IF EXISTS %s" % tablename) 
        except:
            loggerdatabase.info("diline2DB: DIDATA table not yet existing")
        loggerdatabase.info("diline2DB: Old DIDATA table has been deleted")
    
    try:
        cursor.execute(createDItablesql)
        loggerdatabase.info("diline2DB: New DIDATA table created")
    except:
        loggerdatabase.debug("diline2DB: DIDATA table already existing ?? TODO: -- check the validity of this message --")
    
    # 2. Add DI values to the table
    #   Cycle through all lines of the dilinestruct
    #   - a) convert arrays to underscore separated text like 'nan,nan,765,7656,879.6765,nan"

    for line in dilinestruct:
        insertlst = []
        insertlst.append(str(line.pier)+'_'+datetime.strftime(num2date(line.time[4]),"%Y-%m-%d %H:%M:%S"))
        insertlst.append(datetime.strftime(num2date(line.time[4]),"%Y-%m-%d %H:%M:%S"))
        strlist = [str(elem) for elem in line.time]
        timearray = '%s' % ('_'.join(strlist))
        insertlst.append('%s' % ('_'.join(strlist)))
        strlist = [str(elem) for elem in line.hc]
        hcarray = '%s' % ('_'.join(strlist))
        insertlst.append('%s' % ('_'.join(strlist)))
        strlist = [str(elem) for elem in line.vc]
        vcarray = '%s' % ('_'.join(strlist))
        insertlst.append('%s' % ('_'.join(strlist)))
        strlist = [str(elem) for elem in line.res]
        resarray = '%s' % ('_'.join(strlist))
        insertlst.append('%s' % ('_'.join(strlist)))
        strlist = [str(elem) for elem in line.opt]
        optarray = '%s' % ('_'.join(strlist))
        insertlst.append('%s' % ('_'.join(strlist)))
        strlist = [str(elem) for elem in line.laser]
        laserarray = '%s' % ('_'.join(strlist))
        insertlst.append('%s' % ('_'.join(strlist)))
        strlist = [str(elem) for elem in line.ftime]
        ftimearray = '%s' % ('_'.join(strlist))
        insertlst.append('%s' % ('_'.join(strlist)))
        strlist = [str(elem) for elem in line.f]
        farray = '%s' % ('_'.join(strlist))
        insertlst.append('%s' % ('_'.join(strlist)))
        insertlst.append(str(line.t))
        insertlst.append(str(line.scaleflux))
        insertlst.append(str(line.scaleangle))
        insertlst.append(str(line.azimuth))
        insertlst.append(str(line.pier))
        insertlst.append(str(line.person))
        insertlst.append(str(line.di_inst))
        insertlst.append(str(line.f_inst))
        insertlst.append(str(line.fluxgatesensor))
        insertlst.append(str(line.inputdate))
        insertlst.append("No comment")

        disql = "INSERT INTO %s(%s) VALUES (%s)" % (tablename,', '.join(DIDATAKEYLIST), '"'+'", "'.join(insertlst)+'"')
        if mode == "replace":
            disql = disql.replace("INSERT","REPLACE")

        try:
            cursor.execute(disql)
        except:
            loggerdatabase.debug("diline2DB: data already existing")

    db.commit()
    cursor.close ()

def db2diline(db,**kwargs):
    """
    DEFINITION:
        Method to read DI values from a database and write them to a list of DILineStruct's

    PARAMETERS:
    Variables:
        - db:   	(mysql database) defined by MySQLdb.connect().
    kwargs:
        - starttime:    (string/datetime) - time range to select
        - endtime:      (string/datetime) - 
        - sql:          (string) - define any additional selection criteria (e.g. "Pier = 'A2'" AND "Observer = 'Mickey Mouse'")
                                important: dont forget the ' ' 
        - tablename:    (string) - specify tablename of the DI table (default is DIDATA)

    EXAMPLE:
        >>> resultlist = db2diline(db,starttime="2013-01-01",sql="Pier='A2'")

    APPLICATION:
        Requires an existing mysql database (e.g. mydb)
        so first connect to the database
        db = MySQLdb.connect (host = "localhost",user = "user",passwd = "secret",db = "mysqldb")

    RETURNS:
        list of DILineStruct elements
    """

    starttime = kwargs.get('starttime')
    endtime = kwargs.get('endtime')
    sql = kwargs.get('sql')
    tablename = kwargs.get('tablename')

    stream = DataStream() # to access some time functions from the stream package

    if not db:
        loggerdatabase.error("DB2diline: No database connected - aborting")
        return didata

    cursor = db.cursor ()

    resultlist = []

    if not tablename:
        tablename = 'DIDATA'

    whereclause = ''
    if starttime:
        starttime = stream._testtime(starttime)
        print starttime
        st = datetime.strftime(starttime, "%Y-%m-%d %H:%M:%S")
        whereclause += "StartTime >= '%s' " % st
    if endtime:
        if len(whereclause) > 1: 
            whereclause += "AND "
        endtime = stream._testtime(endtime)
        et = datetime.strftime(endtime, "%Y-%m-%d %H:%M:%S")
        whereclause += "StartTime <= '%s' " % et
    if sql: 
        if len(whereclause) > 1: 
            whereclause += "AND "
        whereclause += sql

    if len(whereclause) > 0:
        getdidata = 'SELECT * FROM ' + tablename + ' WHERE ' + whereclause
    else:
        getdidata = 'SELECT * FROM ' + tablename
 
    print "Where: ", whereclause   
    cursor.execute(getdidata)
    rows = cursor.fetchall()
    for di in rows:
        loggerdatabase.debug("DB2stream: Extracting DI values for %s" % str(di[1]))
        # Zerlege time column
        timelst = [float(elem) for elem in di[2].split('_')]
        distruct = DILineStruct(len(timelst))
        distruct.time = timelst
        distruct.hc = [float(elem) for elem in di[3].split('_')]
        distruct.vc = [float(elem) for elem in di[4].split('_')]
        distruct.res = [float(elem) for elem in di[5].split('_') if len(di[5].split('_')) > 1]
        distruct.opt = [float(elem) for elem in di[6].split('_') if len(di[6].split('_')) > 1]
        distruct.laser = [float(elem) for elem in di[7].split('_') if len(di[7].split('_')) > 1]
        distruct.ftime = [float(elem) for elem in di[8].split('_') if len(di[8].split('_')) > 1]
        distruct.f = [float(elem) for elem in di[9].split('_') if len(di[9].split('_')) > 1]
        distruct.t = di[10]
        distruct.scaleflux =  di[11]
        distruct.scaleangle =  di[12]
        distruct.azimuth =  di[13]
        distruct.person =  di[14]
        distruct.pier =  di[15]
        distruct.di_inst =  di[16]
        distruct.f_inst =  di[17]
        distruct.fluxgatesensor =  di[18]
        distruct.inputdate =  stream._testtime(di[19])
        resultlist.append(distruct)

    return resultlist


def getBaselineProperties(db,datastream,distream=None):
    """
    method to extract baseline properties from a DB for a given time
    reads starttime, endtime, and baseline properties (like function, degree, knots etc) from DB
    if no information is provided then the baseline method has to be used
    The method creates database inputs for each analyzed segment using the 'replace' mode
    ideally 
    """
    stream = DataStream()
    basecorr = DataStream()
    streamdat = []
    flist = []

    if not db:
        print "No database connected - aborting"
        return stream

    cursor = db.cursor ()

    sensid = datastream.header['SensorID']

    if not sensid or len(sensid) < 1:
        print "No Sensor specified in datastream header - aborting"
        return stream

    # Remove flagged data
    #datastream = datastream.remove_flagged()
        
    # Test whether table "Baseline" exists
    testsql = 'SHOW TABLES LIKE "BASELINE"'
    cursor.execute(testsql)
    rows = cursor.fetchall()
    if len(rows) < 1:
        print "No Baselinetable existing - creating an empty table in the selected database and aborting then"
        baseheadstr = 'SensorID CHAR(50) NOT NULL, MinTime DATETIME, MaxTime DATETIME, TmpMaxTime DATETIME, BaseFunction CHAR(50), BaseDegree INT, BaseKnots FLOAT, BaseComment TEXT'
        createbasetablesql = "CREATE TABLE IF NOT EXISTS BASELINE (%s)" % baseheadstr
        cursor.execute (createbasetablesql)
        # TmpMaxTime is used to store current date if MaxTime is Emtpy
        #basesql = "INSERT INTO BASELINE(%s) VALUES (%s)" % (', '.join(sensorhead), '"'+'", "'.join(sensorvalue)+'"')
        # Insert code here for creating empty table
        return

    # get starttime
    starttime = datastream._testtime(datastream[0].time)
    endtime = datastream._testtime(datastream[-1].time)

    # get the appropriate basedatatable database input
    #absstream = ...
    # Test whether table "SENSORID_Basedata" exists
    testsql = 'SHOW TABLES LIKE "%s_BASEDATA"' % sensid
    cursor.execute(testsql)
    rows = cursor.fetchall()
    if len(rows) < 1:
        print "No Basedatatable existing - trying to create one from file"
        if not distream:
            print "No DI data provided - aborting"
            return
        stream2db(db,distream,mode='replace',tablename=sensid+'_BASEDATA')
    else:
        if distream:
            print "Resetting basedata table from file"
            stream2db(db,distream,mode='replace',tablename=sensid+'_BASEDATA')
            distream = distream.remove_flagged()            
        else:
            table = sensid+'_BASEDATA' 
            distream = db2stream(db,tableext=table)
            distream = distream.remove_flagged()
            
    #print sensid


    # update TmpMaxTime column with current time in empty MaxTime Column
    currenttime = datetime.strftime(datetime.utcnow(),'%Y-%m-%d %H:%M:%S')
    copy2tmp = "UPDATE BASELINE SET TmpMaxTime = MaxTime"
    insertdatesql = "UPDATE BASELINE SET TmpMaxTime = '%s' WHERE TmpMaxTime IS NULL" % (currenttime)

    cursor.execute(copy2tmp)
    cursor.execute(insertdatesql)
    #
    select = 'MinTime, TmpMaxTime, BaseFunction, BaseDegree, BaseKnots'
    # start before and end within datastream time range
    where1 = '"%s" < MinTime AND "%s" <= TmpMaxTime AND "%s" > MinTime' % (starttime,endtime,endtime)
    # start within and end after datastream time range
    where2 = '"%s" >= MinTime AND "%s" < TmpMaxTime AND "%s" > MaxTime' % (starttime,starttime,endtime)
    # start and end within datastream time range
    where3 = '"%s" > MinTime AND "%s" < TmpMaxTime AND "%s" > MinTime AND "%s" < MaxTime' % (starttime,starttime,endtime,endtime)
    # if where1 to where3 unsuccessfull then use where4
    where4 = '"%s" <= MinTime AND "%s" >= TmpMaxTime' % (starttime,endtime)

    where = 'SensorID = "%s" AND ((%s) OR (%s) OR (%s) OR (%s))' % (sensid,where1,where2,where3,where4)
    
    getbaselineinfo = 'SELECT %s FROM BASELINE WHERE %s' % (select, where)
    cursor.execute(getbaselineinfo)
    rows = cursor.fetchall()
    print rows
    for line in rows:
        # Get stream between min and maxtime and do the baseline fit
        start = date2num(line[0])
        stop = date2num(line[1])
        datalist = [row for row in datastream if start <= row.time <= stop]
        #To do: if MinTime << starttime then distart = start - 30 Tage
        if line[0] < starttime-timedelta(days=30):
            distart = date2num(starttime-timedelta(days=30))
        else:
            distart = start
        #To do: if MaxTime >> endtime then distop = stop + 30 Tage 
        if line[0] > endtime+timedelta(days=30):
            distop = date2num(endtime+timedelta(days=30))
        else:
            distop = stop
        print start,distart, stop,distop
        dilist = [row for row in distream if start <= row.time <= stop]
        part = DataStream(datalist,datastream.header)
        abspart =  DataStream(dilist,distream.header)
        fitfunc = line[2]
        try:
            fitdegree=float(line[3])
        except:
            fitdegree=5
        try:
            fitknots=float(line[4])
        except:
            fitknots=0.05

        # return baseline function as well
        basecorr,func = part.baseline(abspart,fitfunc=fitfunc,fitdegree=fitdegree,knotstep=fitknots,plotbaseline=True,returnfunction=True)
        flist.append(func)
        dat = [row for row in basecorr]
        deltaf = abspart.mean('df',meanfunction='median',percentage=1)
        # Update header information
        part.header['DataDeltaF'] = deltaf
        part.header['DataAbsMinTime'] = datetime.strftime(num2date(dat[0].time),"%Y-%m-%d %H:%M:%S")
        part.header['DataAbsMaxTime'] = datetime.strftime(num2date(dat[-1].time),"%Y-%m-%d %H:%M:%S")
        part.header['DataAbsKnots'] = str(fitknots)
        part.header['DataAbsDegree'] = str(fitdegree)
        part.header['DataAbsFunc'] = fitfunc
        part.header['DataType'] = 'preliminary'
        streamdat.extend(dat)
        print "Stream: ", len(streamdat), len(basecorr)
        stream2db(db,DataStream(dat,part.header),mode='replace')

    print flist
    for elem in flist:
        for key in KEYLIST:
            fkey = 'f'+key
            if fkey in elem[0]:
                ttmp = arange(0,1,0.0001)# Get the minimum and maximum relative times
                #ax.plot_date(self._denormalize(ttmp,function[1],function[2]),function[0][fkey](ttmp),'r-')
            
    return DataStream(streamdat,datastream.header)
    
    db.commit()


def flaglist2db(db,flaglist,mode=None,sensorid=None,modificationdate=None):
    """
    Function to converts a python list (actually an array)
    within flagging information to a data base table
    required parameters are the 
    db: name of the mysql data base
    cursor: a pointer to the data base
    flaglist: the list containing flagging information of format:
                [[starttime, endtime, singlecomp, flagNum, flagReason, (SensorID, ModificationDate)],...]

    Optional:
    mode: default inserts information if not existing
          use 'replace' to replace any existing information (check auto_increment with flag ID !!!!!!!)
          use 'delete' to remove any preexisting FLAG Table from data base first
    sensorid: a string with the sensor id, if not provided within the list
    modificationdate: a string with the flagging modificationdate, if not provided within the list

    Flag Table looks like:
    data base format: flagID, sensorID, starttime, endtime, components, flagNum, flagReason, ModificationDate
    """
    if not sensorid:
        sensorid = 'defaultsensor'
    if not modificationdate:
        sensorid = '1971-11-22 11:22:00'

    if not db:
        print "No database connected - aborting"
        return
    cursor = db.cursor ()

    lentype = len(flaglist[0])

    if lentype <= 5:
        listwithoutcomp = [[elem[0],elem[1],elem[3],elem[4]] for elem in flaglist]
    else:
        listwithoutcomp = [[elem[0],elem[1],elem[3],elem[4],elem[5],elem[6]] for elem in flaglist]

    newlst = []
    for elem in listwithoutcomp:
        elem[0] = datetime.strftime(elem[0],"%Y-%m-%d %H:%M:%S.%f")
        elem[1] = datetime.strftime(elem[1],"%Y-%m-%d %H:%M:%S.%f")
        if elem not in newlst:
            newlst.append(elem)

    for elem in newlst:
        complst = []
        for elem2 in flaglist:
            comp = elem2[2]
            if lentype <= 5:
                el2 = [datetime.strftime(elem2[0],"%Y-%m-%d %H:%M:%S.%f"),datetime.strftime(elem2[1],"%Y-%m-%d %H:%M:%S.%f"),elem2[3],elem2[4]]
            else:
                el2 = [datetime.strftime(elem2[0],"%Y-%m-%d %H:%M:%S.%f"),datetime.strftime(elem2[1],"%Y-%m-%d %H:%M:%S.%f"),elem2[3],elem2[4],elem2[5],elem2[6]]
            if el2 == elem:
                complst.append(comp)
        compstr = '_'.join(complst)
        if lentype <= 5:
            elem.extend([sensorid,modificationdate])
        elem.append(compstr)

    # Flagging TABLE
    # Create flagging table
    if mode == 'delete':
        cursor.execute("DROP TABLE IF EXISTS FLAGS") 

    flagstr = 'FlagID INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, SensorID CHAR(50), FlagBeginTime CHAR(50), FlagEndTime CHAR(50), FlagComponents CHAR(50), FlagNum INT, FlagReason TEXT, ModificationDate CHAR(50)'
    createflagtablesql = "CREATE TABLE IF NOT EXISTS FLAGS (%s)" % flagstr
    cursor.execute(createflagtablesql)

    # add flagging data
    #if lentype <= 4:
    #    flaghead = 'FlagID, FlagBeginTime, FlagEndTime, FlagNum, FlagReason, FlagComponents'
    flaghead = 'FlagBeginTime, FlagEndTime, FlagNum, FlagReason, SensorID, ModificationDate, FlagComponents'

    for elem in newlst:
        elem = [str(el) for el in elem]
        flagsql = "INSERT INTO FLAGS(%s) VALUES (%s)" % (flaghead, '"'+'", "'.join(elem)+'"')
        if mode == "replace":
            try:
                cursor.execute(flagsql.replace("INSERT","REPLACE"))
            except:
                print "Write MySQL: Replace failed"
        else:
            try:
                cursor.execute(flagsql)
            except:
                print "Record already existing: use mode 'replace' to override"

    db.commit()
    cursor.close ()


def db2flaglist(db,sensorid, begin=None, end=None):
    """
    Read flagging information for specified sensor from data base and return a flagging list
    """

    if not db:
        print "No database connected - aborting"
        return []
    cursor = db.cursor ()

    searchsql = 'SELECT FlagBeginTime, FlagEndTime, FlagComponents, FlagNum, FlagReason, SensorID, ModificationDate FROM FLAGS WHERE SensorID = "%s"' % sensorid
    if begin:
        addbeginsql = ' AND FlagBeginTime >= "%s"' % begin
    else:
        addbeginsql = '' 
    if end:
        addendsql = ' AND FlagEndTime <= "%s"' % end 
    else:
        addendsql = '' 
    
    cursor.execute (searchsql + addbeginsql + addendsql)
    rows = cursor.fetchall()

    res=[]
    for line in rows:
        comps = line[2].split('_')
        for elem in comps:
            res.append([line[0],line[1],elem,int(line[3]),line[4],line[5],line[6]])

    cursor.close ()
    return res

