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
        self._color = color

        time = referee["time_remaining"]
        print(time)

        #we will set up a list with all the cells
        #following project part a, the format for the list
        #will be [colour, power] of the cell
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
        match self._color:
            case PlayerColor.RED:
                return SpawnAction(HexPos(3, 3))
            case PlayerColor.BLUE:
                # This is going to be invalid... BLUE never spawned!
                return SpreadAction(HexPos(3, 3), HexDir.Up)

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


class Node:

    def __init__(self, player: int, boardstate: dict, parentNode = None,):
        
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
        

    def addChildNode(self, childNode):

        self.childNodes.append(childNode)

    def backPropagateWin(self, player: int):

        currNode = self

        while (currNode != None):
            
            if (currNode.player == player):

                currNode.totalGames += 1
                currNode.wonGames += 1

            else:

                currNode.totalGames += 1

            currNode = currNode.parentNode

def MCTS(boardstate: dict, agent: Agent, root: Node) -> list:

    #for this, we will allocate 5% of the remaining time for the algorithm to run??
    #may be changed
    #inspired by chess players, who spend more time thinking in the initial stages
    #of the game as there are more moves available
    now = datetime.now()
    timeRemaining = agent.time/20
    limit = now + timedelta(seconds=timeRemaining)
    
    #player colour to be adjusted
    rootNode = root
    
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
        if (currNode.totalGames == 0):
            
            score = simulateNode(currNode, agent._color)
            

            currPlayer = currNode.player
            backPropagate(currNode, currPlayer, score)


    #return the best move
    return

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
def simulateNode(currNode: Node, color: PlayerColor) -> int:

    moves = 0
    #make a copy of the boardstate that we will manipulate
    simulatedBoardstate = currNode.boardstate.copy()

    while (moves < 30):
        
        #add heurisitc for moving here
        if ((moves % 2) == 0):
            moveHeuristic(simulatedBoardstate, color)
        else:
            moveHeuristic(simulatedBoardstate, color)

        moves+= 1

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

def moveHeuristic(boardstate: dict, player: int):

    return