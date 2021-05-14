import socket
import json
import threading as th
import time
import random
from copy import deepcopy

Recieved=""
Recieveflag=False
name="abalone-Chan"
moves={
        'NE': (-1,  0),
	    'NW': (-1, -1),
	    'SE': ( 1,  1),
	    'SW': ( 1,  0),
        'E': ( 0,  1),
	    'W': ( 0, -1)
    }
turn=0

directionList=('NE','NW','SE','SW','E','W')
board=[
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

def connectToServ():
    s = socket.socket ()
    s.setblocking(1)
    s.bind(('0.0.0.0',8045))
    return s

def pingServ(s):
    request=json.dumps({
   "request": "ping"
    })
    data = request.encode ('utf8')
    sent = s.send(data)
    if sent ==len(data):
        print("Envoi  complet")
    data = s.recv(512).decode ()
    print('Reçu',len(data), 'octets :')
    print(data)

def inscription():
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

def sendJSON(socket, obj):#source:  Qlurkin/PI2CChampionshipRunner
	message = json.dumps(obj)
	if message[0] != '{':
		raise NotAJSONObject('sendJSON support only JSON Object Type')
	message = message.encode('utf8')
	total = 0
	while total < len(message):
		sent = socket.send(message[total:])
		total += sent

def receiveJSON(socket, timeout = 1):#source:  Qlurkin/PI2CChampionshipRunner
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

def asyncRecieve():
    global s
    global turn
    s.listen()
    while True:
        client, adress = s.accept()
        data=receiveJSON(client)
        print(data)
        if data['request']=='ping':
            sendJSON(client,{"response":"pong"})
        if data['request']=='play':
            turn+=1
            possibleMoves=findallmoves(data['state'])
            chosenMove=possibleMoves[random.randint(0,len(possibleMoves)-1)]
            sendJSON(client,{
                "response":"move",
                "move" : {
                    "marbles": chosenMove[0],
                    "direction": chosenMove[1]
                },
                "message":"lololo"
            })
            print("replied: ",turn)

        client.close()

def sumTuple(t1,t2):
    output=[]
    for i in range(len(t1)):
        output.append(t1[i]+t2[i])
    return tuple(output)

def getColor(pos,state):
    x,y=pos
    if x in range(len(state["board"])) and y in range(len(state["board"][x])):
        return state["board"][x][y]
    else:
        return "X"

def getPlayerColor(state,isOponent=False):
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


def isValidMove(move,state,isOponent=False):
    marbles,direction = move
    for marble in marbles:
        if getColor(marble,state)!=getPlayerColor(state,isOponent=isOponent):
            return False
    pos=marbles[0]
    while getColor(pos,state)==getPlayerColor(state,isOponent=isOponent) and pos in marbles:
        pos=sumTuple(pos,moves[direction])
    if getColor(pos,state)==getPlayerColor(state,isOponent=isOponent) and not(pos in marbles):
        return False
    if getColor(pos,state)=="E":
        return True
    elif getColor(pos,state)=="X":
        return False
    elif getColor(pos,state)==getPlayerColor(state,isOponent=True^isOponent):
        count=0
        while getColor(pos,state)==getPlayerColor(state,isOponent=True^isOponent):
            count+=1
            pos=sumTuple(pos,moves[direction])
        if getColor(pos,state)!=getPlayerColor(state,isOponent=isOponent):
            return count<len(marbles) #returns true if more player marbles than ennemy marbles, false otherwise.
        else:
            return False


def findallmoves(state,isOponent=False):
    validMoves=[]
    for line in range(len(state["board"])):
        for column in range(len(state["board"][line])):
            for direction in directionList:
                pos=(line,column)
                move=(list(),direction)
                while getColor(pos,state)==getPlayerColor(state,isOponent=isOponent):
                    move[0].append(pos)
                    pos=sumTuple(pos,moves[direction])
                if len(move[0])>0:
                    if isValidMove(move,state,isOponent=isOponent):
                        validMoves.append(move)
    return validMoves

def simulateMove(move,state,isOponent=False):
    newState=deepcopy(state)
    if isValidMove(move,state,isOponent=isOponent):
        marbles,direction = move
        pos=marbles[0]
        while getColor(pos,state)==getPlayerColor(state,isOponent=isOponent) and pos in marbles:
            pos=sumTuple(pos,moves[direction])
        print(move)
        while getColor(pos,state)!="X"and getColor(pos,state)!="E":
            x,y=pos
            newX,newY=sumTuple(pos,moves[direction])
            if newX in range(len(state["board"])) and newY in range(len(state["board"][x])):
                newState["board"][newX][newY]=state["board"][x][y]
            pos=sumTuple(pos,moves[direction])
            #print(pos)
        for marble in marbles:
            x,y=marble
            newX,newY=sumTuple(marble,moves[direction])
            newState["board"][x][y]="E"
            newState["board"][newX][newY]=state["board"][x][y]
            print(state["board"][x][y])
        return newState





s=connectToServ()
inscription()
asyncRecieve()

