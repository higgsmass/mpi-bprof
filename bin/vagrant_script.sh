#!/bin/sh

echo "------------------------------------------------"
echo "--> Executing custom shell script in vagrant env"

echo -ne '\n\n--> Checking environment\n'
python -V &> /dev/null && python -mplatform
echo -ne '\n--> Architecture\n'
arch

echo -ne '\n--> '
python -V 

## virtual env does not play nicely with cx_Oracle/paramiko (why?)
##. ~vagrant/venv/bin/activate 

echo -ne '\n--> Building and Installing Software\n'
cd /vagrant && sudo python setup.py test && sudo python setup.py install
echo -ne '\n--> Running Integration Test\n'
mpiws -c /files/mpiprof_vagrant_test.conf -i /files/HSSC_SampleFile.txt.gpg -o /tmp/myOut.txt -t
echo "------------------------------------------------"
