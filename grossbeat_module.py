import device
import plugins
import mixer
import playlist
from math import floor
import helpers
h = helpers.Helper()

class PluginGrossBeat():
    def __init__(self) -> None:
        self.mixerIndex = -1
        self.slotIndex = -1
        self.padSelectedTime = 81
        self.padSelectedVol = 85
        self.viewDown = False

        self.lastTimeVal = -1
        self.lastVolVal = -1

    def reset(self):
        self.mixerIndex = -1
        self.slotIndex = -1
        self.padSelectedTime = 81
        self.padSelectedVol = 85
        self.viewDown = False
        self.lastTimeVal = -1
        self.lastVolVal = -1

    def OnMidiMsg(self, event):
        if event.data2 == 127:
            if event.data1 == 91 and self.viewDown:
                h.lightPad(9,1,"WHITE",0)
                event.handled = True
            if event.data1 == 92 and not self.viewDown:
                h.lightPad(9,2,"WHITE",0)
                event.handled = True
        else:
            if event.data1 == 91 and self.viewDown:
                self.viewDown = False
                self.updateArrows(0)
                self.colorPad(self.padSelectedTime, "DARK_GREEN", "STATIC")
                self.colorPad(self.padSelectedVol, "BROWN", "STATIC")
                self.padSelectedTime -= 10
                self.padSelectedVol -= 10
                if self.padSelectedTime > 9:
                    self.colorPad(self.padSelectedTime,"LIGHT_GREEN", "PULSING")
                if self.padSelectedVol > 9:
                    self.colorPad(self.padSelectedVol,"ORANGE", "PULSING")
                event.handled = True

            if event.data1 == 92 and not self.viewDown:
                self.viewDown = True
                self.updateArrows(0)
                self.colorPad(self.padSelectedTime,"DARK_GREEN", "STATIC")
                self.colorPad(self.padSelectedVol,"BROWN", "STATIC")
                self.padSelectedTime += 10
                self.padSelectedVol += 10
                if self.padSelectedTime < 89:
                    self.colorPad(self.padSelectedTime,"LIGHT_GREEN", "PULSING")
                if self.padSelectedVol < 89:
                    self.colorPad(self.padSelectedVol,"ORANGE", "PULSING")
                event.handled = True

        
    def OnNoteOn(self, event):
        if event.data2 > 0:
            pad = event.data1
            offset = 4 if self.viewDown else 0
            if floor((pad%10)/5) == 0:
                event.note = (pad - ((14 * (floor(pad/10)-6)) - 7)) + offset
                self.colorPad(self.padSelectedTime,"DARK_GREEN", "STATIC")
                self.padSelectedTime = pad
                self.colorPad(self.padSelectedTime,"LIGHT_GREEN", "PULSING")
            else:
                event.note = (pad - ((14 * (floor(pad/10)-6)) + 33)) + offset
                self.colorPad(self.padSelectedVol,"BROWN", "STATIC")
                self.padSelectedVol = pad
                self.colorPad(self.padSelectedVol,"ORANGE", "PULSING")


    def updateGrossBeatLayout(self, currentScreen, mixerIndex, slotIndex):
        if currentScreen == 13:
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 0, 247]))
            currentScreen = 0
        if currentScreen == 0:
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 18, 1, 0, 0, 247]))
            self.mixerIndex = mixerIndex
            self.slotIndex = slotIndex
            self.lastTimeVal = -1
            self.lastVolVal = -1
            self.updateArrows(currentScreen)
            self.updatePadsColor()

    def updateArrows(self, currentScreen):
        if currentScreen == 1:
            return
        if playlist.getPerformanceModeState():
            h.lightPad(9,4,69,currentScreen)
        else:
            h.lightPad(9,4,"OFF",currentScreen)
        h.lightPad(9,2,"OFF",currentScreen)
        h.lightPad(9,3,"OFF",currentScreen)
        if self.viewDown:
            h.lightPad(9,1,"DARK_GRAY",currentScreen)
            h.lightPad(9,2,"OFF",currentScreen)
        else:
            h.lightPad(9,1,"OFF",currentScreen)
            h.lightPad(9,2,"DARK_GRAY",currentScreen)
            

    def updatePadsColor(self):
        viewButton = {0:89, 1:79, 2:69, 3:59, 4:49, 5:39, 6:29, 7:19}
        for i in range(1,9):
            h.lightPad(i,9,"OFF",0)
            #self.colorPad(viewButton[i],"OFF","STATIC")
        for row in range(1,9):
            for column in range(1,9):
                if column < 5:
                    h.lightPad(row,column,"DARK_GREEN",0)
                else:
                   h.lightPad(row,column,"BROWN",0) 
        if self.lastTimeVal == -1 and self.lastVolVal == -1: 
            self.updateSlots()

    def updateSlots(self):
        mixerIndex = mixer.getActiveEffectIndex()
        if self.mixerIndex != mixerIndex[0] or self.slotIndex != mixerIndex[1]:
            self.mixerIndex = mixerIndex[0]
            self.slotIndex = mixerIndex[1]
        timeSlot = round(plugins.getParamValue(0, self.mixerIndex, self.slotIndex)/0.02857)
        volSlot = round(plugins.getParamValue(1, self.mixerIndex, self.slotIndex)/0.02857)
        if timeSlot == self.lastTimeVal and volSlot == self.lastVolVal:
            return
        self.lastTimeVal = timeSlot
        self.lastVolVal = volSlot
        offset = 10 if self.viewDown else 0
        padTime = 81 + offset if timeSlot == 0 else round((timeSlot+1) - (14 * (floor(((timeSlot+1)-0.1)/4))-80)) + offset
        padVol = 85 + offset if volSlot == 0 else round((volSlot+1) - (14 * (floor(((volSlot+1)-0.1)/4))-84)) + offset
        if padTime > 9:
            self.colorPad(self.padSelectedTime,"DARK_GREEN", "STATIC")
            self.padSelectedTime = padTime
            self.colorPad(self.padSelectedTime,"LIGHT_GREEN", "PULSING")
        else:
            self.colorPad(self.padSelectedTime,"DARK_GREEN", "STATIC")
            self.padSelectedTime = padTime
        if padVol > 9:
            self.colorPad(self.padSelectedVol,"BROWN", "STATIC")
            self.padSelectedVol = padVol
            self.colorPad(self.padSelectedVol,"ORANGE", "PULSING")
        else:
            self.colorPad(self.padSelectedVol,"BROWN", "STATIC")
            self.padSelectedVol = padVol
    
    def colorPad(self,pad:int,color:str,state:str):
        h.lightPad(floor(pad/10),pad%10,color,0,state)