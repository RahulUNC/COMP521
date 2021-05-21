import requests
import json


def runTest(testname, method, endpoint, payload, expected_status, expected_json):
    try:
        url_base = "http://localhost:8080"
        
        headers = {
            'Content-Type': 'application/json'
        }
    
        response = requests.request(method, url_base + endpoint, headers=headers, json=payload)

        if response.status_code != expected_status:
            print(f"Test '{testname}' received unexpected response status {response.status}. Expected {expected_status}")
            return False

        if response.ok and expected_json != None:
            result = response.json()

            for item in expected_json:
                if item not in result:
                    print(f"Test '{testname}' missing key {item} in JSON result")
                    return False
                if expected_json[item] != result[item]:
                    print(f"Test '{testname}' expected key {item} with value {expected_json[item]} in JSON result. Received {result[item]} instead.")
                    return False

    except Exception as err:
        print(err)
        print(f"Test '{testname}' caused unexpected exception")
        return False

    print(f"Test '{testname}' passed")
    return True

runTest('GET /question for empty database', 'GET', '/question', None, 200, {'mc':[], 'sa':[], 'sql':[]})
runTest('Create multiple choice question', 'POST', '/question',
        {'type':'mc', 'question_text':'MC test 1', 'points':3, 'setup':None}, 
        200, {'id': 1, 'type':'mc', 'question_text':'MC test 1', 'points':3, 'setup':None, 'true_options': [], 'false_options': []})
runTest('Create short answer question', 'POST', '/question',
        {'type':'sa', 'question_text':'Short answer test 1','points':2, 'setup':None, 'answer':'short answer answer'},
        200, {'id': 2, 'type':'sa', 'question_text':'Short answer test 1','points':2, 'setup':None, 'answer':'short answer answer', 'rubrics':[]})
runTest('Create sql question', 'POST', '/question',
        {'id': 3, 'type':'sql', 'question_text':'SQL question test', 'points':1, 'setup':1, 'answer':'sql answer'},
        200, {'type':'sql', 'question_text':'SQL question test', 'points':1, 'setup':1, 'answer':'sql answer'})
runTest('Bad sql create with no setup', 'POST', '/question',
        {'type':'sql', 'question_text':'SQL question test', 'points':1, 'setup':None, 'answer':'sql answer'},
        400, None)
runTest('Bad short answer create with no answer', 'POST', '/question',
            {'type':'sa', 'question_text':'dummy text', 'points': 3, 'setup': None},
            400, None)
runTest('Bad short answer create with whitespace question', 'POST', '/question',
            {'type':'sa', 'question_text':'       ', 'points': 2, 'setup': None},
            400, None)
runTest('Bad multiple choice create with negative points', 'POST', '/question',
            {'type':'mc', 'question_text':'dummy text', 'points':-2, 'setup':None},
            400, None)
runTest('Creating true option for previously created multiple choice', 'POST', '/mc_option',
            {'is_true': True, 'option_text':'option 1', 'qid':1},
            200, {'id': 1, 'is_true': True, 'option_text':'option 1', 'qid':1})
runTest('Creating false option for previously created multiple choice', 'POST', '/mc_option',
            {'is_true': False, 'option_text':'option 2', 'qid':1},
            200, {'id': 2, 'is_true': False, 'option_text':'option 2', 'qid':1})
runTest('Retrieving previously created multiple choice question with options', 'GET', '/question/1', None,
            200, {'id': 1, 'type':'mc', 'question_text':'MC test 1', 'points':3, 'setup':None, 'true_options': [{'id':1, 'is_true':True, 'option_text':'option 1', 'qid': 1}], 'false_options': [{'id':2, 'is_true':False, 'option_text':'option 2', 'qid':1}]})
runTest('Creating rubric for previously created short answer', 'POST', '/rubric',
            {'rubric_text': 'Rubric 1', 'points': -1.5, 'qid': 2},
            200, {'id': 1, 'rubric_text': 'Rubric 1', 'points': -1.5, 'qid': 2})
runTest('Retrieving previously created short answer question with rubric', 'GET', '/question/2', None,
            200, {'id': 2, 'type':'sa', 'question_text':'Short answer test 1','points':2, 'setup':None, 'answer':'short answer answer', 'rubrics':[{'id':1, 'rubric_text': 'Rubric 1', 'points': -1.5, 'qid': 2}]})
runTest('Creating sql question with long question text', 'POST', '/question',
            {'type':'sql', 'question_text':'This is very long question text which will help test getting the question index with just the first 40 characters', 'points':1, 'setup':1, 'answer':'dummy answer'},
            200,
            {'id':4, 'type':'sql', 'question_text':'This is very long question text which will help test getting the question index with just the first 40 characters', 'points':1, 'setup':1, 'answer':'dummy answer'})
runTest('GET /question with questions created by prior tests', 'GET', '/question', None,
            200, {'mc':[{'id': 1, 'question_start': 'MC test 1'}], 'sa':[{'id': 2, 'question_start': 'Short answer test 1'}], 'sql':[{'id': 3, 'question_start': 'SQL question test'}, {'id': 4, 'question_start': 'This is very long question text which wi'}]})
runTest('Updating sql question with new question text, answer text, point value, and setup', 'PUT', '/question/4',
        {'type':'sql', 'question_text':'now short', 'points':5, 'setup':2, 'answer':'different answer'},
        200, {'id': 4, 'type':'sql', 'question_text':'now short', 'points':5, 'setup':2, 'answer':'different answer'})
runTest('Rerunning GET /question with questions created by prior tests and change made by prior test', 'GET', '/question', None,
            200, {'mc':[{'id': 1, 'question_start': 'MC test 1'}], 'sa':[{'id': 2, 'question_start': 'Short answer test 1'}], 'sql':[{'id': 3, 'question_start': 'SQL question test'}, {'id': 4, 'question_start': 'now short'}]})
runTest('Updating question with different question type should fail with 400 response', 'PUT', '/question/1',
            {'type':'sa', 'question_text':'bogus', 'points':1, 'setup':None, 'answer':'bogus'},
            400, None)
runTest('Updating non-existant question should fail with 404 response', 'PUT', '/question/10',
            {'type':'sa', 'question_text':'bogus', 'points':1, 'setup':None, 'answer':'bogus'},
            404, None)
runTest('Deleting multiple choice question', 'DELETE', '/question/1', None, 200, None)
runTest('True option for deleted multiple choice question should be gone now', 'GET', '/mc_option/1', None, 404, None)
runTest('False option for deleted multiple choice question should be gone now', 'GET', '/mc_option/2', None, 404, None)
runTest('Deleting short answer question', 'DELETE', '/question/2', None, 200, None)
runTest('Rubric for deleted short answer question should be gone now', 'GET', '/rubric/1', None, 404, None)
runTest('Deleting non-existant question should 404 fail', 'DELETE', '/question/100', None, 404, None)
