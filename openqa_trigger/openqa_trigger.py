#!/usr/bin/env python

import json
import urllib2
import re
import urlgrabber
import os.path
import sys
import subprocess
import argparse
import datetime
# We can at least find images and run OpenQA jobs without wikitcms
try:
    import wikitcms.wiki
except:
    pass
import fedfind.release

from report_job_results import report_results

PERSISTENT = "/var/tmp/openqa_watcher.json"
ISO_PATH = "/var/lib/openqa/factory/iso/"
RUN_COMMAND = "/var/lib/openqa/script/client isos post ISO=%s DISTRI=fedora VERSION=rawhide FLAVOR=server ARCH=%s BUILD=%s"
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

def download_image(image):
    """Download a given image with a name that should be unique for
    this event and arch (until we start testing different images
    for the same event and arch). Returns the filename of the image
    (not the path).
    """
    isoname = "{0}_{1}.iso".format(image.version.replace(' ', '_'), image.arch)
    filename = os.path.join(ISO_PATH, isoname)
    if not os.path.isfile(filename):
        # Icky hack around a urlgrabber bug:
        # https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=715416
        urlgrabber.urlgrab(image.url.replace('https', 'http'), filename)
    return isoname

def run_openqa_jobs(isoname, arch, image_version):
    """# run OpenQA 'isos' job on selected isoname, with given arch
    and a version string. **NOTE**: the version passed to OpenQA as
    BUILD and is parsed back into the 'relval report-auto' arguments
    by report_job_results.py; it is expected to be in the form of a
    3-tuple on which join('_') has been run, and the three elements
    will be passed as --release, --compose and --milestone. Returns
    list of job IDs.
    """
    command = RUN_COMMAND % (isoname, arch, image_version)

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

def jobs_from_current(wiki):
    """Schedule jobs against the 'current' release validation event
    (according to wikitcms) if we have not already. Returns a tuple,
    first value is the job list, second is the current event.
    """
    if not wiki:
        print("python-wikitcms is required for current validation event "
              "discovery.")
        return ([], None)
    last_versions, json_parsed = read_last()
    currev = wiki.current_event
    print("Current event: {0}".format(currev.version))
    runarches = []
    for arch in VERSIONS:
        last_version = last_versions.get(arch, None)
        if last_version and last_version >= currev.sortname:
            print("Skipped: {0}".format(arch))
        else:
            runarches.append(arch)
            json_parsed[arch] = currev.sortname

    # write info about latest versions
    f = open(PERSISTENT, "w")
    f.write(json.dumps(json_parsed))
    f.close()

    jobs = jobs_from_fedfind(currev.ff_release, runarches)

    return (jobs, currev)

def jobs_from_fedfind(ff_release, arches=VERSIONS):
    """Given a fedfind.Release object, find the ISOs we want and run
    jobs on them. arches is an iterable of arches to run on, if not
    specified, we'll use our constant.
    """
    # Find boot.iso images for our arches; third query is a bit of a
    # bodge till I know what 22 TCs/RCs will actually look like,
    # ideally we want a query that will reliably return one image per
    # arch without us having to filter further, but we can always just
    # take the first image for each arch if necessary
    jobs = []
    queries = (
        fedfind.release.Query('imagetype', ('boot',)),
        fedfind.release.Query('arch', arches),
        fedfind.release.Query('payload', ('server', 'generic')))

    for image in ff_release.find_images(queries):
        print("{0} {1}".format(image.url, image.desc))
        isoname = download_image(image)
        version = '_'.join(
            (ff_release.release, ff_release.milestone, ff_release.compose))
        job_ids = run_openqa_jobs(isoname, image.arch, version)
        jobs.extend(job_ids)
    return jobs

## SUB-COMMAND FUNCTIONS

def run_current(args, wiki):
    """run OpenQA for current release validation event, if we have
    not already done it.
    """
    jobs, _ = jobs_from_current(wiki)
    # wait for jobs to finish and display results
    if jobs:
        print jobs
        report_results(jobs)
    sys.exit()

def run_compose(args, wiki=None):
    """run OpenQA on a specified compose, optionally reporting results
    if a matching wikitcms ValidationEvent is found by relval/wikitcms
    """
    # get the fedfind release object
    try:
        ff_release = fedfind.release.get_release(
            release=args.release, milestone=args.milestone,
            compose=args.compose)
    except ValueError as err:
        sys.exit(err[0])

    print("Running on compose: {0}".format(ff_release.version))
    if args.arch:
        jobs = jobs_from_fedfind(ff_release, [args.arch])
    else:
        jobs = jobs_from_fedfind(ff_release)
    print(jobs)
    if args.submit_results:
        report_results(jobs)
    sys.exit()

def run_all(args, wiki=None):
    """Do everything we can: test both Rawhide and Branched nightlies
    if they exist, and test current compose if it's different from
    either and it's new.
    """
    skip = None
    (jobs, currev) = jobs_from_current(wiki)
    print("Jobs from current validation event: {0}".format(jobs))

    yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    if currev and currev.compose == yesterday.strftime('%Y%m%d'):
        skip = currev.milestone

    if not skip.lower() == 'rawhide':
        rawhide_ffrel = fedfind.release.get_release(
            release='Rawhide', compose=yesterday)
        rawjobs = jobs_from_fedfind(rawhide_ffrel)
        print("Jobs from {0}: {1}".format(rawhide_ffrel.version, rawjobs))
        jobs.extend(rawjobs)

    if not skip.lower() == 'branched':
        branched_ffrel = fedfind.release.get_release(
            release=currev.release, compose=yesterday)
        branchjobs = jobs_from_fedfind(branched_ffrel)
        print("Jobs from {0}: {1}".format(branched_ffrel.version, branchjobs))
        jobs.extend(branchjobs)

    if jobs:
        report_results(jobs)
    sys.exit()

if __name__ == "__main__":
    test_help = "Operate on the staging wiki (for testing)"
    parser = argparse.ArgumentParser(description=(
        "Run OpenQA tests for a release validation test event."))
    subparsers = parser.add_subparsers()

    parser_current = subparsers.add_parser(
        'current', description="Run for the current event, if needed.")
    parser_current.add_argument(
        '-t', '--test', help=test_help, required=False, action='store_true')
    parser_current.set_defaults(func=run_current)

    parser_compose = subparsers.add_parser(
        'compose', description="Run for a specific compose (TC/RC or nightly)."
        " If a matching release validation test event can be found and "
        "--submit-results is passed, results will be reported.")
    parser_compose.add_argument(
        '-r', '--release', type=int, required=False, choices=range(12, 100),
        metavar="12-99", help="Release number of a specific compose to run "
        "against. Must be passed for validation event discovery to succeed.")
    parser_compose.add_argument(
        '-m', '--milestone', help="The milestone to operate on (Alpha, Beta, "
        "Final, Branched, Rawhide). Must be specified for a TC/RC; for a "
        "nightly, will be guessed if not specified", required=False,
        choices=['Alpha', 'Beta', 'Final', 'Branched', 'Rawhide'])
    parser_compose.add_argument(
        '-c', '--compose', help="The version to run for; either the compose "
        "(for a TC/RC), or the date (for a nightly build)", required=False,
        metavar="{T,R}C1-19 or YYYYMMDD")
    parser_compose.add_argument(
        '-a', '--arch', help="The arch to run for", required=False,
        choices=('x86_64', 'i386'))
    parser_compose.add_argument(
        '-s', '--submit-results', help="Submit the results to the release "
        "validation event for this compose, if possible", required=False,
        action='store_true')
    parser_compose.add_argument(
        '-t', '--test', help=test_help, required=False, action='store_true')
    parser_compose.set_defaults(func=run_compose)

    parser_all = subparsers.add_parser(
        'all', description="Run for the current validation event (if needed) "
        "and today's Rawhide and Branched nightly's (if found).")
    parser_all.add_argument(
        '-t', '--test', help=test_help, required=False, action='store_true')
    parser_all.set_defaults(func=run_all)

    args = parser.parse_args()

    wiki = None
    if args.test:
        try:
            wiki = wikitcms.wiki.Wiki(('https', 'stg.fedoraproject.org'),
                                      '/w/')
        except NameError:
            pass
    else:
        try:
            wiki = wikitcms.wiki.Wiki(('https', 'fedoraproject.org'), '/w/')
        except NameError:
            pass
    args.func(args, wiki)
