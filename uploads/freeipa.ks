cdrom
bootloader --location=mbr
network --device=link --activate --bootproto=static --ip=172.16.2.100 --netmask=255.255.255.0 --gateway=172.16.2.2 --hostname=ipa001.test.openqa.fedoraproject.org
lang en_US.UTF-8
keyboard us
timezone --utc America/New_York
clearpart --all
autopart
%packages
@^server-product-environment
@freeipa-server
# we need this to create the fake repo to make DNF happy for offline deployment
createrepo_c
%end
rootpw anaconda
reboot
