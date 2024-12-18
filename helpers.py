import device

class Helper():
    def lightPad(self,row:int,column:int,color,view:int, *args, **kwargs) -> None:
        """
        Light a pad using a specific row, column, and color. Row 1, Column 1 is Bottom Left Pad.
        * Errors with color picking will result in the pad to light up WHITE.
        ## Args
        * Row: `Row` pad is at (1 to 9).            NOTE: Use 0 if lighting fader in DAW Fader Mode
        * Column: `Column` pad is at (1 to 9).
        * Color: `Color` for pads -                 NOTE: The only way to get Black/Off is to use the BLACK/OFF Keyword.
           * Format: `Name`                (LIGHT_RED, RED, DARK_RED, ORANGE, YELLOW, LIGHT_GREEN, GREEN, DARK_GREEN, CYAN, LIGHT_BLUE, BLUE, DARK_BLUE, PURPLE, MAGENTA, PINK, BROWN, GRAY, DARK_GRAY, WHITE, OFF/BLACK)
           * Format: `RGB`                 ("0xRRBBGG")
           * Format: `BGR`                 (-16777216 to -1) - Default FL Studio Color Return
           * Format: `Launchpad X Palette` (0 to 127)
        * View: `Current View`. (0: Session, 1: Note Mode/DAW Drum Rack, 13: DAW Fader, 127: Programmer Mode)
        ### Optional Args
        * State: `State` of Pad. Default: `STATIC`. - NOTE: Only STATIC in DAW Fader Mode
           * Format: `Name`                (`STATIC`, `FLASHING`, `PULSING`)
        * ColorVib: `Color Vibrancy.` Default: `NORMAL`.
           * Format: Name                (`DULL`, `NORMAL`, `VIBRANT`)
        * ColorRem: `Color Removal.` Default: `-1`.   NOTE: ONLY works for RGB/BGR inputs.
           * Format: `Launchpad X Palette` (0 to 127)
        """
        if view == None:
            view = 0
        if (9 in [row, column]):
            view = -1
        state = ""
        colorVib = ""
        colorRem = -1
        for argument in args:
            try:
                a = str(argument)
                if (a in ["STATIC", "FLASHING", "PULSING"]):
                    state = argument
                elif (a in ["DULL", "NORMAL", "VIBRANT"]):
                    colorVib = argument
            except TypeError:
                try:
                    a = int(argument)
                    if (int(argument) >= 0 & int(argument) < 128 ):
                        colorRem = argument
                except TypeError:
                    print("Invalid LightPad Extra Params!")
        pad = 0
        if (row != 0):
            pad = self.rowColToPad(row,column,view)
        else:
            pad = column-1
            state = "STATIC"
        try:
            c = str(color)
            if "0x" in c:
                color = self.__RGBToPalette(c,colorVibrancy[colorVib],colorRem)
            else:
                try:
                    color = nameToPalette[c]
                except KeyError:
                    try:
                        c = int(color)
                        if (c < 0):
                            color = self.__BGRToPalette(c,colorVibrancy[colorVib],colorRem)
                        elif (c > 128):
                            color = 3
                    except TypeError:
                        print("Invalid Color Type or String!")
                        color = 3  
        except TypeError:
            print("Invalid Color!")
        device.midiOutMsg(layoutToPadStateCC[view],layoutToPadStateCC[view]+stateToNum[state],pad,color)  

    def changeFaderValue(self,column:int,value:float,conversion:str) -> None:
        """
        Changes the `DAW Fader` Value at a specific fader.
        ## Args
        * `Column`: `Column` the Fader is.
        * `Value`: `Value` to set the fader.
        * `Conversion`: `Conversion Mode` For Specific Values
           * Format: `"KNOB"` - For `Knob Values` e.g. Pan. (-1 to 1)
           * Format: `"VOL"` - For `Volume Values` e.g. Mixer Track Volume. (0 to 1)
           * Format: `Any Other String` - `No Format`. (0 to 127) 
        """
        column = column-1
        DAW_FADER_POS = 180
        if conversion == "KNOB":
            device.midiOutMsg(DAW_FADER_POS, DAW_FADER_POS, column, self.__knobToFaderPos(value))
        elif conversion == "VOL":
            device.midiOutMsg(DAW_FADER_POS, DAW_FADER_POS, column, self.__volToFaderPos(value))
        else:
            device.midiOutMsg(DAW_FADER_POS, DAW_FADER_POS, column, value)

    def rowColToPad(self,row:int,column:int,view:int) -> int:
        """
        Converts a Row and Column Value to a Pad Index.
        ## Args:
        * `Row`: `Row` of Pad.
        * `Column`: `Column` of Pad.
        * `View`: `Current View`. (0: Session, 1: Note Mode/DAW Drum Rack, 13: DAW Fader, 127: Programmer Mode)
        ## Return:
        * `Int`: `Pad` at specific `Row` and `Column`. (11 to 99)
        """
        if (view in [-1,0,127]) | (9 in [row, column]):
            return int(str(row) + str(column))
        if (view == 1):
            startNum = lambda col: 36 if col < 5 else 68
            return startNum(column) + (((row-1) * 4) + ((column-1) % 4))

    def __BGRToPalette(self, color:int, vib:int, colorRem:int) -> int: #Convert gotten color to color in Launchpad X Color Palette
        """
        Converts BGR Number to Color Palette Index. (Default Format for most FL Color Returns)
        ## Args:
        * `Color`: `Color` in BGR Format (-16777216 to -1)
        * `Vib`: `Vibrancy` (-1: `Dull`, 0: `Normal`, 1: `Vibrant`)
        * `ColorRem`: `Color To Remove` - Launchpad X Color Palette (0 to 127)
        ## Return:
        * `Int`: `Color Palette Index`. (0 to 127)
        """
        RGBHex = hex(16777216 + color)
        return self.__RGBToPalette(RGBHex,vib,colorRem)
        

    def __RGBToPalette(self, color:str, vib:int, colorRem:int) -> int:
        """
        Converts RGB Number to Color Palette Index.
        ## Args:
        * `Color`: `Color` in RGB Format. (0xRRGGBB)
        * `Vib`: `Vibrancy` (-1: `Dull`, 0: `Normal`, 1: `Vibrant`)
        * `ColorRem`: `Color To Remove` - Launchpad X Color Palette (0 to 127)
        ## Return:
        * `Int`: `Color Palette Index`. (0 to 127)
        """
        if "-" in color:
            return self.__BGRToPalette(int(color,16),vib,colorRem)
        RGBSplit = [color[i:i+2] for i in range(0, len(color), 2)]
        RGBInt = [int, int, int]
        for i in range(1,4):
            RGBColor = 0
            if (vib < 0):   # Dull
                RGBColor = int(RGBSplit[i], 16) + 16
            elif (vib < 1): # Normal
                RGBColor = int(RGBSplit[i], 16) * 1.5
            else:           # Vibrant
                RGBColor = (int(RGBSplit[i], 16) + 48) * 1.5
            
            if RGBColor > 254:
                RGBInt[i-1] = 255
            else:
                RGBInt[i-1] = RGBColor
        return self.__getPaletteColorFromRGB([RGBInt[0], RGBInt[1], RGBInt[2]],colorRem)

    def __knobToFaderPos(self, knob:float) -> int: #Knob Value to Fader Position
        """
        DAW Knob Value to Fader Position.
        ## Args:
        * `Knob`: `Knob Value`. (-1 to 1)
        ## Return:
        * `Int`: `Fader Position Value`. (0 to 127)
        """
        if (knob < 0):
            return round(63 * (knob + 1))
        else:
            return round((63 * (knob + 1)) + 1)
        
    def FaderPosToKnob(self, faderPos:int) -> float: #Fader Position to Knob Value
        """
        DAW Fader Position to Knob Value.
        ## Args:
        * `FaderPos`: `Fader Position Value`. (0 to 127)
        ## Return:
        * `Float`: `Knob Value`. (-1 to 1)
        """
        if (faderPos <= 63):
            return (faderPos / 63) - 1
        else:
            return ((faderPos - 1) / 63) - 1
    
    def __volToFaderPos(self, volume:float) -> int:
        """
        Mixer Fader Volume to DAW Fader Position.
        ## Args:
        * `Volume`: `Volume of Track`. (0 to 1)
        ## Return:
        * `Int`: `Fader Position Value`. (0 to 127)
        """
        if (volume <= 0.8):
            return round(volume * 135)
        else:
            return round((volume * 95) + 32)
        
    def FaderPosToVol(self, faderPos:int) -> float:
        """
        DAW Fader Position to Mixer Fader Volume.
        ## Args:
        * `FaderPos`: `Fader Position` Value. (0 to 127)
        ## Return:
        * `Float`: `Volume Value`. (0 to 1)
        """
        if (faderPos <= 108):
            return faderPos/135
        else:
            return ((faderPos-32)/95)
        
    def clearPads(self,currentScreen:int) -> None: 
        """
        Clears All Pads.
        ## Args:
        * `CurrentScreen`: `Current View`. (0: Session, 1: Note Mode/DAW Drum Rack, 13: DAW Fader, 127: Programmer Mode)
        """
        for row in range(1,9):
            for column in range(1,9):
                self.lightPad(row,column,"OFF",currentScreen)


    def __getPaletteColorFromRGB(self, input:[int,int,int], colorRem:int) -> int: #Gets closest Palette Color to RGB # type: ignore
        """
        Converts Hex Number to Nearest Color Palette Index.
        ## Args:
        * `Input`: `Input in Int List`. [Int:Red, Int:Green, Int:Blue]
        * `ColorRem`: `Color Palette Index` to Remove from Color Conversion. (0 to 127)
        ## Return:
        * `Int`: `Color Palette Index` (0 to 127)
        """
        best_palette_match = 0
        best_palette_match_distance = (0.3 * (input[0] - paletteRGBDecimal[0][0])**2) + (0.6 * (input[1] - paletteRGBDecimal[0][1])**2) + (0.1 * (input[2] - paletteRGBDecimal[0][2])**2)
        # Starts at 1 because 0 is Off, and so is removed from the list
        for i in range(1, len(paletteRGBDecimal)):
            if (i == colorRem):
                continue
            distance = (0.3 * (input[0] - paletteRGBDecimal[i][0])**2) + (0.6 * (input[1] - paletteRGBDecimal[i][1])**2) + (0.1 * (input[2] - paletteRGBDecimal[i][2])**2)
            if distance < best_palette_match_distance:
                best_palette_match = i
                best_palette_match_distance = distance

        return best_palette_match + 1


colorVibrancy = {"DULL":-1, "NORMAL":0, "":0, "VIBRANT":1}
stateToNum = {"":0, "STATIC":0, "FLASHING":1, "PULSING":2}
layoutToPadStateCC = {-1:176, 0:144, 1:152, 13:181, 127:144}

nameToPalette = {"LIGHT_RED":4, "RED":5, "DARK_RED":6, "ORANGE":9, "YELLOW":13, "LIGHT_GREEN":21, "GREEN":22, "DARK_GREEN":23, "CYAN":33, "LIGHT_BLUE":41, "BLUE":42, "DARK_BLUE":43, "PURPLE":49, "MAGENTA":53, "PINK":82, "BROWN":11, "GRAY":2, "DARK_GRAY":1, "WHITE":3, "OFF":0, "BLACK":0}
paletteRGBDecimal = [ #Launchpad X Color Palette in index. [1] = 1, [2] = 2, etc.
(179,179,179),
(221,221,221),
(255,255,255),
(255,179,179),
(255,97,97),
(221,97,97),
(179,97,97),
(255,243,213),
(255,179,97),
(221,140,97),
(179,118,97),
(255,238,161),
(255,255,97),
(221,221,97),
(179,179,97),
(221,255,161),
(194,255,97),
(161,221,97),
(129,179,97),
(194,255,179),
(97,255,97),
(97,221,97),
(97,179,97),
(194,255,194),
(97,255,140),
(97,221,118),
(97,179,107),
(194,255,204),
(97,255,204),
(97,221,161),
(97,179,129),
(194,255,243),
(97,255,233),
(97,221,194),
(97,179,150),
(194,243,255),
(97,238,255),
(97,199,221),
(97,161,179),
(194,221,255),
(97,199,255),
(97,161,221),
(97,129,179),
(161,140,255),
(97,97,255),
(97,97,221),
(97,97,179),
(204,179,255),
(161,97,255),
(129,97,221),
(118,97,179),
(255,179,255),
(255,97,255),
(221,97,221),
(179,97,179),
(255,179,213),
(255,97,194),
(221,97,161),
(179,97,140),
(255,118,97),
(233,179,97),
(221,194,97),
(161,161,97),
(97,179,97),
(97,179,140),
(97,140,213),
(97,97,255),
(97,179,179),
(140,97,243),
(204,179,194),
(140,118,129),
(255,97,97),
(243,255,161),
(238,252,97),
(204,255,97),
(118,221,97),
(97,255,204),
(97,233,255),
(97,161,255),
(140,97,255),
(204,97,252),
(238,140,221),
(161,118,97),
(255,161,97),
(221,249,97),
(213,255,140),
(97,255,97),
(179,255,161),
(204,252,213),
(179,255,246),
(204,228,255),
(161,194,246),
(213,194,249),
(249,140,255),
(255,97,204),
(255,194,97),
(243,238,97),
(228,255,97),
(221,204,97),
(179,161,97),
(97,186,118),
(118,194,140),
(129,129,161),
(129,140,204),
(204,170,129),
(221,97,97),
(249,179,161),
(249,186,118), 
(255,243,140),
(233,249,161),
(213,238,118),
(255,255,255),
(249,249,213),
(221,252,228),
(233,233,255),
(228,213,255),
(179,179,179),
(213,213,213),
(249,255,255),
(233,97,97),
(170,97,97),
(129,246,97),
(97,179,97),
(243,238,97),
(179,161,97),
(238,194,97),
(194,118,97),
]

arrowLights = {1:[122,69],2:[108,23],3:[68,122],4:[69,108]}