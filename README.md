# createhdds.py

createhdds.py creates and maintains the set of pre-rolled hard disk images needed for some of the Fedora openQA tests.

## Usage

Most usage information can be seen in the help text - just run `createhdds.py -h` for an overview of the subcommands available, and `createhdds.py (subcommand) -h` for help on a subcommand. To put it simply, the most common usage is simply to run `createhdds.py all -c`. This will create all the currently-expected images that have not already been created, and recreate any that need recreating (images can have a 'maximum age' causing them to be rebuilt by `all` when they're older than that age, and images also have a 'version' - if the image's 'version' is bumped by the maintainers, `all` will rebuild it). It will also remove any image files that are present that aren't expected to be present - usually images for old releases that are no longer tested, or images we've simply stopped using. In a typical deployment of a Fedora openQA instance, the admin should set things up so the `openqa_fedora_tools` git checkout is updated and `createhdds.py all -c` is run regularly - say, once a day (and probably not while tests are being run).

`createhdds.py check` will just check whether all expected images are present and up-to-date; if they are, it will exit 0, if they are not, it will exit 1 and print a message. This can be handy for use with things like Ansible (so you can run the check to decide whether you need to run the creation, and thus avoid spurious 'changed' statuses).

There are also individual subcommands for each of the named 'image groups', allowing you to create just the image(s) from that group. For image groups which usually generate multiple images, the subcommand will have arguments that let you restrict creation to just a subset of those images (and for virt-builder type images, you can create the image(s) for a different release than would usually be the case, too).

In `all` mode, and in single-image mode if you do not pass `--release`, createhdds can decide what releases to build images for, for those image groups that include an installed Fedora release (the virt-builder type images). A virt-builder type image group can specify the releases to build images for absolutely (by giving the release numbers as positive integers), or relative to the next pending release (by giving the release numbers as negative integers). When it encounters one of these 'relative' release numbers, `createhdds` uses [fedfind](https://www.happyassassin.net/fedfind) to discover the 'current' release, and adds 1 to that (to find the 'pending' release). Just in case anything goes wrong with this, or you need to override it for some reason, the `--nextrel` argument is available for relevant subcommands to explicitly specify the 'next release'.

## Specifying images / 'image groups': `hdds.json` and `.commands` files

All the information on what images can/should be created comes from the `hdds.json` file and some `virt-builder` commands files. You can add, modify and remove image definitions without touching `createhdds.py`. `hdds.json` should define a single dictionary with three keys: `guestfs`, `virtbuilder`, and `renames`. The meat is `guestfs` and `virtbuilder`, which define 'image groups': for each image group, `createhdds all` will create one or more images (multiple images produced from a single group are referred to as 'variants'). Groups and variants are provided for so that if you want to create, say, three images that are identical but for their disk label, you don't have to create a whole new almost-identical entry for each one. The rules about what particular attributes of an image can be implemented as 'variants' are somewhat arbitrary and actually just taken from the old `createhdds.sh`; each function in that implementation became an 'image group' in this rewrite, and the attributes that can vary between variants are the same ones that could be set as function arguments in `createhdds.sh`. The `.commands` files allow for customization of `virt-builder` images; more on this later. `hdds.json` and any `.commands` files must always be in the same folder as `createhdds.py` (not necessarily the same folder the disk images reside in).

### renames

The value of `renames` is a simple list-of-lists. Each item is a pair of strings. In `all` mode, and optionally in `check` mode, createhdds will read in all the items from the `renames` list. For each item it will look for a file (in the working directory - createhdds always works on the working directory) named the same as the first string, and if it finds such a file, change its name to the second string. So for instance, the value of `renames` could be `[['disk_foo.img', 'disk_bar.img'], ['disk_monkey.img', 'disk_fish.img']]`; that would result in createhdds renaming `disk_foo.img` to `disk_bar.img` and `disk_monkey.img` to `disk_fish.img`. This mechanism is provided to aid in the situation where an image's expected name changes, but the existing image file is still valid; instead of forcing the user to rename it manually or re-generate it, we can list it in `renames` and it will get renamed automatically. Of course, if the image's content changes too, we shouldn't use this mechanism.

### guestfs and virtbuilder

The value for both `guestfs` and `virtbuilder` is a list of dicts. Each dict defines a single 'image group'; an image group can produce just a single image, or several variants - we will learn what determines the possible variants for an image group below. The images in `guestfs` are produced using libguestfs - these are images that just contain a particular partition layout and perhaps some files we seed directly, but no installed operating system. The images in `virtbuilder` are produced using `virt-builder` - these are images containing an installed operating system. Some keys are common to both image group types:

#### `imgver`

This is the 'image version'. It is **optional** for both image types. By convention, it should be an integer digit string, but its practical effect is simply to be included in the image filename(s), so it *can* be any string valid in a filename. If omitted or set to the empty string, no imgver component will be included in the filename. This means that by changing the version you can change the expected name - which will cause the `check` mode to report the old file as 'unknown' and the new file as 'missing', and will cause the `all` mode to build the new file. Thus if you're maintaining the image set, and you make some change to an image group which would mean that existing image files for that group can no longer be used, you can change `imgver` to cause the images to be rebuilt.

#### `name`

The image group's name (a string). **Required** for both image types. This is included in the image file names, of course, and it will also be the subcommand to create image(s) from this group.

#### `size`

This key is **required** for `guestfs`, **optional** for `virtbuilder`. It is the size of the image. A plain digit string is a size in bytes. A digit string followed by 'M', 'MB' or 'MiB' is a size in megabytes (power-of-2). A digit string followed by 'G', 'GB' or 'GiB' is a size in gigabytes (power-of-2). For `virtbuilder`, if `size` is not set, the image will be whatever size the `virt-builder` base image it's created from is.

Some keys are specific to each type of image. These are the `guestfs`-specific keys:

#### `parts`

This key is **required**. This key's value is a list of dicts. Each dict represents a single partition that should be created on the disk. Required keys are:

* `type` - the partition type: 'p' for primary, 'l' for logical, 'e' for extended
* `start` - start sector
* `end` - end sector

These values are just passed straight to libguestfs, so you can find further info on them in the libguestfs documentation, especially on various special values for `start` and `end` (negative values are relative to the end of the disk, for e.g.)

Optional keys are:

* `filesystem` - if set, this partition will *always* have this filesystem. If not set, the filesystem will be determined according to the image group's `filesystems` value (see below).
* `label` - if set, this partition will have this label

#### `writes`

This key is **optional**. Its value is a list of dicts. Each dict represents a single file that should be created on one of the partitions in the image. There are exactly three required keys for the dict:

* `part` - the number of the partition the file should be written to, starting at 1
* `path` - the path where the file should be written (root is the root of the partition it's being written to)
* `content` - the actual content to write to the file (a string)

#### `uploads`

This key is **optional**. Its value is a list of dicts. Each dict represents a single file that should be retrieved from a web site and copied to a partition in the image. There are exactly three required keys for the dict:

* `part` - the number of the partition the file should be written to, starting at 1
* `target` - the path where the file should be written (root is the root of the partition it's being written to)
* `source` - the URL of the file to download

There's currently no provision for uploading a *local* file, or any protocol besides http/https (you can use either).

#### `labels` and `filesystems`

These keys are **optional**. Each one's value is a list of strings. These keys together determine how many image variants are expected to be produced from the image group. If not set, the default value of `labels` is ['mbr'], and the default value of `filesystems` is ['ext4'] (both single-item lists). For each `guestfs` image group, the expected images will be the combinations of `labels` and `filesystems`. This means that if you don't set either key, or you set either key to a single item list, only a single image will be expected. If you set `labels` to a two-item list and `filesystems` to a single-item list, two images will be expected. If you set both keys to a two-item list, four images will be expected...and so on.

When multiple combinations are in play, the names of the images will include the relevant values. So if an image group has multiple entries in the `labels` list but not the `filesystems` list, the filenames will be `disk_(name)_(label1).img`, `disk_(name)_(label2).img`, and so on. If there are multiple entries in both lists, you'll get `disk_(name)_(filesystem1)_(label1).img`, `disk_(name)_(filesystem1)_(label2).img`, etc etc. The `all` subcommand will always create all the expected images; the image group subcommand will create all the expected images by default, but will have `--label` and `--filesystem` arguments allowing the user to restrict creation to a single item from either or both lists.

For `labels`, the values represent disk label types, and are passed to guestfs. The only values used at present are `gpt` and `mbr`. Obviously, `gpt` formats the disk with a GPT disk label, `mbr` formats the disk with an MBR label.

For `filesystems`, the values represent...filesystems. Any of the partitions defined in `parts` (see above) which does not specify a `filesystem` will be formatted with this filesystem.

Let's consider some examples!

Say an image group specifies `name : "blank"`, `labels : ["mbr", "gpt"]` and does not specify `filesystems`. There will be two expected images: `disk_blank_mbr.img` and `disk_blank_gpt.img`. The former will have an MBR disk label, the latter a GPT disk label. In all other respects, the images will be identical. If any partition does not specify a filesystem, it will be formatted as `ext4` (as the default for `filesystems` is `['ext4']`).

Say an image group specifies `name : "blank"`, `filesystems : ["ext4", "ntfs"]` and does not specify `labels`. There will be two expected images: `disk_blank_ext4.img` and `disk_blank_ntfs.img`. Both will have an MBR disk label (as the default for `labels` is `['mbr']`). On the former, all partitions which do not specify a `filesystem` will be formatted as ext4; on the latter, all partitions which do not specify a `filesystem` will be formatted as ntfs. In all other respects the images will be identical. As a special note: it is nonsense to specify multiple `filesystems`, but also explicitly specify a `filesystem` for each partition in `parts`. This will result in the creation of multiple identical images, because none of the values from `filesystems` will actually do anything. However, it's perfectly reasonable to have an image group with *some* partitions that explicitly specify a filesystem and *some* that do not, and then have multiple filesystem variants - say, you want multiple variant images with the data partitions formatted using different filesystems, but you want the `/boot` partition in each variant to be ext4.

Finally, say an image group specifies `name : "blank"`, `filesystems : ["ext4", "ntfs"]` and `labels : ["mbr", "gpt"]`. There will be *four* expected images, `disk_blank_ext4_mbr.img`, `disk_blank_ntfs_mbr.img`, `disk_blank_ext4_gpt.img`, `disk_blank_ntfs_gpt.img`. The `mbr` images will have MBR disk labels, the `gpt` images will have GPT disk labels, the `ext4` images will have partitions that don't explicitly specify a filesystem formatted as ext4, and the `ntfs` images will have partitions that don't explicitly specify a filesystem formatted as NTFS.

Whew! That was a lot of explanation, but it's not really a super-complicated concept, you'll get it easy. OK, let's move on to the `virtbuilder`-specific keys:

#### `releases`

This key is **required**. It defines the releases and arches for which images are expected; thus it determines the number of images that will be expected for this group. The value is a dict. Each key in the dict represents a release; the value for each key is a list of the arches for which images should be built for that release. The keys should be integer digit strings. **Positive** values indicate absolute release numbers. **Negative** values are relative to whatever is the pending release at the time the images are created. So a release number `-1` means 'the release one before the pending release at the time the images are built'. So if the next Fedora release will be Fedora 24 at the time the images are created, and one of the dict keys is `-1`, an image will be expected for Fedora 23.

The filename for a virt-builder type image always includes the release number and arch it's built for - `disk_f(release)_(name)_(arch).img`.

Let's look at an example! Say the `name` is `minimal` and the `releases` dict is `{ "-1" : ["i686", "x86_64"], "-2" : ["x86_64"] }`. Three images will be expected, and the expected releases will be relevant to the pending release. Say the pending release is Fedora 24, the expected images will be `disk_f23_minimal_i686.img` (Fedora 23 for i686), `disk_f23_minimal_x86_64.img` (Fedora 23 for x86_64), and `disk_f22_minimal_x86_64.img` (Fedora 22 for x86_64). When time moves on and the next pending release is F25, images will be expected for Fedora 23 and Fedora 24, and the Fedora 22 images will be considered obsolete and deleted by cleanup modes of `createhdds`.

As with the `guestfs` case, the single image group subcommand will have parameters to limit creation. So in our example, the `minimal` subcommand will have `--release` and `--arch` parameters, each allowing just a single value. For coding simplicity, passing `--arch` alone is ignored (this may be fixed later) and will just result in the 'expected' images being created. If `--release` is passed, only a single image will be created, for whatever release is specified; by default it will be the x86_64 image, you may pass `--arch (arch)` to build another arch instead.

#### `maxage`

This key is **optional**. If not set, it defaults to 14. Its value should be an integer string. This basically indicates how often (as a number of days) the image should be rebuilt. virt-builder images can go 'stale' - at build time we update the installed OS to the latest packages, but of course by the time the image is used, later updates may be available. If the test the image is used for needs all the latest packages to be installed, the test will have to install the later updates, and it's inefficient to have one or more tests doing that every day. So it makes sense to re-generate the images periodically so that the tests only have to install few if any updates. For any image group with a non-0 maxage, createhdds `check` and `any` modes will check any existing image file's age against maxage; if it exceeds the maxage `check` will consider it 'outdated', and `all` will rebuild it. To disable maxage checks for an image group, set `maxage` to 0.

### `commands` files

Customization of virt-builder type images, beyond the Fedora release/arch combination, is done with `.commands` files. virt-builder allows you to pass in any set of customization commands you like in a text file. It seemed easier to simply let maintainers create a `.commands` file for each virt-builder image group than to come up with a syntax for specifying customizations in the JSON. The logic is simple: for each virt-builder image group, if there is a file named `(name).commands`, that file will be passed to virt-builder as the customization command file. For instance, the `desktop.commands` file contains the customization commands for the 'desktop' virt-builder image group; it installs the Workstation package group, creates a regular user, and does a few other things. The virt-builder documentation explains all the customization commands. The `.commands` file is technically optional, but in most cases you will want to include at least the commands from `minimal.commands` - to set a root password, update packages, and schedule an SELinux relabel (as files touched by other customization commands will have incorrect labels).
