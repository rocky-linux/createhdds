bootloader --location=mbr
network --bootproto=dhcp
url --url="https://download.rockylinux.org/pub/rocky/8/BaseOS/x86_64/os/"
lang en_US.UTF-8
keyboard us
timezone --utc America/New_York
clearpart --all
autopart
rootpw weakpassword
user --name=test --password=weakpassword --plaintext
poweroff

%packages
@^server-product-environment
plymouth-system-theme
%end
