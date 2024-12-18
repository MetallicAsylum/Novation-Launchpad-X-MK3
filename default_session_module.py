import device
import channels
import playlist
import helpers
h = helpers.Helper()

class DefaultSessionModule():
    def __init__(self) -> None:
        self.pitchBendRange = 2 #In Semitones
        self.selectedView = 1 # Arrows under Novation Logo

    def reset(self):
        self.pitchBendRange = 2
        self.selectedView = 1

    def OnMidiMsg(self, event):
        if event.data1 in [19, 29, 39, 49, 59, 69, 79, 89] and event.data2 == 127: # Arrows under Novation Logo
            viewButton = {19:8, 29:7, 39:6, 49:5, 59:4, 69:3, 79:2, 89:1} #Views corresponding to arrows
            self.selectedView = viewButton[event.data1]
            self.updateLayout(13)

    def OnControlChange(self, event, chanNum):
        if chanNum < 0: #No selected channel
            return
        if event.controlNum == 8: #Pitch Bend Fader
            if channels.channelNumber(True) != -1:
                channels.setChannelPitch(channels.channelNumber(True), h.FaderPosToKnob(event.controlVal))
                event.handled = True

    def updateLayout(self, currentScreen):
        layouts = {1:self.lay0, 2:self.lay1, 3:self.lay2, 4:self.lay3, 5:self.lay4, 6:self.lay5, 7:self.lay6, 8:self.lay7}
        if (currentScreen in [0, 13]):
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 13, 247])) #DAW Fader Mode
        layouts[self.selectedView]()
        if not playlist.getPerformanceModeState():
            for i in range (1, 5):
                h.lightPad(9,i,"OFF",currentScreen)

        viewColor = {1:"LIGHT_GREEN", 2:"ORANGE", 3:"PURPLE", 4:"MAGENTA", 5:"CYAN", 6:"YELLOW", 7:"BLUE", 8:"RED"}
        for i in range(1,9): #Update Arrow Colors
            if i == self.selectedView:
                h.lightPad(9-i,9,viewColor[i],currentScreen)
            else:
                h.lightPad(9-i,9,"DARK_GRAY",currentScreen)
        if currentScreen == 0:
            for i in range(1,5):
                h.lightPad(9,i,"OFF",currentScreen)

    def lay0(self):
        #For all of these Sysex Messages, they just set the faders and corresponding CC messages to be assigned by User,
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 0,     0, 1, 11, 9,  1, 0, 12, 41,  2, 0, 13, 50, 3, 0, 14, 50,  4, 0, 15, 50, 5, 0, 16, 50,  6, 0, 17, 50,  7, 0, 18, 50,          247]))
        h.changeFaderValue(1,0,"KNOB")

    def lay1(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 0,     0, 0, 21, 50,  1, 0, 22, 50,  2, 0, 23, 50, 3, 0, 24, 50,  4, 0, 25, 50, 5, 0, 26, 50,  6, 0, 27, 50,  7, 0, 28, 50,          247]))

    def lay2(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 0,     0, 0, 31, 50,  1, 0, 32, 50,  2, 0, 33, 50, 3, 0, 34, 50,  4, 0, 35, 50, 5, 0, 36, 50,  6, 0, 37, 50,  7, 0, 38, 50,          247]))

    def lay3(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 0,     0, 0, 41, 50,  1, 0, 42, 50,  2, 0, 43, 50, 3, 0, 44, 50,  4, 0, 45, 50, 5, 0, 46, 50,  6, 0, 47, 50,  7, 0, 48, 50,          247]))

    def lay4(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 1,     0, 0, 51, 50,  1, 0, 52, 50,  2, 0, 53, 50, 3, 0, 54, 50,  4, 0, 55, 50, 5, 0, 56, 50,  6, 0, 57, 50,  7, 0, 58, 50,          247]))

    def lay5(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 1,     0, 0, 61, 50,  1, 0, 62, 50,  2, 0, 63, 50, 3, 0, 90, 50,  4, 0, 65, 50, 5, 0, 99, 50,  6, 0, 67, 50,  7, 0, 68, 50,          247]))

    def lay6(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 0,     0, 1, 71, 50,  1, 1, 72, 50,  2, 1, 73, 50, 3, 1, 74, 50,  4, 1, 75, 50, 5, 1, 76, 50,  6, 1, 77, 50,  7, 1, 78, 50,          247]))
        for i in range(1,9):
            h.changeFaderValue(i,0,"KNOB")
    def lay7(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 1,     0, 1, 81, 50,  1, 1, 82, 50,  2, 1, 83, 50, 3, 1, 84, 50,  4, 1, 85, 50, 5, 1, 86, 50,  6, 1, 87, 50,  7, 1, 88, 50,          247]))
        for i in range(1,9):
            h.changeFaderValue(i,0,"KNOB")