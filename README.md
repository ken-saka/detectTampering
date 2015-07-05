# detectTampering
to detect tampering of files.

 # search the directory and make a hash db.
 # create hash from files.
 # check their difference.

Require:
 * Perl
 * perl modules
   * Fcntl
   * File::Find
   * Digest::MD5
   * SDBM_File
   * Config::Tiny
   * CGI
 * environment to execute the cgi

## How to install

set up config.ini file

    [common]
    com_diff = /tooldir/bin/check.pl diff
    dbpath   = /tooldir/var/dbfile.
    resfile  = /tooldir/var/result_
    
    [site]
    path1 = /dir-for-your-site-1
    path2 = /dir-for-your-site-2


set web page

    # (cd html ;tar cpf - *) | (cd /your cgi dir/; tar xpf -)

change to index.html and index.cgi file


## How to use

  1. set a cron 
    0 0 * * * /your path/check.pl make

  2. check the hash file
    ls /dbpath/

  3. access to cgi


## Copyright

* Copyright (c) 2015- Ken'ichi SAKAGUCHI
* License
  * Apache License, Version 2.0 (see LICENSE)
