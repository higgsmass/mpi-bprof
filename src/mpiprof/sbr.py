
import os
import re
import sys
import csv
import time
import logging
import httplib
import datetime

from suds.sax.text import Raw
from suds import WebFault

## local imports
import config
import logger
import mpi_util

class sbr:

    def __init__(self, options):

        self.options = options

        self.config_path = None
        self.config_vars = None

        self.gpg = None
        self.wsdl = None
        self.client = None

        self.payload_all = []
        self.required_search_keys = []
        self.optional_search_keys = []

        self.payload_cols = dict()
        self.append_cols = dict()
        self.payload_map = dict()

        self.patients = []
        self.enrollees = []
        self.output_header = []
        self.outfile = None

        sys.stderr.write("\n--> Reading configuration file: %s\n" % options.conf)
        try:
            with open (options.conf, 'r') as f:
                f.close()
            self.config_path = options.conf
            self.config_vars = config.getConfigParser(self.config_path)
        except IOError, err:
            sys.stderr.write('ERROR: %s\n' % str(err))
            traceback.print_exc()
            sys.exit(err.errno)

        self.infile = self.options.inputfile

        self.gpg_opts = config.getConfigSectionMap( self.config_vars, "gpg" )
        self.wsdl_opts = config.getConfigSectionMap( self.config_vars, "wsdl" )
        self.mpi_opts = config.getConfigSectionMap( self.config_vars, "mpi" )
        self.log = logger.logInit(self.options.logLevel, self.gpg_opts['log_path'], type(self).__name__)

        self.gpg = mpi_util.gpgkey(self.gpg_opts)
        self.wsdl = mpi_util.wsdl_client(self.wsdl_opts)

        if self.options.show:
            self.printconfig()

        if self.options.logLevel == 'DEBUG':
            logging.basicConfig(level=logging.INFO)
            logging.getLogger('suds.client').setLevel(logging.DEBUG)
            logging.getLogger('suds.transport').setLevel(logging.DEBUG)

    def printconfig(self):
        sec_done = []
        for item in self.config_vars.sections():
            qq = config.getConfigSectionMap(self.config_vars, item)
            sys.stderr.write('\n----------------------[ %s ]----------------------\n' % item)
            for j in qq:
                if j not in sec_done:
                    sys.stderr.write( '%-25s: %s\n' % (j, qq[j]))
                    sec_done.append(j)


    def configure(self):

        ## read mapping document
        self.read_sl_data()

        ## initialize client
        self.client = self.wsdl.http_client()


    def read_sl_data(self, block_size = 1024*10):
        try:
            with open( self.mpi_opts['enrollee_config'], 'rb') as tsv:
                in_dialect = csv.Sniffer().sniff( tsv.read(block_size) )
                tsv.seek(0)
                reader = csv.DictReader(tsv, dialect=in_dialect)
                for line in reader:
                    self.payload_all.append(line)
                    if (line['Datafile_Option'] == 'Required') or (line['Datafile_Option'] == 'Internal'):
                        if line['Datafile_Option'] == 'Required':
                            self.payload_cols [ line['EMPI_FieldName'] ] = line['Datafile_Name']
                        if line['Enrollee_FieldName'] != '':
                            if line['Enrollee_Option'] == 'Required':
                                self.required_search_keys.append( line['EMPI_FieldName'] )
                            else:
                                self.optional_search_keys.append( line['EMPI_FieldName'] )
                            self.payload_map[ line['EMPI_FieldName'] ] = line['Enrollee_FieldName']

        except IOError as err:
            sys.stderr.write ('IO error({0}): {1}\n'.format(err.errno, err.strerror))
            sys.exit(err.errno)


    def read_input(self, encrypted = True):
        read_status = True
        in_dialect = None
        if encrypted:
            status, self.infile = self.gpg.decrypt( self.options.inputfile, self.gpg_opts['extract_path'])
            if not status.ok:
                sys.stderr.write(status.status + '\n' + status.stderr)
                sys.exit(1)

        try:
            with open(self.infile, 'rb') as tsv:
                in_dialect = csv.Sniffer().sniff( tsv.read(1024*10), delimiters=';\t,')
                tsv.seek(0)
                data = csv.DictReader(tsv, dialect=in_dialect)
                for line in data:
                    self.enrollees.append(line)
        except IOError as err:
            sys.stderr.write ('IO error({0}): {1}\n'.format(err.errno, err.strerror))
            read_status = False

        return read_status, in_dialect


    def prep_output(self, csv_dialect = None):
        for key in self.payload_cols:
            self.append_cols [ self.payload_cols[key] ] = '(null)'

        self.output_header = [ key for key in self.enrollees[0] if self.enrollees[0] ]
        [ self.output_header.append( self.payload_cols[key]) for key in self.payload_cols ]

        try:
            self.outfile = open ( self.options.outputfile, 'w' )
            if csv_dialect:
                csv_dialect.skipinitialspace = True
                csv_dialect.escapechar = '\\'
                csv_dialect.quoting = csv.QUOTE_MINIMAL
            else:
                log.warn('No dialect specified, using \'excel-tab\'')
                csv_dialect = 'excel-tab'
            self.serializer = csv.DictWriter(self.outfile, fieldnames = self.output_header, dialect = csv_dialect, extrasaction='ignore')
            if not self.options.no_header:
                self.serializer.writeheader()

        except IOError as err:
            sys.stderr.write ('IO error({0}): {1}\n'.format(err.errno, err.strerror))


    def transform(self, value, key):

        tr_keys = [ 'DATE', 'GENDER' ]

        ## need to transform gender to HSSC gender code
        hssc_mpi_gender = { 'F':'11', 'M':'12', 'I':'13', 'U':'14', 'O':'15', '':'' }

        if self.payload_map[key] not in tr_keys:
            return value
        if self.payload_map[key] == 'DATE':
            return datetime.datetime.strptime( value, '%m/%d/%Y').strftime('%Y%m%d%H%M%S')

        if self.payload_map[key] == 'GENDER':
            return hssc_mpi_gender [ value ]

        return value

    def process_enrollees(self):

        person = self.client.factory.create('searchBlock')
        address = self.client.factory.create('address')
        incl_pattern = re.compile(self.mpi_opts['filter_pattern'])

        threshold = 19.
        apply_lid_filter = True
        sleep_secs = 1
        use_aux_info = False

        try:
            threshold = float ( self.mpi_opts['match_threshold'] )
            apply_lid_filter = self.mpi_opts['apply_lid_filter'] == 'True'
            sleep_secs = int ( self.mpi_opts['throttle_time_s'] )
            use_aux_info = self.mpi_opts['use_auxiliary_info'] == 'True'
        except ValueError:
            threshold = 19.
            apply_lid_filter = True
            sleep_secs = 1
            use_aux_info = False


        ## loop over enrollees -- begin
        for en in self.enrollees:

            if self.options.throttle:
                time.sleep(sleep_secs)

            null_in_required_keys = False

            en_out = en

            ## check if required keys have null-values. We cannot process it if that's the case
            for key in self.required_search_keys:
                #print key, payload_map[key], hasattr(person.objBean, key), en[ payload_map[key] ]
                if en[ self.payload_map[key] ] == '(null)':
                    null_in_required_keys = True
                    break
                else:
                    if hasattr(person.objBean, key):
                        setattr(person.objBean, key, self.transform ( en[ self.payload_map[key]], key ) )


            en_out.update(self.append_cols) ## additional columns (may have nulls, but it's ready)

            if null_in_required_keys:
                self.serializer.writerow(en_out)
                continue

            ## TODO
            if use_aux_info:
                self.log.info('Using auxiliary data (address block) in search')

            patients = None
            try:
                patients = self.client.service.searchBlock(person.objBean)
            except WebFault, f:
                sys.stderr.write(f)
                sys.exit(f.fault)
            except Exception, e:
                sys.stderr.write(e)
                sys.exit(e.errno)


            if patients:
                if patients[0] == httplib.OK:
                    for pat in patients[1]:

                        score = float( pat.comparisonScore )
                        if score < threshold:
                            continue

                        ## serialize output from patient, patient.address
                        for attr in self.payload_cols:
                            if hasattr(pat.patient, attr):
                                en_out[ self.payload_cols[attr] ] = getattr(pat.patient, attr)
                            elif hasattr(pat, attr):
                                en_out[ self.payload_cols[attr] ] = getattr(pat, attr)
                            elif hasattr(pat.patient, 'address'):
                                if len(pat.patient.address) > 0:
                                    if hasattr(pat.patient.address[0], attr):
                                        en_out[ self.payload_cols[attr] ] = getattr(pat.patient.address[0], attr)


                        lids = None
                        xml_lid = Raw('%s' % pat.EUID)
                        try:

                            lids = self.client.service.getLIDs(xml_lid)

                        except WebFault, f:
                            sys.stderr.write(f)
                            sys.exit(f.fault)

                        except Exception, e:
                            sys.stderr.write(e)
                            sys.exit(e.errno)

                        if not lids:
                            self.serializer.writerow(en_out_lid)
                        else:
                            if lids[0] == httplib.OK:
                                en_out_lid = en_out
                                for lid in lids[1]:
                                    for attr in self.payload_cols:
                                        if apply_lid_filter:
                                            if attr == self.mpi_opts['site_lid_field'] and ( not incl_pattern.search( getattr(lid, attr) ) ):
                                                continue
                                        if hasattr(lid, attr):
                                            en_out_lid[ self.payload_cols[attr] ] = getattr(lid, attr)
                                    self.serializer.writerow(en_out_lid)

                            else:
                                sys.stderr.write('ERROR: http request failed for LID: %s\n%s\n' % (xml_lid, httplib.responses(lids[0])))
                else:
                    sys.stderr.write('ERROR: failed http request for PATIENT SSN = : %s\n%s\n' % (en['SSN'], httplib.responses(patients[0])))


    def run(self):
        self.configure()
        status_ok, dialect = self.read_input()
        if status_ok:
            self.log.info('Read %d rows of data' % len(self.enrollees))
            self.prep_output(dialect)
            self.process_enrollees()
        self.log.info('Processing complete')


