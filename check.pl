#!/usr/bin/perl -w

use strict;
use Fcntl;
use File::Find;
use Digest::MD5;
use SDBM_File;
use Config::Tiny;

use lib './lib';
use detectTampering;

my %option = (
  make => 'make',
  show => 'show',
  diff => 'diff',
);

my $myName = $0;
my $cfg = Config::Tiny->new->read("./config.ini");

my $c = detectTampering->new();
$c->setDbFileName($cfg->{common}->{dbpath});

# make: read files and make hashdb.
if($ARGV[0] eq 'make') {
  my @dirs;
  foreach my $path (keys %{$cfg->{site}}){
    push @dirs, $cfg->{site}->{$path}; 
  }
  $c->setDirs(\@dirs);
  $c->make($c->getDate);
  exit 0;
}

# show: hashdb dump.
if($ARGV[0] eq 'show') {
  if($ARGV[1] !~ /[0-9]{8}/){
    print "input format error. [$ARGV[1]]\n";
    exit 1;
  }
  $c->show($ARGV[1]);
  exit 0;
}

# difference old dbhash to new dbhash.
if($ARGV[0] eq 'diff') {
  if($ARGV[1] !~ /[0-9]{8}/ or $ARGV[2] !~ /[0-9]{8}/){
    print "Date format error. [$ARGV[1]],[$ARGV[2]]\n";
    exit 1;
  }
  $c->diff($ARGV[1], $ARGV[2]);
  exit 0;
}
  
print "usage: $myName [make|show YYYYMMDD|diff YYYYMMDD YYYYMMDD]\n"
     ," ex. ./$myName make\n"
     ," ex. ./$myName show 20101010\n"
     ," ex. ./$myName diff 20101010 20101011\n"
     ;
exit 0;
