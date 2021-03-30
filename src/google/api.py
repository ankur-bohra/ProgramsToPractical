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

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    #                                                 HEADING AREA                                                #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    
    # Write raw heading text
    documents.batchUpdate(
        documentId = documentId,
        body = {
            "requests": [{
                "insertText": {
                    "text": f"Practical {practical.get('number')}\n{practical.get('description')}\n~ Ankur Bohra (12E)", # Each \n makes a new paragraph
                    "endOfSegmentLocation": {
                        "segmentId": "" # End of body
                    }
                }
            }]
        }
    ).execute()
    content = documents.get(documentId=documentId).execute().get("body").get("content")

    # Style heading text
    # content -> paragraph -> elements -> (element) -> endIndex, startIndex
    main_heading = content[1].get("paragraph").get("elements")[0] # 0th is the section for header
    sub_heading = content[2].get("paragraph").get("elements")[0]
    author = content[3].get("paragraph").get("elements")[0]
    documents.batchUpdate(
        documentId = documentId,
        body = {
            "requests": [
                {
                    "updateParagraphStyle": {
                        "paragraphStyle": {
                            "namedStyleType": "TITLE",
                            "alignment": "CENTER"
                        },
                        "fields": "namedStyleType,alignment",
                        "range": {
                            "segmentId": "",
                            "startIndex": main_heading.get("startIndex"),
                            "endIndex": main_heading.get("endIndex")
                        }
                    }
                },
                {
                    "updateParagraphStyle": {
                        "paragraphStyle": {
                            "namedStyleType": "SUBTITLE",
                            "alignment": "CENTER"
                        },
                        "fields": "namedStyleType,alignment",
                        "range": {
                            "segmentId": "",
                            "startIndex": sub_heading.get("startIndex"),
                            "endIndex": sub_heading.get("endIndex")
                        }
                    }
                },
                {
                    "updateParagraphStyle": {
                        "paragraphStyle": {
                            "namedStyleType": "SUBTITLE",
                            "alignment": "CENTER"
                        },
                        "fields": "namedStyleType,alignment",
                        "range": {
                            "segmentId": "",
                            "startIndex": author.get("startIndex"),
                            "endIndex": author.get("endIndex")
                        }
                    }
                }
            ]
        }
    ).execute()
    


if __name__ == "__main__":
    docId = "1O3W4pGfbPiYq_2C-Ao4QekWuaI791vDLE-agsDKf9vo"
    practical = {
        "name": "Practical n - Do something",
        "description": "Do something",
        "number": "n"
    }

    start_requests(practical, documentId=docId)