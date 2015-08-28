#!/usr/bin/env python

import json
import urlgrabber
import os.path
import sys
import argparse
import datetime
import logging
import time
# We can at least find images and run OpenQA jobs without wikitcms
try:
    import wikitcms.wiki
except ImportError:
    wikitcms = None
import fedfind.exceptions
import fedfind.release

from openqa_client.client import OpenQA_Client
from report_job_results import report_results

PERSISTENT = "/var/tmp/openqa_watcher.json"
ISO_PATH = "/var/lib/openqa/factory/iso/"
ARCHES = ['x86_64', 'i386']


class TriggerException(Exception):
    pass


# read last tested version from file
def read_last():
    logging.debug("reading latest checked version from %s", PERSISTENT)
    result = {}
    try:
        f = open(PERSISTENT, "r")
        json_raw = f.read()
        f.close()
        json_parsed = json.loads(json_raw)
    except IOError:
        logging.warning("cannot read file %s", PERSISTENT)
        return result, {}

    for arch in ARCHES:
        result[arch] = json_parsed.get(arch, None)
        logging.info("latest version for %s: %s", arch, result[arch])
    return result, json_parsed


def download_image(image):
    """Download a given image with a name that should be unique.
    Returns the filename of the image (not the path).
    """
    ver = image.version.replace(' ', '_')
    if image.imagetype == 'boot':
        isoname = "{0}_{1}_{2}_boot.iso".format(ver, image.payload, image.arch)
    else:
        isoname = "{0}_{1}".format(ver, image.filename)
    filename = os.path.join(ISO_PATH, isoname)
    if not os.path.isfile(filename):
        logging.info("downloading %s (%s) to %s", image.url, image.desc, filename)
        # Icky hack around a urlgrabber bug:
        # https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=715416
        urlgrabber.urlgrab(image.url.replace('https', 'http'), filename)
    else:
        logging.info("%s already exists", filename)
    return isoname


def run_openqa_jobs(client, isoname, flavor, arch, build):
    """# run OpenQA 'isos' job on selected isoname, with given arch
    and a version string. **NOTE**: the version passed to OpenQA as
    BUILD and is parsed back into the 'relval report-auto' arguments
    by report_job_results.py; it is expected to be in the form of a
    3-tuple on which join('_') has been run, and the three elements
    will be passed as --release, --compose and --milestone. Returns
    list of job IDs.
    """
    logging.info("sending jobs on OpenQA")

    # starts OpenQA jobs
    params = {
        'ISO': isoname,
        'DISTRI': 'fedora',
        'VERSION': build.split('_')[0],
        'FLAVOR': flavor,
        'ARCH': arch,
        'BUILD': build
    }
    output = client.openqa_request('POST', 'isos', params)

    logging.debug("executed")
    logging.info("planned jobs: %s", output["ids"])

    return output["ids"]


def jobs_from_current(wiki, client):
    """Schedule jobs against the 'current' release validation event
    (according to wikitcms) if we have not already. Returns the job
    list.
    """
    if not wiki:
        logging.warning("python-wikitcms is required for current validation event discovery.")
        return ([], None)
    last_versions, json_parsed = read_last()
    currev = wiki.current_event
    logging.info("current event: %s", currev.version)
    runarches = []
    for arch in ARCHES:
        last_version = last_versions.get(arch, None)
        if last_version and last_version >= currev.sortname:
            logging.info("skipped: %s: %s is newer or equal to %s",
                         arch, last_version, currev.sortname)
        else:
            runarches.append(arch)
            logging.debug("%s will be tested in version %s", arch, currev.sortname)
            json_parsed[arch] = currev.sortname

    jobs = []

    if not runarches:
        raise TriggerException("Skipped all arches, nothing to do.")

    jobs = jobs_from_fedfind(currev.ff_release, client, runarches)
    logging.info("planned jobs: %s", ' '.join(str(j) for j in jobs))

    # write info about latest versions
    f = open(PERSISTENT, "w")
    f.write(json.dumps(json_parsed))
    f.close()
    logging.debug("written info about newest version")

    return jobs


def jobs_from_fedfind(ff_release, client, arches=ARCHES):
    """Given a fedfind.Release object, find the ISOs we want and run
    jobs on them. arches is an iterable of arches to run on, if not
    specified, we'll use our constant.
    """
    # Find currently-testable images for our arches.
    jobs = []
    queries = (
        fedfind.release.Query('imagetype', ('boot', 'live')),
        fedfind.release.Query('arch', arches),
        fedfind.release.Query('payload', ('server', 'generic', 'workstation')))
    logging.debug("querying fedfind for images")
    images = ff_release.find_images(queries)

    if len(images) == 0:
        raise TriggerException("no available images")

    # Now schedule jobs. First, let's get the BUILD value for openQA.
    build = '_'.join((ff_release.release, ff_release.milestone, ff_release.compose))

    # Next let's schedule the 'universal' tests.
    # We have different images in different composes: nightlies only
    # have a generic boot.iso, TC/RC builds have Server netinst/boot
    # and DVD. We always want to run *some* tests -
    # default_boot_and_install at least - for all images we find, then
    # we want to run all the tests that are not image-dependent on
    # just one image. So we have a special 'universal' flavor and
    # product in openQA; all the image-independent test suites run for
    # that product. Here, we find the 'best' image we can for the
    # compose we're running on (a DVD if possible, a boot.iso or
    # netinst if not), and schedule the 'universal' jobs on that
    # image.
    for arch in arches:
        okimgs = (img for img in images if img.arch == arch and
                  any(img.imagetype == okt for okt in ('dvd', 'boot', 'netinst')))
        bestscore = 0
        bestimg = None
        for img in okimgs:
            if img.imagetype == 'dvd':
                score = 10
            else:
                score = 1
            if img.payload == 'generic':
                score += 5
            elif img.payload == 'server':
                score += 3
            elif img.payload == 'workstation':
                score += 1
            if score > bestscore:
                bestimg = img
                bestscore = score
        if not bestimg:
            logging.warn("no universal tests image found for %s", arch)
            continue
        logging.info("running universal tests for %s with %s", arch, bestimg.desc)
        isoname = download_image(bestimg)
        job_ids = run_openqa_jobs(client, isoname, 'universal', arch, build)
        jobs.extend(job_ids)

    # Now schedule per-image jobs.
    for image in images:
        isoname = download_image(image)
        flavor = '_'.join((image.payload, image.imagetype))
        job_ids = run_openqa_jobs(client, isoname, flavor, image.arch, build)
        jobs.extend(job_ids)
    return jobs


# SUB-COMMAND FUNCTIONS


def run_current(args, client, wiki):
    """run OpenQA for current release validation event, if we have
    not already done it.
    """
    logging.info("running on current release")
    try:
        jobs = jobs_from_current(wiki, client)
    except TriggerException as e:
        logging.debug("No jobs run: %s", e)
        sys.exit(1)
    # wait for jobs to finish and display results
    if jobs:
        logging.info("waiting for jobs: %s", ' '.join(str(j) for j in jobs))
        report_results(jobs, client)
    logging.debug("finished")
    sys.exit()


def run_compose(args, client, wiki=None):
    """run OpenQA on a specified compose, optionally reporting results
    if a matching wikitcms ValidationEvent is found by relval/wikitcms
    """
    # get the fedfind release object
    try:
        logging.debug("querying fedfind on specific compose: %s %s %s", args.release,
                      args.milestone, args.compose)
        ff_release = fedfind.release.get_release(release=args.release, milestone=args.milestone,
                                                 compose=args.compose)
    except ValueError as err:
        logging.critical("compose %s %s %s was not found", args.release, args.milestone,
                         args.compose)
        sys.exit(err[0])

    logging.info("running on compose: %s", ff_release.version)

    if args.ifnotcurrent:
        try:
            currev = wiki.current_event
            # Compare currev's fedfind release version with ours
            if currev.ff_release.version == ff_release.version:
                logging.info("Compose is the current validation compose. Exiting.")
                sys.exit()
        except AttributeError:
            sys.exit("Wikitcms is required for --ifnotcurrent.")

    if args.wait:
        logging.info("Waiting up to %s mins for compose", str(args.wait))
        try:
            ff_release.wait(waittime=args.wait)
        except fedfind.exceptions.WaitError:
            sys.exit("Waited too long for compose to appear!")

    jobs = []
    try:
        if args.arch:
            jobs = jobs_from_fedfind(ff_release, client, [args.arch])
        else:
            jobs = jobs_from_fedfind(ff_release, client)
    except TriggerException as e:
        logging.debug("No jobs run: %s", e)
        sys.exit(1)
    logging.info("planned jobs: %s", ' '.join(str(j) for j in jobs))
    if args.submit_results:
        report_results(jobs, client)
    logging.debug("finished")
    sys.exit()


if __name__ == "__main__":
    test_help = "Operate on the staging wiki (for testing)"
    parser = argparse.ArgumentParser(description=(
        "Run OpenQA tests for a release validation test event."))
    subparsers = parser.add_subparsers()

    parser_current = subparsers.add_parser(
        'current', description="Run for the current event, if needed.")
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
        '-w', '--wait', help="Wait NN minutes for the compose to appear, if "
        "it doesn't yet exist", type=int, metavar="NN", default=0,
        required=False)
    parser_compose.add_argument(
        '-i', '--ifnotcurrent', help="Only run if the compose is not the "
        "'current' validation compose. Mainly intended for cron runs on "
        "nightly builds, to avoid duplicating jobs run by a 'current' "
        "cron job. Requires wikitcms", action='store_true')
    parser_compose.set_defaults(func=run_compose)

    parser.add_argument(
        '-t', '--test', help=test_help, required=False, action='store_true')
    parser.add_argument(
        '-f', '--log-file', help="If given, log into specified file. When not provided, stdout"
        " is used", required=False)
    parser.add_argument(
        '-l', '--log-level', help="Specify log level to be outputted", required=False)
    parser.add_argument('-i', '--iso-directory', help="Directory for downloading isos, default"
                        " is %s" % PERSISTENT, required=False)

    args = parser.parse_args()

    if args.log_level:
        log_level = getattr(logging, args.log_level.upper(), None)
        if not isinstance(log_level, int):
            log_level = logging.INFO
    else:
        log_level = logging.INFO
    if args.log_file:
        logging.basicConfig(format="%(levelname)s:%(name)s:%(asctime)s:%(message)s",
                            filename=args.log_file, level=log_level)
    else:
        logging.basicConfig(level=log_level)

    if args.iso_directory:
        ISO_PATH = args.iso_directory

    wiki = None
    if args.test:
        logging.debug("using test wiki")
        if wikitcms:
            wiki = wikitcms.wiki.Wiki(('https', 'stg.fedoraproject.org'), '/w/')
        else:
            logging.warn("wikitcms not found, reporting to wiki disabled")
    else:
        if wikitcms:
            wiki = wikitcms.wiki.Wiki(('https', 'fedoraproject.org'), '/w/')
        else:
            logging.warn("wikitcms not found, reporting to wiki disabled")

    client = OpenQA_Client()  # uses first server from ~/.config/openqa/client.conf

    args.func(args, client, wiki)
