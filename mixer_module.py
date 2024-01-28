import mixer
import device
import time

class MixerModule():
    def __init__(self) -> None:
        self.selectedTrack = -1 
        self.selectedPlugin = -1 #Updates Up/Down arrows, allows picking of plugin
        self.selectedView = 0 # 0: Volume, 1: Pan, 2: Stereo Sep, 3: Polarity 4: Channel Swap 5: Mute, 6: Solo, 7: Arm Disk
        self.timeSinceLastCall = 0
        self.calledByButton = False

    def reset(self):
        self.selectedTrack = -1 
        self.selectedPlugin = -1
        self.selectedView = 0
        self.timeSinceLastCall = 0
        self.calledByButton = False

    def OnMidiIn(self):
        self.activateDAWFader() #puts Session into DAW Fader Mode

    def OnMidiMsg(self, event):
        if event.data1 in [19, 29, 39, 49, 59, 69, 79, 89] and event.data2 == 127: #Press of Arrows under Novation Light
            viewButton = {19:7, 29:6, 39:5, 49:4, 59:3, 69:2, 79:1, 89:0}
            if viewButton[event.data1] == self.selectedView:
                mixer.focusEditor(self.selectedTrack, self.selectedPlugin)
                return
            self.selectedView = viewButton[event.data1]
            self.updateMixerLayout(0, None)
        if event.data1 == 91: #Up Arrow
            if event.data2 == 127:
                self.updatePluginScrollArrows(0)
                event.handled = True
            if event.data2 == 0:
                event.handled = True
        if event.data1 == 92: #Down Arrow
            if event.data2 == 127:
                self.updatePluginScrollArrows(1)
                event.handled = True
            if event.data2 == 0:
                event.handled = True
        if event.data1 == 93: #Left Arrow
            self.calledByButton = True
            if event.data2 == 127:
                if self.selectedTrack == 0:
                    prevTrack = 126
                else:
                    prevTrack = self.selectedTrack - 1
                mixer.setActiveTrack(prevTrack)
                event.handled = True
                device.midiOutMsg(176, 144, 93, 3)
            if event.data2 == 0:
                event.handled = True
                device.midiOutMsg(176, 144, 93, 1)
        if event.data1 == 94: #Right Arrow
            if event.data2 == 127:
                self.calledByButton = True
                if self.selectedTrack == 126:
                    nextTrack = 0
                else:
                    nextTrack = self.selectedTrack + 1
                mixer.setActiveTrack(nextTrack)
                event.handled = True
                device.midiOutMsg(176, 144, 94, 3)
            if event.data2 == 0:
                event.handled = True
                device.midiOutMsg(176, 144, 94, 1)

    def OnControlChange(self, event):
        #Handle each Fader Function for each different View
        if (self.selectedView == 0): #Volume
            if (event.controlNum < 8):
                offset = self.getOffset()
                self.timeSinceLastCall = time.time()
                event.handled = True
                mixer.setTrackVolume(self.selectedTrack + (event.controlNum - offset), self.CCToVol(event.controlVal))
        if (self.selectedView == 1): #Pan
            if (event.controlNum < 8):
                offset = self.getOffset()
                self.timeSinceLastCall = time.time()
                event.handled = True
                mixer.setTrackPan(self.selectedTrack + (event.controlNum - offset), self.CCToKnob(event.controlVal))
        if (self.selectedView == 2): #Stereo Seperation
            if (event.controlNum < 8):
                offset = self.getOffset()
                self.timeSinceLastCall = time.time()
                event.handled = True
                mixer.setTrackStereoSep(self.selectedTrack + (event.controlNum - offset), self.CCToKnob(event.controlVal))
        if (self.selectedView == 3): #Reverse Polarity
            offset = self.getOffset()
            if event.controlNum > 10 and event.controlNum < 19 and event.controlVal > 0:
                if mixer.isTrackRevPolarity(self.selectedTrack + ((event.controlNum - 11) - offset)):
                    mixer.revTrackPolarity(self.selectedTrack + ((event.controlNum - 11) - offset), False)
                else:
                    mixer.revTrackPolarity(self.selectedTrack + ((event.controlNum - 11) - offset), True)
                self.mixerPolarity()
        if (self.selectedView == 4): #Swap Channels
            offset = self.getOffset()
            if event.controlNum > 10 and event.controlNum < 19 and event.controlVal > 0:
                if mixer.isTrackSwapChannels(self.selectedTrack + ((event.controlNum - 11) - offset)):
                    mixer.swapTrackChannels(self.selectedTrack + ((event.controlNum - 11) - offset), False)
                else:
                    mixer.swapTrackChannels(self.selectedTrack + ((event.controlNum - 11) - offset), True)
                self.mixerSwapChannels()
        if (self.selectedView == 5): #Mute Track
            offset = self.getOffset()
            if event.controlNum > 10 and event.controlNum < 19 and event.controlVal > 0:
                mixer.muteTrack(self.selectedTrack + ((event.controlNum - 11) - offset))
                self.mixerMute()
        if (self.selectedView == 6): #Solo Track
            offset = self.getOffset()
            if event.controlNum > 10 and event.controlNum < 19 and event.controlVal > 0:
                mixer.soloTrack(self.selectedTrack + ((event.controlNum - 11) - offset), -1, 3)
                self.mixerSolo()
        if (self.selectedView == 7): #Arm Track for Recording
            offset = self.getOffset()
            if event.controlNum > 10 and event.controlNum < 19 and event.controlVal > 0:
                mixer.armTrack(self.selectedTrack + ((event.controlNum - 11) - offset))
                self.mixerRecordArm()

    def activateDAWFader(self):
        #Sets Launchpad into DAW Fader Mode
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 13, 247]))

    def updateMixerLayout(self, currentScreen, flag):
        layouts = {0:self.mixerVolume, 1:self.mixerPan, 2:self.mixerStereo, 3:self.mixerPolarity, 4:self.mixerSwapChannels, 5:self.mixerMute, 6:self.mixerSolo, 7:self.mixerRecordArm}
        if (currentScreen in [0, 13] and self.selectedView < 3): # Current Screen in Session or DAW Fader, and Selected View has Faders
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 247]))
        if currentScreen in [0, 13]:
            if self.selectedTrack != mixer.trackNumber():
                self.updatePluginScrollArrows(-2)
            else:
                self.updatePluginScrollArrows(-1)
        layouts[self.selectedView]()
        self.setViewButton()
        
    def mixerVolume(self):
        #Sets DAW Faders
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 0,     0, 0, 0, 50,  1, 0, 1, 50,  2, 0, 2, 50, 3, 0, 3, 50,  4, 0, 4, 50, 5, 0, 5, 50,  6, 0, 6, 50,  7, 0, 7, 50,          247]))
        self.selectedTrack = mixer.trackNumber()
        offset = self.getOffset()
        for i in range(0, 8):
            device.midiOutMsg(180, 180, i, self.volToCC(mixer.getTrackVolume(self.selectedTrack + (i-offset))))
            device.midiOutMsg(181, 181, i, self.convertColor(mixer.getTrackColor(self.selectedTrack + (i-offset))))
        device.midiOutMsg(181, 181, offset, 96)
    
    def mixerPan(self):
        #Sets DAW Faders
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 1,     0, 1, 0, 50,  1, 1, 1, 50,  2, 1, 2, 50, 3, 1, 3, 50,  4, 1, 4, 50, 5, 1, 5, 50,  6, 1, 6, 50,  7, 1, 7, 50,          247]))
        self.selectedTrack = mixer.trackNumber()
        offset = self.getOffset()
        for i in range(0, 8):
            device.midiOutMsg(180, 180, i, self.knobToCC(mixer.getTrackPan(self.selectedTrack + (i-offset))))
            device.midiOutMsg(181, 181, i, self.convertColor(mixer.getTrackColor(self.selectedTrack + (i-offset))))
        device.midiOutMsg(181, 181, offset, 96)

    def mixerStereo(self):
        #Sets DAW Faders
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 1,     0, 1, 0, 50,  1, 1, 1, 50,  2, 1, 2, 50, 3, 1, 3, 50,  4, 1, 4, 50, 5, 1, 5, 50,  6, 1, 6, 50,  7, 1, 7, 50,          247]))
        self.selectedTrack = mixer.trackNumber()
        offset = self.getOffset()
        for i in range(0, 8):
            device.midiOutMsg(180, 180, i, self.knobToCC(mixer.getTrackStereoSep(self.selectedTrack + (i-offset))))
            device.midiOutMsg(181, 181, i, self.convertColor(mixer.getTrackColor(self.selectedTrack + (i-offset))))
        device.midiOutMsg(181, 181, offset, 96)

    def mixerMasterSend(self):
        #Sets DAW Faders
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 1, 0, 0,     0, 0, 0, 50,  1, 0, 1, 50,  2, 0, 2, 50, 3, 0, 3, 50,  4, 0, 4, 50, 5, 0, 5, 50,  6, 0, 6, 50,  7, 0, 7, 50,          247]))
        self.selectedTrack = mixer.trackNumber()
        offset = self.getOffset()
        for i in range(0, 8):
            if mixer.getRouteSendActive(self.selectedTrack + (i-offset), 0):
                device.midiOutMsg(180, 180, i, self.volToCC(mixer.getTrackVolume(self.selectedTrack + (i-offset))))
                device.midiOutMsg(181, 181, i, self.convertColor(mixer.getTrackColor(self.selectedTrack + (i-offset))))

        device.midiOutMsg(181, 181, offset, 96)
                
    def mixerPolarity(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 0, 247])) #Sets Session to Session View, not DAW Fader
        self.selectedTrack = mixer.trackNumber()
        offset = self.getOffset()
        for button in range(11, 19):
            if (mixer.isTrackRevPolarity(self.selectedTrack + ((button - 11) - offset))):
                color = self.convertColor(mixer.getTrackColor(self.selectedTrack + ((button - 11) - offset)))
            else:
                color = self.convertColorDull(mixer.getTrackColor(self.selectedTrack + ((button - 11) - offset)))
            device.midiOutMsg(144, 144, button, color)
        if mixer.isTrackRevPolarity(self.selectedTrack):
            device.midiOutMsg(144, 144, 11 + offset, 96)
        else:
            device.midiOutMsg(144, 144, 11 + offset, 10)

    def mixerSwapChannels(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 0, 247])) #Sets Session to Session View, not DAW Fader
        self.selectedTrack = mixer.trackNumber()
        offset = self.getOffset()
        for button in range(11, 19):
            if (mixer.isTrackSwapChannels(self.selectedTrack + ((button - 11) - offset))):
                color = self.convertColor(mixer.getTrackColor(self.selectedTrack + ((button - 11) - offset)))
            else:
                color = self.convertColorDull(mixer.getTrackColor(self.selectedTrack + ((button - 11) - offset)))
            device.midiOutMsg(144, 144, button, color)
        if mixer.isTrackSwapChannels(self.selectedTrack):
            device.midiOutMsg(144, 144, 11 + offset, 96)
        else:
            device.midiOutMsg(144, 144, 11 + offset, 10)

    def mixerMute(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 0, 247])) #Sets Session to Session View, not DAW Fader
        self.selectedTrack = mixer.trackNumber()
        offset = self.getOffset()
        for button in range(11, 19):
            if (mixer.isTrackMuted(self.selectedTrack + ((button - 11) - offset))):
                color = self.convertColorDull(mixer.getTrackColor(self.selectedTrack + ((button - 11) - offset)))
            else:
                color = self.convertColor(mixer.getTrackColor(self.selectedTrack + ((button - 11) - offset)))
            device.midiOutMsg(144, 144, button, color)
        if mixer.isTrackMuted(self.selectedTrack):
            device.midiOutMsg(144, 144, 11 + offset, 10)
        else:
            device.midiOutMsg(144, 144, 11 + offset, 96)

    def mixerSolo(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 0, 247])) #Sets Session to Session View, not DAW Fader
        self.selectedTrack = mixer.trackNumber()
        offset = self.getOffset()
        for button in range(11, 19):
            if (mixer.isTrackSolo(self.selectedTrack + ((button - 11) - offset))):
                color = self.convertColor(mixer.getTrackColor(self.selectedTrack + ((button - 11) - offset)))
            else:
                color = self.convertColorDull(mixer.getTrackColor(self.selectedTrack + ((button - 11) - offset)))
                
            device.midiOutMsg(144, 144, button, color)
        if mixer.isTrackSolo(self.selectedTrack):
            device.midiOutMsg(144, 144, 11 + offset, 96)
        else:
            device.midiOutMsg(144, 144, 11 + offset, 10)

    def mixerRecordArm(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 0, 247])) #Sets Session to Session View, not DAW Fader
        self.selectedTrack = mixer.trackNumber()
        offset = self.getOffset()
        for button in range(11, 19):
            if (mixer.isTrackArmed(self.selectedTrack + ((button - 11) - offset))):
                color = self.convertColor(mixer.getTrackColor(self.selectedTrack + ((button - 11) - offset)))
                mode = 146
            else:
                color = self.convertColorDull(mixer.getTrackColor(self.selectedTrack + ((button - 11) - offset)))
                mode = 144
            device.midiOutMsg(144, mode, button, color)
        if mixer.isTrackArmed(self.selectedTrack):
            device.midiOutMsg(144, 146, 11 + offset, 96)
        else:
            device.midiOutMsg(144, 144, 11 + offset, 10)

    def updatePluginScrollArrows(self, direction):
        self.selectedTrack = mixer.trackNumber()
        if not self.calledByButton:
            device.midiOutMsg(176, 144, 93, 1)
            device.midiOutMsg(176, 144, 94, 1)
        else:
            self.calledByButton = False
        if direction == -2: #Init and New Mixer
            self.selectedPlugin = -1
            device.midiOutMsg(176, 144, 91, 0)
            device.midiOutMsg(176, 144, 92, 0)
            for i in range(0,10):
                if mixer.isTrackPluginValid(self.selectedTrack, i):
                    self.selectedPlugin = i
                    self.updatePluginScrollArrows(-1)
                    break
            if self.selectedPlugin == -1:
                return    
        if direction == -1: #Update lights only
            if self.selectedPlugin < 1:
                device.midiOutMsg(176, 144, 91, 0)
            if self.selectedPlugin > 8:
                device.midiOutMsg(176, 144, 92, 0)
            for i in reversed(range(0, self.selectedPlugin)):
                if i < 1 and not mixer.isTrackPluginValid(self.selectedTrack, i):
                    device.midiOutMsg(176, 144, 91, 0)
                    break
                if mixer.isTrackPluginValid(self.selectedTrack, i):
                    device.midiOutMsg(176, 144, 91, (i+1) * 4)
                    break
            for i in range(self.selectedPlugin + 1, 10):
                if i > 8 and not mixer.isTrackPluginValid(self.selectedTrack, i):
                    device.midiOutMsg(176, 144, 92, 0)
                    break
                if mixer.isTrackPluginValid(self.selectedTrack, i):
                    device.midiOutMsg(176, 144, 92, (i+1) * 4)
                    break
        if direction == 0: #Up Arrow
            for i in reversed(range(0, self.selectedPlugin)):
                if mixer.isTrackPluginValid(self.selectedTrack, i):
                    self.selectedPlugin = i
                    break
            self.updatePluginScrollArrows(-1)
        if direction == 1: #Down Arrow
            for i in range(self.selectedPlugin + 1, 10):
                if mixer.isTrackPluginValid(self.selectedTrack, i):
                    self.selectedPlugin = i
                    break
            self.updatePluginScrollArrows(-1)



            
    def userMixerInteraction(self): #Called when User interacts with Mixer
        if time.time() - self.timeSinceLastCall <= 0.3:
            return
        self.timeSinceLastCall = 0
        layouts = {0:self.mixerVolume, 1:self.mixerPan, 2:self.mixerStereo, 3:self.mixerPolarity, 4:self.mixerSwapChannels, 5:self.mixerMute, 6:self.mixerSolo, 7:self.mixerRecordArm}
        layouts[self.selectedView]()

    def setViewButton(self): #Updates Arrows under Novation Logo
        viewColor = {0:21, 1:9, 2:49, 3:53, 4:33, 5:13, 6:79, 7:5}
        viewButton = {0:89, 1:79, 2:69, 3:59, 4:49, 5:39, 6:29, 7:19}
        for i in range(0,8):
            if i == self.selectedView:
                device.midiOutMsg(176, 144, viewButton[i], viewColor[self.selectedView])
            else:
                device.midiOutMsg(176, 144, viewButton[i], 1)

    def getOffset(self) -> int: #Gets track offset for extremes, with 0 being Master (least) and Current being 126 (most)
        if (self.selectedTrack - 3 <= 0):
            return self.selectedTrack
        elif (self.selectedTrack + 4 >= 126):
            return self.selectedTrack - 119
        else:
            return 3

    def volToCC(self, volume) -> int: #Volume to Fader Position
        if (volume <= 0.8):
            return round(volume * 135)
        else:
            return round((volume * 95) + 32)
        
    def CCToVol(self, CC) -> float: #Fader Position to Volume
        if (CC <= 108):
            return CC/135
        else:
            return ((CC-32)/95)
        
    def knobToCC(self, knob) -> int: #Knob Value to Fader Position
        if (knob < 0):
            return round(63 * (knob + 1))
        else:
            return round((63 * (knob + 1)) + 1)
        
    def CCToKnob(self, CC) -> float: #Fader Position to Knob Value
        if (CC <= 63):
            return (CC / 63) - 1
        else:
            return ((CC - 1) / 63) - 1

    def convertColor(self, color) -> int: #Convert gotten color to color in Launchpad X Color Palette
        RGBHex = hex(16777216 + color)
        RGBSplit = [RGBHex[i:i+2] for i in range(0, len(RGBHex), 2)]
        RGBInt = [int, int, int]
        for i in range(1,4):
            if (int(RGBSplit[i], 16) * 1.5) > 254:
                RGBInt[i-1] = 255
            else:
                RGBInt[i-1] = int(RGBSplit[i], 16) * 1.5
        return self.getPaletteColorFromRGB([RGBInt[0], RGBInt[1], RGBInt[2]])

    def convertColorDull(self, color) -> int: #Convert gotten color to color in Launchpad X Color Palette but less saturated
        RGBHex = hex(16777216 + color)
        RGBSplit = [RGBHex[i:i+2] for i in range(0, len(RGBHex), 2)]
        RGBInt = [int, int, int]
        for i in range(1,4):
            if (int(RGBSplit[i], 16) + 16) > 254:
                RGBInt[i-1] = 255
            else:
                RGBInt[i-1] = int(RGBSplit[i], 16) + 16
        return self.getPaletteColorFromRGB([RGBInt[0], RGBInt[1], RGBInt[2]])
    
    def getPaletteColorFromRGB(self, input: (int, int, int)) -> int: #Gets closest Palette Color to RGB
        best_palette_match = 0
        best_palette_match_distance = (0.3 * (input[0] - palette[0][0])**2) + (0.6 * (input[1] - palette[0][1])**2) + (0.1 * (input[2] - palette[0][2])**2)

        # we already checked [0]
        for i in range(1, len(palette)):
            distance = (0.3 * (input[0] - palette[i][0])**2) + (0.6 * (input[1] - palette[i][1])**2) + (0.1 * (input[2] - palette[i][2])**2)
            if distance < best_palette_match_distance:
                best_palette_match = i
                best_palette_match_distance = distance

        return best_palette_match + 1
# Pad 0 Removed, so all entries start from 1
palette = [ #Launchpad X Color Palette
(179,179,179),
(221,221,221),
(255,255,255),
(255,179,179),
(255,97,97),
(221,97,97),
(179,97,97),
(255,243,213),
(255,179,97), # Pad 9
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
(255,179,97), # Pad 96 changed to Pad 9 to keep color from being picked (Selection Color)
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