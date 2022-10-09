bootloader --location=mbr
network --bootproto=dhcp
url --url="https://download.rockylinux.org/stg/rocky/8.7-Beta/BaseOS/x86_64/os/"
lang en_US.UTF-8
keyboard us
timezone --utc America/New_York
clearpart --all
autopart
rootpw weakpassword
poweroff

%packages
@core
%end

%post
touch $INSTALL_ROOT/home/home_preserved
%end
