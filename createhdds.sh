#!/bin/bash
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

echo "Creating fedora21.img..."
# TODO: it should be possible to create updated image, but there is a bug, see https://bugzilla.redhat.com/show_bug.cgi?id=1084221
# so you are required to manually boot this image and run 'yum -y update'
#virt-builder fedora-21 -o fedora21.img --update --selinux-relabel --root-password password:weakpassword
virt-builder fedora-21 -o fedora21.img --root-password password:weakpassword

echo "Creating disk_ks.img..."
curl -o "/tmp/root-user-crypted-net.ks" "https://jskladan.fedorapeople.org/kickstarts/root-user-crypted-net.ks"
guestfish <<_EOF_
sparse disk_ks.img 100MB
run
part-init /dev/sda mbr
part-add /dev/sda p 4096 -1
mkfs ext4 /dev/sda1
mount /dev/sda1 /
upload /tmp/root-user-crypted-net.ks /root-user-crypted-net.ks
_EOF_
