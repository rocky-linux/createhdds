cdrom
bootloader --location=mbr
network --device=link --activate --bootproto=static --ip=172.16.2.101 --netmask=255.255.255.0 --gateway=172.16.2.2 --hostname=client001.test.openqa.fedoraproject.org --nameserver=172.16.2.100
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
realm join --one-time-password=monkeys ipa001.test.openqa.fedoraproject.org
