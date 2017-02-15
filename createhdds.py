#!/usr/bin/env python3

# Copyright (C) 2015 Red Hat
#
# createhdds is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Adam Williamson <awilliam@redhat.com>

"""Tool for creating hard disk images for Fedora openQA."""

import argparse
import logging
import json
import os
import subprocess
import sys
import tempfile
import time

import fedfind.helpers
import guestfs
import libvirt

from six.moves.urllib.request import urlopen

# this is a bit icky, but it means you can run the script from
# anywhere - we use this to locate hdds.json and the virtinstall
# image kickstarts, so they must always be in the same place
# as the script itself. images are checked/created in the working
# directory.
SCRIPTDIR = os.path.abspath(os.path.dirname(sys.argv[0]))
logger = logging.getLogger('createhdds')

def handle_size(size):
    """Simple function to handle sizes like '10G' or '100MB', returns
    the size in bytes as an int. Used by both image classes.
    """
    size = str(size)
    if size.endswith('G') or size.endswith('GB') or size.endswith('GiB'):
        return int(size.split('G')[0]) * 1024 * 1024 * 1024
    elif size.endswith('M') or size.endswith('MB') or size.endswith('MiB'):
        return int(size.split('M')[0]) * 1024 * 1024
    else:
        return int(size)

class GuestfsImage(object):
    """Class representing an image created by guestfs. 'size' is the
    desired image size, valid formats are a digit string (size in
    bytes, digit string plus 'M', 'MB' or 'MiB' (size in power of two
    megabytes), or digit string plus 'G', 'GB' or 'GiB' (size in power
    of two gigabytes). 'imgver' is the image 'version' - in practice
    it's simply a string that gets included in the image file name
    if specified. 'filesystem' is the default filesystem for the image
    - it will be used for parts that don't explicitly specify a
    filesystem. 'label' is the disk label format to be used. parts,
    writes, and uploads are lists of dicts that specify the partitions
    that should be created and files that should be written or copied
    ('uploaded') to them. These are read in from hdds.json by
    get_guestfs_images and passed here. 'name_extras' is an iterable
    of strings which should be appended to the image file name, with _
    separators (this provides a mechanism for get_guestfs_images to
    include the label and/or filesystem in the image name when
    creating images from a group with variants).
    """
    def __init__(self, name, size, imgver='', filesystem='ext4', label='mbr', parts=None,
                 writes=None, uploads=None, name_extras=None):
        self.name = name
        self.size = handle_size(size)
        # guestfs images are never outdated
        self.outdated = False
        self.filesystem = filesystem
        self.label = label
        self.parts = []
        self.writes = []
        self.uploads = []
        if parts:
            self.parts = parts
        if writes:
            self.writes = writes
        if uploads:
            self.uploads = uploads

        self.filename = "disk_{0}".format(name)
        if imgver:
            self.filename = "{0}_{1}".format(self.filename, imgver)
        if name_extras:
            for item in name_extras:
                self.filename = "{0}_{1}".format(self.filename, item)
        self.filename = "{0}.img".format(self.filename)

    def create(self, _):
        """Create the image. The unused arg is the 'textinst' arg that
        only VirtInstallImages care about (but which has to be passed
        here too).
        """
        gfs = guestfs.GuestFS(python_return_dict=True)
        try:
            # Create the disk image with a temporary name
            tmpfile = "{0}.tmp".format(self.filename)
            gfs.disk_create(tmpfile, "raw", int(self.size))
            # 'launch' guestfs with the disk attached
            gfs.add_drive_opts(tmpfile, format="raw", readonly=0)
            gfs.launch()
            # identify the disk and create a disk label
            disk = gfs.list_devices()[0]
            gfs.part_init(disk, self.label)
            # create and format the partitions
            for part in self.parts:
                # each partition can specify a filesystem, if it doesn't,
                # we use the image default
                if 'filesystem' not in part:
                    part['filesystem'] = self.filesystem
                # create the partition: the dict must specify type ('p'
                # for primary, 'l' for logical, 'e' for extended), and
                # start and end sector numbers - more details in
                # guestfs docs
                gfs.part_add(disk, part['type'], int(part['start']), int(part['end']))
                # identify the partition and format it
                partn = gfs.list_partitions()[-1]
                gfs.mkfs(part['filesystem'], partn, label=part.get('label'))
            # do file 'writes' (create a file with a given string as
            # its content)
            for write in self.writes:
                # the write dict must specify the partition to be
                # written to, numbered from 1 as humans usually do;
                # find that part and mount it
                partn = gfs.list_partitions()[int(write['part'])-1]
                gfs.mount(partn, "/")
                # do the write: the dict must specify the target path
                # and the string to be written ('content')
                gfs.write(write['path'], write['content'])
                gfs.sync()
                gfs.umount_opts("/")
            # do file 'uploads'. in guestfs-speak that means transfer
            # a file from the host to the image, we use it to mean
            # download a file from an http server and transfer that
            # to the image
            for upload in self.uploads:
                # as with write, the dict must specify a target
                # partition and location ('target')
                partn = gfs.list_partitions()[int(upload['part'])-1]
                gfs.mount(partn, "/")
                gfs.upload('/'.join((SCRIPTDIR, 'uploads', upload['source'])), upload['target'])
                gfs.sync()
                gfs.umount_opts("/")
            # we're all done! rename to the correct name
            os.rename(tmpfile, self.filename)
        except:
            # if anything went wrong, we want to wipe the temp file
            # then raise
            os.remove(tmpfile)
            raise
        finally:
            # whether things go right or wrong, we want to close the
            # gfs instance, and rwmj recommends 'shutdown()' too
            gfs.shutdown()
            gfs.close()


class VirtInstallImage(object):
    """Class representing an image created by virt-install. 'release'
    is the release the image will be built for. 'variant' is the
    variant whose install tree should be used. 'arch' is the arch.
    'size' is the desired image size, in gigabytes. 'imgver' is
    the image 'version' - in practice it's simply a string that gets
    included in the image file name if specified. 'maxage' is the
    maximum age of the image file (in days) - if the image is older
    than this, 'check' will report it as 'outdated' and 'all' will
    rebuild it.
    """
    def __init__(self, name, release, arch, size, variant=None, imgver='', maxage=14):
        self.name = name
        self.size = size
        self.filename = "disk_f{0}_{1}".format(str(release), name)
        if imgver:
            self.filename = "{0}_{1}".format(self.filename, imgver)
        self.filename = "{0}_{1}.img".format(self.filename, arch)
        self.release = release
        self.variant = variant
        self.arch = arch
        self.maxage = maxage
        if variant:
            self.variant = variant
        else:
            if str(release).isdigit() and int(release) < 24:
                self.variant = "Server"
            else:
                self.variant = "Everything"

    def create(self, textinst, retries=3):
        """Create the image."""
        # figure out the best os-variant. NOTE: libosinfo >= 0.3.1
        # properly returns 1 on failure, but using workaround for old
        # bug where it didn't in case EPEL doesn't have 0.3.1
        shortid = "fedora{0}".format(self.release)
        args = ["osinfo-query", "os", "short-id={0}".format(shortid)]
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        out = process.communicate()[0].decode()
        if shortid not in out:
            # this will just use the most recent fedora release number
            # virt-install / osinfo knows
            shortid = 'fedora-unknown'

        # destroy and delete the domain we use for all virt-installs
        conn = libvirt.open()
        try:
            dom = conn.lookupByName('createhdds')
            try:
                dom.destroy()
            except libvirt.libvirtError:
                # domain may not be running, so this is fine
                pass
            dom.undefine()
        except libvirt.libvirtError:
            # domain may not exist, so this is fine
            pass
        conn.close()

        tmpfile = "{0}.tmp".format(self.filename)
        try:
            # this is almost complex enough to need fedfind but not
            # quite, I think. also fedfind can't find the 'transient'
            # rawhide and branched locations at present
            if self.release == 'rawhide':
                loctmp = "https://dl.fedoraproject.org/pub/fedora/linux/development/rawhide/{1}/{2}/os"
            elif int(self.release) > fedfind.helpers.get_current_release(branched=False):
                # branched
                loctmp = "https://dl.fedoraproject.org/pub/fedora/linux/development/"
                loctmp += self.release[1:]
                loctmp += "/{1}/{2}/os"
            else:
                loctmp = "https://download.fedoraproject.org/pub/fedora/linux/releases/{0}/{1}/{2}/os"
            arch = self.arch
            if arch == 'i686':
                arch = 'i386'
            args = ["virt-install", "--disk", "size={0},path={1}".format(self.size, tmpfile),
                    "--os-variant", shortid, "-x",
                    "inst.ks=file:/{0}.ks".format(self.name), "--initrd-inject",
                    "{0}/{1}.ks".format(SCRIPTDIR, self.name), "--location",
                    loctmp.format(str(self.release), self.variant, arch), "--name", "createhdds",
                    "--memory", "2048", "--noreboot", "--wait", "-1"]
            if textinst:
                args.extend(("--graphics", "none", "--extra-args", "console=ttyS0"))
            else:
                args.extend(("--graphics", "vnc", "--noautoconsole"))
            # this is a hacky workaround for a weird bug on Fedora's prod
            # openQA server:
            # https://bugzilla.redhat.com/show_bug.cgi?id=1387798
            args.extend(("--network", "user"))
            # run the command, timing out after 1 hour; sometimes creation
            # seems to just get mysteriously stuck, we need to bail and
            # retry in this case
            try:
                logger.info("Install starting...")
                logger.debug("Command: %s", ' '.join(args))
                if not textinst:
                    logger.info("Connect via VNC to monitor")
                ret = subprocess.call(args, timeout=3600)
            except subprocess.TimeoutExpired:
                logger.warning("Image creation timed out!")
                if os.path.isfile(tmpfile):
                    os.remove(tmpfile)
                if retries:
                    logger.info("Retrying: %s retries remain after this", str(retries))
                    return self.create(retries=retries-1)
                else:
                    sys.exit("Image creation timed out too many times!")
            if ret > 0:
                # wipe the temp file
                if os.path.isfile(tmpfile):
                    os.remove(tmpfile)
                sys.exit("virt-install command {0} failed!".format(' '.join(args)))
            # at this point the domain should be shut off; if it's
            # anything else, something went wrong: clean up and exit
            conn = libvirt.open()
            dom = conn.lookupByName('createhdds')
            if dom.state()[0] != libvirt.VIR_DOMAIN_SHUTOFF:
                conn.close()
                if os.path.isfile(tmpfile):
                    os.remove(tmpfile)
                sys.exit("libvirt domain ('createhdds') is not shutdown! "
                         "this is an unexpected condition, aborting.")
            # we're all done! rename to the correct name and clean up
            # the domain
            os.rename(tmpfile, self.filename)
            os.chmod(self.filename, 0o644)
            dom.undefine()
            conn.close()
        except:
            # if anything went wrong, we want to wipe the temp file
            # then raise. we leave the domain intact in case we want
            # to debug it
            if os.path.isfile(tmpfile):
                os.remove(tmpfile)
            raise

    @property
    def outdated(self):
        """Whether the image is outdated - if self.maxage is set and
        it's older than that.
        """
        if not os.path.isfile(self.filename):
            return False

        if self.maxage:
            age = int(time.time()) - int(os.path.getmtime(self.filename))
            # maxage is in days
            if age > int(self.maxage) * 24 * 60 * 60:
                return True

        return False


def get_guestfs_images(imggrp, labels=None, filesystems=None):
    """Passed a single 'image group' dict (usually read out of hdds.
    json), returns a list of GuestfsImage instances. labels and
    filesystems act as overrides to the values specified in hdds.json
    and the defaults in this function; multiple images will be created
    for whatever combinations of labels and filesystems are specified.
    If they're not passed, then we use the values from the dict; if
    the dict doesn't specify, we just create a single image with the
    label set to 'mbr' and the filesystem to 'ext4'. The filesystem
    setting is itself a default - it's only used for 'part' entries
    which don't specify a filesystem (see the GuestfsImage docs).
    """
    imgs = []
    # Read in the various dict values
    name = imggrp['name']
    size = imggrp['size']
    parts = imggrp['parts']
    # These are optional
    writes = imggrp.get('writes')
    uploads = imggrp.get('uploads')
    imgver = imggrp.get('imgver')

    # Here we implement the 'labels / filesystems' behaviour explained
    # in the docstring
    if not labels:
        labels = imggrp.get('labels', ['mbr'])
    if not filesystems:
        filesystems = imggrp.get('filesystems', ['ext4'])

    # Now we've sorted out all our settings, instantiate the images
    for label in labels:
        for filesystem in filesystems:
            # We want to indicate filesystem/label in the filename
            # when we're creating images with more than one. We check
            # both the passed 'filesystems' value and the imggrp
            # value, so if the caller overrode the imggrp value we
            # still get the the long name (happens when using the
            # single-image CLI subcommand and restricting the label/
            # filesystem)
            name_extras = []
            if len(imggrp.get('filesystems', [])) > 1 or len(filesystems) > 1:
                name_extras.append(filesystem)
            if len(imggrp.get('labels', [])) > 1 or len(labels) > 1:
                name_extras.append(label)
            img = GuestfsImage(
                name, size, imgver, filesystem, label, parts, writes, uploads, name_extras)
            imgs.append(img)
    return imgs

def get_virtinstall_images(imggrp, nextrel=None, releases=None):
    """Passed a single 'image group' dict (usually read out of hdds.
    json), returns a list of VirtInstallImage instances. 'nextrel'
    indicates the 'next' release of Fedora: sometimes we determine the
    release to build image(s) for in relation to this, so we need to
    know it. If it's not specified, we ask fedfind to figure it out
    for us (this is the usual case, we just allow specifying it
    in case there's an issue with fedfind or you want to test image
    creation for the next-next release ahead of time or something).
    The image group dict must include a dict named 'releases' which
    indicates what releases to build images for and what arches to
    build for each release; 'releases' can be used to override that. If
    set, the image group 'releases' dict is ignored, and this dict is
    used instead. The dict's keys must be release numbers or negative
    integers: -1 means 'one release lower than the "next" release',
    -2 means 'two releases lower than the "next" release', and so on.
    The values are the arches to build for that release.
    """
    imgs = []
    # Set this here so if we need to calculate it, we only do it once
    if not nextrel:
        nextrel = 0
    name = imggrp['name']
    # this is the second place we set a default for maxage - bit ugly
    maxage = int(imggrp.get('maxage', 14))
    # ditto variant
    variant = imggrp.get('variant')
    if not releases:
        releases = imggrp['releases']
    size = imggrp.get('size', 0)
    imgver = imggrp.get('imgver')
    # add an image for each release/arch combination
    for (release, arches) in releases.items():
        if release.lower() == 'branched':
            # find Branched, if it exists
            curr = fedfind.helpers.get_current_release(branched=False)
            branch = fedfind.helpers.get_current_release(branched=True)
            if branch > curr:
                release = branch
            else:
                logger.info("Branched image requested, but Branched does not currently exist")
                continue
        elif release != 'rawhide' and int(release) < 0:
            # negative release indicates 'relative to next release'
            if not nextrel:
                nextrel = fedfind.helpers.get_current_release() + 1
            release = int(nextrel) + int(release)
        for arch in arches:
            imgs.append(
                VirtInstallImage(name, release, arch, variant=variant, size=size, imgver=imgver,
                                 maxage=maxage))
    return imgs

def get_all_images(hdds, nextrel=None):
    """Simply iterates over the 'image group' dicts in hdds.json and
    calls the appropriate get_foo_images() function for each, then
    returns the list of all images. No overrides for labels,
    filesystems, releases or arches are provided here, this function
    is just for painting inside the lines - it's used to determine
    what images are 'expected' to exist according to hdds.json. We
    do allow passing of 'nextrel' just in case there's some issue
    with the auto-discovery.
    """
    imgs = []
    for imggrp in hdds['guestfs']:
        imgs.extend(get_guestfs_images(imggrp))

    for imggrp in hdds['virtinstall']:
        imgs.extend(get_virtinstall_images(imggrp, nextrel=nextrel))
    return imgs

def do_renames(hdds):
    """Rename files according to the 'renames' list in hdds.json,
    which is just a list of 'old name, new name' pairs. Say there's
    an image we used to only create an mbr version of, but now we add
    a gpt version; that means the expected name of the mbr version
    changes. This function allows us to specify in hdds.json that the
    mbr image should be renamed, which saves having to rebuild it.
    'all' always does renames, 'check' can be told to do renames.
    """
    for (orig, new) in hdds['renames']:
        if os.path.isfile(orig) and not os.path.exists(new):
            logger.info("Renaming %s to %s...", orig, new)
            os.rename(orig, new)

def delete_all():
    """Remove absolutely all createhdds-controlled files; we assume
    anything in the working directory starting with 'disk' and ending
    with 'img' is one of our files.
    """
    files = [fl for fl in os.listdir('.') if fl.startswith('disk') and fl.endswith('img')]
    for _file in files:
        os.remove(_file)

def clean(unknown):
    """This simply removes all the files in the list. The list is
    expected to be the list of 'unknown' files returned by check();
    both 'all' and 'clean' can delete 'unknown' files if requested.
    'unknown' files are usually images for old releases we're no
    longer testing, images we've simply stopped using, or old image
    files when the image group name has been changed to indicate an
    incompatible change to the image(s).
    """
    for filename in unknown:
        try:
            logger.info("Removing unknown image %s", filename)
            os.remove(filename)
        except OSError:
            # We don't really care if the file didn't exist for some
            # reason, so just pass.
            pass

def check(hdds, nextrel=None):
    """This calls get_all_images() to find out what images are expected
    to exist, then compares that to the images that are actually
    present and returns three lists. The first two are lists of Image
    subclass instances, the last is a list of filenames. The first is a
    list of the images that just aren't there at all. The second is a
    list of images that are present but 'outdated', because they've
    exceeded their maxage. The last is a list of image files that are
    present but don't match any of the expected images - 'unknown'
    images. The 'clean()' function can be used to remove these.
    'nextrel' is passed through to get_all_images(), and is available
    in case auto-detection via fedfind fails.
    """
    current = []
    missing = []
    outdated = []
    unknown = []
    # Get the list of all 'expected' images
    expected = get_all_images(hdds, nextrel=nextrel)
    # Get the list of all present image files
    files = set(fl for fl in os.listdir('.') if fl.startswith('disk') and fl.endswith('img'))
    # Compare present images vs. expected images to produce 'unknown'
    expnames = set(img.filename for img in expected)
    unknown = list(files.difference(expnames))

    # Now determine if images are absent or outdated
    for img in expected:
        if not os.path.isfile(img.filename):
            missing.append(img)
            continue
        if img.outdated:
            outdated.append(img)
            continue
        current.append(img)

    logger.debug("Current images: %s", ', '.join([img.filename for img in current]))
    logger.debug("Missing images: %s", ', '.join([img.filename for img in missing]))
    logger.debug("Outdated images: %s", ', '.join([img.filename for img in outdated]))
    logger.debug("Unknown images: %s", ', '.join(unknown))
    return (missing, outdated, unknown)

def cli_all(args, hdds):
    """Function for the CLI 'all' subcommand. Creates all images. If
    args.delete is set, blows all existing images away and recreates
    them; otherwise it will just fill in missing or outdated images.
    If args.clean is set, also wipes 'unknown' images.
    """
    if args.delete:
        logger.info("Removing all images...")
        delete_all()

    # handle renamed images (see do_renames docstring)
    do_renames(hdds)

    # call check() to find out what we need to do
    (missing, outdated, unknown) = check(hdds, nextrel=args.nextrel)

    # wipe 'unknown' images if requested
    if args.clean:
        clean(unknown)

    # 'missing' plus 'outdated' is all the images we need to build; if
    # args.delete was set, all images will be in this list
    missing.extend(outdated)
    for (num, img) in enumerate(missing, 1):
        logger.info("Creating image %s...[%s/%s]", img.filename, str(num), str(len(missing)))
        img.create(args.textinst)

def cli_check(args, hdds):
    """Function for the CLI 'check' subcommand. Basically just calls
    check() and prints the results. Does renames before checking if
    args.rename was set, and wipes 'unknown' images after checking if
    args.clean was set. Exits with status 2 if any images are missing,
    1 if all images are present but one or more is outdated.
    """
    if args.rename:
        do_renames(hdds)

    (missing, outdated, unknown) = check(hdds, nextrel=args.nextrel)
    if missing:
        print("Missing images: {0}".format(', '.join([img.filename for img in missing])))
    if outdated:
        print("Outdated images: {0}".format(', '.join([img.filename for img in outdated])))
    if unknown:
        print("Unknown images: {0}".format(', '.join(unknown)))
        if args.clean:
            clean(unknown)

    if missing:
        sys.exit(2)
    elif outdated:
        sys.exit(1)
    else:
        sys.exit()

def cli_image(args, *_):
    """Function for CLI image group subcommands (a subcommand is added
    for each image group in hdds.json). Will create the image(s) from
    the specified group. For guestfs image groups with multiple labels
    and/or filesystems, the user can pass args.label and/or args.
    filesystem to limit creation to a single label and/or filesystem.
    Note this function does no checking; the image will always be
    recreated, even if it already exists and is current.
    """
    # Note that on this path, the parsing of hdds is done by
    # parse_args(). It passes us the image type and the image group
    # dict from hdds as a tuple; we need to know the type so we know
    # what fiddling to do with the args and what function to call
    imggrp = args.imggrp[1]
    imgtype = args.imggrp[0]

    if imgtype == 'guestfs':
        # If the user passed in label or filesystem, we pass them on
        # to get_guestfs_images as single-item lists, otherwise we
        # just pass 'None', causing it to use the values from imggrp
        # (which come from hdds.json)
        labels = None
        filesystems = None
        if args.label:
            labels = [args.label]
        if args.filesystem:
            filesystems = [args.filesystem]
        imgs = get_guestfs_images(imggrp, labels=labels, filesystems=filesystems)

    elif imgtype == 'virtinstall':
        # If the user passed args.release, we construct a releases
        # dict to pass to get_virtinstall_images to override the dict
        # from imggrp. If they passed args.arch, we use that arch,
        # otherwise we default to x86_64. If args.release isn't set,
        # we just pass None as release, and the releases dict from
        # imggrp will be used, and images created for all release/
        # arch combinations listed there. FIXME: if the user passes
        # args.arch but not args.release, we just ignore it...
        releases = None
        if args.release:
            if args.arch:
                arches = [args.arch]
            else:
                arches = ['x86_64']
            releases = {args.release: arches}
        imgs = get_virtinstall_images(imggrp, releases=releases)

    for (num, img) in enumerate(imgs, 1):
        logger.info("Creating image %s...[%s/%s]", img.filename, str(num), str(len(imgs)))
        img.create(args.textinst)

def parse_args(hdds):
    """Parse arguments with argparse."""
    parser = argparse.ArgumentParser(description=(
        "Tool for creating hard disk images for Fedora openQA."))
    parser.add_argument(
        '-l', '--loglevel', help="The level of log messages to show",
        choices=('debug', 'info', 'warning', 'error', 'critical'),
        default='info')
    parser.add_argument(
        '-t', '--textinst', help="For any virt-install images, run the install in text mode "
        "and show details on stdout", action='store_true')

    # This is a workaround for a somewhat infamous argparse bug
    # in Python 3. See:
    # https://stackoverflow.com/questions/23349349/argparse-with-required-subparser
    # http://bugs.python.org/issue16308
    subparsers = parser.add_subparsers(dest='subcommand')
    subparsers.required = True

    parser_all = subparsers.add_parser(
        'all', description="Ensure all images are present and up-to-date.")
    parser_all.add_argument(
        '-d', '--delete', help="Delete and re-build all images",
        action='store_true')
    parser_all.add_argument(
        '-c', '--clean', help="Remove unknown (usually old) images",
        action='store_true')
    parser_all.add_argument(
        '-n', '--nextrel', help="The release to treat as the 'next' release "
        "- this determines what releases some images will be built for. If "
        "not set or set to 0, createhdds will try to discover it when needed",
        type=int, default=0)
    parser_all.set_defaults(func=cli_all)

    parser_check = subparsers.add_parser(
        'check', description="Check status of existing image files.")
    parser_check.add_argument(
        '-n', '--nextrel', help="The release to treat as the 'next' release "
        "- this determines what releases some images are expected to exist for. If "
        "not set or set to 0, createhdds will try to discover it when needed",
        type=int, default=0)
    parser_check.add_argument(
        '-r', '--rename', help="Whether to rename images when the expected name "
        "has changed or not", action="store_true")
    parser_check.add_argument(
        '-c', '--clean', help="Remove unknown (usually old) images",
        action='store_true')
    parser_check.set_defaults(func=cli_check)

    # This here is somewhat clever-clever: we generate a subcommand for
    # each image group listed in hdds.json, which can be used to build
    # image(s) from that group. For guestfs image groups, we also check
    # if the group has multiple labels and/or filesystems by default,
    # and add arguments to limit image creation to just a single label
    # and/or filesystem.
    for imggrp in hdds['guestfs']:
        imgparser = subparsers.add_parser(
            imggrp['name'], description="Create {0} image(s)".format(imggrp['name']))
        labels = imggrp.get('labels', [])
        if len(labels) > 1:
            imgparser.add_argument(
                '-l', '--label', help="Create only images with this disk label",
                choices=labels)
        filesystems = imggrp.get('filesystems', [])
        if len(filesystems) > 1:
            imgparser.add_argument(
                '-f', '--filesystem', help="Create only images with this filesystem",
                choices=filesystems)
        imgparser.set_defaults(func=cli_image, label=None, filesystem=None)
        # Here we're stuffing the type of the image and the dict from
        # hdds into args for cli_image() to use.
        imgparser.set_defaults(imggrp=('guestfs', imggrp))

    # For virtinstall images, we provide args to override the release/
    # arch combination; using args.release will always result in just a
    # single image being built, for x86_64 unless args.arch is set to
    # i686.
    for imggrp in hdds['virtinstall']:
        imgparser = subparsers.add_parser(
            imggrp['name'], description="Create {0} image(s)".format(imggrp['name']))
        imgparser.add_argument(
            '-r', '--release', help="The release to build the image(s) for. If not "
            "set, createhdds will attempt to determine the current release and build "
            "for appropriate releases relative to that",
            default='')
        imgparser.add_argument(
            '-a', '--arch', help="The arch to build the image(s) for. If neither "
            "this nor --release is set, createhdds will decide the appropriate "
            "arch(es) to build for each release. If this is not set but --release "
            "is set, only x86_64 image(s) will be built.",
            choices=('x86_64', 'i686'))
        imgparser.set_defaults(func=cli_image)
        # Here we're stuffing the type of the image and the dict from
        # hdds into args for cli_image() to use.
        imgparser.set_defaults(imggrp=('virtinstall', imggrp))
    return parser.parse_args()

def main():
    """Main loop - set up logging, parse args, run subcommand
    function.
    """
    try:
        with open('{0}/hdds.json'.format(SCRIPTDIR), 'r') as fout:
            hdds = json.load(fout)
        args = parse_args(hdds)
        loglevel = getattr(
            logging, args.loglevel.upper(), logging.INFO)
        logging.basicConfig(level=loglevel)
        args.func(args, hdds)
    except KeyboardInterrupt:
        sys.stderr.write("Interrupted, exiting...\n")
        # there may be temp image files lying around...
        tmps = [fl for fl in os.listdir('.') if fl.startswith('disk') and fl.endswith('.tmp')]
        for tmp in tmps:
            os.remove(tmp)
        sys.exit(1)

if __name__ == '__main__':
    main()
