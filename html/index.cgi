#!/usr/bin/perl

use strict;
use CGI;
use Fcntl;
use File::Find;
use Digest::MD5;
use SDBM_File;


# init
my $cfg = Config::Tiny->new->read("./config.ini");
my $pg     = $cfg->{common}->{com_diff};
my $res    = $cfg->{common}->{resfile};
our $dbpath = $cfg->{common}->{dbpath};

my @dirs;
foreach my $path (keys %{$cfg->{site}}){
  push @dirs, $cfg->{site}->{$path};
}

my %option = (
  make => 'make',
  show => 'show',
  diff => 'diff',
);


# Main
my $obj = new CGI;
print $obj->header(-charset=>'utf-8');

my $from  = $obj->param("from");
my $to    = $obj->param("to");
my $submit= escape($obj->param("submit"));
my @tmp   = localtime(time);
my $now   = sprintf("%04d%02d%02d", $tmp[5]+1900, $tmp[4]+1, $tmp[3]);

if($from){
  # 入力値チェック
  unless($from =~ /[0-9]+/ or $to =~ /[0-9]+/){
    print 'Invalid string.';
    exit;
  }
  if($from ge $to ){ print 'From and To are reversed.'; exit;}
  if($from ge $now){ print 'Future date.'; exit;}

  # 差分チェック済みファイルがあればそれを表示、
  # でなければ差分チェック実施してファイルに保存しつつ結果を表示
  # 時間がかかり、ブラウザのタイムアウトが懸念されるようになったら
  # forkして結果をajaxで確認にくるような仕組みに変更が必要
  unless(-f $res.$from.$to){
    my $ret = diff($from, $to);
    open(FH, ">".$res.$from.$to);
    print FH $ret;
    $ret =~ s/\n/<BR>\n/g;
    print $ret;
    close(FH);
  }
  else {
    open(FH, $res.$from.$to);
    my @list = <FH>;
    foreach my $line (@list){
      chomp($line);
      print $line,"<BR>\n";
    }
    close(FH);
  }
}
else{
# POST値が無い時はHTMLを出力
#-----------------------------------------------------------------------------
 print << 'EOF'
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/
DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <link rel="stylesheet" href="./css/common.css" type="text/css" media="screen"/>
  <link rel="stylesheet" href="./css/smoothness/jquery-ui-1.8.10.custom.css" type="text/css" media="screen"/>
  <script src="./js/jquery-1.4.4.min.js" type="text/javascript"></script>
  <script src="./js/jquery-ui-1.8.10.custom.min.js" type="text/javascript"></script>
  <script type="text/javascript">

  // getDiff
  function getresult() {
    $("#result").html('<img src="images/load.gif" alt="Now Loding..."/>');
    var f = $("#from_day").val();
    var t = $("#to_day").val();
    var s = $("#submit").val();
    var d = "from="+f+"&to="+t+"&submit="+s;
    $("#result").html($.ajax({
      url: "./index.cgi",
      async: false,
      data : d
    }).responseText)
  }

  $(function(){
    // Datepicker
    $(".date").datepicker({ dateFormat: "yymmdd"});

    // fix nav
    var nav    = $('#formarea');
    var offset = nav.offset();
    $(window).scroll(function () {
      if ($(window).scrollTop() > offset.top ) {
        nav.addClass('fixed');
      }
      else {
        nav.removeClass('fixed');
      }
    });
  });
  </script>

</head>

<body>
  <div id='formarea'>
    <form action='./index.cgi' method='get'>
      <input type='text' value="From" id='from_day' class='date'> ~
      <input type='text' value="To" id='to_day' class='date'>
      <input type='button' id='submit' class='submit' value='DIFF' onclick='getresult(this)'>
    [1...diff , 2...delete , 3...new]
    </form>
  </div>
  <div id='result'></div>
</body></html>
EOF
#-----------------------------------------------------------------------------
}


# DBへ渡す値のエスケープ処理
sub escape {
    my $self = shift;
    my $str = shift;
    return $str unless( defined($str) );
    $str =~ s/\\/\\\\\\\\/go;
    $str =~ s/'/''/go; #' make emacs happy
    $str =~ s/%/\\\\%/go;
#    $str =~ s/_/\\\\_/go;
    return $str;
}


# MD5ハッシュ計算してDBへ書き込み
sub make {
  my ($tmp) = shift;
  my $file = $File::Find::name;
  return if( -d $file);
  return if(! -e $file);
  #return if(! $tmp or $tmp eq '.' or $tmp eq '..');

  my %db_h;
  my $md5_res;

  return if(! open(FH, $file));
  binmode(FH);
  $md5_res = Digest::MD5->new->addfile(*FH)->hexdigest;
  close(FH);

  # DBのファイル名は /data/var/dbfile.YYYYMMDD
  my ($year, $month, $day) = (localtime(time))[5,4,3];
  my $date =   sprintf('%4d%02d%02d', $year+1900, $month+1, $day);
  tie(%db_h, 'SDBM_File', $dbpath.$date, O_RDWR|O_CREAT, 0660);
  $db_h{"$file"} = $md5_res;
  untie %db_h;
}


# 結果を表示する
sub show {
  my ($date) = shift;

  my $ref_db;
  my @keys;
  my $key;
  my $value;

  $ref_db = getHash($date);
  while(($key, $value) = each %$ref_db){
    print "$value,$key\n";
  }
}

# 差分を出力する
sub diff {
  my $date_old = shift;
  my $date_new = shift;

  my %dif;
  my $key;
  my $value;
  my @ret;

  my $ref_old = getHash($date_old);
  my $ref_new = getHash($date_new);

  # OLD日付の一覧取得し新しい方と値が異なる場合       = 1 (変更があったもの)
  # OLD日付の一覧取得し新しいに同じファイルが無い場合 = 2 (削除されたもの)
  while(($key, $value) = each %$ref_old){
    $dif{$key} = 1 if($value ne $ref_new->{$key} and $ref_new->{$key});
    $dif{$key} = 2 if(! $ref_new->{$key});
  }

  # NEW日付の一覧取得し古い方と値が異なる場合         = 1 (変更があったもの)
  # NEW日付の一覧取得し古い方に同じファイルが無い場合 = 3 (追加されたもの)
  while(($key, $value) = each %$ref_new){
    next if($dif{$key});
    $dif{$key} = 3 if(! $ref_old->{$key});
    #$dif{$key} = 1 if($value ne $ref_old->{$key} and $ref_old->{$key});
    #↑OLDのループで検知済みのはず
  }
  
  foreach $key (sort keys %dif){
    $ret[$dif{$key}] .= $dif{$key} .' - '.$key."\n";
  }
  close(FH);
  return $ret[1].$ret[2].$ret[3];
}

# DBからハッシュに読み込む
sub getHash {
  my $date = shift;
  my %db_h;

  # DBのファイル名は /data/var/dbfile.YYYYMMDD
  tie(%db_h, 'SDBM_File', $dbpath.$date, O_RDONLY, 0640);
  return \%db_h;
}

# 参考
## 改竄チェックプログラムの使い方
#print "usage: kaizanCheck.pl [make|show YYYYMMDD|diff YYYYMMDD YYYYMMDD]\n"
#     ," ex. ./kaizanCheck.pl make\n"
#     ," ex. ./kaizanCheck.pl show 20101010\n"
#     ," ex. ./kaizanCheck.pl diff 20101010 20101011\n"
#     ;


