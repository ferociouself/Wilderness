"""
Definition for window manager, which is itself a Window that contains
multiple sub-Windows and arranges when each is displayed/updated.
"""
from window import Window
from help_window import HelpWindow
from loading_window import LoadingWindow
from input_window import InputWindow
from map_window import MapWindow
from history_window import HistoryWindow
from title_window import TitleWindow
from settings_window import SettingsWindow
from palette_window import PaletteWindow
from inarea_window import InAreaWindow
from inventory_window import InventoryWindow
from saves_window import SavesWindow
from credits_window import CreditsWindow
from asset_loader import AssetLoader
from game_state import GameState, GameMode
from global_vars import Globals

class WindowManager(Window):

    def __init__(self):
        super().__init__(Globals.NumCols, Globals.NumRows)

        # list of all the windows that the window manager is going to draw
        self.windowList = []
        # list of locations (top-left coordinate) of corresponding windows in windowList
        self.windowPos = []

        # list of list of indices that represent the windows that are part of one possible screen
        self.windowGroups = []
        # stack of indices into windowGroups representing the active groups (what is on screen now)
        self.activeWindowGroups = []

        # whether the screen should be in fullscreen mode
        self.fullScreen = 0
        # create instances of all the Windows
        self.initWindows()

        # vars for transition animations between window groups
        self.isTransitioning = False
        self.transitionTimer = 0.0
        self.transitionThreshold = 2.5
        self.resetOnTransitionComplete = False

        # register a handler for changing the active window groups based on game mode
        GameState().onGameModeChange += self.gameModeChangeHandler()
        # register a handler for screen transitioning when protagonist changes
        GameState().onCharacterSwitch += self.characterSwitchHandler()

    def gameModeChangeHandler(self):
        inGameModes = [GameMode.inAreaCommand, GameMode.inAreaChoice,
            GameMode.inAreaInput, GameMode.inAreaAnimating]
        worldMapModes = [GameMode.worldMap, GameMode.worldMapOverArea]
        def _queueTransition(windowGroup, reset=False):
            self.isTransitioning = True
            self.resetOnTransitionComplete = reset
            self.activeWindowGroups = [windowGroup]
        def _gameModeChangeHandler(*args, **kwargs):
            old, new = args[0]  # first arg is (old state, new state)
            if new == GameMode.isLoading:
                # push the loading window onto the screen
                self.activeWindowGroups.append(0)
            elif old == GameMode.isLoading:
                # pop the loading window off the screen
                self.activeWindowGroups.pop()
            elif (old in [GameMode.titleScreen, GameMode.selectFile] or old in worldMapModes) and new in inGameModes:
                # use the "main game" window group
                _queueTransition(2)
            elif old in inGameModes and new in worldMapModes:
                # switch to map window group
                _queueTransition(3, False)
            elif old in inGameModes and new == GameMode.inAreaInventory:
                # add inventory window
                self.activeWindowGroups.append(6)
            elif old in inGameModes and new == GameMode.inAreaMap:
                # switch to in area map window group
                self.activeWindowGroups.append(4)
            elif old in [GameMode.inAreaInventory, GameMode.inAreaMap] and new in inGameModes:
                # pop off overlay
                self.activeWindowGroups.pop()
            elif old == GameMode.titleScreen and new == GameMode.selectFile:
                self.activeWindowGroups.append(7)
            elif old == GameMode.titleScreen and new == GameMode.credits:
                self.activeWindowGroups.append(8)
            elif old == GameMode.titleScreen and new == GameMode.settings:
                self.activeWindowGroups.append(5)
            elif old in [GameMode.selectFile, GameMode.credits, GameMode.settings] and new == GameMode.titleScreen:
                # reset and pop off overlay
                for winind in self.windowGroups[self.activeWindowGroups[-1]]:
                    self.windowList[winind].refresh()
                self.activeWindowGroups.pop()
                # if going from select file back to main, refresh main command list
                if old == GameMode.selectFile:
                    for winind in self.windowGroups[self.activeWindowGroups[-1]]:
                        self.windowList[winind].refresh()
            elif new in [GameMode.titleScreen]:
                # use the "title" window group
                _queueTransition(1, True)
        return _gameModeChangeHandler

    def characterSwitchHandler(self):
        def _characterSwitchHandler(*args, **kwargs):
            # enqueue screen transition
            self.isTransitioning = True
        return _characterSwitchHandler

    def clear(self):
        super().clear()
        # relay clear to all windows
        for win in self.windowList:
            win.clear()

    def reset(self):
        # relay reset to all windows
        if hasattr(self, 'windowList'):
            for win in self.windowList:
                win.reset()

    def load(self):
        # now that AssetLoader is ready, do any other init
        for win in self.windowList:
            win.load()

    def addWindow(self, windowcls, startr, startc, numrows, numcols):
        """ Creates a Window of a certain width and height at a certain location """
        # adjust the row, col, width, and height values for the border
        self.windowList.append(windowcls(numcols - 2, numrows - 2))
        self.windowPos.append((startr + 1, startc + 1))

    def initWindows(self):
        """ Instantiates all Windows needed in game at the start """
        # clear out window list data
        self.windowList = []
        self.windowPos = []

        # add all the windows our game needs
        midCol = Globals.NumCols // 2
        midRow = Globals.NumRows // 2
        self.addWindow(LoadingWindow, midRow - 2, midCol - 10, 5, 20)    # default to small size

        self.addWindow(TitleWindow, 0, 0, Globals.NumRows, Globals.NumCols)

        splitCol = Globals.NumCols * 19 // 24
        splitRow = Globals.NumRows * 5 // 7
        self.addWindow(HistoryWindow, 0, 0, splitRow, splitCol)
        self.addWindow(InputWindow, splitRow - 1, 0, Globals.NumRows - (splitRow - 1) - 2, splitCol)
        self.addWindow(PaletteWindow, 0, splitCol - 1, Globals.NumRows - 2, Globals.NumCols - (splitCol - 1))

        self.addWindow(MapWindow, Globals.NumRows//4-1, Globals.NumCols//4, (Globals.NumRows//2)-2+2, (Globals.NumCols//2))
        self.addWindow(InAreaWindow, Globals.NumRows//5, Globals.NumCols//6, (Globals.NumRows*3//5)-2, (Globals.NumCols*2//3))
        self.addWindow(SettingsWindow, Globals.NumRows * 3 // 7, 0, Globals.NumRows * 4 // 7, Globals.NumCols)
        self.addWindow(InventoryWindow, Globals.NumRows//5, Globals.NumCols//6, (Globals.NumRows*3//5)-2, (Globals.NumCols*2//3))
        self.addWindow(HelpWindow, Globals.NumRows - 3, 0, 3, Globals.NumCols)
        self.addWindow(SavesWindow, Globals.NumRows * 3 // 7, 0, Globals.NumRows * 4 // 7, Globals.NumCols)
        self.addWindow(CreditsWindow, Globals.NumRows * 3 // 7, 0, Globals.NumRows * 4 // 7, Globals.NumCols)

        # NOTE to debug, add a tuple with the index (in self.windowList) of your window to self.windowGroups
        #  then change self.activeWindowGroups to be a list containing just the index (in self.windowGroups) of that tuple
        self.windowGroups = [
            (0,),       # Loading window
            (1,),       # Title window
            (3, 2, 4, 9),  # Input, History, Palette, and Help windows
                        #NOTE the ordering here is specific as Input gets updated before History
            (5,9),      # Map window
            (6,9),      # InArea window
            (7,),       # Settings window
            (8,9),      # Inventory window
            (10,),      # Save window
            (11,),      # Credits window
        ]
        # which window group is on screen initially
        self.activeWindowGroups = [1]

    def draw(self):
        """ stitches together multiple Windows from active group into the screen """
        # if transitioning, freeze draw calls and use last drawn frame
        if self.isTransitioning:
            self.alphaLevel = min(int(self.transitionTimer * Globals.AlphaMax\
                * 1.1 / self.transitionThreshold) + 1, Globals.AlphaMax)
            return self.pixels

        formatting = []
        for groupind in self.activeWindowGroups:
            group_formatting = []
            for winind in self.windowGroups[groupind]:
                pixels = self.windowList[winind].draw()
                startr, startc = self.windowPos[winind]
                height = len(pixels)
                width = len(pixels[0])
                # fill in pixel content
                for r in range(height):
                    for c in range(width):
                        self.pixels[startr + r][startc + c] = pixels[r][c]
                # add border around window
                for r in range(height):
                    self.pixels[startr + r][startc-1] = '|'
                    self.pixels[startr + r][startc + width] = '|'
                for c in range(width):
                    self.pixels[startr-1][startc + c] = '-'
                    self.pixels[startr + height][startc + c] = '-'
                self.pixels[startr-1][startc-1] = 'o'
                self.pixels[startr + height][startc-1] = 'o'
                self.pixels[startr + height][startc + width] = 'o'
                self.pixels[startr-1][startc + width] = 'o'

                # go through previous formatters (those of background windows) and clip their indices
                #  if the current window groups cover them
                # TODO refactor for efficiency
                filtered_formatting = []
                for i, winformat in enumerate(formatting):
                    filtered_winformat = []
                    for formatter in winformat:
                        style, (start_index, end_index) = formatter
                        r = start_index // self.width    # start and end row should be same
                        c1 = start_index % self.width
                        c2 = end_index % self.width
                        if r >= startr-1 and r <= startr + height:
                            if c1 >= startc-1 and c1 <= startc + width:
                                c1 = startc + width + 1 # push start col to right edge
                            if c2 >= startc-1 and c2 <= startc + width:
                                c2 = startc - 2 # push end col to left edge
                        f1 = r * self.width + c1
                        f2 = r * self.width + c2
                        # if bg indices not contained entirely within foreground window
                        if f1 <= f2:
                            filtered_winformat.append((style, (f1, f2)))
                    filtered_formatting.append(filtered_winformat)
                formatting = filtered_formatting

                # add new elements to formatting
                winformat = []
                for formatter in self.windowList[winind].formatting:
                    style, (start_index, end_index) = formatter
                    r1 = start_index // width
                    c1 = start_index % width
                    r2 = end_index // width
                    c2 = end_index % width
                    # if the start and end rows are different, add multiple formatter entries
                    # that way the rows are broken up
                    c = c1
                    for r in range(r1, r2):
                        f1 = (r + startr) * self.width + (c + startc)
                        f2 = (r + startr) * self.width + (width - 1 + startc)
                        winformat.append((style, (f1, f2)))
                        c = 0
                    f1 = (r2 + startr) * self.width + (c + startc)
                    f2 = (r2 + startr) * self.width + (c2 + startc)
                    winformat.append((style, (f1, f2)))
                group_formatting.append(winformat)
            formatting.extend(group_formatting)

        flattened_formatting = []
        for winformat in formatting:
            flattened_formatting.extend(winformat)
        self.formatting = sorted(flattened_formatting, key=lambda tup: tup[1][0])
        return self.pixels

    def update(self, timestep, keypresses):
        """ sends update signal to Windows in the active group """
        # scan for the fullscreen key to change the mode
        for key in keypresses:
            if key == 'F11':
                self.fullScreen = 1 - self.fullScreen
                GameState().onSettingChange('fullScreen', self.fullScreen)

        # if in transition mode, freeze update calls
        if self.isTransitioning:
            self.transitionTimer += timestep
            if self.transitionTimer >= self.transitionThreshold:
                self.transitionTimer = 0.0
                self.isTransitioning = False
                self.alphaLevel = 0
                self.clear()
                if self.resetOnTransitionComplete:
                    # reload save files
                    AssetLoader().loadSaves()
                    self.refresh()
                    self.resetOnTransitionComplete = False
            return

        # update the playtime clock
        GameState().incPlaytime(timestep)

        # update is only sent to activeWindowGroups[-1], so the foreground windows
        for winind in self.windowGroups[self.activeWindowGroups[-1]]:
            self.windowList[winind].update(timestep, keypresses)
