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

def MCTS(boardstate: dict, agent: Agent) -> list:

    now = datetime.now()
    timeRemaining = agent.time/20
    limit = now + timedelta(seconds=timeRemaining)
    
    #player colour to be adjusted
    root = Node(1, boardstate, None)
    
    while (datetime.now() < limit):
        
        currNode = root
        #perform MCTS
        #selecting a leaf node, if not at leaf node, traverse down
        while (len(currNode.childNodes) != 0):
                
                #using UCB1 to select the best nodes amongst the child nodes
                bestChild = None
                bestVal = -1

                for child in currNode.childNodes:

                    currVal = calcUCB1(child)
                    
                    if currVal > bestVal:
                        bestVal = currVal
                        bestChild = child

                currNode = bestChild

        #now at leaf node, we shall expand the node
                


    #return the best move
    return

def calcUCB1(childNode: Node) -> float:

    x = float(childNode.wonGames/childNode.totalGames)
    #constant 2 here may change depending on exploration etc.
    y = 2 * sqrt(log(childNode.parentNode.totalGames)/(childNode.totalGames))

    return (x + y)
