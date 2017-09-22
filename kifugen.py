import sys
import os
import subprocess
import argparse

parser = argparse.ArgumentParser(description='Convert sgf go records into a kifu format.')

parser.add_argument('sgfFile')
parser.add_argument('-se', "--splitevery", dest="step", type=int, default=50)
parser.add_argument('-c', "--compile", action="store_true", dest="c", default=False)
parser.add_argument('-o', "--open", action="store_true", dest="o", default=False)

args = parser.parse_args(sys.argv[1:])

filePath = args.sgfFile
splitBoardAt = [x for x in range(0, 400, args.step)]

with open(filePath, 'r') as myfile:
    sgfData = myfile.read().replace("\n", "").split(";")[1:]
    sgfData[-1] = sgfData[-1][:-1]

header = sgfData[0]
moves = sgfData[1:]

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
    out = ""
    if parsedHeader["event"] != "":
        out+=parsedHeader["event"] + "\\\\"
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

outFileBaseName = ".".join(filePath.split(".")[:-1])
with open(outFileBaseName+ ".tex", 'w') as outFile:
    outFile.write(outText)

# should be compiled to pdf?
if args.c:
    try:
        subprocess.check_call(['latex', outFileBaseName + ".tex"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess.check_call(['dvips', "-P", "pdf", outFileBaseName + ".dvi"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess.check_call(['ps2pdf', outFileBaseName + ".ps"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        print("error")
    else:
        if args.o:
            os.system('"%s.pdf"' % outFileBaseName)
