import glob
from os import error
import re

from .ioproxy import IOProxy

info_regex = r"^'''\n@summary: (.+)\n@question-no: (\d+)\n@question: ((?:.*\n)+)'''"
prac_name_regex = r".+\\(Practical (\d+) - (.+))"

def extract_from_file(filename):
    '''
    Pull the summary, question, source and output of a program with following docstring:

    @question-no: question no
    @summary: summary
    @question: question
    that may have 
    newlines
    '''
    with open(filename, "r") as file:
        source = file.read()

        match = re.search(info_regex, source)
        summary = match.group(1)
        question_no = int(match.group(2))
        question = match.group(3)
        question = question[:len(question) - 1]

        newlines = 5 + question.count("\n") # ''', @question-no, @summary, question-content, last line of q-content, '''
        first_source_line = newlines + 1

        proxy = IOProxy()
        print("\n> Running",file.name.split("\\")[-1])
        with proxy:
            try:
                exec(source, {}) # Specify environment
            except NameError as e:
                return summary, question, question_no, e, first_source_line
        return summary, question_no, question, proxy.record, first_source_line

def extract_from_practical(path):
    '''
    Search a folder for python files and extract info from them.
    '''
    practical = {
        "name": re.search(prac_name_regex, path).group(1),
        "number": re.search(prac_name_regex, path).group(2),
        "description": re.search(prac_name_regex, path).group(3),
        "questions": {}
    }
    for filename in glob.glob(path+"\\*.py"):
        summary, question_no, question, output, first_source_line = extract_from_file(filename)
        practical["questions"][question_no] = {
            "summary": summary,
            "question": question,
            "path": filename,
            "output": output,
            "firstSourceLine": first_source_line
        }
    return practical