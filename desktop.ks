bootloader --location=mbr
network --bootproto=dhcp
url --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=fedora-$releasever&arch=$basearch
repo --name=updates --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=updates-released-f$releasever&arch=$basearch
lang en_US.UTF-8
keyboard us
timezone --utc America/New_York
clearpart --all
autopart
rootpw --plaintext weakpassword
user --name=test --password=weakpassword --plaintext
firstboot --enable
poweroff

%packages
@^workstation-product-environment
-selinux-policy-minimum
%end

%post
touch $INSTALL_ROOT/home/home_preserved
%end
