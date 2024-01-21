import device
import plugins
from math import floor

class PluginFPC():
    def __init__(self) -> None:
        self.chanIndex = 0 #Channel Index of FPC

    def OnMidiMsg(self, event):
        if event.data1 == 93: #Previous Preset
            if event.data2 == 127:
                device.midiOutMsg(176, 144, 93, 3)
                plugins.prevPreset(self.chanIndex)
                event.handled = True
            if event.data2 == 0:
                device.midiOutMsg(176, 144, 93, 1)
                event.handled = True

        if event.data1 == 94: #Next Preset
            if event.data2 == 127:
                device.midiOutMsg(176, 144, 94, 3)
                plugins.nextPreset(self.chanIndex)
                event.handled = True
            if event.data2 == 0:
                device.midiOutMsg(176, 144, 94, 1)
                event.handled = True
                

    def OnNoteOn(self, event):
        if (event.note >= 52 and event.note < 68) or (event.note >= 84): #Notes on top of Drum Rack never used
            return
        noteToPad = {36 : 0,37 : 1,38 : 2,39 : 3,40 : 4,41 : 5,42 : 6,43 : 7,44 : 8,45 : 9,46 : 10,47 : 11,48 : 12,49 : 13,50 : 14,51 : 15,68 : 16,69 : 17,70 : 18,71 : 19,72 : 20,73 : 21,74 : 22,75 : 23,76 : 24,77 : 25,78 : 26,79 : 27,80 : 28,81 : 29,82 : 30,83 : 31}
        event.note = plugins.getPadInfo(self.chanIndex, -1, 1, noteToPad[event.note]) #Pressed Note to Note on FPC
        #event.note = 36

    def updateNoteMode(self, chanIndex, currentScreen):
        self.chanIndex = chanIndex
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 18, 0, 1, 0, 247])) #Clear Note Mode
        self.updateArrows(currentScreen)
        device.midiOutMsg(176, 144, 91, 0)
        device.midiOutMsg(176, 144, 92, 0)
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 15, 1, 247])) # Update to Drum Rack
        self.updatePadsColor(chanIndex)
        
    def updateArrows(self, currentScreen):
        if currentScreen == 1 or currentScreen == None:
            device.midiOutMsg(176, 144, 93, 1)
            device.midiOutMsg(176, 144, 94, 1)  
        else:
            device.midiOutMsg(176, 144, 93, 0)
            device.midiOutMsg(176, 144, 94, 0)
    def updatePadsColor(self, chanIndex): #Update Launchpad Pad Color
        for i in range(36, 84):
            if i >= 52 and i < 68:
                continue
            if i < 52:
                 offset = 36
            else:
                 offset = 52
            device.midiOutMsg(152, 152, i, convertColor(plugins.getPadInfo(chanIndex, -1, 2, i - offset)))

class PluginGrossBeat():
    def __init__(self) -> None:
        self.mixerIndex = -1
        self.slotIndex = -1
        self.padSelectedTime = 81
        self.padSelectedVol = 85
        self.viewDown = False

    def OnMidiMsg(self, event):
        if event.data2 == 127:
            if event.data1 == 91 and self.viewDown:
                device.midiOutMsg(176, 144, 91, 3) 
                event.handled = True
            if event.data1 == 92 and not self.viewDown:
                device.midiOutMsg(176, 144, 92, 3)
                event.handled = True
        else:
            if event.data1 == 91 and self.viewDown:
                self.viewDown = False
                self.updateArrows()
                device.midiOutMsg(144, 144, self.padSelectedTime, 27)
                device.midiOutMsg(144, 144, self.padSelectedVol, 11)
                self.padSelectedTime -= 10
                self.padSelectedVol -= 10
                if self.padSelectedTime > 9:
                    device.midiOutMsg(144, 146, self.padSelectedTime, 25)
                if self.padSelectedVol > 9:
                    device.midiOutMsg(144, 146, self.padSelectedVol, 9)
                event.handled = True

            if event.data1 == 92 and not self.viewDown:
                self.viewDown = True
                self.updateArrows()
                device.midiOutMsg(144, 144, self.padSelectedTime, 27)
                device.midiOutMsg(144, 144, self.padSelectedVol, 11)
                self.padSelectedTime += 10
                self.padSelectedVol += 10
                if self.padSelectedTime < 89:
                    device.midiOutMsg(144, 146, self.padSelectedTime, 25)
                if self.padSelectedVol < 89:
                    device.midiOutMsg(144, 146, self.padSelectedVol, 9)
                event.handled = True

        
    def OnNoteOn(self, event):
        if event.data2 > 0:
            pad = event.data1
            offset = 4 if self.viewDown else 0
            if floor((pad%10)/5) == 0:
                event.note = (pad - ((14 * (floor(pad/10)-6)) - 7)) + offset
                device.midiOutMsg(144, 144, self.padSelectedTime, 27)
                self.padSelectedTime = pad
                device.midiOutMsg(144, 146, self.padSelectedTime, 25)
            else:
                event.note = (pad - ((14 * (floor(pad/10)-6)) + 33)) + offset
                device.midiOutMsg(144, 144, self.padSelectedVol, 11)
                self.padSelectedVol = pad
                device.midiOutMsg(144, 146, self.padSelectedVol, 9)


    def updateGrossBeatLayout(self, currentScreen, mixerIndex, slotIndex):
        if currentScreen == 13:
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 0, 247]))
            currentScreen = 0
        if currentScreen == 0:
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 18, 1, 0, 0, 247]))
            self.mixerIndex = mixerIndex
            self.slotIndex = slotIndex
            print("param:", plugins.getParamName(0, self.mixerIndex, self.slotIndex))
            self.updateArrows()
            self.updatePadsColor()

    def updateArrows(self):
        device.midiOutMsg(176, 144, 93, 0)
        device.midiOutMsg(176, 144, 94, 0)
        if self.viewDown:
            device.midiOutMsg(176, 144, 91, 1)
            device.midiOutMsg(176, 144, 92, 0)  
        else:
            device.midiOutMsg(176, 144, 91, 0)
            device.midiOutMsg(176, 144, 92, 1)
            

    def updatePadsColor(self):
        for i in range(11, 89):
            if floor((i%10)/5) == 0:
                device.midiOutMsg(144, 144, i, 27)
            else:
                device.midiOutMsg(144, 144, i, 11)
        self.updateSlots()

    def updateSlots(self):
        print("param time:", plugins.getParamValue(0, self.mixerIndex, self.slotIndex))
        print("param vol:", plugins.getParamValue(1, self.mixerIndex, self.slotIndex))
        timeSlot = round(plugins.getParamValue(0, self.mixerIndex, self.slotIndex)/0.02857)
        volSlot = round(plugins.getParamValue(1, self.mixerIndex, self.slotIndex)/0.02857)
        offset = 10 if self.viewDown else 0
        padTime = 81 + offset if timeSlot == 0 else round((timeSlot+1) - (14 * (floor(((timeSlot+1)-0.1)/4))-80)) + offset
        padVol = 85 + offset if volSlot == 0 else round((volSlot+1) - (14 * (floor(((volSlot+1)-0.1)/4))-84)) + offset
        print(timeSlot, padTime,volSlot, padVol)
        if padTime > 9:
            device.midiOutMsg(144, 144, self.padSelectedTime, 27)
            self.padSelectedTime = padTime
            device.midiOutMsg(144, 146, padTime, 25)
        if padVol > 9:
            device.midiOutMsg(144, 144, self.padSelectedVol, 11)
            self.padSelectedVol = padVol
            device.midiOutMsg(144, 146, padVol, 9)





def convertColor(color) -> int: #Convert gotten color to color in Launchpad X Color Palette
        if color == 10462118:
             return 0
        if color > 0:
            RGBHex = hex(color)
        else:
            RGBHex = hex(16777216 + color)
        #print(RGBHex)
        RGBSplit = [RGBHex[i:i+2] for i in range(0, len(RGBHex), 2)]
        RGBInt = [int, int, int]
        for i in range(1,4):
            if (int(RGBSplit[i], 16) * 1.5) > 254:
                RGBInt[i-1] = 255
            else:
                RGBInt[i-1] = int(RGBSplit[i], 16) * 1.5
        return getPaletteColorFromRGB([RGBInt[0], RGBInt[1], RGBInt[2]])

def getPaletteColorFromRGB(input: (int, int, int)) -> int: #Gets closest Palette Color to RGB
        best_palette_match = 0
        best_palette_match_distance = (0.3 * (input[0] - palette[0][0])**2) + (0.6 * (input[1] - palette[0][1])**2) + (0.1 * (input[2] - palette[0][2])**2)

        # we already checked [0]
        for i in range(1, len(palette)):
            distance = (0.3 * (input[0] - palette[i][0])**2) + (0.6 * (input[1] - palette[i][1])**2) + (0.1 * (input[2] - palette[i][2])**2)
            if distance < best_palette_match_distance:
                best_palette_match = i
                best_palette_match_distance = distance

        return best_palette_match

palette = [ #Color Palette of Launchpad X
(97,97,97),
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