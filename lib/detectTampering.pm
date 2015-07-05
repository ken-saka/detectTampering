package detectTampering;

use strict;
use Fcntl;
use File::Find;
use Digest::MD5;
use SDBM_File;
use Config::Tiny;
use Fatal;

our $VERSION = 'v0.01';

sub new {
  my $class = shift;
  bless {
    date	=> undef,
    oldDate	=> undef,
    newDate	=> undef,
    dirs        => undef,
    dbh         => undef,
    tieHash     => undef,
    dbBasename	=> './',
  }, $class;
}

sub DESTROY {
  my $self = shift;
}

sub setDbFileName {
  my $self = shift;
  my $filename = shift;
  $self->{dbBasename} = $filename;
  return 0;
}

sub getDbFileName {
  my $self = shift;
  return $self->{dbBasename};
}

sub setDirs {
  my $self    = shift;
  my $refDirs = shift;
  $self->{dirs} = $refDirs;
}

sub openDb {
  my $self = shift;
  my $dbFilename = shift;
  my $perm       = shift;
  my %option = (
    'ro' => O_RDWR|O_CREAT,
    'rw' => O_RDONLY,
  );
  my %dbh;
  eval {
    $self->{tieHash} = tie(%dbh, 'SDBM_File', $dbFilename, O_RDWR|O_CREAT, 0664) or die "Counld't tie SDBM file $dbFilename: $!;aborting";
  };
  if($@){
    print $@;
    exit 1;
  }
  return \%dbh;
}

sub closeDb {
  my $self = shift;
  untie $self->{dbh};
}

sub setDate {
  my $self = shift;
  my $date = shift;
  
  if(!$date){ 
    my ($year, $month, $day) = (localtime(time))[5,4,3];
    $self->{date} = sprintf('%4d%02d%02d', $year+1900, $month+1, $day);
  }
  else {
    $self->{date} = $date;
  }
}

sub getDate {
  my $self = shift;
  return $self->{date};
}

sub make {
  my $self = shift;

  my $store = sub {
    my $file = $File::Find::name;
    return if(! -f $file);
    open my $fh, "$file" or die "cant open $file";
    binmode($fh);
    my $resMd5 = Digest::MD5->new->addfile(*$fh)->hexdigest;
    close($fh);

    $self->{dbh}->{$file} = $resMd5;
  };

  {
    $self->setDate();
    $self->{dbh} = $self->openDb($self->{dbBasename}.'.'.$self->getDate(), 'rw');
    foreach my $dir (@{$self->{dirs}}) {
      File::Find::find($store, $dir);
    }
    #$self->closeDb();
  }
  return 0;
}

sub show {
  my $self = shift;
  my $date = shift;

  my @keys;
  my $key;
  my $value;

  $self->setDate($date);
  $self->{dbh} = $self->openDb($self->{dbBasename}.'.'.$self->getDate(), 'ro');
  
  while(($key, $value) = each %{$self->{dbh}}){
    print "$value,$key\n";
  }
  $self->closeDb();
  return 0;
}

sub diff {
  my $self = shift;
  my $dateOld = shift;
  my $dateNew = shift;

  my %dif;
  my $key;
  my $value;

  my $refDbOld = $self->openDb($self->{dbBasename}.'.'.$dateOld, 'ro');
  my $refDbNew = $self->openDb($self->{dbBasename}.'.'.$dateNew, 'ro');

  while(($key, $value) = each %{$refDbOld}){
    $dif{$key} = 1 if($value ne $refDbNew->{$key});
  }

  while( ($key, $value) = each %{$refDbNew}){
    $dif{$key} = 2 + $dif{$key} if($value ne $refDbOld->{$key});
  }

  foreach $key (keys %dif){
    print "$key\n";
  }
  return 0;
}
