install
cdrom
bootloader --location=mbr
network --device=link --activate --bootproto=static --ip=10.0.2.101 --netmask=255.255.255.0 --gateway=10.0.2.2 --hostname=client001.domain.local --nameserver=10.0.2.100
lang en_US.UTF-8
keyboard us
timezone --utc America/New_York
clearpart --all
autopart
%packages
@^server-product-environment
%end
rootpw anaconda
reboot
realm join --one-time-password=monkeys ipa001.domain.local
