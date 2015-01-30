#!/usr/bin/env python

import json
import urllib2
import re
import urlgrabber
import os.path
import sys
import subprocess

#from evaluate_jobs import evaluate_jobs

PERSISTENT = "/var/tmp/openqa_watcher.json"
CURRENT_TEST = "https://fedoraproject.org/wiki/Test_Results:Current_Installation_Test"
ISO_URL = "https://kojipkgs.fedoraproject.org/mash/rawhide-%s/rawhide/%s/os/images/boot.iso"
ISO_REGEX = re.compile(r'https://kojipkgs\.fedoraproject\.org/mash/(?P<name>rawhide-(?P<build>\d+))/rawhide/(?P<arch>x86_64|i386)/os/images/boot\.iso')
ISO_PATH = "/var/lib/openqa/factory/iso/"
RUN_COMMAND = "/var/lib/openqa/script/client isos post ISO=%s DISTRI=fedora VERSION=rawhide FLAVOR=server ARCH=%s BUILD='%s_%s'"
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
    f_regex = re.compile(r'<title>.*Fedora (?P<version>\d+).*</title>')
    m = f_regex.search(page)
    for match in ISO_REGEX.finditer(page):
        yield m.group('version'), match.group("build"), match.group(0), match.group("name"), match.group("arch")

# download rawhide iso from koji
def download_rawhide_iso(link, name, arch):
    isoname = "%s_%s.iso" % (name, arch)
    filename = os.path.join(ISO_PATH, isoname)
    link = "http://" + link[len("https://"):]
    urlgrabber.urlgrab(link, filename)
    return isoname

# run OpenQA 'isos' job on selected isoname, with given arch and build
# returns list of job IDs
def run_openqa_jobs(isoname, arch, fedora_version, build):
    command = RUN_COMMAND % (isoname, arch, fedora_version, build)

    # starts OpenQA jobs
    output = subprocess.check_output(command.split())

    # read ids from OpenQA to wait for
    r = re.compile(r'ids => \[(?P<from>\d+)( \.\. (?P<to>\d+))?\]')
    match = r.search(output)
    if match and match.group('to'):
        from_i = int(match.group('from'))
        to_i = int(match.group('to')) + 1
        return range(from_i, to_i)
    elif match:
        return [int(match.group('from'))]
    else:
        return []

# run OpenQA on rawhide if there is newer version since last run
def run_if_newer():
    last_versions, json_parsed = read_last()
    jobs = []

    # for every architecture
    for f_version, current_version, link, name, arch in read_currents():
        # don't run when there is newer version
        last_version = last_versions.get(arch, None)
        if last_version is not None and (last_version == current_version):
            continue

        json_parsed[arch] = current_version

        isoname = download_rawhide_iso(link, name, arch)
        job_ids = run_openqa_jobs(isoname, arch, f_version, current_version)

        jobs.extend(job_ids)

    # write info about latest versions
    f = open(PERSISTENT, "w")
    f.write(json.dumps(json_parsed))
    f.close()

    # wait for jobs to finish and display results
    #evaluate_jobs(jobs)
    print jobs


if __name__ == "__main__":
    if len(sys.argv) == 1:
        run_if_newer()
    elif len(sys.argv) == 3:
        version = sys.argv[1]
        arch = sys.argv[2]
        name = "rawhide-%s" % version
        link = ISO_URL % (sys.argv[1], sys.argv[2])
        isoname = download_rawhide_iso(link, name, arch)
        job_ids = run_openqa_jobs(isoname, arch, "", version)
        print job_ids
    else:
        print "%s [rawhide_version arch]" % sys.arv[0]
