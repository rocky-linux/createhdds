bootloader --location=mbr
network --bootproto=dhcp
url --url=https://download.rockylinux.org/pub/rocky/$releasever/BaseOS/$basearch/os/
# AppStream repo must be defined to provide dns-masq and targetcli package access
repo --name=AppStream --baseurl=https://download.rockylinux.org/pub/rocky/$releasever/AppStream/$basearch/os/
repo --name=CRB --baseurl=https://download.rockylinux.org/pub/rocky/$releasever/CRB/$basearch/os/
lang en_US.UTF-8
keyboard us
timezone --utc America/New_York
clearpart --all
autopart
rootpw weakpassword
poweroff
text

%packages
@core
%end

%addon com_redhat_kdump --enable --reserve-mb='auto'
%end

%post
touch $INSTALL_ROOT/home/home_preserved
%end
