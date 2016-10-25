import unittest


import os, sys
import datetime
from mpiprof import logger
from mpiprof import config
from mpiprof import mpi_util
from mpiprof import throttle

class TestUtils(unittest.TestCase):

    def test_mpiprof_cmdline(self):
        from mpiprof.command_line import main
        main()

    ## unit test for logger
    def test_mpiprof_logger(self):

        ## init a logfile using module
        logf = 'log_test.txt'
        if os.path.exists(logf):
            os.remove(logf)
        log = logger.logInit('INFO', logf, 'test', 2);

        ## check logfile was created
        self.assertEqual(os.path.exists(logf), True);
        if log:
            log.info('this is an info line')
            log.error('this is an error line')

        self.assertEqual(os.stat(logf).st_size, 104)
        os.remove(logf)

    ## unit test for config
    def test_mpiprof_config(self):

        inpf = 'config_test.csv'
        comp = [ {'var1a': 'value1A', 'var2a': 'value2A'}, {'var2b': 'value2B'} ]
        secs = ['sectionA', 'sectionB']

        ## create an ini file to parse
        with open(inpf, 'w') as f:
            f.write('\n;comment A\n[sectionA]\nvar1A: value1A\nvar2A: value2A\n\n[sectionB]\nvar2B: value2B\n\n')
            f.close()

        ## parse ini file using module and compare sections, vars
        cfg_parse = config.getConfigParser(inpf)
        self.assertEqual(cfg_parse.sections(), secs)
        rep = []
        for item in cfg_parse.sections():
            rep.append( config.getConfigSectionMap(cfg_parse, item) )
        self.assertEqual(rep, comp)

        comp = [{'col2': 'b', 'col3': 'c', 'col1': 'a'}, {'col2': 'e', 'col3': 'f', 'col1': 'd'}, {'col2': 'h', 'col3': 'i', 'col1': 'g'}]
        with open(inpf, 'w') as f:
            f.write('#this is a comment\n\ncol1,col2,col3\na, b, c\nd, e, f\ng, h, i\n')
            f.close()
        data = config.parseCSV(inpf)
        self.assertEqual(data, comp)
        os.remove(inpf)

    def test_mpiprof_throttle(self):
        f = 4; N = 2
        res = throttle.measure_throttle(n=N, per_sec=f)
        self.assertLess(res, f) and self.assertGreater(res, 0.9*f)


class TestDriver(unittest.TestCase):

    def test_gnu_cipher(self):

        cnf = '/home/venkat/work/dev/mpi_pilot/MPIProf/mpiprof.conf'
        ptf = 'gnu_cipher_test.txt'
        ctf = ptf + '.gpg'

        ## read config for
        if os.path.exists(cnf):
            cfg = config.getConfigParser(cnf)
            gpg_opt = config.getConfigSectionMap(cfg, 'gpg')
            gpg = mpi_util.gpgkey(gpg_opt)

            with open (ptf,  'wb') as f:
                f.write('testing cipher text\nfrom gnupg util')
            if os.path.exists(ptf):
                d = os.path.join ( os.getcwd(), ptf)
                key = [ i.strip() for i  in gpg_opt['recipients'].split(',') ]
                status, ofile = gpg.encrypt(d,d,key)
                self.assertEqual(status.ok, True)

                if status.ok:
                    if os.path.exists( os.path.join(os.getcwd(), ctf) ):
                        status, ofile = gpg.decrypt( os.path.join(os.getcwd(), ctf), os.getcwd() )
                        self.assertEqual(status.ok, True)
            try:
                os.remove(ptf)
                os.remove(ctf)
            except OSError:
                pass

    def test_wsdl_client(self):

        cnf = '/home/venkat/work/dev/mpi_pilot/MPIProf/mpiprof.conf'
        if os.path.exists(cnf):
            cfg = config.getConfigParser(cnf)
            wsdl_opt = config.getConfigSectionMap(cfg, 'wsdl')
            client = mpi_util.wsdl_client(wsdl_opt)
            self.assertIsNotNone(client)



if __name__ == '__main__':
    func_tests = unittest.TestLoader().loadTestsFromTestCase(TestUtils)
    func_tests.TextTestRunner(stream=sys.stdout).run(func_tests)

    driver_tests = unittest.TestLoader().loadTestsFromTestCase(TestDriver)
    driver_tests.TextTestRunner(stream=sys.stdout).run(driver_tests)

    #unittest.main(failfast=True, exit=False)
