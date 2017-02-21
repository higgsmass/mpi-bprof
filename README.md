# mpi-bprof

# Summary
_EMPI Business Object Profiler_ - A web services interface to Master Index Data Manager (MIDM) 
It takes as it's input demographic information (in plain-text or encrypted format), queries (using WSDL/SOAP web services) the database and returns matching patient records. For each matching record, it also returns a list of local ID's (LID's) found.
The search can be restricted to an institution. The number of matches can be controlled using the match score. See the configuration for more details. The output is serialized and (optionally) can be encrypted.

# Documentation
https://higgsmass.github.io/mpi-bprof/

# Instructions to run

Login to hssc-vetl-p, sudo as root and attach the existing screen session (103857.pts-0.hssc-vetl-p) OR sudo as mpiprof

Activate the virtual environment to run the program

```
[mpiprof@hssc-vetl-p ~]$ source ~mpiprof/mpienv/bin/activate
```

For help with the application use:
```
[ mpi-bprof ] : [mpiprof@hssc-vetl-p ~]$ mpiws --help
```

Note: We received an encrypted enrollment file from MUSC (which will be the input file) and use `-t [ --throttle ]` option to throttle the API that hits the EMPI DB using the web services. Throttling is necessary to prevent swarming the DB. Use the default configuration file (`/usr/local/etc/mpi-bprof/mpiprof.conf`)
```
[ mpi-bprof ] : [mpiprof@hssc-vetl-p ~]$ time mpiws \
             -c /usr/local/etc/mpi-bprof/mpiprof.conf --throttle\
             -i /data/hssclts/hssclts/mpiprof/HSSC_MonthlyTest_27799.txt.gpg \
             -o /tmp/HSSC_MonthlyTest_27800.txt
```
Here's the output
```
--> Reading configuration file: /usr/local/etc/mpi-bprof/mpiprof.conf
Enter cipher key for decrypting "/data/hssclts/hssclts/mpiprof/HSSC_MonthlyTest_27799.txt.gpg":

real    776m39.895s
user    185m26.273s
sys     0m15.519s

[ mpi-bprof ] : [mpiprof@hssc-vetl-p ~]$ ls -l /tmp/HSSC_MonthlyTest_27800.txt 
-rw-rw-r--. 1 mpiprof mpiprof 14940373 Oct 25 22:59 /tmp/HSSC_MonthlyTest_27800.txt

```

