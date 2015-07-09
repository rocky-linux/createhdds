import requests
import argparse
import sys
import time
import logging
import conf_test_suites

from operator import attrgetter
from wikitcms.wiki import Wiki, ResTuple

API_ROOT = "http://localhost/api/v1"
SLEEPTIME = 60
logger = logging.getLogger(__name__)


def get_passed_testcases(job_ids):
    """
    job_ids ~ list of int (job ids)
    Returns ~ list of str - names of passed testcases
    """
    running_jobs = dict([(job_id, "%s/jobs/%s" % (API_ROOT, job_id)) for job_id in job_ids])
    logger.info("running jobs: %s", running_jobs)
    finished_jobs = {}

    while running_jobs:
        for job_id, url in running_jobs.items():
            job_state = requests.get(url).json()['job']
            if job_state['state'] == 'done':
                logger.info("job %s is done", job_id)
                finished_jobs[job_id] = job_state
                del running_jobs[job_id]
        if running_jobs:
           time.sleep(SLEEPTIME)
    logger.info("all jobs finished")

    passed_testcases = set()
    for job_id in job_ids:
        job = finished_jobs[job_id]
        if job['result'] =='passed':
            (release, milestone, compose) = job['settings']['BUILD'].split('_')
            testsuite = job['settings']['TEST']
            arch = job['settings']['ARCH']
            flavor = job['settings']['FLAVOR']

            for testcase in conf_test_suites.TESTSUITES[testsuite]:
                # each 'testsuite' is a list using testcase names to indicate which Wikitcms tests have
                # passed if this job passes. Each testcase name is the name of a dict in the TESTCASES
                # dict-of-dicts which more precisely identifies the 'test instance' (when there is more
                # than one for a testcase) and environment for which the result should be filed.
                uniqueres = conf_test_suites.TESTCASES[testcase]
                testname = ''
                if 'name_cb' in uniqueres:
                    testname = uniqueres['name_cb'](flavor)
                env = arch if uniqueres['env'] == '$RUNARCH$' else uniqueres['env']
                result = ResTuple(
                    testtype=uniqueres['type'], release=release, milestone=milestone, compose=compose,
                    testcase=testcase, section=uniqueres['section'], testname=testname, env=env, status='pass',
                    bot=True)
                passed_testcases.add(result)

    return sorted(list(passed_testcases), key=attrgetter('testcase'))

def report_results(job_ids, verbose=False, report=True):
    passed_testcases = get_passed_testcases(job_ids)
    if verbose:
        for restup in passed_testcases:
            print restup
    logger.info("passed testcases: %s", passed_testcases)

    if report:
        if verbose:
            print "Reporting test passes:"
        logger.info("reporting test passes")
        wiki = Wiki()
        wiki.login()
        if not wiki.logged_in:
            logger.error("could not log in to wiki")
            sys.exit("Could not log in to wiki!")

        # Submit the results
        (insuffs, dupes) = wiki.report_validation_results(passed_testcases)
        for dupe in dupes:
            tmpl = "already reported result for test %s, env %s! Will not report dupe."
            if verbose:
                print tmpl % (dupe.testcase, dupe.env)
            logger.info(tmpl, dupe.testcases, dupe.env)

    else:
        if verbose:
            print "\n\n### No reporting is done! ###\n\n"
        logger.warning("no reporting is done")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate per-testcase results from OpenQA job runs")
    parser.add_argument('jobs', type=int, nargs='+')
    parser.add_argument('--report', default=False, action='store_true')

    args = parser.parse_args()
    report_results(args.jobs, verbose=True, report=args.report)
