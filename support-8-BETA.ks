bootloader --location=mbr
network --bootproto=dhcp
url --url="https://download.rockylinux.org/stg/rocky/8-BETA/BaseOS/x86_64/os/"
#repo --name="epel" --baseurl="http://mirrors.kernel.org/fedora-epel/8/Everything/x86_64/"
# use epel to keep scsi-target-utils instead of targetcli
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
targetcli
nfs-utils
dnsmasq
%end

%post
/usr/bin/sed -i 's/^mirrorlist/#mirrorlist/g' /etc/yum.repos.d/Rocky-*.repo
/usr/bin/sed -i 's,^#\(baseurl=http[s]*://\),\1,g' /etc/yum.repos.d/Rocky-*.repo
/usr/bin/echo "stg/rocky" > /etc/dnf/vars/contentdir
%end
