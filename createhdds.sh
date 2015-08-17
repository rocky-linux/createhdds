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

function disk_f22_minimal {
echo "Creating disk_f22_minimal.img..."
virt-builder fedora-22 -o disk_f22_minimal.img --update --selinux-relabel --root-password password:weakpassword > /dev/null
expect <<_EOF_
log_user 0
set timeout -1

spawn qemu-kvm -m 2G -nographic disk_f22_minimal.img

expect "localhost login:"
send "root\r"
expect "Password:"
send "weakpassword\r"
expect "~]#"
send "poweroff\r"
expect "reboot: Power down"
_EOF_
}

function disk_f22_desktop {
echo "Creating disk_f22_desktop.img..."
# these steps are required
# 1. remove firewalld - firewalld configuration in minimal and desktop are conflicting
# 2. update fedora
# 3. install @Fedora Workstation group
# 4. add new user on first boot
# 5. use expect to do selinux relabelling and to set password for user
virt-builder fedora-22 -o disk_f22_desktop.img --size 10G --run-command "yum -y remove firewalld*" --update --selinux-relabel --install "@^workstation-product-environment" --root-password password:weakpassword --firstboot-command 'useradd -m -p "" ejohn' > /dev/null
expect <<_EOF_
log_user 0
set timeout -1

spawn qemu-kvm -m 2G -nographic disk_f22_desktop.img

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

if [ "$#" -eq 0 ]; then
    disk_full
    disk_freespace
    disk_f22_minimal
    disk_f22_desktop
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
        minimal)
            disk_f22_minimal
            ;;
        desktop)
            disk_f22_desktop
            ;;
        ks)
            disk_ks
            ;;
        updates)
            disk_updates_img
            ;;
        *)
            echo "$0 [full|freespace|minimal|desktop|ks|updates]"
            ;;
    esac
fi
