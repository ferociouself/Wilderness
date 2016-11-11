"""
Window containing the history/feedback of a player's actions. The content of
the game is exposed through this window.
"""
from window import Window
from game_state import GameState, GameMode
from global_vars import Globals

class HistoryWindow(Window):

    def __init__(self, width, height):
        super().__init__(width, height)
        self.threshold = 0.02  # Delay in seconds before each character appears on-screen
        self.speedButtonFactor = 5.0  # Speedup factor for the text animation when "speed" button pressed
        self.speedPeriodFactor = 0.15 # Factor for additional time special chars like period take
        self.timestep = 0.0     # Tracks the time since the last character was displayed
        self.charLimit = 0      # The current number of characters (exclude newlines) that can be displayed

        self.historyBufferWatch = [0, 0] # Number of chars already processed from history buffer (one index per protagonist)
        self.wrappedLines = []  # Strings corresponding to word wrapped lines in window
        self.rowIndices = []    # Mappings of char indices in history buffer for particular rows
        self.startingLine = 0   # Index of line to start displaying in window

        self.allWritten = True  # True if everything has been displayed, false otherwise

    def update(self, timestep, keypresses):
        # TODO refactor
        # do word wrapping logic, but only when more has been added to buffer since last update
        historyProcessed = self.historyBufferWatch[GameState().activeProtagonistInd]
        if len(GameState().historyBuffer) > historyProcessed:
            input_list = GameState().historyBuffer[historyProcessed:].split("\n")

            output_list = []    # list of additional row text - each row contains a string
            row_indices = []    # list of additional (start, end) indices of historyBuffer corresponding to row
            if len(self.rowIndices) > 0:
                total_count = self.rowIndices[-1][1] # NOTE math is strange here due to leading/trailing newlines
            else:
                total_count = 0     # number of characters from historyBuffer (including whitespace) written
            start_row_count = total_count # number of characters written by start of current line

            i = 0
            line_remaining = input_list[i]
            while i < len(input_list):
                # cut off chunk of input line that will fit in row of window
                end_ind = len(line_remaining) if len(line_remaining) < self.width \
                    else line_remaining.rfind(' ', 0, self.width)
                output_list.append(line_remaining[:end_ind])
                total_count += len(line_remaining[:end_ind]) + 1
                row_indices.append((start_row_count, total_count-1))
                start_row_count = total_count
                # repeat with the remainder of the input line; use new one if done with current
                line_remaining = line_remaining[end_ind+1:]
                if line_remaining == '':
                    i += 1
                    if i < len(input_list):
                        line_remaining = input_list[i]
            self.historyBufferWatch[GameState().activeProtagonistInd] = len(GameState().historyBuffer)
            self.wrappedLines.extend(output_list)
            self.rowIndices.extend(row_indices)
            self.allWritten = False # start animation

        # Only increment charLimit when there's unrendered text still to be displayed
        # Otherwise, there will be no delay when the next batch of text is sent
        # since charLimit has been incrementing the whole time
        if self.allWritten == False:
            self.timestep += timestep
            unwrappedText = ''.join(self.wrappedLines)
            speedFlag = False
            skipFlag = False
            # scan for keys that speed up animation
            for key in keypresses:
                if key == ' ':
                    speedFlag = True
                elif key == 'Return' and Globals.IsDev:
                    skipFlag = True
                    break
            if not skipFlag:
                # add as many characters as possibly allowed by new timestep
                while True:
                    speedMultiple = 1.0 if not speedFlag else self.speedButtonFactor
                    ch = unwrappedText[self.charLimit-1] if 0 < self.charLimit < len(unwrappedText) else ''
                    if ch == '.':
                        speedMultiple *= self.speedPeriodFactor
                    if self.timestep > self.threshold / speedMultiple:
                        self.timestep -= self.threshold / speedMultiple
                        self.charLimit += 1
                    else:
                        break
            # check if animation is complete
            if self.charLimit >= len(unwrappedText)+1 or skipFlag:
                self.charLimit = len(unwrappedText)+1
                self.allWritten = True
            # update starting line based on where the animation index is at
            lineIndex = 0
            charCounter = 0
            while lineIndex < len(self.wrappedLines) and charCounter < self.charLimit:
                charCounter += len(self.wrappedLines[lineIndex])
                lineIndex += 1
            self.startingLine = lineIndex - self.height if lineIndex - self.height >= 0 else 0
        else: # Only allow scrolling if we're not writing text to the screen
            for key in keypresses:
                if key == "Prior":
                    if self.startingLine > 0:
                        self.startingLine -= 1
                elif key == "Next":
                    if self.startingLine + self.height < len(self.wrappedLines):
                        self.startingLine += 1

    def draw(self):
        output_list = self.wrappedLines[self.startingLine : self.startingLine + self.height]
        row_indices = self.rowIndices[self.startingLine : self.startingLine + self.height]
        charsWritten = len(''.join(self.wrappedLines[:self.startingLine]))

        # map output_list to self.pixels
        # NOTE r and c represent where the animation "leaves off" after this loop
        r = 0
        stopWriting = False     # flag that indicates if we hit charLimit
        for line in output_list:
            c = 0
            # fill in pixels with word
            for ch in line:
                self.pixels[r][c] = ch
                charsWritten += 1
                if charsWritten >= self.charLimit:
                    stopWriting = True
                    break
                c += 1
            # fill in what remains with spaces
            for cc in range(c, self.width):
                self.pixels[r][cc] = " "
            if stopWriting:
                break
            r += 1
        # fill in blank lines
        for rr in range(r+1, self.height):
            for cc in range(self.width):
                self.pixels[rr][cc] = " "

        # map LangNode formatting to Window formatting
        # TODO super inefficient - refactor later
        input_formatting = GameState().historyFormatting
        output_formatting = []
        for style in input_formatting:
            first_index = row_indices[0][0]
            last_index = row_indices[-1][1]
            if not self.allWritten and r < len(row_indices):
                last_index = row_indices[r][0] + c - 1 # bound formatted text to what's displayed
            for indices in input_formatting[style]:
                start_index = indices[0]
                end_index = indices[1]
                # see if (start_index, end_index) is contained within current view of history
                # clip indices if needed
                if start_index >= first_index and start_index <= last_index:
                    if end_index > last_index:
                        end_index = last_index
                elif end_index >= first_index and end_index <= last_index:
                    start_index = first_index
                else:
                    continue
                # scan through row_indices to find the rows where the style applies
                for ri1, row1 in enumerate(row_indices):
                    if start_index >= row1[0] and start_index <= row1[1]:
                        ci1 = start_index - row1[0]
                        for ri2, row2 in enumerate(row_indices[ri1:]):
                            if end_index >= row2[0] and end_index <= row2[1]:
                                ci2 = end_index - row2[0]
                                # the row and column values translate to window indices
                                fi1 = ri1 * self.width + ci1
                                fi2 = (ri1 + ri2) * self.width + ci2
                                output_formatting.append((style, (fi1, fi2)))
                                break
                        break

        self.formatting = output_formatting
        return self.pixels

if __name__ == '__main__':
    h = HistoryWindow(30, 10)
    # NOTE do not set GameState values directly in non-test code
    test_input = "Kipp stepped back to take a good look at the room. He eyed a fancy bookself with some books that may be worth inspecting. In the far left corner of the room, Kipp also saw a sleeping bag. It may not be the right time to take a nap, but maybe he could use it to de-stress for a while. He looked back at Arthur. It looked like he hasn't gotten any better since we last talked. Maybe Kipp should go talk to Arthur again. \n  \n Kipp: Hmm...what should I do?"
    GameState().subStates[0].historyBuffer = test_input
    formatting = {'yellow': [(67, 74), (174, 185)],
        'green': [(302, 307), (404, 409)],
        'red': [(110, 119), (251, 253), (396, 402)],
    }
    GameState().subStates[0].historyFormatting = formatting
    h.debugDraw()
