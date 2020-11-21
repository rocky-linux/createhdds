install
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

# FIXME: fedora-jam-kde-theme-2.0.0-1.fc31 provides kde-settings,
# and anaconda prefers it to the real kde-settings for some reason,
# so F31 images are getting fedora-jam-kde-theme instead of
# kde-settings and this means they have the wrong background and
# some other issues. This should be fixed by 3.0.0-1.fc31, so we
# can probably remove this when
# https://bodhi.fedoraproject.org/updates/FEDORA-2020-3753ee3716
# is pushed stable
-fedora-jam-kde-theme

imsettings-qt
-initial-setup
-initial-setup-gui
%end
