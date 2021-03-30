import glob
import re

from ioproxy import IOProxy

info_regex = r"^'''\n@heading: (.+)\n@question-no: (\d+)\n@question: ((?:.*\n)+)'''"
prac_name_regex = r".+\\(Practical (\d+) - (.+))"

def extract_from_file(filename):
    '''
    Pull the heading, question, source and output of a program with following docstring:

    @heading: heading
    @question-no: question no
    @question: question
    that may have 
    newlines
    '''
    with open(filename, "r+") as file:
        source = file.read()

        match = re.search(info_regex, source)
        heading = match.group(1)
        question_no = match.group(2)
        question = match.group(3)

        proxy = IOProxy()
        with proxy:
            exec(compile(
                source = source,
                filename = file.name,
                mode = "exec" 
            ))
        return heading, question, question_no, proxy.record

def extract_from_practical(path):
    '''
    Search a folder for python files and extract info from them.
    '''
    practical = {
        "name": re.search(prac_name_regex, path).group(1),
        "number": re.search(prac_name_regex, path).group(2),
        "description": re.search(prac_name_regex, path).group(3),
        "practicals": {}
    }
    for filename in glob.glob(path+"\\*.py"):
        heading, question_no, question, output = extract_from_file(filename)
        practical["practicals"][question_no] = {
            "heading": heading,
            "question": question,
            "path": path+"\\"+filename,
            "output": output
        }
    return practical