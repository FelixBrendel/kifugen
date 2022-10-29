import itertools
from pprint import pprint

blackMoves = []
whiteMoves = []
boardSize = 19

board = []
blackGroups = []
whiteGroups = []

def lastIndex(list, item):
    finalIndex = -1
    try:
        while True:
            finalIndex = list.index(item, finalIndex+1)
    except ValueError:
        if finalIndex == -1:
            raise ValueError
        else:
            return finalIndex


def get_neighbouring_coordinates(point):
    neighbours = []
    potentialNeighbours = [
        (point[0]-1,point[1]),
        (point[0]+1,point[1]),
        (point[0],point[1]-1),
        (point[0],point[1]+1)
    ]

    for point in potentialNeighbours:
        if 1 <= point[0] <= 19 and 1 <= point[1] <= 19:
            neighbours.append(point)

    return neighbours

def get_neighbouring_groups(position, color):
    groups = whiteGroups if color == "w" else blackGroups

    neighbouringGroups = set()
    neighbours = get_neighbouring_coordinates(position)

    for point in neighbours:
        for index, group in enumerate(groups):
            if point in group:
                neighbouringGroups.add(index)

    return list(neighbouringGroups)


def get_liberties(group):
    ret = set()
    for point in group:
        neighbours = get_neighbouring_coordinates(point)
        for neighbour in neighbours:
            if board[neighbour[0]-1][neighbour[1]-1] == "":
                ret.add(neighbour)
    return ret


def remove_dead_groups(color):
    bothGroups = []

    # get the order right so that black can kill a white
    # group by playing into whites only eye (and not killing himself first)
    if color == "w":
        bothGroups = whiteGroups + blackGroups
    else:
        bothGroups = blackGroups + whiteGroups

    # remove dead from board
    for group in bothGroups:
        if len(get_liberties(group)) == 0:
            for pos in group:
                board[pos[0]-1][pos[1]-1] = ""

    # remove dead from groups lists
    whiteGroups[:] = [ group for group in whiteGroups if len(get_liberties(group)) != 0 ]
    blackGroups[:] = [ group for group in blackGroups if len(get_liberties(group)) != 0 ]

def play_move(color, move):
    playerGroups = whiteGroups if color == "w" else blackGroups

    neighbouringGroups = get_neighbouring_groups(move, color)

    # no neighbouring groups make new one
    if len(neighbouringGroups) == 0:
        playerGroups.append([(move[0], move[1])])
    else:
        # we want to merge everything into the first group and then pop the others in
        # reverse index order so no indecies are getting wrong
        neighbouringGroups.sort()
        neighbouringGroups[1:] = neighbouringGroups[1:][::-1]

        # 1 or more neighbouring groups -> extend first one
        playerGroups[neighbouringGroups[0]].append((move[0], move[1]))

        # if also more than one group -> merge with others
        for i, group in enumerate(neighbouringGroups[1:]):
            playerGroups[neighbouringGroups[0]].extend(playerGroups.pop(group))

    board[move[0]-1][move[1]-1] = color
    remove_dead_groups("w" if color == "b" else "b")


def simulate_board_up_to(lastMoveNumber):
    global board
    global whiteGroups
    global blackGroups

    # reset board and groups
    blackGroups = []
    whiteGroups = []
    board = [ [ "" for i in range(boardSize) ] for y in range(boardSize) ]
    moveSequence = [ j for i in itertools.zip_longest(blackMoves,whiteMoves) for j in i ]

    for i in range(len(blackMoves) + len(whiteMoves)):
        if i == lastMoveNumber:
            break

        # blacks turn
        if i % 2 == 0:
            if len(blackMoves) == 0: continue
            play_move("b", blackMoves[i//2])
        else:
            if len(whiteMoves) == 0: continue
            play_move("w", whiteMoves[i//2])


def show_board():
    print(" "*3 + "A B C D E F G H J K L M N O P Q R S T")
    i = 0
    for y in range(boardSize):
        i += 1
        if boardSize-i+1 < 10:
            print(f" {boardSize-i+1}", end="")
        else:
            print(f"{boardSize-i+1}", end="")

        for x in range(boardSize):
            if board[x][boardSize-y-1] == "":
                print(" .", end="")
            else:
                print(" " + board[x][boardSize-y-1], end ="")

        print(f" {boardSize-i+1}")
    print(" "*3 + "A B C D E F G H J K L M N O P Q R S T")

def get_latex_at_move(fromMove):
    latexList = []

    simulate_board_up_to(fromMove)
    # just dumping the baord, nothing special
    for y in range(len(board)):
        for x in range(len(board)):
            if board[x][y] != "":
                color = "white" if board[x][y] == "w" else "black"
                if ord("a")+x < ord("i"):
                    firstCoordinate = chr(ord("a")+x)
                else:
                    firstCoordinate = chr(ord("a")+x+1)
                latexList.append(f"\\stone{{{color}}}{{{firstCoordinate}}}{{{y+1}}}\n")

    return latexList

def produce_latex(fromMove, toMove, continousCounting):
    # old moves
    latexList = ["\\begin{psgoboard}\n\t"]
    latexList.extend(get_latex_at_move(fromMove))

    playedMoves = []
    removedMoves = []
    removedMoveIndices = []

    finished = False
    moveCount = 1
    if continousCounting:
        moveCount = fromMove + 1

    # new moves
    for i in range(fromMove, len(blackMoves) + len(whiteMoves)):
        if i == toMove: break
        moves = []
        color = ""

        if i % 2 == 0: # blacks turn
            moves = blackMoves
            color = "black"
        else: # whites turn
            moves = whiteMoves
            color = "white"

        # if this player has no moves left -> continue
        if len(moves) == 0: continue

        x, y = moves[i//2]

        if (x, y) in playedMoves:
            removedMoves.append((x,y))
            removedMoveIndices.append(1+lastIndex(playedMoves, (x,y)))

        playedMoves.append((x,y))

        # skip the 'i' coordinate
        if ord("a")+x-1 < ord("i"):
            firstCoordinate = chr(ord("a")+x-1)
        else:
            firstCoordinate = chr(ord("a")+x)

        latexList.append(f"\\stone[\\marklb{{{moveCount}}}]{{{color}}}{{{firstCoordinate}}}{{{y}}}")
        moveCount += 1

    else:
        # played the last move
        finished = True

    latexList.append("\n\\end{psgoboard}\n")
    # Add text for moves that have been replaced
    if len(removedMoves) > 0:
        latexList.append("\n")
        for (idx, move) in zip(removedMoveIndices, removedMoves):
            if idx % 2 == 0:
                replacedstone = f"\\stone[{{{idx}}}]{{white}}"
            else:
                replacedstone = f"\\stone[{{{idx}}}]{{black}}"

            finalLabel = 1+lastIndex(playedMoves, move)
            if finalLabel % 2 == 0:
                finalstone = f"\\stone[{{{finalLabel}}}]{{white}}"
            else:
                finalstone = f"\\stone[{{{finalLabel}}}]{{black}}"

            latexList.append(f"{replacedstone} at {finalstone}\,,\,")

        latexList.append("\n")

    return latexList, finished


if __name__ == '__main__':
    blackMoves.append((4,4))
    whiteMoves.append((4,3))
    blackMoves.append((5,3))
    whiteMoves.append((5,4))
    blackMoves.append((3,3))
    whiteMoves.append((3,4))
    blackMoves.append((4,2))
    whiteMoves.append((4,5))
    blackMoves.append((10,10))
    whiteMoves.append((4,3))
    blackMoves.append((4,4))
    whiteMoves.append((4,3))

    produce_latex(7, 200)
    show_board()
