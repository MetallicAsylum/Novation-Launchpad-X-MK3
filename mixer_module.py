import mixer
import device
import time
import playlist
import helpers
h = helpers.Helper()

class MixerModule():
    def __init__(self) -> None:
        self.selectedView = 0 # 0: Volume, 1: Pan, 2: Stereo Sep, 3: Polarity 4: Channel Swap 5: Mute, 6: Solo, 7: Arm Disk
        self.timeSinceLastCall = 0
        self.calledByButton = False

    def reset(self):
        self.selectedView = 0
        self.timeSinceLastCall = 0
        self.calledByButton = False

    def OnMidiIn(self):
        self.activateDAWFader() #puts Session into DAW Fader Mode

    def OnMidiMsg(self, event):
        if event.data1 in [19, 29, 39, 49, 59, 69, 79, 89] and event.data2 == 127: #Press of Arrows under Novation Light
            viewButton = {19:7, 29:6, 39:5, 49:4, 59:3, 69:2, 79:1, 89:0}
            self.selectedView = viewButton[event.data1]
            self.updateMixerLayout(0, None)
        if event.data1 in [93, 94]: # Left and Right Arrow
            self.calledByButton = True
            if event.data2 == 127:
                h.lightPad(9,event.data1%10,"WHITE",0)
                event.handled = True
            if event.data2 == 0:
                if event.data1 == 93:
                    newTrack = 126 if self.selectedTrack == 0 else self.selectedTrack-1
                else:
                    newTrack = 0 if self.selectedTrack == 126 else self.selectedTrack+1
                mixer.setActiveTrack(newTrack)
                h.lightPad(9,3,"DARK_GRAY",0)
                event.handled = True

    def OnControlChange(self, event):
        #Handle each Fader Function for each different View
        mixerAction = {0:mixer.setTrackVolume,1:mixer.setTrackPan,2:mixer.setTrackStereoSep,3:mixer.revTrackPolarity,4:mixer.swapTrackChannels,5:mixer.muteTrack,6:mixer.soloTrack,7:mixer.armTrack}
        offset = self.getOffset()
        if (self.selectedView < 3):
            if (event.controlNum < 8):
                self.timeSinceLastCall = time.time()
                helpFunc = h.FaderPosToVol if self.selectedView == 0 else h.FaderPosToKnob
                mixerAction[self.selectedView]((self.selectedTrack+1) + (event.controlNum - offset), helpFunc(event.controlVal))
                event.handled = True
        elif (self.selectedView < 8):
            if event.controlNum > 10 and event.controlNum < 19 and event.controlVal > 0:
                valCheck = {3:mixer.isTrackRevPolarity,4:mixer.isTrackSwapChannels}
                if self.selectedView in [3,4]:
                    mode = False if valCheck[self.selectedView]((self.selectedTrack+1) + ((event.controlNum - 11) - offset)) else True
                else:
                    mode = -1
                mixerAction[self.selectedView]((self.selectedTrack+1) + ((event.controlNum - 11) - offset), mode)
                self.updateLights(layouts[self.selectedView])

    def activateDAWFader(self):
        #Sets Launchpad into DAW Fader Mode
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 13, 247]))

    def updateMixerLayout(self, currentScreen, flag):
        if (currentScreen in [0, 13] and self.selectedView < 3): # Current Screen in Session or DAW Fader, and Selected View has Faders
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 247])) # Makes sure Session is in DAW Fader
        self.updateLights(layouts[self.selectedView])
        self.setViewButton()

    def updateLights(self,view:str) -> None:
        if view == "VOL":
            # Sets to Regular DAW Fader
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 0,     0, 0, 0, 50,  1, 0, 1, 50,  2, 0, 2, 50, 3, 0, 3, 50,  4, 0, 4, 50, 5, 0, 5, 50,  6, 0, 6, 50,  7, 0, 7, 50,          247]))
        elif view in ["PAN", "STEREO"]:
            # Sets to Polar DAW Fader
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 1,     0, 1, 0, 50,  1, 1, 1, 50,  2, 1, 2, 50, 3, 1, 3, 50,  4, 1, 4, 50, 5, 1, 5, 50,  6, 1, 6, 50,  7, 1, 7, 50,          247]))
        else:
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 0, 247]))        #Sets Session to Session View, not DAW Fader
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 18, 1, 0, 0, 247])) #Clear Session
        self.selectedTrack = mixer.trackNumber()
        offset = self.getOffset()
        mixerAction = {"VOL":mixer.getTrackVolume, "PAN":mixer.getTrackPan, "STEREO":mixer.getTrackStereoSep, "POLARITY":mixer.isTrackRevPolarity, "SWAP":mixer.isTrackSwapChannels, "MUTE":mixer.isTrackMuted, "SOLO":mixer.isTrackSolo, "ARM":mixer.isTrackArmed}
        if view in ["VOL", "PAN", "STEREO"]:
            mode = "VOL" if view == "VOL" else "KNOB"
            for i in range(1, 9):
                h.lightPad(0,i,mixer.getTrackColor((self.selectedTrack+1) + ((i-1)-offset)),13,9)
                h.changeFaderValue(i,mixerAction[view]((self.selectedTrack+1) + ((i-1)-offset)),mode)
            h.lightPad(0,offset,"ORANGE",13)
        elif view in ["POLARITY", "SWAP", "MUTE", "SOLO", "ARM"]:
            for i in range(1, 9):
                if (mixerAction[view]((self.selectedTrack+1) + ((i-1) - offset))):
                    h.lightPad(1,i,mixer.getTrackColor((self.selectedTrack+1) + ((i-1) - offset)),0)
                else:
                    h.lightPad(1,i,mixer.getTrackColor((self.selectedTrack+1) + ((i-1) - offset)),0,"DULL")
            if mixerAction[view](self.selectedTrack):
                h.lightPad(1,offset,"ORANGE",0)
            else:
                h.lightPad(1,offset,"BROWN",0)

    def userMixerInteraction(self): #Called when User interacts with Mixer
        if time.time() - self.timeSinceLastCall <= 0.3:
            return
        self.timeSinceLastCall = 0
        layouts = {0:self.mixerVolume, 1:self.mixerPan, 2:self.mixerStereo, 3:self.mixerPolarity, 4:self.mixerSwapChannels, 5:self.mixerMute, 6:self.mixerSolo, 7:self.mixerRecordArm}
        layouts[self.selectedView]()

    def setViewButton(self): #Updates Arrows under Novation Logo
        if playlist.getPerformanceModeState():
            h.lightPad(9,1,"PURPLE",0)
        else:
            h.lightPad(9,1,"OFF",0)
        h.lightPad(9,2,"OFF",0)
        h.lightPad(9,3,"DARK_GRAY",0)
        h.lightPad(9,4,"DARK_GRAY",0)

        viewColor = {1:"LIGHT_GREEN", 2:"ORANGE", 3:"PURPLE", 4:"MAGENTA", 5:"CYAN", 6:"YELLOW", 7:"BLUE", 8:"RED"}
        for i in range(1,9):
            if i == self.selectedView+1:
                h.lightPad(9-i,9,viewColor[i],0)
            else:
                h.lightPad(9-i,9,"DARK_GRAY",0)

    def getOffset(self) -> int: #Gets track offset for extremes, with 0 being Master (least) and Current being 126 (most)
        if (self.selectedTrack - 3 <= 0):
            return self.selectedTrack+1
        elif (self.selectedTrack + 4 >= 126):
            return (self.selectedTrack - 119)+1
        else:
            return 4

layouts = {0:"VOL",1:"PAN",2:"STEREO",3:"POLARITY",4:"SWAP",5:"MUTE",6:"SOLO",7:"ARM"}