install
bootloader --location=mbr
network --bootproto=dhcp
url --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=fedora-$releasever&arch=$basearch
repo --name=updates --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=updates-released-f$releasever&arch=$basearch
# Contains fix for https://gitlab.gnome.org/GNOME/gnome-initial-setup/-/issues/106
# Remove when updates for that fix are stable
repo --name gistest --baseurl=https://www.happyassassin.net/temp/gistest/$releasever/$basearch
lang en_US.UTF-8
keyboard us
timezone --utc America/New_York
clearpart --all
autopart --encrypted --passphrase=weakpassword
rootpw --plaintext weakpassword
user --name=test --password=weakpassword --plaintext
firstboot --enable
poweroff

%packages
@^workstation-product-environment
-selinux-policy-minimum
%end
