#!/bin/bash

function disk_full {
echo "Creating disk_full.img..."
guestfish <<_EOF_
sparse disk_full.img 10G
run
part-init /dev/sda mbr
part-add /dev/sda p 1 10485760
part-add /dev/sda p 10485761 -1
mkfs ext4 /dev/sda1
mkfs ext4 /dev/sda2
mount /dev/sda1 /
write /testfile "Hello, world!"
umount /
mount /dev/sda2 /
write /testfile "Oh, hi Mark"
umount /
_EOF_
}

function disk_freespace {
echo "Creating disk_freespace.img..."
guestfish <<_EOF_
sparse disk_freespace.img 10G
run
part-init /dev/sda mbr
part-add /dev/sda p 4096 2097152
mkfs ext4 /dev/sda1
mount /dev/sda1 /
write /testfile "Hello, world!"
_EOF_
}

function disk_minimal {
version=$1
arch=$2
echo "Creating disk_f${version}_minimal_${arch}.img..."
virt-builder fedora-${version} -o disk_f${version}_minimal_${arch}.img --arch ${arch} --run-command \
  "setarch ${arch} dnf -y update" --selinux-relabel --root-password password:weakpassword > /dev/null
expect <<_EOF_
log_user 0
set timeout -1

spawn qemu-kvm -m 2G -nographic disk_f${version}_minimal_${arch}.img

expect "localhost login:"
send "root\r"
expect "Password:"
send "weakpassword\r"
expect "~]#"
send "poweroff\r"
expect "reboot: Power down"
_EOF_
}

function disk_desktop {
version=$1
arch=$2
echo "Creating disk_f${version}_desktop_${arch}.img..."
# these steps are required
# 1. remove firewalld - firewalld configuration in minimal and desktop are conflicting
# 2. update fedora
# 3. install @Fedora Workstation group
# 4. add new user on first boot
# 5. use expect to do selinux relabelling and to set password for user
virt-builder fedora-${version} -o disk_f${version}_desktop_${arch}.img --size 20G --arch ${arch} --run-command \
  "setarch ${arch} dnf -y remove firewalld* && setarch ${arch} dnf -y update && setarch ${arch} dnf -y install @'Fedora Workstation'" \
  --selinux-relabel --root-password password:weakpassword --firstboot-command 'useradd -m -p "" ejohn' > /dev/null
expect <<_EOF_
log_user 0
set timeout -1

spawn qemu-kvm -m 2G -nographic disk_f${version}_desktop_${arch}.img

expect "localhost login:"
send "root\r"
expect "Password:"
send "weakpassword\r"
expect "~]#"
send "systemctl set-default graphical.target\r"
send "echo 'ejohn:weakpassword' | chpasswd\r"
send "poweroff\r"
expect "reboot: Power down"
_EOF_
}

function disk_ks {
echo "Creating disk_ks.img..."
curl --silent -o "/tmp/root-user-crypted-net.ks" "https://jskladan.fedorapeople.org/kickstarts/root-user-crypted-net.ks" > /dev/null
guestfish <<_EOF_
sparse disk_ks.img 100MB
run
part-init /dev/sda mbr
part-add /dev/sda p 4096 -1
mkfs ext4 /dev/sda1
mount /dev/sda1 /
upload /tmp/root-user-crypted-net.ks /root-user-crypted-net.ks
_EOF_
}

function disk_updates_img {
echo "Creating disk_updates_img.img..."
curl --silent -o "/tmp/updates.img" "https://fedorapeople.org/groups/qa/updates/updates-unipony.img" > /dev/null
guestfish <<_EOF_
sparse disk_updates_img.img 100MB
run
part-init /dev/sda mbr
part-add /dev/sda p 4096 -1
mkfs ext4 /dev/sda1 label:UPDATES_IMG
mount /dev/sda1 /
upload /tmp/updates.img /updates.img
_EOF_
}

if [[ "$1" != "" ]]; then
    VERSION="$1"
    shift
    if [[ "$#" -eq 0 ]]; then
        disk_full
        disk_freespace
        disk_minimal ${VERSION} "x86_64"
        disk_minimal ${VERSION} "i686"
        disk_desktop ${VERSION} "x86_64"
        disk_desktop ${VERSION} "i686"
        disk_ks
        disk_updates_img
    else
        case $1 in
            full)
                disk_full
                ;;
            freespace)
                disk_freespace
                ;;
            minimal_64bit)
                disk_minimal ${VERSION} "x86_64"
                ;;
            minimal_32bit)
                disk_minimal ${VERSION} "i686"
                ;;
            desktop_64bit)
                disk_desktop ${VERSION} "x86_64"
                ;;
            desktop_32bit)
                disk_desktop ${VERSION} "i686"
                ;;
            ks)
                disk_ks
                ;;
            updates)
                disk_updates_img
                ;;
            *)
                echo "name not in [full|freespace|minimal_64bit|minimal_32bit|desktop_64bit|desktop_32bit|ks|updates]"
                exit 1
                ;;
        esac
    fi
else
    echo "USAGE: $0 VERSION [full|freespace|minimal_64bit|minimal_32bit|desktop_64bit|desktop_32bit|ks|updates]"
    exit 1
fi
