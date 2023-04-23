# COMP30024 Artificial Intelligence, Semester 1 2023
# Project Part B: Game Playing Agent

from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir


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
    