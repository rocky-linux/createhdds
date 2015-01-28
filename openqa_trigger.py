#!/usr/bin/env python

import json
import urllib2
import re
import urlgrabber
import os.path
import sys
import subprocess

import jozuv_bomba_script

PERSISTENT="/var/tmp/openqa_watcher.json"
CURRENT_TEST="https://fedoraproject.org/wiki/Test_Results:Current_Installation_Test"
ISO_REGEX=re.compile(r'https://kojipkgs\.fedoraproject\.org/mash/(?P<name>rawhide-(?P<build>\d+))/rawhide/(?P<arch>x86_64|i386)/os/images/boot\.iso')
ISO_PATH="/var/lib/openqa/factory/iso/"
RUN_COMMAND="/var/lib/openqa/script/client isos post ISO=%s DISTRI=fedora VERSION=rawhide FLAVOR=server ARCH=%s BUILD=%s"
VERSIONS = ['i386', 'x86_64']

# read last tested version from file
def read_last():
    result = {}
    try:
        f = open(PERSISTENT, "r")
        json_raw = f.read()
        f.close()
        json_parsed = json.loads(json_raw)
    except IOError:
        return result, {}

    for version in VERSIONS:
        result[version] = json_parsed.get(version, None)
    return result, json_parsed

# read current version from Current Installation Test page
def read_currents():
    page = urllib2.urlopen(CURRENT_TEST).read()
    for match in ISO_REGEX.finditer(page):
        yield match.group("build"), match.group(0), match.group("name"), match.group("arch")

last_versions, json_parsed = read_last()
jobs = []

# for every architecture
for current_version, link, name, arch in read_currents():
    # don't run when there is newer version
    last_version = last_versions.get(arch, None)
    if last_version is not None and (last_version == current_version):
        continue

    json_parsed[arch] = current_version

    isoname = "%s_%s.iso" % (name, arch)
    filename = os.path.join(ISO_PATH, isoname)
    urlgrabber.urlgrab(link, filename)

    command = RUN_COMMAND % (isoname, arch, current_version)

    output = subprocess.check_output(command.split())

    # read ids from OpenQA to wait for
    r = re.compile(r'ids => \[(?P<from>\d+)( \.\. (?P<to>\d+))?\]')
    match = r.search(output)
    if match:
        from_i = int(match.group('from'))
        to_i = int(match.group('to')) + 1
        jobs.extend(range(from_i, to_i))

# write info about latest versions
f = open(PERSISTENT, "w")
f.write(json.dumps(json_parsed))
f.close()

jozuv_bomba_script.vyres_problemy(jobs)
