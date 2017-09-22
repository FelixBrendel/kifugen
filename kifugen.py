import argparse
import os
import sys
from subprocess import check_call, DEVNULL, STDOUT, CalledProcessError
from shutil import copyfile, rmtree

parser = argparse.ArgumentParser(description='Convert sgf go records into a kifu format.')

parser.add_argument('sgfFile')
parser.add_argument('-se', "--splitevery", dest="step", type=int, default=50)
parser.add_argument('-cn', "--continuousNumbers", action="store_true", dest="cn", default=False)
parser.add_argument('-c', "--compile", action="store_true", dest="c", default=False)
parser.add_argument('-o', "--open", action="store_true", dest="o", default=False)

args = parser.parse_args(sys.argv[1:])

filePath = args.sgfFile
fileBase = ".".join(filePath.split(".")[:-1])
splitBoardAt = [x for x in range(0, 400, args.step)]

with open(filePath, 'r') as myfile:
    sgfData = myfile.read().replace("\n", "").split(";")[1:]
    sgfData[-1] = sgfData[-1][:-1]

header = sgfData[0]
moves = sgfData[1:]

def get_tag_from_header(tag):
    eventIdxStart = header.lower().find(f"{tag.lower()}[")
    eventIdxEnd = -1

    if eventIdxStart != -1 :
        eventIdxEnd =  header.find("]", eventIdxStart)
        return header[len(tag) + 1 + eventIdxStart:eventIdxEnd]
    return ""

def extract_coordinates(move):
    try:
        firstCoordinate = move[2]
        secondCoordinate = ord(move[3])-96
        # mirror at x axis so it looks normal
        secondCoordinate = parsedHeader["boardSize"] - secondCoordinate + 1
        if ord(move[2]) >= ord("i"):
            firstCoordinate = chr(ord(firstCoordinate) + 1)
        return firstCoordinate, secondCoordinate
    except IndexError:
        # wierd move
        return -1,-1

def generate_title():
    out = []
    if parsedHeader["event"] != "":
        out.extend([parsedHeader["event"], "\\\\"])
    out.append(parsedHeader["playerBlack"])
    if parsedHeader["rankBlack"] != "":
        out.extend(["[", parsedHeader["rankBlack"], "]"])
    out.extend([" - ", parsedHeader["playerWhite"]])
    if parsedHeader["rankWhite"] != "":
        out.extend(["[", parsedHeader["rankWhite"], "]"])

    return "".join(out)

def generate_moves():
    finished = False
    outText = []
    for i in range(len(splitBoardAt)-1):
        currentSplit = splitBoardAt[i]
        nextSplit = splitBoardAt[i+1]

        outText.append("\\begin{psgoboard}\n\t")

        # old moves
        for j in range(currentSplit):
            firstCoordinate, secondCoordinate = extract_coordinates(moves[j])
            if not (firstCoordinate == -1 or secondCoordinate == -1):
                outText.append(f"\\move*{{{firstCoordinate}}}{{{secondCoordinate}}} ")
                if j % 5 == 4:
                    outText.append("\n\t")
                elif secondCoordinate < 10: # nice spacing
                    outText.append(" ")

        # new moves
        for j in range(nextSplit-currentSplit):
            firstCoordinate, secondCoordinate = extract_coordinates(moves[currentSplit+j])
            if not (firstCoordinate == -1 or secondCoordinate == -1):
                outText.append(f"\\move{{{firstCoordinate}}}{{{secondCoordinate}}}  ")
                if j % 5 == 4:
                    outText.append("\n\t")
                elif secondCoordinate < 10: # nice spacing
                    outText.append(" ")

            # was it the last move?
            if currentSplit+j == len(moves)-1:
                finished = True
                break

        outText.append("\n\\end{psgoboard}\n")
        if finished:
            break
        elif not args.cn:
            outText.append("\n\\setcounter{gomove}{0}\n")

    return "".join(outText)

parsedHeader = {
    "event"       : get_tag_from_header("EV"),
    "gameName"    : get_tag_from_header("GN"),
    "date"        : get_tag_from_header("DT"),
    "boardSize"   : int(get_tag_from_header("SZ")),
    "playerBlack" : get_tag_from_header("PB"),
    "playerWhite" : get_tag_from_header("PW"),
    "rankBlack"   : get_tag_from_header("BR"),
    "rankWhite"   : get_tag_from_header("WR"),
    "komi"        : get_tag_from_header("KM"),
    "result"      : get_tag_from_header("RE")
}


# title = generate_title()
event = parsedHeader["event"]
date = parsedHeader["date"]
result = parsedHeader["result"]
komi = parsedHeader["komi"]
playerWhite = parsedHeader["playerWhite"]
playerBlack = parsedHeader["playerBlack"]
if parsedHeader["rankBlack"] != "":
    playerBlack += f" ({parsedHeader['rankBlack']})"
if parsedHeader["rankWhite"] != "":
    playerWhite += f" ({parsedHeader['rankWhite']})"
moves = generate_moves()

outText = f"""
\\documentclass[a4paper]{{article}}
\\usepackage{{psgo}}
\\usepackage[ngerman]{{babel}}
\\usepackage[margin=2cm,nohead]{{geometry}}
\\usepackage{{tabularx}}

\\newcolumntype{{R}}{{>{{\\raggedleft\\arraybackslash}}X}}

\\setgounit{{0.5cm}}
\\setcounter{{gomove}}{{0}}

\\begin{{document}}
\\sffamily
\\def\\arraystretch{{2}}
\\begin{{center}}
    \\vspace*{{1cm}}
    {{\\Huge {event} \\par}}
	\\vspace{{1cm}}
	{{\\huge {date} \\par}}
	\\vspace{{2cm}}
	\\begin{{tabularx}}{{\\textwidth}}{{ R | c | X }}
    \\hline
    \\stone{{black}} {playerBlack} & \\textbf{{{result}}} & {playerWhite} \\stone{{white}} \\\\\\hline
     & {komi} Komi &  \\\\\\hline
  \\end{{tabularx}}
  \\vspace{{3cm}}

{moves}

\\end{{center}}
\\end{{document}}
"""

with open(f"{fileBase}.tex", 'w') as outFile:
    outFile.write(outText)

# should be compiled to pdf?
if args.c:
    try:
        os.makedirs(os.path.dirname(f"{fileBase}/"), exist_ok=True)
        copyfile(f"{fileBase}.tex", f"{fileBase}/temp.tex")
        os.remove(f"{fileBase}.tex") # poor mans `move` that works on win and linux
        check_call(['latex',  f"temp.tex"],
            stdout=DEVNULL, stderr=STDOUT, cwd=f'{fileBase}')
        check_call(['dvips',  f"temp.dvi", "-P", "pdf"],
            stdout=DEVNULL, stderr=STDOUT, cwd=f'{fileBase}')
        check_call(['ps2pdf', f"temp.ps"],
            stdout=DEVNULL, stderr=STDOUT, cwd=f'{fileBase}')
    except CalledProcessError:
        print("error")
    else:
        copyfile(f"{fileBase}/temp.pdf", f"{fileBase}.pdf")
        rmtree(f"{fileBase}/")
        if args.o:
            os.system(f'"{fileBase}.pdf"')
