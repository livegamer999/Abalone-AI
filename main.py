import socket
import json
import threading as th
import time
import random
from copy import deepcopy

Recieved=""
Recieveflag=False
name="abalone-Chan"
moves={#conversion table from direction name
        'NE': (-1,  0),
	    'NW': (-1, -1),
	    'SE': ( 1,  1),
	    'SW': ( 1,  0),
        'E': ( 0,  1),
	    'W': ( 0, -1)
    }
turn=0#turn counter for console turn id (used for debug)

directionList=('NE','NW','SE','SW','E','W')#list of different possible directions
board=[# default board setup
    ['W','W','W','W','W','X','X','X','X'], 
    ['W','W','W','W','W','W','X','X','X'], 
    ['E','E','W','W','W','E','E','X','X'], 
    ['E','E','E','E','E','E','E','E','X'], 
    ['E','E','E','E','E','E','E','E','E'], 
    ['X','E','E','E','E','E','E','E','E'], 
    ['X','X','E','E','B','B','B','E','E'], 
    ['X','X','X','B','B','B','B','B','B'], 
    ['X','X','X','X','B','B','B','B','B']
]

def connectToServ():#open connection to server
    s = socket.socket ()
    s.setblocking(1)
    s.bind(('0.0.0.0',8045))
    return s

def inscription():#giving required info to the server to register the AI
    global s
    s.connect(( socket.gethostname (), 3000))
    request=json.dumps({
   "request": "subscribe",
   "port": 8045,
   "name": name,
   "matricules":["195260"]
    })
    data = request.encode ('utf8')
    sent = s.send(data)
    s.close()
    s=connectToServ()
    if sent ==len(data):
        print("Envoi  complet")

def sendJSON(socket, obj):#source:  Qlurkin/PI2CChampionshipRunner (sends json to server)
	message = json.dumps(obj)
	if message[0] != '{':
		raise NotAJSONObject('sendJSON support only JSON Object Type')
	message = message.encode('utf8')
	total = 0
	while total < len(message):
		sent = socket.send(message[total:])
		total += sent

def receiveJSON(socket, timeout = 1):#source:  Qlurkin/PI2CChampionshipRunner (recieves json and decodes it)
	finished = False
	message = ''
	data = ''
	start = time.time()
	while not finished:
		message += socket.recv(4096).decode('utf8')
		if len(message) > 0 and message[0] != '{':
			raise NotAJSONObject('Received message is not a JSON Object')
		try:
			data = json.loads(message)
			finished = True
		except json.JSONDecodeError:
			if time.time() - start > timeout:
				break
	return data

def run(): #main function listens from connection and replies accordingly
    global s
    global turn
    s.listen()
    while True:
        client, adress = s.accept()
        data=receiveJSON(client)
        #print(data)
        if data['request']=='ping':                            # replies to ping requests
            sendJSON(client,{"response":"pong"})
        if data['request']=='play':                            #analyses the state of the game, chooses the move to play and sends the move to the server
            turn+=1
            possibleMoves=findallmoves(data['state'])          #gets all possible valid moves
            chosenMove=getbestMove(possibleMoves,data['state'])#chooses the best move
            sendJSON(client,{                                  #sends the move
                "response":"move",
                "move" : {
                    "marbles": chosenMove[0],
                    "direction": chosenMove[1]
                },
                "message":"u mad?"
            })
            print("replied: ",turn)                             #writes the turn on console for debugging

        client.close()                                          #closes the connection with the server and waits for a new one.

def sumTuple(t1,t2):                                            #adds two tuple's individual values together (1,2)+(3,4)->(4,6) works with lists too (tuple's have to have the same length)
    output=[]
    for i in range(len(t1)):
        output.append(t1[i]+t2[i])
    return tuple(output)

def getColor(pos,state):                                        #returns content of the position of the board in the given state
    x,y=pos
    if x in range(len(state["board"])) and y in range(len(state["board"][x])):
        return state["board"][x][y]
    else:                                                       #if the position is outside of the board table return "X" to signify "out of board"
        return "X"

def getPlayerColor(state,isOponent=False):                      #gets the color ("W" or "B") of the player or the opponent from the state
    if state["players"][0]==name:
        outputBool=True
    else:
        outputBool=False
    if isOponent:
        outputBool=not outputBool
    if outputBool:
        return "B"
    else:
        return "W"


def isValidMove(move,state,isOponent=False):                    #verifies the move is valid
    marbles,direction = move
    for marble in marbles:
        if getColor(marble,state)!=getPlayerColor(state,isOponent=isOponent):   #verifies all moved marbles are the player's
            return False
    if len(marbles)>3:                                          #verifies you do not move more than 3 marbles.
        return False
    pos=marbles[0]
    while getColor(pos,state)==getPlayerColor(state,isOponent=isOponent) and pos in marbles:         #moves to the first position out that isn't a part of the moved marble
        pos=sumTuple(pos,moves[direction])
    if getColor(pos,state)==getPlayerColor(state,isOponent=isOponent) and not(pos in marbles):    #if you try to push one of your own marbles without including it in the moved marbles move is invalid
        return False
    if getColor(pos,state)=="E":                                 #if there is an empty spot after your marbles you can move
        return True
    elif getColor(pos,state)=="X":                               #pushing your own marbles out of the board is suicide and should not be accepted
        return False
    elif getColor(pos,state)==getPlayerColor(state,isOponent=True^isOponent):
        count=0
        while getColor(pos,state)==getPlayerColor(state,isOponent=True^isOponent):         #counts the number of enemy marbles you'd be pushing
            count+=1
            pos=sumTuple(pos,moves[direction])
        if getColor(pos,state)!=getPlayerColor(state,isOponent=isOponent):                #verify's you don't have any of your own marbles behind enemy ones.
            return count<len(marbles)                                                     #returns true if more player marbles than ennemy marbles, false otherwise.
        else:
            return False


def findallmoves(state,isOponent=False):                        #find all possible valid moves
    validMoves=[]
    for line in range(len(state["board"])):
        for column in range(len(state["board"][line])):
            for direction in directionList:                     #tries every board position every direction
                pos=(line,column)
                move=(list(),direction)
                while getColor(pos,state)==getPlayerColor(state,isOponent=isOponent):      #groups marbles that would be pushed together
                    move[0].append(pos)
                    pos=sumTuple(pos,moves[direction])
                if len(move[0])>0:                               #if a possible move exists verify it is valid
                    if isValidMove(move,state,isOponent=isOponent):
                        validMoves.append(move)
    return validMoves

def simulateMove(move,state,isOponent=False):                   #outputs a new state that represents what the state would be after a move is applied
    newState=deepcopy(state)
    if isValidMove(move,state,isOponent=isOponent):
        marbles,direction = move
        pos=marbles[0]
        while getColor(pos,state)==getPlayerColor(state,isOponent=isOponent) and pos in marbles:     #get to the first marble out of the moved marbles
            pos=sumTuple(pos,moves[direction])
        #print(move)
        while getColor(pos,state)!="X"and getColor(pos,state)!="E":        #while there is a marble to move, move it
            x,y=pos
            newX,newY=sumTuple(pos,moves[direction])
            if newX in range(len(state["board"])) and newY in range(len(state["board"][x])) and state["board"][newX][newY]!="X": #verifies you don't place a marble on an out of board location
                newState["board"][newX][newY]=state["board"][x][y]
            pos=sumTuple(pos,moves[direction])
            #print(pos)
        for marble in marbles:                                             #remove "moved marbles" from their position
            x,y=marble
            newState["board"][x][y]="E"
        for marble in marbles:                                              #place them back at their new location.
            newX,newY=sumTuple(marble,moves[direction])
            newState["board"][newX][newY]=state["board"][x][y]
            #print(state["board"][x][y])
        return newState

def calculateScore(state):                                              #calculate the score (+1 for each marble you have,-1 for each one the opponent has)
    player=getPlayerColor(state)
    opponent=getPlayerColor(state,isOponent=True)
    score=0
    for line in range(len(state["board"])):
        for pos in state["board"][line]:
            if pos==player:
                score+=1
            elif pos==opponent:
                score-=1
    return score

def getbestMove(possibleMoves,state):                                   #simulates all valid moves, gets the scores of their result and pick the one who gives the best result.
    print(possibleMoves)
    bestMoves=[possibleMoves[0]]
    bestscore=calculateScore(simulateMove(possibleMoves[0],state))
    for move in possibleMoves:
        score=calculateScore(simulateMove(move,state))
        #print(score)
        if score>bestscore:
            bestMoves=[move]
            bestscore=score
        elif score==bestscore:
            bestMoves.append(move)
    bestMove=bestMoves[random.randint(0,len(bestMoves)-1)]
    print("move ",bestMove,"score ",bestscore, "state ",simulateMove(bestMove,state))
    return bestMove

def createMoveArborescence(state,cycles,isOponent=False):                #attempt at a recursive function for later use in minmax optimisation. works but is too slow, times out with only 2 layers(4 seconds). could work with performance optimisation
    arborescence=[]
    possibleMoves=findallmoves(state,isOponent=isOponent)
    if cycles>0:
        for move in possibleMoves:
            newState=simulateMove(move,state,isOponent=isOponent)
            arborescence.append({
                "move":move,
                "state":deepcopy(newState),
                "score":calculateScore(newState),
                "nextMoves":createMoveArborescence(deepcopy(newState),cycles-1,isOponent=not isOponent)
            })
    return arborescence





s=connectToServ()            #connect
inscription()                #register
run()               #run

