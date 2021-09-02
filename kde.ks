bootloader --location=mbr
network --bootproto=dhcp
url --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=fedora-$releasever&arch=$basearch
repo --name=updates --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=updates-released-f$releasever&arch=$basearch
# contains FEDORA-2021-085f0122dd for F35 to fix KDE background, remove
# when stable
repo --name=f35-kde-bg --baseurl=https://fedorapeople.org/groups/qa/openqa-repos/f35-kde-bg/$releasever

lang en_US.UTF-8
keyboard us
timezone --utc America/New_York
clearpart --all
autopart
rootpw --plaintext weakpassword
user --name=test --password=weakpassword --plaintext
poweroff

%packages
@^kde-desktop-environment
# these are all in the KDE live image, we want to match that as it's
# the most common KDE deployment method
@firefox
@kde-apps
@kde-media
@kde-office
@networkmanager-submodules
fedora-release-kde
falkon

imsettings-qt
-initial-setup
-initial-setup-gui
%end
