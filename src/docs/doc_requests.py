from token import TYPE_IGNORE
import tokenize
import keyword
from googleapiclient.errors import HttpError
import pprint
from webbrowser import get
printer = pprint.PrettyPrinter(indent=1, stream=open("debug/sink.py", "w"))

def get_writers(documents, documentId):
    def write_and_style_bridge(*args):
        return write_and_style(documents, documentId, *args)    
    def break_page_bridge():
        return break_page(documents, documentId)    
    def write_code_bridge(*args):
        return write_code(documents, documentId, *args)
    def write_output_bridge(*args):
        return write_output(documents, documentId, *args)
    return write_and_style_bridge, break_page_bridge, write_code_bridge, write_output_bridge

def write_and_style(documents, documentId, text, styleData, addNewLine=True):
    # Store last endIndex to fix content-based filtering
    content = documents.get(documentId=documentId).execute().get("body").get("content")
    lastIndex = content[-1].get("endIndex")

    # Write text
    documents.batchUpdate(
        documentId = documentId,
        body = {
            "requests": [{
                "insertText": {
                    "text": "\n"+text if addNewLine else text,
                    "endOfSegmentLocation": {
                        "segmentId": "" # Body
                    }
                }
            }]
        }
    ).execute()

    # Find the startIndex and endIndex for the whole multiline text
    content = documents.get(documentId=documentId).execute().get("body").get("content")
    text = text + "\n" # Docs adds a \n at the end of an insertText call, and strips \n from start
    first_line = text.split("\n")[0]
    last_line = text.split("\n")[-2] + "\n" # "text\n".split("\n") = ["text", ""]

    # Update each paragraph in separate request
    paragraphs = []
    recordText = False
    printer.pprint(content)
    for StructuralElement in content:
        if StructuralElement.get("endIndex") <= lastIndex:
            continue
        # Addition is new
        if StructuralElement.get("paragraph"):
            for element in StructuralElement.get("paragraph").get("elements"):
                if element.get("textRun"):
                    line_content = element.get("textRun").get("content")
                    if line_content == first_line or line_content == first_line + "\n":
                        recordText = True # Start recording if text starts
                    if recordText:
                        paragraphs.append(element)
                    if line_content == last_line:
                        recordText = False # Stop recording if text is stopping
    
    requests = []
    for paragraph_element in paragraphs:
        requests.append({
                "updateParagraphStyle": {
                    "paragraphStyle": {
                        "namedStyleType": styleData[0],
                        "alignment": styleData[1]
                    },
                    "fields": "namedStyleType,alignment",
                    "range": {
                        "segmentId": "", # Body
                        "startIndex": paragraph_element.get("startIndex"),
                        "endIndex": paragraph_element.get("endIndex")
                    }
                }
            })

    documents.batchUpdate(
        documentId = documentId,
        body = {"requests": requests}
    ).execute()

def break_page(documents, documentId):
    documents.batchUpdate(
        documentId = documentId,
        body = {
            "requests": [{
                "insertPageBreak": {
                    "endOfSegmentLocation": {
                        "segmentId": ""
                    }
                }
            }]
        }
    ).execute()

colors = {
    "KEYWORD": (166, 38, 164),
    "FUNC_NAME": (64, 126, 242),
    tokenize.NAME: (56, 58, 66),
    tokenize.NUMBER: (152, 104, 1),
    tokenize.STRING: (80, 161, 79),
    tokenize.OP: (56, 58, 66),
    tokenize.AWAIT: (56, 58, 66),
    tokenize.ASYNC: (56, 58, 66),
    tokenize.TYPE_IGNORE: (160, 161, 167),
    tokenize.TYPE_COMMENT: (160, 161, 167),
    tokenize.COMMENT: (160, 161, 167),
    tokenize.ENCODING: (160, 161, 167)
}

def get_index(position, lines):
    index = position[1] # the row componenet
    lineNo = position[0]
    for line_no in range(1, lineNo): # Goes from 1 to lineNo-1
        line = lines[line_no - 1]
        if line_no != 1:
            lineLength = len(line) # first startIndex is 1
        else:
            lineLength = len(line)
        index += lineLength
    return index

text_tokens = [
    tokenize.NAME,
    tokenize.NUMBER,
    tokenize.STRING,
    tokenize.OP,
    tokenize.AWAIT,
    tokenize.ASYNC,
    tokenize.TYPE_IGNORE,
    tokenize.TYPE_COMMENT,
    tokenize.COMMENT,
    tokenize.ENCODING
]
def write_code(documents, documentId, sourcePath, firstSourceLine):
    with open(sourcePath, "r") as program:
        lines = []
        rangeToTokenMap = []

        # Remove non-source lines from queue
        for _ in range(1, firstSourceLine):
            program.readline()

        tokenGenerator = tokenize.generate_tokens(program.readline)
        tokens = []
        for token in tokenGenerator:
            tokens.append(token)

        for index in range(len(tokens)):
            token = tokens[index]
            tokenType = token.type
            if len(lines) == 0 or token.line != lines[-1]: # lines[-1] fixes identical lines bug
                lines.append(token.line)
            if tokenType not in text_tokens:
                continue
            if tokenType == tokenize.NAME:
                if token.string in keyword.kwlist:
                    tokenType = "KEYWORD"
                elif index > 0 and index < len(tokens)-1:
                    prevToken = tokens[index-1]
                    nextToken = tokens[index+1]
                    if prevToken.string == "def" and nextToken.string == "(":
                        tokenType = "FUNC_NAME"
                    
                
                
            startIndex = get_index(token.start, lines)
            endIndex = get_index(token.end, lines)
            rangeToTokenMap.append({
                'start': startIndex,
                'end': endIndex,
                'type': tokenType,
                'content': token.string
            })

    # Create container cell
    documents.batchUpdate(
        documentId = documentId,
        body = {
            "requests" : [{
                "insertTable": {
                    "rows": 1,
                    "columns": 1,
                    "endOfSegmentLocation": {
                        "segmentId": ""
                    }
                }
            }]
        }
    ).execute()

    # Format cell
    content = documents.get(documentId=documentId).execute().get("body").get("content")
    tableStart = None
    for StructuralElement in content:
        if StructuralElement.get("table"):
            tableStart = StructuralElement.get("startIndex")
    borderObject = {
        "width": {
            "magnitude": 0,
            "unit": "PT"
        },
        "color": {
            "color": {
                "rgbColor": {
                    "red": 0,
                    "green": 0,
                    "blue": 0
                }
            }
        },
        "dashStyle": "SOLID"
    }
    paddingObject = {
        "magnitude": 7,
        "unit": "PT"
    }
    documents.batchUpdate(
        documentId = documentId,
        body = {
            "requests": [{
                "updateTableCellStyle": {
                    "fields": "*",
                    "tableStartLocation": {
                        "segmentId": "",
                        "index": tableStart
                    },
                    "tableCellStyle": {
                        "backgroundColor": {
                            "color": {
                                "rgbColor": {
                                    "red": 250/255,
                                    "green": 250/255,
                                    "blue": 250/255
                                }
                            }
                        },
                        "borderRight": borderObject,
                        "borderLeft": borderObject,
                        "borderTop": borderObject,
                        "borderBottom": borderObject,
                        "paddingRight": paddingObject,
                        "paddingLeft": paddingObject,
                        "paddingTop": paddingObject,
                        "paddingBottom": paddingObject
                    }
                }
            }]
        }
    ).execute()

    # Store last endIndex to fix content-based filtering
    content = documents.get(documentId=documentId).execute().get("body").get("content")
    cellBodyIndex = tableStart+3#content[-1].get("endIndex")
    
    documents.batchUpdate(
        documentId = documentId,
        body = {
            "requests": [{
                "insertText": {
                    "text": "".join(lines),
                    "location": {
                        "segmentId": "",
                        "index": cellBodyIndex
                    }
                }
            }]
        }
    ).execute()

    # Get the relative zero index
    content = documents.get(documentId=documentId).execute().get("body").get("content")
    requests = []
    for run in rangeToTokenMap:
        color = colors[run.get("type")] if run.get("type") in colors else (0, 0, 0)
        updateTextStyleRequest = {
            "textStyle": {
                "fontSize": {
                    "magnitude": 10.5,
                    "unit": "PT"
                },
                "weightedFontFamily": {
                    "fontFamily": "Consolas",
                    "weight": 400 # normal
                },
                "foregroundColor": {
                    "color": {
                        "rgbColor": {
                            "red": color[0]/255,
                            "green": color[1]/255,
                            "blue":  color[2]/255
                        }
                    }
                }
            },
            "fields": "fontSize,weightedFontFamily,foregroundColor",
            "range": {
                "segmentId": "",
                "startIndex": cellBodyIndex + run.get("start"),
                "endIndex": cellBodyIndex + run.get("end")
            }
        }
        requests.append({
            "updateTextStyle": updateTextStyleRequest
        })
    documents.batchUpdate(
        documentId = documentId,
        body = {
            "requests": requests
        }
    ).execute()

def write_output(documents, documentId, output):
    # Create container cell
    documents.batchUpdate(
        documentId = documentId,
        body = {
            "requests" : [{
                "insertTable": {
                    "rows": 1,
                    "columns": 1,
                    "endOfSegmentLocation": {
                        "segmentId": ""
                    }
                }
            }]
        }
    ).execute()

    # Format cell
    content = documents.get(documentId=documentId).execute().get("body").get("content")
    tableStart = None
    for StructuralElement in content:
        if StructuralElement.get("table"):
            tableStart = StructuralElement.get("startIndex")
    borderObject = {
        "width": {
            "magnitude": 0,
            "unit": "PT"
        },
        "color": {
            "color": {
                "rgbColor": {
                    "red": 0,
                    "green": 0,
                    "blue": 0
                }
            }
        },
        "dashStyle": "SOLID"
    }
    paddingObject = {
        "magnitude": 7,
        "unit": "PT"
    }
    documents.batchUpdate(
        documentId = documentId,
        body = {
            "requests": [{
                "updateTableCellStyle": {
                    "fields": "*",
                    "tableStartLocation": {
                        "segmentId": "",
                        "index": tableStart
                    },
                    "tableCellStyle": {
                        "backgroundColor": {
                            "color": {
                                "rgbColor": {
                                    "red": 250/255,
                                    "green": 250/255,
                                    "blue": 250/255
                                }
                            }
                        },
                        "borderRight": borderObject,
                        "borderLeft": borderObject,
                        "borderTop": borderObject,
                        "borderBottom": borderObject,
                        "paddingRight": paddingObject,
                        "paddingLeft": paddingObject,
                        "paddingTop": paddingObject,
                        "paddingBottom": paddingObject
                    }
                }
            }]
        }
    ).execute()

     # Store last endIndex to fix content-based filtering
    content = documents.get(documentId=documentId).execute().get("body").get("content")
    cellBodyIndex = tableStart+3#content[-1].get("endIndex")

    documents.batchUpdate(
        documentId = documentId,
        body = {
            "requests": [{
                "insertText": {
                    "text": output,
                    "location": {
                        "segmentId": "",
                        "index": cellBodyIndex
                    }
                }
            }]
        }
    ).execute()

    color = colors.get(tokenize.NUMBER)
    documents.batchUpdate(
        documentId = documentId,
        body = {
            "requests": [{
                "updateTextStyle": {
                    "textStyle": {
                        "fontSize": {
                            "magnitude": 10.5,
                            "unit": "PT"
                        },
                        "weightedFontFamily": {
                            "fontFamily": "Consolas",
                            "weight": 400 # normal
                        },
                        "foregroundColor": {
                            "color": {
                                "rgbColor": {
                                    "red": color[0]/255,
                                    "green": color[1]/255,
                                    "blue":  color[2]/255
                                }
                            }
                        }
                    },
                    "fields": "fontSize,weightedFontFamily,foregroundColor",
                    "range": {
                        "segmentId": "",
                        "startIndex": cellBodyIndex,
                        "endIndex": cellBodyIndex + len(output)
                    }
                }
            }]
        }
    ).execute()
