# mpi-bprof

## Summary
EMPI Business Object Profiler - A web services interface to Master Index Data Manager (MIDM)
## Documentation
https://hssc.github.io/mpi-bprof/

# Instructions to run

Login to hssc-vetl-p, sudo as root and attach the existing screen session (103857.pts-0.hssc-vetl-p) OR sudo as mpiprof

Activate the virtual environment to run the program
[mpiprof@hssc-vetl-p ~]$ source ~mpiprof/mpienv/bin/activate

For help with the application use:
[ mpi-bprof ] : [mpiprof@hssc-vetl-p ~]$ mpiws --help

Note: We received an encrypted enrollment file from MUSC (which will be the input file) and use `-t` option to throttle the API that hits the EMPI DB using the web services. Throttling is necessary to prevent swarming the DB.
```
[ mpi-bprof ] : [mpiprof@hssc-vetl-p ~]$ time mpiws -c /usr/local/etc/mpi-bprof/mpiprof.conf -i /data/hssclts/hssclts/mpiprof/HSSC_MonthlyTest_27799.txt.gpg -o /tmp/HSSC_MonthlyTest_27800.txt -t

--> Reading configuration file: /usr/local/etc/mpi-bprof/mpiprof.conf
Enter cipher key for decrypting "/data/hssclts/hssclts/mpiprof/HSSC_MonthlyTest_27799.txt.gpg":

real    776m39.895s
user    185m26.273s
sys     0m15.519s
```
