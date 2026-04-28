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
user --name=test --password=weakpassword --plaintext --groups=wheel
poweroff
text

%packages
@^server-product-environment
plymouth-system-theme
%end

%addon com_redhat_kdump --enable --reserve-mb='auto'
%end
