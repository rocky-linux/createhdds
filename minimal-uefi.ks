install
bootloader --location=mbr
network --bootproto=dhcp
url --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=fedora-$releasever&arch=$basearch
repo --name=updates --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=updates-released-f$releasever&arch=$basearch
lang en_US.UTF-8
keyboard us
timezone --utc America/New_York
clearpart --all
part /boot/efi --fstype=efi --grow --maxsize=200 --size=20
part /boot --fstype=ext4 --size=1024
part / --fstype=ext4 --size=17000
part swap --size=2000
rootpw weakpassword
poweroff

%packages
@core
%end
