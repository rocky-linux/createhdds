bootloader --location=mbr
network --bootproto=dhcp
url --url="https://download.rockylinux.org/pub/rocky/9/BaseOS/x86_64/os/"
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
