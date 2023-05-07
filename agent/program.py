# COMP30024 Artificial Intelligence, Semester 1 2023
# Project Part B: Game Playing Agent

from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir
from datetime import datetime, timedelta
from math import sqrt, log

# This is the entry point for your game playing agent. Currently the agent
# simply spawns a token at the centre of the board if playing as RED, and
# spreads a token at the centre of the board if playing as BLUE. This is
# intended to serve as an example of how to use the referee API -- obviously
# this is not a valid strategy for actually playing the game!

class Agent:
    def __init__(self, color: PlayerColor, **referee: dict):
        """
        Initialise the agent.
        """

        #Note to self: red starts first always
        self._color = color

        self.time = referee["time_remaining"]

        #we will set up a list with all the cells
        #following project part a, the format for the list
        #will be [coords] : [colour, power] of the cell
        self.boardstate = {}

        match color:
            case PlayerColor.RED:
                print("Testing: I am playing as red")
            case PlayerColor.BLUE:
                print("Testing: I am playing as blue")

    def action(self, **referee: dict) -> Action:
        """
        Return the next action to take.
        """

        #first move starting 1st (as red)
        if len(self.boardstate) == 0:
            return SpawnAction(HexPos(3, 3))
        
        #first move starting 2nd (as blue)
        if (len(self.boardstate) == 1):
            if (self.boardstate.values[0][1] == 1):
                
                pos = self.boardstate.keys[0].__add__(HexDir.DownRight)
                pos = pos.__add__(HexDir.DownRight)
                return SpawnAction(HexPos(pos))

        else:
            print("MCTS")
            MCTS(self.boardstate, self)

        #match self._color:
        #    case PlayerColor.RED:
        #        return SpawnAction(HexPos(3, 3))
        #    case PlayerColor.BLUE:
        #        # This is going to be invalid... BLUE never spawned!
        #        return SpreadAction(HexPos(3, 3), HexDir.Up)
            
            

    def turn(self, color: PlayerColor, action: Action, **referee: dict):
        """
        Update the agent with the last player's action.
        """
        match action:
            case SpawnAction(cell):
                print(f"Testing: {color} SPAWN at {cell}")
                
                #just add the cell into the list
                self.boardstate[cell] = [color, 1]
                pass

            case SpreadAction(cell, direction):
                print(f"Testing: {color} SPREAD from {cell}, {direction}")

                #add power and change colour if necessary if cell is already
                #infected, otherwise add the cell
                currCellPower = self.boardstate[cell]

                newCellPos = cell
                for i in range(0, currCellPower):
                    
                    newCellPos.__add__(direction)
                    
                    #if new Pos has no cell, add one
                    if self.boardstate[newCellPos] == None:

                        self.boardstate[newCellPos] = [color, 1]
                    else:
                        temp = self.boardstate[newCellPos]
                        temp[0] = color
                        temp[1] += 1
                        self.boardstate[newCellPos] = temp    

                pass
    
#we shall use this program to set up data structures necessary for 
#an implementation of the Monte Carlo Tree Search (MCTS)

from agent.program import Agent

#structure for a singular node in the MCTS tree
class Node:

    def __init__(self, player: int, boardstate: dict, depth: int, parentNode = None,):
        
        #which player is making the move, to simulate best/worse outcomes
        #0 will be us, 1 will simulate the opp player
        self.player = player

        #the list of child nodes that spawn from the current node
        self.childNodes = []

        #parent node of the current node
        self.parentNode = parentNode

        self.totalGames = 0
        self.wonGames = 0
        self.simulated = False

        self.boardstate = boardstate

        self.depth = depth
        self.lastmove = None
        
    #function will append a childnode to the list of child nodes
    def addChildNode(self, childNode):

        self.childNodes.append(childNode)

    #function to back propagate scores after simulation
    def backPropagateWin(self, player: int):

        currNode = self

        while (currNode != None):
            
            if (currNode.player == player):

                currNode.totalGames += 1
                currNode.wonGames += 1

            else:

                currNode.totalGames += 1

            currNode = currNode.parentNode

#function for performing Monte Carlo Tree Search, will return the optimal move derived
#from said search
def MCTS(boardstate: dict, agent: Agent) -> list:

    #for this, we will allocate 5% of the remaining time for the algorithm to run??
    #may be changed
    #inspired by chess players, who spend more time thinking in the initial stages
    #of the game as there are more moves available
    now = datetime.now()
    timeRemaining = agent.time/20
    limit = now + timedelta(seconds=timeRemaining)
    
    #player colour to be adjusted
    rootNode = Node(0, boardstate, 0)
    
    while (datetime.now() < limit):
        
        currNode = rootNode
        #perform MCTS
        #selecting a leaf node, if not at leaf node, traverse down
        while (len(currNode.childNodes) != 0):
                
                #using UCB1 to select the best nodes amongst the child nodes
                bestChild = None
                bestVal = -1

                for child in currNode.childNodes:

                    currVal = calcUCB1(child)

                    #if node has never been simulated, simulate it immediately
                    #and forgo selection of best node
                    if (currVal == -1):
                        currNode = bestChild
                        break
                    
                    #else we compare to find best node to expand
                    if currVal > bestVal:
                        bestVal = currVal
                        bestChild = child

                currNode = bestChild        

        #now at leaf node, we simulate if no simulation done yet
        if (currNode.totalGames == 0 and currNode.depth != 0):
            
            score = simulateNode(currNode, agent._color, agent)
            
            currPlayer = currNode.player
            backPropagate(currNode, currPlayer, score)

        #simulated, but no children
        if (len(currNode.childNodes) == 0):

            #create the child nodes
            createChildNodes(currNode, agent)

    #after time has run out, return the best move
    print("returning best move")
    return findBestMove(rootNode)

#function used to calculateUCB1 value
def calcUCB1(childNode: Node) -> float:

    if (childNode.totalGames == 0):
        return -1

    x = float(childNode.wonGames/childNode.totalGames)
    #constant 2 here may change depending on exploration etc.
    y = 2 * sqrt(log(childNode.parentNode.totalGames)/(childNode.totalGames))

    return (x + y)

#function will be used to simulate the Nodes all the way to the goal state
#in this particularly case we limit it to a max of 30 moves for time
def simulateNode(currNode: Node, color: PlayerColor, agent: Agent) -> int:

    moves = 0
    #make a copy of the boardstate that we will manipulate
    simulatedBoardstate = currNode.boardstate.copy()

    while (moves < 30):
        
        #add heurisitc for moving here
        ??
        if ((moves % 2) == 0):
            moveHeuristic(simulatedBoardstate, agent)
        else:
            moveHeuristic(simulatedBoardstate, agent)

        moves+= 1

    currNode.simulated = True    

    #win condition: since it is unlikely we can simulate until an end goal
    #is achieved, after 15 moves from each side, we count the number of points from
    #both ends and the side with more points shall be considered the "winner"
    numOwnCells = 0
    numOppCells = 0

    for cell in simulatedBoardstate.values():

        if cell[0] == color:
            numOwnCells += cell[1]
        else:
            numOppCells += cell[1]   

    #should return 1 if won, 0 if lost
        if numOwnCells > numOppCells:
            return 1
        else:
            return 0

#function will back propagate the results, adding 1 to total games 
#and additionally adding 1 to the GamesWon of the player who "played"
#the current node
def backPropagate(childNode: Node, player: int, score: int):

    currNode = childNode
    
    while (currNode != None):
        currNode.totalGames += 1
        
        #owner player won, add 1 to all his nodes
        if (score == 1):
            if (currNode.player == player):
                currNode.wonGames += 1

        #owner player lost, add 1 to all opp nodes
        else:
            if (currNode.player != player):
                currNode.wonGames += 1    

        currNode = currNode.parentNode

    return

#function will be the heuristic used to determine moves
#for simulation of the node during MCTS
def moveHeuristic(boardstate: dict, agent: Agent):

    #due to the nature of the infinite board, the first move
    #of spawning can go anywhere, so 
    if len(boardstate) == 0:
        return SpawnAction(HexPos(3, 3))
    
    else:

        dangerCells = []

        for cell in boardstate.items():
            if cell[1][0] == agent._color:

                safe = isSafe(boardstate, cell, agent)
                if (safe >= 0):
                    dangerCells.append(cell[0])

        #check the dangercells list
        if (len(dangerCells) != 0):
            #reinforce the cells
            for cellPos in dangerCells:
                
                #look for a safe position to insert a friendly cell, so as to
                #increase trading potential between cells in the area
                for dir in HexDir:
                    newPos = cellPos.__add__(dir)
                    if (boardstate.get(newPos) == None):
                        if (isSafe(boardstate, newPos, agent) == 1):
                            return SpawnAction(newPos)

                #assuming no safe spots were found to spawn additional cell
                #attempt to see if we can spread to opp cell without losing value

                for dir in HexDir:
                    newPos = cellPos.__add__(dir)
                    if (boardstate.get(newPos) != None):
                        if (boardstate.get(newPos) != agent._color):
                            if (isSafe(boardstate, newPos, agent) >= 1):
                                SpreadAction(cellPos, dir)

                #couldnt spread aggressively, couldnt spawn, try spread defensively
                for dir in HexDir:
                    newPos = cellPos.__add__(dir)
                    if (boardstate.get(newPos) != None):
                        if (boardstate.get(newPos) == agent._color):
                            if (isSafe(boardstate, newPos, agent) >= 1):
                                SpreadAction(cellPos, dir)
        
        #no cells in danger, we can play aggressively
        #attempt to attack other opp cells that are free
        for cell in boardstate.items():
            if cell[1][0] == agent._color:
                for dir in HexDir:
                    newPos = cell[0]
                    newPos = newPos.__add__(dir)
                    if (boardstate.get(newPos) != None):
                        if (boardstate.get(newPos)[1][0] != agent._color):
                            if (isSafe(boardstate, newPos, agent) >= 1):
                                return SpreadAction(cell[1][0], dir)

        #no cells in danger, not position to attack
        #reinforce own position
        for cell in boardstate.items():
            if cell[1][0] == agent._color:
                for dir in HexDir:
                    newPos = cell[0]
                    newPos = newPos.__add__(dir)
                    if (boardstate.get(newPos) == None):
                        if (isSafe(boardstate, newPos, agent) >= 0):
                            return SpawnAction(newPos)
                        
        #assuming we gone through all protocols and there are no good moves to do
        #aka we are solemnly screwed, perform random move?? (i hope it never comes to this)
        return SpreadAction(cellPos, HexDir.DownRight)                    
    

#function will handle the logic of branching the leaf nodes
#for MCTS
def createChildNodes(currNode: Node, agent: Agent):

    for cell in currNode.boardstate.items():

        cellColor = cell[1][0]
        cellPower = cell[1][1]
        #note to self: cellCoord is a HexPos
        cellCoord = cell[0]

        #if the cell is ours, we create child nodes by either
        #spreading from any given cell, or spawining cells around
        #existing cells
        if (cellColor == agent._color):
            
            for dir in HexDir:
                
                #spread action
                newBoardstate = currNode.boardstate.copy()

                for power in range(0, cellPower):
                    
                    cellCoord = cellCoord.__add__(dir)          

                    #if existing cell is in place, overwrite it and +1 to the existing power,
                    #otherwise create a new cell in the spot
                    if (newBoardstate.get(cellCoord) == None):
                        newBoardstate[cellCoord] = (cellColor, 1)
                    else:
                        newPower = newBoardstate.get(cellCoord)[1] + 1
                        newBoardstate[cellCoord] = (cellColor, newPower)    

                #deleting original expended cell
                newBoardstate.pop(cellCoord)    
                lastMove = SpreadAction(cellCoord, dir)

                newNode = Node(1, newBoardstate, (currNode.depth+1), currNode)
                newNode.lastmove = lastMove
                currNode.addChildNode(newNode)

            #spawn action, we spawn in the cells to areas around our existing cells
            #cluster together to maintain easier trading
            for dir in HexDir:

                newBoardstate = currNode.boardstate.copy()

                cellCoord = cell[0]
                cellCoord = cellCoord.__add__(dir)

                if (newBoardstate.get(cellCoord) == None):
                    newBoardstate[cellCoord] = (cellColor, 1)

                    newNode = Node(1, newBoardstate, (currNode.depth+1), currNode)
                    newNode.lastmove = SpawnAction(cellCoord)
                    currNode.addChildNode(newNode)
                

#function will check whether a cell is safe, by comparing number of opponent
#cells around itself compared to number of friendly cells. Will >= 0 if safe
#and <= -1 if not safe
def isSafe(boardstate: dict, pos: HexPos, agent: Agent) -> int:

    newPos = pos
    closeOppCells = 0
    closeOwnCells = 0

    for dir in HexDir:
        newPos.__add__(dir)
        if (boardstate.get(newPos) != None):
            if (boardstate.get(newPos)[1][0] == agent._color):
                closeOwnCells += 1
            else:
                closeOppCells += 1

    return closeOwnCells - closeOppCells          

def findBestMove(root: Node):

    bestChild = None
    bestWinRate = -1
    for child in root.childNodes:

        currWinRate = float(child.totalGames/child.wonGames)
        if (currWinRate > bestWinRate):
            bestWinRate = currWinRate
            bestChild = child

    return bestChild.lastmove    
