#!/bin/bash

#######################
## shell script to remove sensitive files before commit to github
## or add them back (locally) for testing. also added to gitignore
#######################

ddir_i="roles/pyenv/files/"
sdir_i="/home/venkat/Downloads"
input_file='HSSC_SampleFile.txt.gpg'

function usage() {
    echo "Usage:"
    echo "$0 [setup|teardown]"
}

function setup() {

  ## setup gpg-key
  ddir_w="roles/pyenv/files/gpghome"
  sdir_w="../gpghome"
  for item in `ls $sdir_w`; do
      cp -p $sdir_w/$item $ddir_w
  done

  ## setup input file
  ddir_w="roles/pyenv/files/"
  cp -p ../$input_file $ddir_w


  ## setup wallet  
  ddir_w="roles/pyenv/files/scsqc.wxt"
  sdir_w="../scsqc.wxt"

  rm -f $ddir_w/cwallet.sso $ddir_w/ewallet.p12
  cp $sdir_w/cwallet.sso $ddir_w
  cp $sdir_w/ewallet.p12 $ddir_w

}

function teardown() {
    
  ## remove gpg-key
  ddir_w="roles/pyenv/files/gpghome"
  sdir_w="../gpghome"
  for item in `ls $ddir_w`; do
      rm -f $ddir_w/$item && touch $ddir_w/$item
  done

  ## remove input file
  ddir_w="roles/pyenv/files/"
  rm -f $ddir_w/$input_file && touch $ddir_w/$input_file

  ## remove wallet  files
  ddir_w="roles/pyenv/files/scsqc.wxt"
  sdir_w="../scsqc.wxt"
  rm -f $ddir_w/cwallet.sso $ddir_w/ewallet.p12
  touch $ddir_w/cwallet.sso $ddir_w/ewallet.p12
  
}


[ $# -lt 1 ] && echo -ne "too few arguments\n" && usage && exit 0
[ $1 == "setup" ] && setup
[ $1 == "teardown" ] && teardown

