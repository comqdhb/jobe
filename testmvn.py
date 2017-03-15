#! /usr/bin/env python3
''' A tester and demo program for jobe
    Richard Lobb
    2/2/2015

    Modified 6/8/2015 to include --verbose command line parameter, to do
    better file upload and pylint testing and to improve error messages
    in some cases.

    Modified 7/11/2016 by Tim Hunt. Allow selection of languages to run
    from the command line, and use a non-zero exit code (number of
    failures + number of exceptions) if not all tests pass.

    Usage:
    To run all tests:
        ./testsubmit.py
    or
        ./testsubmit.py --verbose

    To run selected tests by language:
        ./testsubmit.py python3 octave --verbose
    (Use of --verbose is optional here.)
'''

from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError
import json
import sys
import http.client
from threading import Thread
import copy
from base64 import b64encode
import re


# Set VERBOSE to true to get a detailed report on each run as it is done
# Can also be set True with --verbose command argument.
VERBOSE = False

# Set DEBUGGING to True to instruct Jobe to use debug mode, i.e., to
# leave all runs (commands, input output etc) in /home/jobe/runs, rather
# than deleting each run as soon as it is done.
DEBUGGING = True

# Set JOBE_SERVER to the Jobe server URL.
# If Jobe expects an X-API-Key header, set API_KEY to a working value and set
# USE_API_KEY to True.
API_KEY = '2AAA7A5415B4A9B394B54BF1D2E9D'  # A working (100/hr) key on Jobe2

USE_API_KEY = True
JOBE_SERVER = 'localhost'

#JOBE_SERVER = 'jobe2.cosc.canterbury.ac.nz'

# The next constant controls the maximum number of parallel submissions to
# throw at Jobe at once. Numbers less than or equal to the number of Jobe
# users (currently 10) should be safe. Larger numbers might cause
# Overload responses.
NUM_PARALLEL_SUBMITS = 10

GOOD_TEST = 0
FAIL_TEST = 1
EXCEPTION = 2


# ===============================================
#
# Test List
#
# ===============================================

TEST_SET = [
{   
    'comment': 'inValid mvn',
    'language_id': 'mvn',
    'sourcecode': r'''<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/maven-v4_0_0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.mycompany.app</groupId>
  <artifactId>my-app</artifactId>
  <packaging>jar</packaging>
  <version>1.0-SNAPSHOT</version>
  <name>my-app</name>
  <url>http://maven.apache.org</url>
  <dependencies>
    <dependency>
      <groupId>junit</groupId>
      <artifactId>junit</artifactId>
      <version>3.8.1</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
</project>''',
    'parameters': {'memorylimit': 20000000,'cputime': 30},
    'sourcefilename': 'pom.xml',
    'expect': {  'stdout': '.*INFO.*' }
},
{
    'comment': 'sh ls',
    'language_id': 'sh',
    'sourcecode': r'''ls''',
    'parameters': {'memorylimit': 20000000,'cputime': 30},
    'sourcefilename': 'prog.sh',
    'expect': {  'stdout': '.*prog.sh.*' }
}

]

#==========================================================================
#
# Now the tester code
#
#==========================================================================


def check_parallel_submissions():
    '''Check that we can submit several jobs at once to Jobe with
       the process limit set to 1 and still have no conflicts.
    '''

    job = {
        'comment': 'C program to check parallel submissions',
        'language_id': 'c',
        'sourcecode': r'''#include <stdio.h>
#include <unistd.h>
int main() {
    printf("Hello 1\n");
    sleep(2);
    printf("Hello 2\n");
}''',
        'sourcefilename': 'test.c',
        'parameters': { 'numprocs': 1 },
        'expect': { 'outcome': 15, 'stdout': 'Hello 1\nHello 2\n' }
    }

    threads = []
    print("\nChecking parallel submissions")
    for child_num in range(NUM_PARALLEL_SUBMITS):
        print("Doing child", child_num)
        def run_job():
            this_job = copy.deepcopy(job)
            this_job['comment'] += '. Child' + str(child_num)
            run_test(job)

        t = Thread(target=run_job)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    print("All done")




def is_correct_result(expected, got):
    '''True iff every key in the expected outcome exists in the
       actual outcome and the associated values are equal, too'''
    for key in expected:
        print("key = " + key)
        print("expected = " + expected[key])
        print("got = " + got[key])
        if key not in got:
            return False
        if re.search(expected[key],got[key]):
            return True
        else :
           return False

# =============================================================

def http_request(method, resource, data, headers):
    '''Send a request to Jobe with given HTTP method to given resource on
       the currently configured Jobe server and given data and headers.
       Return the connection object. '''
    if USE_API_KEY:
            headers["X-API-KEY"] = API_KEY
    connect = http.client.HTTPConnection(JOBE_SERVER)
    connect.request(method, resource, data, headers)
    return connect


def check_file(file_id):
    '''Checks if the given fileid exists on the server.
       Returns status: 204 denotes file exists, 404 denotes file not found.
    '''

    resource = '/jobe/index.php/restapi/files/' + file_id
    headers = {"Accept": "text/plain"}
    try:
        connect = http_request('HEAD', resource, '', headers)
        response = connect.getresponse()

        if VERBOSE:
            print("Response to getting status of file ", file_id, ':')
            content = ''
            if response.status != 204:
                content =  response.read(4096)
            print(response.status, response.reason, content)

        connect.close()

    except HTTPError:
        return -1

    return response.status



def put_file(file_desc):
    '''Put the given (file_id, contents) to the server. Throws
       an exception to be caught by caller if anything fails.
    '''
    file_id, contents = file_desc
    contentsb64 = b64encode(contents.encode('utf8')).decode(encoding='UTF-8')
    data = json.dumps({ 'file_contents' : contentsb64 })
    resource = '/jobe/index.php/restapi/files/' + file_id
    headers = {"Content-type": "application/json",
               "Accept": "text/plain"}
    connect = http_request('PUT', resource, data, headers)
    response = connect.getresponse()
    if VERBOSE or response.status != 204:
        print("Response to putting", file_id, ':')
        content = ''
        if response.status != 204:
            content =  response.read(4096)
        print(response.status, response.reason, content)
    connect.close()


def run_test(test):
    '''Execute the given test, checking the output'''
    runspec = {}
    for key in test:
        if key not in ['comment', 'expect', 'files']:
            runspec[key] = test[key]
    if DEBUGGING:
        runspec['debug'] = True

    # First put any files to the server
    for file_desc in test.get('files', []):
        put_file(file_desc)
        response_code = check_file(file_desc[0])
        if response_code != 204:
            print("******** Put file/check file failed ({}). File not found.****".
                  format(response_code))

    # Prepare the request

    resource = '/jobe/index.php/restapi/runs/'
    data = json.dumps({ 'run_spec' : runspec })
    headers = {"Content-type": "application/json; charset=utf-8",
               "Accept": "application/json"}
    response = None
    content = ''

    # Do the request, returning EXCEPTION if it broke
    ok, result = do_http('POST', resource, data)
    if not ok:
        return EXCEPTION
    
   # If not an exception, check the response is as specified

    if is_correct_result(test['expect'], result):
        if VERBOSE:
            display_result(test['comment'], result)
        else:
            print(test['comment'] + ' OK')
        return GOOD_TEST
    else:
        print("\n***************** FAILED TEST ******************\n")
        print(result)
        display_result(test['comment'], result)
        print("\n************************************************\n")
        return FAIL_TEST


def do_http(method, resource, data=None):
    """Send the given HTTP request to Jobe, return a pair (ok result) where
       ok is true if no exception was thrown, false otherwise and 
       result is a dictionary of the JSON decoded response (or an empty
       dictionary in the case of a 204 response.
    """
    result = {}
    ok = True
    headers = {"Content-type": "application/json; charset=utf-8",
               "Accept": "application/json"}
    try:
        connect = http_request(method, resource, data, headers)
        response = connect.getresponse()
        if response.status != 204:
            content = response.read().decode('utf8')
            if content:
                result = json.loads(content)
        connect.close()

    except (HTTPError, ValueError) as e:
        print("\n***************** HTTP ERROR ******************\n")
        if response:
            print(' Response:', response.status, response.reason, content)
        else:
            print(e)
        ok = False
    return (ok, result)


def trim(s):
    '''Return the string s limited to 10k chars'''
    MAX_LEN = 10000
    if len(s) > MAX_LEN:
        return s[:MAX_LEN] + '... [etc]'
    else:
        return s


def display_result(comment, ro):
    '''Display the given result object'''
    print(comment)
    if not isinstance(ro, dict) or 'outcome' not in ro:
        print("Bad result object", ro)
        return

    outcomes = {
        0:  'Successful run',
        11: 'Compile error',
        12: 'Runtime error',
        13: 'Time limit exceeded',
        15: 'Successful run',
        17: 'Memory limit exceeded',
        19: 'Illegal system call',
        20: 'Internal error, please report',
        21: 'Server overload. Excessive parallelism?'}

    code = ro['outcome']
    print("{}".format(outcomes[code]))
    print()
    if ro['cmpinfo']:
        print("Compiler output:")
        print(ro['cmpinfo'])
        print()
    else:
        if ro['stdout']:
            print("Output:")
            print(trim(ro['stdout']))
        else:
            print("No output")
        if ro['stderr']:
            print()
            print("Error output:")
            print(trim(ro['stderr']))


def do_get_languages():
    """List all languages available on the jobe server"""
    print("Supported languages:")
    resource = '/jobe/index.php/restapi/languages'
    ok, lang_versions = do_http('GET', resource)
    if not ok:
        print("**** An exception occurred when getting languages ****")
    else:
        for lang, version in lang_versions:
            print("    {}: {}".format(lang, version))
    print()


def main():
    '''Every home should have one'''
    global VERBOSE
    do_get_languages()
    langs_to_run = set(sys.argv[1:]) #get rid of the program name
    if '--verbose' in langs_to_run:
        VERBOSE = True
        langs_to_run.remove('--verbose')
    if len(langs_to_run) == 0:
        langs_to_run = set([testcase['language_id'] for testcase in TEST_SET])
    counters = [0, 0, 0]  # Passes, fails, exceptions
    tests_run = 0;
    for test in TEST_SET:
        if test['language_id'] in langs_to_run:
            tests_run += 1
            result = run_test(test)
            counters[result] += 1
            if VERBOSE:
                print('=====================================')

    print()
    print("{} tests, {} passed, {} failed, {} exceptions".format(
        tests_run, counters[0], counters[1], counters[2]))

    if 'c' in langs_to_run:
        check_parallel_submissions()

    return counters[1] + counters[2]


sys.exit(main())


