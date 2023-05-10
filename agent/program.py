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
        self.oppColour = color.opponent

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
            pos = list(self.boardstate.keys())[0]

            pos = pos.__add__(HexDir.DownRight)
            pos = pos.__add__(HexDir.DownRight)
            return SpawnAction(pos)

        else:
            print("MCTS")
            return MCTS(self.boardstate, self)         

    def turn(self, color: PlayerColor, action: Action, **referee: dict):
        """
        Update the agent with the last player's action.
        """
        match action:
            case SpawnAction(cell):
                print(f"Testing: {color} SPAWN at {cell}")
                
                #just add the cell into the list
                self.boardstate[cell] = [color, 1]

            case SpreadAction(cell, direction):
                print(f"Testing: {color} SPREAD from {cell}, {direction}")

                #add power and change colour if necessary if cell is already
                #infected, otherwise add the cell
                currCellPower = self.boardstate[cell][1]

                newCellPos = cell
                for i in range(0, currCellPower):
                    
                    newCellPos = newCellPos.__add__(direction)
                    
                    #if new Pos has no cell, add one
                    if self.boardstate.get(newCellPos) == None:
                        self.boardstate[newCellPos] = [color, 1]

                    #cell alr exists there
                    else:
                        oldPower = self.boardstate[newCellPos][1]
                        self.boardstate[newCellPos] = [color, oldPower+1]
                        #remove if pow greater than 7
                        if self.boardstate[newCellPos][1] >= 7:
                            self.boardstate.pop(newCellPos)

                #remove old (spreaded) cell
                self.boardstate.pop(cell)
    
#we shall use this program to set up data structures necessary for 
#an implementation of the Monte Carlo Tree Search (MCTS)

from .program import Agent

#structure for a singular node in the MCTS tree
class Node:

    def __init__(self, colour: PlayerColor, boardstate: dict, depth: int, parentNode = None,):
        
        #which player owns this node, aka the player who will make the next move
        #for this purpose, we shall always own the root, then the next layer will be
        #owned by the opp, then following layer by us etc.
        self.colour = colour

        #the list of child nodes that spawn from the current node
        self.childNodes = []
        self.parentNode = parentNode

        self.totalCells = 0
        self.ourCells = 0

        self.boardstate = boardstate

        #?? may be used if needed to limit the depth of the search
        self.depth = depth

        #lastmove, to return the move if chosen as the best action
        self.lastmove = None
        
    #function will append a childnode to the list of child nodes
    def addChildNode(self, childNode):

        self.childNodes.append(childNode)

    #function to back propagate scores after simulation
    def backPropagate(self, won: bool, agent: Agent):

        currNode = self

        while (currNode != None):
            currNode.totalCells += 1

            #seems counterintuitive, but the node that holds the UCB1 Score
            #is the node with the opposing colour
            if (won == True):
                if (currNode.colour != agent._color):
                    currNode.ourCells += 1
            elif (won == False):
                if (currNode.colour == agent._color):
                    currNode.ourCells += 1        

            currNode = currNode.parentNode

    #new propagate we will use, produces better results than previous
    #this function calculates the winlost ratio and applies to all nodes
    #we do not worry about which node belongs to which player
    #also changed the style instead of win or loss, to total cell number, better
    #reflecting the advantages we hold
    def backPropagate2(self, cellNum: list, agent: Agent):

        currNode = self
        while (currNode!= None):
            currNode.totalCells += cellNum[1]
            currNode.ourCells += cellNum[0]

            currNode = currNode.parentNode                  

#function for performing Monte Carlo Tree Search, will return the optimal move derived
#from said search
def MCTS(boardstate: dict, agent: Agent) -> list:

    #to allow maximum time for the maximum number of moves, we allocate each move 1 second
    #initial we allowed for longer time periods but realised our program ran out of time often
    now = datetime.now()
    limit = now + timedelta(seconds=1)

    #root node shall be our given boardstate, and from there we simulate
    #possible next moves
    rootNode = Node(agent._color, boardstate, 0)
    
    while (datetime.now() < limit):
        
        #reset to the top of the tree
        currNode = rootNode 
        
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
                        bestChild = child
                        break
                    
                    #else we compare to find best node to expand
                    elif currVal > bestVal:
                        bestVal = currVal
                        bestChild = child

                currNode = bestChild

        #now at leaf node, we simulate if no simulation done yet
        #currNode.depth !=0 is to ensure we do not simulate the root node
        if (currNode.totalCells == 0 and currNode.depth != 0):
            
            #if its an even number layer node, our node, 
            #else if odd number layer node, opp node
            if (currNode.depth % 2 == 0):
                cellNum = simulateNode(currNode, agent, agent._color)
            else:
                cellNum = simulateNode(currNode, agent, agent._color.opponent)

            currNode.backPropagate2(cellNum, agent)
            continue

        #we are at simulated node/root, but no children yet
        if (len(currNode.childNodes) == 0):

            #check whether we have reached an end state, if we have we stop further simulations
            #aka do not create child nodes
            if (ongoing(currNode.boardstate) == True):

                #create the child nodes
                createChildNodes(currNode, agent, currNode.colour)

    #after time has run out, return the best move
    print("returning best move")
    return findBestMove(rootNode)

#function used to calculateUCB1 value
def calcUCB1(childNode: Node) -> float:

    if (childNode.totalCells == 0):
        #return value beyond the possible score, to ensure that
        #we do not mix it up with the actual possible UCB1 value
        return -1

    x = float(childNode.ourCells/childNode.totalCells)
    #constant 2 here may change depending on exploration etc.
    y = 2 * sqrt(log(childNode.parentNode.totalCells)/(childNode.totalCells))

    return (x + y)          


#function will be used to simulate the Nodes all the way to the goal state
#in this particularly case we limit it to a max of 30 moves for time
def simulateNode(currNode: Node, agent: Agent, startPlayer: PlayerColor) -> int:

    moves = 0
    #make a copy of the boardstate that we will manipulate
    simulatedBoardstate = currNode.boardstate.copy()

    #if it is ourNode, we start by simulating our colour
    #else we simulate starting using opp color
    while (moves < 30):
        
        #if we have reached an end state
        if (ongoing(simulatedBoardstate) == False):
            break
        
        #heuristic for simulation, taking turns for both us and opp to make moves
        if ((moves % 2) == 0):
            move = moveHeuristic(simulatedBoardstate, agent, startPlayer)
            updateSimulationBoard(simulatedBoardstate, move, startPlayer)
        else:
            move = moveHeuristic(simulatedBoardstate, agent, startPlayer.opponent)
            updateSimulationBoard(simulatedBoardstate, move, startPlayer.opponent)

        moves+= 1

    #win condition: since it is unlikely we can simulate until an end goal
    #is achieved, after 15 moves from each side, we count the number of cells
    #from both ends, and return our cells, alongside the total number of cells,
    #using them as a spectrum for how much advantage we hold
    numOwnCells = 0
    numOppCells = 0

    for cell in simulatedBoardstate.values():

        if cell[0] == agent._color:
            numOwnCells += cell[1]
        else:
            numOppCells += cell[1]   

    return [numOwnCells, (numOwnCells + numOppCells)]        

#function will be the heuristic used to determine moves
#for simulation of the node during MCTS
def moveHeuristic(boardstate: dict, agent: Agent, currPlayer: PlayerColor) -> Action:


    #first we shall check defensively, to see if we need to protect our own cells
    #if not then we can make more aggressive moves
    dangerCells = []

    for cell in boardstate.items():

        if cell[1][0] == currPlayer:

            safe = isSafe(boardstate, cell[0], currPlayer)
            if (safe < 0):
                dangerCells.append(cell[0])

    #check the dangercells list
    if (len(dangerCells) != 0):
         
        #try to get our cells out of danger, by attempting a variety
        #of moves
        for cellPos in dangerCells:

            #attempt to see if we can spread to opp cell without losing value
            for dir in HexDir:
                newPos = cellPos.__add__(dir)
                if (boardstate.get(newPos) != None):
                    if (boardstate.get(newPos) != currPlayer):

                        if (isSafe(boardstate, newPos, currPlayer) >= 1):
                            return SpreadAction(cellPos, dir)
                        
            #assuming we could not attack to improve our position               
            #look for a safe position to insert a friendly cell, so as to
            #increase trading potential between cells in the area
            for dir in HexDir:
                newPos = cellPos.__add__(dir)
                if (boardstate.get(newPos) == None):
                    if (isSafe(boardstate, newPos, currPlayer) >= 0):
                        return SpawnAction(newPos)

            #couldnt spread aggressively, couldnt spawn, try spread defensively
            #attempt to spread the cell to a friendly cell
            for dir in HexDir:
                newPos = cellPos.__add__(dir)
                if (boardstate.get(newPos) != None):
                    if (boardstate.get(newPos) == currPlayer):
                            
                        if (isSafe(boardstate, newPos, currPlayer) >= 1):
                            return SpreadAction(cellPos, dir)    
        
    #no cells in danger, we can play aggressively
    #attempt to attack other opp cells that are free

    #sort the board so that we attempt to spread the higher power first
    sortedBoard = list(boardstate.items())
    sortedBoard.sort(key=lambda x: x[1][1], reverse=True)

    for cell in sortedBoard:
        if cell[1][0] == currPlayer:
            for dir in HexDir:
                newPos = cell[0]
                for i in range(0,cell[1][1]):
                    newPos = newPos.__add__(dir)
                    if (boardstate.get(newPos) != None):
                        if (boardstate.get(newPos)[0] != currPlayer):
                            if (isSafe(boardstate, newPos, currPlayer) >= 1):
                                return SpreadAction(cell[0], dir)

    #attempt to accumulate our cells into a singular cell
    #to allow our cells more range when spreading
    #firstly, find cell with the highest power, and accumulate more power to it
    biggestCellPos = None
    biggestPow = 0
    for cell in boardstate.items():
        if cell[1][0] == currPlayer:
            if (cell[1][1] > biggestPow and (cell[1][1] != 6)):
                biggestCellPos = cell[0]
                biggestPow = cell[1][1]

    #check for a nearby cell that we can stack onto it
    for dir in HexDir:
        if (biggestCellPos == None):
            break
        smallerCellPos = biggestCellPos.__add__(dir)
        if boardstate.get(smallerCellPos) != None:
            if (boardstate[smallerCellPos][0] == currPlayer 
                and (biggestPow + boardstate[smallerCellPos][1] < 7)):
                
                return SpreadAction(smallerCellPos, dir.__neg__())
            

    #no cells in danger, not position to attack
    #reinforce own position
    for cell in boardstate.items():
        if cell[1][0] == currPlayer:
            for dir in HexDir:
                newPos = cell[0]
                newPos = newPos.__add__(dir)
                if (boardstate.get(newPos) == None):
                    if (isSafe(boardstate, newPos, currPlayer) >= 0):
                        return SpawnAction(newPos)
                        
    #assuming we gone through all protocols and there are no good moves to do
    #aka we are solemnly screwed, perform random move?? (i hope it never comes to this)
    for cell in boardstate.items():
        if cell[1][0] == currPlayer:
            return SpreadAction(cell[0], HexDir.DownRight)                    
    
def updateSimulationBoard(simulatedBoard: dict, move: Action, currPlayer: PlayerColor):

    if (type(move) == SpreadAction):
        
        currPower = simulatedBoard[move.cell][1]
        newCellPos = move.cell
        for i in range(0, currPower):
            newCellPos = newCellPos.__add__(move.direction)
            if simulatedBoard.get(newCellPos) == None:
                simulatedBoard[newCellPos] = [currPlayer, 1]
            else:
                oldPower = simulatedBoard[newCellPos][1]
                simulatedBoard[newCellPos] = [currPlayer, oldPower+1]
                if simulatedBoard[newCellPos][1] >= 7:
                    simulatedBoard.pop(newCellPos)    

    if (type(move) == SpawnAction):
        simulatedBoard[move.cell] = [currPlayer, 1]     


#function will handle the logic of branching the leaf nodes
#for MCTS
def createChildNodes(currNode: Node, agent: Agent, currPlayer: PlayerColor):

    totalCellPower = 0
    for cell in currNode.boardstate.items():
        totalCellPower += cell[1][1]

    for cell in currNode.boardstate.items():

        cellColor = cell[1][0]
        cellPower = cell[1][1]
        #note to self: cellCoord is a HexPos
        cellCoord = cell[0]

        #if the cell is ours, we create child nodes by either
        #spreading from any given cell, or spawining cells around
        #existing cells
        if (cellColor == currPlayer):
            
            for dir in HexDir:
                
                #spread action
                newBoardstate = currNode.boardstate.copy()

                for power in range(0, cellPower):
                    
                    spreadCoord = cellCoord.__add__(dir)          

                    #if existing cell is in place, overwrite it and +1 to the existing power,
                    #otherwise create a new cell in the spot
                    if (newBoardstate.get(spreadCoord) == None):
                        newBoardstate[spreadCoord] = (cellColor, 1)
                    else:
                        newPower = newBoardstate.get(spreadCoord)[1] + 1
                        newBoardstate[spreadCoord] = (cellColor, newPower)    

                #deleting original expended cell
                newBoardstate.pop(cellCoord)    
                lastmove = SpreadAction(cellCoord, dir)

                newNode = Node(currPlayer.opponent, newBoardstate, (currNode.depth+1), currNode)
                newNode.lastmove = lastmove
                currNode.addChildNode(newNode)

            #spawn action, we spawn in the cells to areas around our existing cells
            #cluster together to maintain easier trading
            for dir in HexDir:

                if totalCellPower >= 49:
                    break

                newBoardstate = currNode.boardstate.copy()

                spawnCoord = cell[0]
                spawnCoord = spawnCoord.__add__(dir)

                if (newBoardstate.get(spawnCoord) == None):
                    newBoardstate[spawnCoord] = (cellColor, 1)

                    newNode = Node(currPlayer.opponent, newBoardstate, (currNode.depth+1), currNode)
                    newNode.lastmove = SpawnAction(spawnCoord)
                    currNode.addChildNode(newNode)
                

#function will check whether a cell is safe, by comparing number of opponent
#cells around itself compared to number of friendly cells. Will >= 0 if safe
#and <= -1 if not safe
def isSafe(boardstate: dict, pos: HexPos, currPlayer: PlayerColor) -> int:

    closeOppCells = 0
    closeOwnCells = 0

    for dir in HexDir:
        newPos = pos
        newPos = newPos.__add__(dir)
        if (boardstate.get(newPos) != None):
            if (boardstate.get(newPos)[0] == currPlayer):
                closeOwnCells += 1
            else:
                closeOppCells += 1

    return closeOwnCells - closeOppCells          

#return the best move produced by the MCTS
#firstly we check if there any obvious moves, where we win outright
#else we use the UCB1 value to look for best moves
def findBestMove(root: Node) -> Action:

    bestChild = None
    bestWinRate = -1
    for child in root.childNodes:
        
        #if the move outright wins the game, take it
        if (ongoing(child.boardstate) == False):
            for value in child.boardstate.values():
                if value[0] == root.colour:
                    return child.lastmove
                break
        
        #else use UCB1 method
        if (child.totalCells == 0):
            continue
        currWinRate = float(child.ourCells/child.totalCells)

        if (currWinRate > bestWinRate):
            bestWinRate = currWinRate
            bestChild = child

    print(bestChild.lastmove)
    return bestChild.lastmove    

#checks whether the game is still ongoing, by checking
#whether there are colours of both opponents in the dict
def ongoing(boardstate: dict) -> bool:
    
    hasBlue = False
    hasRed = False

    for value in list(boardstate.values()):
        if value[0] == PlayerColor.RED:
            hasRed = True
        if value[0] == PlayerColor.BLUE:
            hasBlue = True

        if (hasBlue and hasRed):
            return True

    return False                