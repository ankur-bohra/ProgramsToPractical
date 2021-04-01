import os.path

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from .doc_requests import get_writers # type: ignore

if __name__ == "__main__":
    import pprint
    printer = pprint.PrettyPrinter(indent=1, stream=open("debug/sink.py", "w"))

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/documents"]

# The ID of a sample document.
DOCUMENT_ID = "1eS50Bi65NWY9xql-EbpVaTOTCvTqZTYjOUCKnLFN4Ag"

def build_service():
    """Builds the google docs service.
    """
    creds = None
    # The file token.json stores the user"s access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("src/docs/data/token.json"):
        creds = Credentials.from_authorized_user_file("src/docs/data/token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "src/docs/data/credentials.json", SCOPES)
            creds = flow.run_local_server(port=0, authorization_prompt_message="")
        # Save the credentials for the next run
        with open("src/docs/data/token.json", "w") as token:
            token.write(creds.to_json())

    service = build("docs", "v1", credentials=creds)
    return service

def make_requests(practical, documentId=None):
    service = build_service()
    documents = service.documents()
    if documentId is None:
        document = documents.create(body={"title": practical.get("name")}).execute()
        documentId = document.get("documentId")

    # Document
    write_and_style, break_page, write_code, write_output = get_writers(documents, documentId)

    # HEADING AREA
    write_and_style(f"Practical {practical.get('number')}", ("TITLE", "CENTER"), False) # addNewLine=False
    write_and_style(practical.get("description"), ("SUBTITLE", "CENTER"))
    write_and_style("~ Ankur Bohra (12E)", ("SUBTITLE", "CENTER"))

    # HEADING-BODY FILLER
    write_and_style("\n"*4, ("SUBTITLE", "START")) # 4 newlines of subtitle style are used
    # QUESTIONS
    for question_no in range(1, len(practical.get("questions"))+1): # Questions numbers start from 1
        questionInfo = practical.get("questions").get(question_no)
        # Per question
        write_and_style(f"Q{question_no}) {questionInfo.get('summary')}", ("HEADING_1", "START"))
        write_and_style("\n"+questionInfo.get("question"), ("NORMAL_TEXT", "START"))
        write_and_style("Code", ("HEADING_2", "START"))
        write_code(questionInfo.get("path"), questionInfo.get("firstSourceLine"))
        write_and_style("Output", ("HEADING_2", "START"))
        write_output(questionInfo.get("output"))

        if question_no != len(practical.get("questions")): # The last question (note: q no.s start from 1)
            break_page()


if __name__ == "__main__":
    docId = "1O3W4pGfbPiYq_2C-Ao4QekWuaI791vDLE-agsDKf9vo"
    practical = {
        "name": "Practical n - Do something",
        "description": "Do something",
        "number": "n",
        "questions": {
            1: {
                "summary": "Test Question 1",
                "question": "Write a sample question (1)",
                "path": r"D:\Ankur\Programs\Python\Personal\ProgramsToPractical\debug\sample1.py",
                "output": "[1, 2, 3, 4, 5]"
            },
            2: {
                "summary": "Test Question 2",
                "question": "Write a sample question,\nbut this one spans\nmultiple lines!",
                "path": r"D:\Ankur\Programs\Python\Personal\ProgramsToPractical\debug\sample2.py",
                "output": "[6, 7, 8, 9, 10]"
            },
            3: {
                "summary": "Test Question 3",
                "question": "Write a sample question (3)",
                "path": r"D:\Ankur\Programs\Python\Personal\ProgramsToPractical\debug\sample3.py",
                "output": "[11, 12, 13, 14, 15]"
            }
        }
    }

    make_requests(practical, documentId=docId)
