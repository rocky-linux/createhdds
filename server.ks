bootloader --location=mbr
network --bootproto=dhcp
url --url="https://download.rockylinux.org/pub/rocky/$releasever/BaseOS/$basearch/os/"
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
