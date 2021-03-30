import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import json

if __name__ == "__main__":
    import pprint
    printer = pprint.PrettyPrinter(indent=1, stream=open("response.py", "w"))

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
    if os.path.exists("src/google/data/token.json"):
        creds = Credentials.from_authorized_user_file("src/google/data/token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "src/google/data/credentials.json", SCOPES)
            creds = flow.run_local_server(port=0, authorization_prompt_message="")
        # Save the credentials for the next run
        with open("src/google/data/token.json", "w") as token:
            token.write(creds.to_json())

    service = build("docs", "v1", credentials=creds)
    return service

def get_writer(documents, documentId): # Take documents and documentId only once
    def write_and_style(text, style="NORMAL_TEXT", alignment="START"):
        print("---------------------------------------------")
        print("Writing", text)
        # Write text
        documents.batchUpdate(
            documentId = documentId,
            body = {
                "requests": [{
                    "insertText": {
                        "text": r"Practical nasdadasd\nasdasasdads",
                        "endOfSegmentLocation": {
                            "segmentId": "" # Body
                        }
                    }
                }]
            }
        ).execute()

        # Find the startIndex and endIndex for the whole multiline text
        content = documents.get(documentId=documentId).execute().get("body").get("content")
        printer.pprint(content)
        text = text + "\n" # Docs adds a \n at the end of an insertText call
        first_line = text.split("\n")[0] + "\n"
        last_line = text.split("\n")[-2] + "\n" # "text\n".split("\n") = ["text", ""]

        # Update each paragraph in separate request
        paragraphs = []
        recordText = False
        for StructuralElement in content:
            if StructuralElement.get("paragraph"):
                for element in StructuralElement.get("paragraph").get("elements"):
                    if element.get("textRun"):
                        line_content = element.get("textRun").get("content")
                        if line_content == first_line:
                            recordText = True # Start recording if text starts
                        if recordText:
                            paragraphs.append(element)
                        if line_content == last_line:
                            recordText = False # Stop recording if text is stopping
        
        requests = []
        print(paragraphs)
        for paragraph_element in paragraphs:
            requests.append({
                    "updateParagraphStyle": {
                        "paragraphStyle": {
                            "namedStyleType": style,
                            "alignment": alignment
                        },
                        "fields": "namedStyleType,alignment",
                        "range": {
                            "segmentId": "", # Body
                            "startIndex": paragraph_element.get("startIndex"),
                            "endIndex": paragraph_element.get("endIndex")
                        }
                    }
                })

        try:
            documents.batchUpdate(
                documentId = documentId,
                body = {"requests": requests}
            ).execute()
        except:
            exit()
    return write_and_style
    

def start_requests(practical, documentId=None):
    service = build_service()
    documents = service.documents()
    if documentId is None:
        document = documents.create(body={"title": practical.get("name")}).execute()
        documentId = document.get("documentId")

    content = None

    # |------------------------------------------|
    # |       NAMED STYLE REFERENCE              |
    # |------------------------------------------|
    # | Title = Practical N                      |
    # | Subtitle = Practical description, author |
    # | Heading 1 = QN) Question heading         |
    # | Heading 2 = Code/Output heading          |
    # | Normal text = Question text              |
    # |------------------------------------------|

    write_and_style = get_writer(documents, documentId)
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    #                                                 HEADING AREA                                                #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    
    # Write raw heading texts
    write_and_style([
        (f"Practical {practical.get('number')}", "TITLE", "CENTER"),
        (practical.get("description"), "SUBTITLE", "CENTER"),
        ("~ Ankur Bohra (12E)", "SUBTITLE", "CENTER")
    ])
    


if __name__ == "__main__":
    docId = "1O3W4pGfbPiYq_2C-Ao4QekWuaI791vDLE-agsDKf9vo"
    practical = {
        "name": "Practical n - Do something",
        "description": "Do something",
        "number": "n"
    }

    start_requests(practical, documentId=docId)