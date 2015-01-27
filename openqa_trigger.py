#!/usr/bin/env python

import json
import urllib2
import re
import urlgrabber
import os.path
import sys

PERSISTENT="/var/tmp/openqa_watcher.json"
CURRENT_TEST="https://fedoraproject.org/wiki/Test_Results:Current_Installation_Test"
ISO_REGEX=re.compile(r'https://kojipkgs\.fedoraproject\.org/mash/(?P<name>rawhide-(?P<build>\d+))/rawhide/(?P<arch>(x86_64|i386))/os/images/boot\.iso')
ISO_PATH="/var/lib/openqa/factory/iso/"
RUN_COMMAND="/var/lib/openqa/script/client isos post ISO=%s DISTRI=fedora VERSION=rawhide FLAVOR=server ARCH=%s BUILD=%s"

# read last tested version from file
def read_last():
    try:
        f = open(PERSISTENT, "r")
        json_raw = f.read()
        f.close()
        json_parsed = json.loads(json_raw)
    except IOError:
        return None, None
    return json_parsed["last_version"], json_all

# read current version from Current Installation Test page
def read_current():
    page = urllib2.urlopen(CURRENT_TEST).read()
    match = ISO_REGEX.search(page)
    if match:
        return match.group("build"), match.group(0), match.group("name"), match.group("arch")
    else:
        return None, None, None, None

last, json_all = read_last()
current, link, name, arch = read_current()

# don't run when there is newer version
if last is not None and (last == current):
    sys.exit()

isoname = "%s_%s.iso" % (name, arch)
filename = os.path.join(ISO_PATH, isoname)
urlgrabber.urlgrab(link, filename)

command = RUN_COMMAND % (isoname, arch, current)
