"""
Window for Title screen of game - contains some ASCII art and a list of options
that pull up other windows and/or start up the game.
"""
from game_state import GameState, GameMode
from global_vars import Globals
from lang_interpreter import Interpreter
from asset_loader import AssetLoader
from window import Window
import sys

class TitleWindow(Window):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.pointingTo = 0 # index of option player is looking at
        # options to be selected on screen
        self.options = ('New game', 'Load game', 'Options', 'Credits', 'Exit')
        self.art = None     # set in load()
        self.startRow = 0   # reset in load()
        self.startCol = 0   # reset in load()
        self.isPromptingName = False    # on new game, whether window is asking for player name
        self.nameBuffer = ''            # holds name that player is typing

    def load(self):
        # grab the title art
        self.art = AssetLoader().getArt('title_window.txt')

        # do one-time drawing of title and options onto pixels
        maxLength = 0
        row = self.height // 6 # Looks better than starting at 0
        col = 0
        # Find the longest line...
        for i, char in enumerate(self.art):
            if char == "\n":
                if col > maxLength:
                    maxLength = col
                col = 0
            else:
                col += 1

        # So that we know where to center the ASCII art
        startCol = (self.width - maxLength) // 2
        for i, char in enumerate(self.art):
            if char == "\n":
                row += 1
                col = 0
            else:
                self.pixels[row][col + startCol] = char
                col += 1

        # Same as above, but for the options instead.
        # Note that the options are all left-aligned based on the center
        # of the first option.
        self.startRow = row + (self.height - row - len(self.options)) // 2
        self.startCol = (self.width - len(self.options[0])) // 2
        row = 0
        for option in self.options:
            col = 0
            for char in list(option):
                self.pixels[row + self.startRow][col + self.startCol] = char
                col += 1
            row += 1

    def update(self, timestep, keypresses):
        if self.isPromptingName:
            for key in keypresses:
                if len(key) == 1 and len(self.nameBuffer) < Globals.NameMaxLength:
                    self.nameBuffer += key
                elif key == "BackSpace" and len(self.nameBuffer) > 0:
                    self.nameBuffer = self.nameBuffer[:-1]
                elif key == "Return" and len(self.nameBuffer.strip()) > 0:
                    # set game startup info
                    gs = GameState()
                    gs.init()
                    gs.name = self.nameBuffer.strip()
                    gs.areaId = 'meadows'
                    gs.roomId = 'shepherdHouse'
                    gs.gameMode = GameMode.inAreaCommand   # WindowManager handles window switch
                    self.isPromptingName = False
                    self.nameBuffer = ''
        else:
            for key in keypresses:
                if key == "Up":
                    self.pointingTo = (self.pointingTo - 1) % len(self.options)
                elif key == "Down":
                    self.pointingTo = (self.pointingTo + 1) % len(self.options)
                elif key == "Return":
                    cmd = self.options[self.pointingTo]
                    if cmd == 'New game':
                        # switch to name prompt mode before starting game
                        self.isPromptingName = True
                    elif cmd == 'Options':
                        # TODO: Figure out how to get this to launch the settings window
                        continue
                    elif cmd == 'Exit':
                        sys.exit()

    def draw(self):
        # ensure we are loaded
        if not self.art:
            return self.pixels

        if self.isPromptingName:
            # Clear previous screen
            for i, r in enumerate(range(self.startRow, self.startRow+len(self.options))):
                for c in range(self.startCol, self.startCol+len(self.options[i])):
                    self.pixels[r][c] = ' '
            # Fill where options used to be with prompt
            promptString = 'What is your name?'
            col = self.width // 2 - len(promptString) // 2
            for i, c in enumerate(range(col, col + len(promptString))):
                self.pixels[self.startRow][c] = promptString[i]
            col = self.width // 2 - Globals.NameMaxLength // 2
            for i, c in enumerate(range(col, col + Globals.NameMaxLength)):
                if i < len(self.nameBuffer):
                    self.pixels[self.startRow+1][c] = self.nameBuffer[i]
                elif i == len(self.nameBuffer):
                    self.pixels[self.startRow+1][c] = '_'
                else:
                    self.pixels[self.startRow+1][c] = ' '
        else:
            # Clear previous cursor
            for row, temp in enumerate(self.options):
                self.pixels[self.startRow + row][self.startCol - 4] = " "
            # Draw current cursor
            self.pixels[self.startRow + self.pointingTo][self.startCol - 4] = ">"
        return self.pixels

if __name__ == '__main__':
    AssetLoader().loadAssets()
    window = TitleWindow(120, 35)
    window.debugDraw()
