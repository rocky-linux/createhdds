bootloader --location=mbr
network --bootproto=dhcp
url --url="https://download.rockylinux.org/pub/rocky/$releasever/BaseOS/$basearch/os/"
# AppStream repo must be defined to provide @^workstation-product-environment group
repo --name=AppStream --baseurl=https://download.rockylinux.org/pub/rocky/$releasever/AppStream/$basearch/os/
lang en_US.UTF-8
keyboard us
timezone --utc America/New_York
clearpart --all
autopart --encrypted --passphrase=weakpassword
rootpw --plaintext weakpassword
user --name=test --password=weakpassword --plaintext --groups=wheel
firstboot --enable
poweroff
text

%packages
@^workstation-product-environment
-selinux-policy-minimum
%end

%addon com_redhat_kdump --enable --reserve-mb='auto'
%end
