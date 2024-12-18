import device
import plugins
import helpers
h = helpers.Helper()

class PluginFPC():
    def __init__(self) -> None:
        self.chanIndex = 0 #Channel Index of FPC

    def reset(self):
        self.chanIndex = 0
    def OnMidiMsg(self, event):
        if event.data1 == 93: #Previous Preset
            if event.data2 == 127:
                h.lightPad(9,3,"WHITE",1)
                plugins.prevPreset(self.chanIndex,-1,True)
                event.handled = True
            if event.data2 == 0:
                h.lightPad(9,3,"DARK_GRAY",1)
                event.handled = True

        if event.data1 == 94: #Next Preset
            if event.data2 == 127:
                h.lightPad(9,4,"WHITE",1)
                plugins.nextPreset(self.chanIndex,-1,True)
                event.handled = True
            if event.data2 == 0:
                h.lightPad(9,4,"DARK_GRAY",1)
                event.handled = True
                

    def OnNoteOn(self, event):
        if (event.note >= 52 and event.note < 68) or (event.note >= 84): #Notes on top of Drum Rack never used
            return
        noteToPad = {36 : 0,37 : 1,38 : 2,39 : 3,40 : 4,41 : 5,42 : 6,43 : 7,44 : 8,45 : 9,46 : 10,47 : 11,48 : 12,49 : 13,50 : 14,51 : 15,68 : 16,69 : 17,70 : 18,71 : 19,72 : 20,73 : 21,74 : 22,75 : 23,76 : 24,77 : 25,78 : 26,79 : 27,80 : 28,81 : 29,82 : 30,83 : 31}
        event.note = plugins.getPadInfo(self.chanIndex, -1, 1, noteToPad[event.note],True) #Pressed Note to Note on FPC

    def updateNoteMode(self, chanIndex, currentScreen):
        self.chanIndex = chanIndex
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 18, 0, 1, 0, 247])) #Clear Note Mode
        self.updateArrows(currentScreen)
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 15, 1, 247])) # Update to Drum Rack
        self.updatePadsColor(chanIndex)
        if currentScreen in [0,13]:
            return
        h.lightPad(9,1,"OFF",currentScreen)
        h.lightPad(9,2,"OFF",currentScreen)
        
        
    def updateArrows(self, currentScreen):
        if currentScreen in [0,13]:
            return
        h.lightPad(9,1,"OFF",currentScreen)
        h.lightPad(9,2,"OFF",currentScreen)
        if currentScreen == 1 or currentScreen == None:
            h.lightPad(9,3,"DARK_GRAY",currentScreen)
            h.lightPad(9,4,"DARK_GRAY",currentScreen)  
        else:
            h.lightPad(9,3,"OFF",currentScreen)
            h.lightPad(9,4,"OFF",currentScreen)

    def updatePadsColor(self, chanIndex): #Update Launchpad Pad Color
        for row in range(1,5):
            for column in range(1,9):
                if (column > 4):
                    offset = 16
                else:
                    offset = 0
                color = plugins.getPadInfo(chanIndex,-1,2,offset + ((row-1) * 4) + ((column-1) % 4))
                if color == 0: #Blank Slots on FPC
                    color = 10462118
                h.lightPad(row,column,hex(color),True,1)