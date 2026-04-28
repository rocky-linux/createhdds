bootloader --location=mbr
network --device=link --activate --bootproto=dhcp
url --url=https://download.rockylinux.org/pub/rocky/$releasever/BaseOS/$basearch/os/
repo --name=AppStream --baseurl=https://download.rockylinux.org/pub/rocky/$releasever/AppStream/$basearch/os/
repo --name=CRB --baseurl=https://download.rockylinux.org/pub/rocky/$releasever/CRB/$basearch/os/
lang en_US.UTF-8
keyboard us
timezone --utc America/New_York
clearpart --all
autopart

rootpw --iscrypted $6$ansiogjasd0io9u3$9E1vMbLbXW14grtguedFGVjvhyBz1T.KIA3MJl1SWnGbtTpiXIAjbazIQAUKRNkNIEmd3mI0NCkFIVBrN41fZ.
user --name=test --password=$6$ansioasgfgadsghd$O8O8zom5hx.V8ib1jV91xuvIgYqA2b99tzhibkk3URITdCrDtbRbwJjMK1kW4l0/9W0brraGC4NUBtDoGv4Kl. --iscrypted

reboot

%packages
@core
%end

%addon com_redhat_kdump --enable --reserve-mb='auto'
%end
