import sys

filePath = sys.argv[1]
splitBoardAt = [0,50,100,150,200,250,300,350,400,450]

with open(filePath, 'r') as myfile:
    sgfData = myfile.read().replace("\n", "").split(";")[1:]
    sgfData[-1] = sgfData[-1][:-1]

header = sgfData[0]
moves = sgfData[1:]

# print(header)
# print(moves)


def get_tag_from_header(tag):
    eventIdxStart = header.lower().find(tag.lower() + "[")
    eventIdxEnd = -1

    if eventIdxStart != -1 :
        eventIdxEnd =  header.find("]", eventIdxStart)
        return header[len(tag) + 1 + eventIdxStart:eventIdxEnd]
    return ""

def extractCoordinatesFromMove(move):
    try:
        firstCoordinate = move[2]
        secondCoordinate = ord(move[3])-96
        if ord(move[2]) >= ord("i"):
            firstCoordinate = chr(ord(firstCoordinate) + 1)
        return firstCoordinate, secondCoordinate
    except IndexError:
        return -1,-1

def generateTitle():
    out = parsedHeader["event"] + "\\\\"
    out += parsedHeader["playerBlack"]
    if parsedHeader["rankBlack"] != "":
        out += "[" + parsedHeader["rankBlack"] + "]"
    out += " - " + parsedHeader["playerWhite"]
    if parsedHeader["rankWhite"] != "":
        out += "[" + parsedHeader["rankWhite"] + "]"

    return out

parsedHeader = {
    "event" : get_tag_from_header("EV"),
    "gameName" : get_tag_from_header("GN"),
    "date" : get_tag_from_header("RD"),
    "boardSize" : int(get_tag_from_header("SZ")),
    "playerBlack" : get_tag_from_header("PB"),
    "playerWhite" : get_tag_from_header("PW"),
    "rankBlack" : get_tag_from_header("BR"),
    "rankWhite" : get_tag_from_header("WR"),
    "komi" : get_tag_from_header("KM"),
    "result" : get_tag_from_header("RE")
}

outText = """
\\documentclass[a4paper]{article}
\\usepackage{psgo}
\\usepackage[ngerman]{babel}
\\usepackage[margin=2cm,nohead]{geometry}

\\setgounit{0.5cm}

\\author{}
\\title{%s}
\\date{%s}

\\begin{document}
\\maketitle
\\vspace{3.5cm}
\\begin{center}
""" % (generateTitle(), parsedHeader["date"])

finished = False
for i in range(len(splitBoardAt)-1):
    currentSplit = splitBoardAt[i]
    nextSplit = splitBoardAt[i+1]

    outText += "\n\\setcounter{gomove}{0}\n"
    outText += "\\begin{psgoboard}\n\t"

    # old moves
    for j in range(currentSplit):
        firstCoordinate, secondCoordinate = extractCoordinatesFromMove(moves[j])
        outText += "\\move*{%s}{%d} " % (firstCoordinate, parsedHeader["boardSize"] - secondCoordinate + 1)
        if j % 5 == 4:
            outText += "\n\t"
        elif parsedHeader["boardSize"] - secondCoordinate < 9: # nice spacing
            outText += " "

    # new moves
    for j in range(nextSplit-currentSplit):
        firstCoordinate, secondCoordinate = extractCoordinatesFromMove(moves[currentSplit+j])
        if not (firstCoordinate == -1 or secondCoordinate == -1):
            outText += "\\move{%s}{%d}  " % (firstCoordinate, parsedHeader["boardSize"] - secondCoordinate + 1)
            if j % 5 == 4:
                outText += "\n\t"
            elif parsedHeader["boardSize"] - secondCoordinate < 9: # nice spacing
                outText += " "

        # was it the last move?
        if currentSplit+j == len(moves)-1:
            finished = True
            break

    outText += "\n\\end{psgoboard}\n"
    if finished:
        break

outText += """
\\textbf{%s}

\\end{center}
\\end{document}
""" % parsedHeader["result"]

newFileName = ".".join(filePath.split(".")[:-1]) + ".tex"
with open(newFileName, 'w') as outFile:
    outFile.write(outText)
