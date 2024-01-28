import device
import channels
import plugins

class DefaultSessionModule():
    def __init__(self) -> None:
        self.pitchBendRange = 2 #In Semitones
        self.selectedView = 0 # Arrows under Novation Logo

    def reset(self):
        self.pitchBendRange = 2
        self.selectedView = 0

    def OnMidiMsg(self, event):
        if event.data1 in [19, 29, 39, 49, 59, 69, 79, 89] and event.data2 == 127: # Arrows under Novation Logo
            viewButton = {19:7, 29:6, 39:5, 49:4, 59:3, 69:2, 79:1, 89:0} #Views corresponding to arrows
            self.selectedView = viewButton[event.data1]
            self.updateLayout(13)

    def OnControlChange(self, event, chanNum):
        if chanNum < 0: #No selected channel
            return
        if event.controlNum == 8: #Pitch Bend Fader
            if channels.channelNumber(True) != -1:
                channels.setChannelPitch(channels.channelNumber(True), self.CCToKnob(event.controlVal))
                event.handled = True

    def updateLayout(self, currentScreen):
        layouts = {0:self.lay0, 1:self.lay1, 2:self.lay2, 3:self.lay3, 4:self.lay4, 5:self.lay5, 6:self.lay6, 7:self.lay7}
        if (currentScreen in [0, 13]):
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 13, 247])) #DAW Fader Mode
        layouts[self.selectedView]()
        #if channels.channelNumber(True) != -1:
            #if plugins.isValid(channels.channelNumber(True),-1,True):
                #self.pitchBendRange = channels.getChannelPitch(channels.channelNumber(True), 2, True)

        viewColor = {0:21, 1:9, 2:49, 3:53, 4:33, 5:13, 6:79, 7:5}
        viewButton = {0:89, 1:79, 2:69, 3:59, 4:49, 5:39, 6:29, 7:19}
        for i in range(0,8): #Update Arrow Colors
            if i == self.selectedView:
                device.midiOutMsg(176, 144, viewButton[i], viewColor[self.selectedView])
            else:
                device.midiOutMsg(176, 144, viewButton[i], 1)
        if currentScreen == 0:
            for i in range(91,95):
                device.midiOutMsg(176, 176, i, 0)



    def lay0(self):
        #For all of these Sysex Messages, they just set the faders and corresponding CC messages to be assigned by User,
        #except CC0-8 which 0-7 is Mixer and 8 is Pitch Bend
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 0,     0, 1, 8, 9,  1, 0, 9, 41,  2, 0, 10, 50, 3, 0, 11, 50,  4, 0, 12, 50, 5, 0, 13, 50,  6, 0, 14, 50,  7, 0, 15, 50,          247]))
        #if channels.channelNumber(True) == -1:
            #return
        #if plugins.isValid(channels.channelNumber(True),-1,True):
            #print("chan:", channels.channelNumber())
            #device.midiOutMsg(180, 180, 8, self.knobToCC(channels.getChannelPitch(channels.selectedChannel(True),0,True)))

                

    def lay1(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 0,     0, 0, 16, 50,  1, 0, 17, 50,  2, 0, 18, 50, 3, 0, 19, 50,  4, 0, 20, 50, 5, 0, 21, 50,  6, 0, 22, 50,  7, 0, 23, 50,          247]))

    def lay2(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 0,     0, 0, 24, 50,  1, 0, 25, 50,  2, 0, 26, 50, 3, 0, 27, 50,  4, 0, 28, 50, 5, 0, 29, 50,  6, 0, 30, 50,  7, 0, 31, 50,          247]))

    def lay3(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 0,     0, 0, 32, 50,  1, 0, 33, 50,  2, 0, 34, 50, 3, 0, 35, 50,  4, 0, 36, 50, 5, 0, 37, 50,  6, 0, 38, 50,  7, 0, 39, 50,          247]))

    def lay4(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 0,     0, 0, 40, 50,  1, 0, 41, 50,  2, 0, 42, 50, 3, 0, 43, 50,  4, 0, 44, 50, 5, 0, 45, 50,  6, 0, 46, 50,  7, 0, 47, 50,          247]))

    def lay5(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 0,     0, 0, 48, 50,  1, 0, 49, 50,  2, 0, 50, 50, 3, 0, 51, 50,  4, 0, 52, 50, 5, 0, 53, 50,  6, 0, 54, 50,  7, 0, 55, 50,          247]))

    def lay6(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 0,     0, 0, 56, 50,  1, 0, 57, 50,  2, 0, 58, 50, 3, 0, 59, 50,  4, 0, 60, 50, 5, 0, 61, 50,  6, 0, 62, 50,  7, 0, 63, 50,          247]))

    def lay7(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 0,     0, 0, 64, 50,  1, 0, 65, 50,  2, 0, 66, 50, 3, 0, 67, 50,  4, 0, 68, 50, 5, 0, 69, 50,  6, 0, 70, 50,  7, 0, 71, 50,          247]))

    def knobToCC(self, knob) -> int: #Knob Value to Fader Position
        print("knob:", knob)
        if (knob < 0):
            return round(63 * (knob + 1))
        else:
            return round((63 * (knob + 1)) + 1)
        
    def CCToKnob(self, CC) -> float: #Fader Position to Knob Value
        if (CC <= 63):
            return (CC / 63) - 1
        else:
            return ((CC - 1) / 63) - 1