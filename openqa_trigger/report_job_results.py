import requests
import argparse
import os
import time
import conf_test_suites


API_ROOT = "http://localhost/api/v1"
SLEEPTIME = 60


def get_passed_testcases(job_ids):
    """
    job_ids ~ list of int (job ids)
    Returns ~ list of str - names of passed testcases
    """
    running_jobs = dict([(job_id, "%s/jobs/%s" % (API_ROOT, job_id)) for job_id in job_ids])
    finished_jobs = {}

    while running_jobs:
        for job_id, url in running_jobs.items():
            job_state = requests.get(url).json()['job']
            if job_state['state'] == 'done':
                print "Job %s is done" % job_id
                finished_jobs[job_id] = job_state
                del running_jobs[job_id]
        if running_jobs:
           time.sleep(SLEEPTIME)

    passed_testcases = {} # key = VERSION_BUILD_ARCH
    for job_id in job_ids:
        job = finished_jobs[job_id]
        if job['result'] =='passed':
            key = (job['settings']['VERSION'], job['settings']['FLAVOR'], job['settings'].get('BUILD', None), job['settings']['ARCH'])
            passed_testcases.setdefault(key, [])
            passed_testcases[key].extend(conf_test_suites.TESTSUITES[job['settings']['TEST']])

    for key, value in passed_testcases.iteritems():
        passed_testcases[key] = sorted(list(set(value)))
    return passed_testcases


def get_relval_commands(passed_testcases):
    relval_template = "relval report-auto"
    commands = []
    for key in passed_testcases:
        cmd_ = relval_template
        version, _, build, arch = key
        cmd_ += ' --release "%s" --milestone "%s" --compose "%s"' % tuple(build.split('_'))

        for tc_name in passed_testcases[key]:
            testcase = conf_test_suites.TESTCASES[tc_name]
            tc_env = arch if testcase['env'] == '$RUNARCH$' else testcase['env']
            tc_type = testcase['type']
            tc_section = testcase['section']

            commands.append('%s --environment "%s" --testtype "%s" --section "%s" --testcase "%s" pass' % (cmd_, tc_env, tc_type,  tc_section, tc_name))

    return commands


def report_results(job_ids):
    commands = get_relval_commands(get_passed_testcases(job_ids))
    print "Running relval commands:"
    for command in commands:
        print command
        os.system(command)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate per-testcase results from OpenQA job runs")
    parser.add_argument('jobs', type=int, nargs='+')
    parser.add_argument('--report', default=False, action='store_true')

    args = parser.parse_args()

    passed_testcases = get_passed_testcases(args.jobs)
    commands = get_relval_commands(passed_testcases)

    import pprint
    pprint.pprint(passed_testcases)
    if not args.report:
        print "\n\n### No reporting is done! ###\n\n"
        pprint.pprint(commands)
    else:
        for command in commands:
            print command
            os.system(command)

