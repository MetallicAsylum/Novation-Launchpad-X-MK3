import playlist
import device
import transport
from math import floor
import time
import midi

class PerformanceModule():
    def __init__(self) -> None:
        self.isInPerformanceMode = 0 #0 if False, 1 if True

        self.XOffset = 0 #Offset from Left
        self.YOffset = 0 #Offset from Track 1

    def OnMidiMsg(self, event):
        if event.data1 == 91: #Up
            if event.data2 == 127:
                if self.YOffset != 0:
                    self.YOffset -= 1
                    device.midiOutMsg(176, 176, 91, 3)
                event.handled = True
            else:
                if self.YOffset == 0:
                    device.midiOutMsg(176, 176, 91, 0)
                else:
                    device.midiOutMsg(176, 176, 91, 1)
                self.updatePerformanceLayout(500)
                event.handled = True
        if event.data1 == 92: #Down
            if event.data2 == 127:
                if self.YOffset != 492:
                    self.YOffset += 1
                    device.midiOutMsg(176, 176, 92, 3)
                event.handled = True
            else:
                if self.YOffset == 492:
                    device.midiOutMsg(176, 176, 92, 0)
                else:
                    device.midiOutMsg(176, 176, 92, 1)
                self.updatePerformanceLayout(500)
                event.handled = True
        if event.data1 == 93: #Left
            if event.data2 == 127:
                if self.XOffset != 0:
                    self.XOffset -= 1
                    device.midiOutMsg(176, 176, 93, 3)
                event.handled = True
            else:
                if self.XOffset == 0:
                    device.midiOutMsg(176, 176, 93, 0)
                else:
                    device.midiOutMsg(176, 176, 93, 1)
                self.updatePerformanceLayout(500)
                event.handled = True
        if event.data1 == 94: #Right
            if event.data2 == 127:
                self.XOffset += 1
                device.midiOutMsg(176, 176, 94, 3)
                event.handled = True
            else:
                device.midiOutMsg(176, 176, 94, 1)
                self.updatePerformanceLayout(500)
                event.handled = True
        if event.data1 in [91, 92, 93, 94] and event.data2 == 127:
            playlist.liveDisplayZone(self.XOffset, self.YOffset + 1, self.XOffset + 8, self.YOffset + 9, 200)
        


    def OnNoteOn(self, event):
        padToDisplay = {64 : 0,65 : 1,66 : 2,67 : 3,96 : 4,97 : 5,98 : 6,99 : 7,60 : 8,61 : 9,62 : 10,63 : 11,92 : 12,93 : 13,94 : 14,95 : 15,56 : 16,57 : 17,58 : 18,59 : 19,88 : 20,89 : 21,90 : 22,91 : 23,52 : 24,53 : 25,54 : 26,55 : 27,84 : 28,85 : 29,86 : 30,87 : 31,48 : 32,49 : 33,50 : 34,51 : 35,80 : 36,81 : 37,82 : 38,83 : 39,44 : 40,45 : 41,46 : 42,47 : 43,76 : 44,77 : 45,78 : 46,79 : 47,40 : 48,41 : 49,42 : 50,43 : 51,72 : 52,73 : 53,74 : 54,75 : 55,36 : 56,37 : 57,38 : 58,39 : 59,68 : 60,69 : 61,70 : 62,71 : 63}
        padTrack = floor(padToDisplay[event.data1]/8) + 1
        padNum = padToDisplay[event.data1] % 8
        if event.data2 > 0:
            if (playlist.getLiveTriggerMode(padTrack + self.YOffset) in [0, 1, 2]):
                print("status:", playlist.getLiveBlockStatus(padTrack, padNum, 1))
                if playlist.getLiveBlockStatus(padTrack + self.YOffset, padNum + self.XOffset, 1) == 2:
                    playlist.triggerLiveClip(padTrack + self.YOffset, -1, 2)
                    playlist.triggerLiveClip(padTrack + self.YOffset, -1, 32)
                else:  
                    playlist.triggerLiveClip(padTrack + self.YOffset, padNum + self.XOffset, 2) #Play Clip
                playlist.triggerLiveClip(padTrack + self.YOffset, padNum + self.XOffset, 1) #Mute Others
            elif (playlist.getLiveTriggerMode(padTrack + self.YOffset)) == 3:
                if (playlist.getLiveBlockStatus(padTrack + self.YOffset, padNum + self.XOffset, 1) != 2):
                    playlist.triggerLiveClip(padTrack + self.YOffset, padNum + self.XOffset, 2) #Play Clip
                    playlist.triggerLiveClip(padTrack + self.YOffset, padNum + self.XOffset, 1) #Mute Others
                else:
                    playlist.triggerLiveClip(padTrack + self.YOffset, padNum + self.XOffset, 2) #Play Clip
                    playlist.triggerLiveClip(padTrack + self.YOffset, -1, 2) #Stop All Clips


            playlist.refreshLiveClips()
            event.handled = True
        else:
            padToDisplay = {64 : 0,65 : 1,66 : 2,67 : 3,96 : 4,97 : 5,98 : 6,99 : 7,60 : 8,61 : 9,62 : 10,63 : 11,92 : 12,93 : 13,94 : 14,95 : 15,56 : 16,57 : 17,58 : 18,59 : 19,88 : 20,89 : 21,90 : 22,91 : 23,52 : 24,53 : 25,54 : 26,55 : 27,84 : 28,85 : 29,86 : 30,87 : 31,48 : 32,49 : 33,50 : 34,51 : 35,80 : 36,81 : 37,82 : 38,83 : 39,44 : 40,45 : 41,46 : 42,47 : 43,76 : 44,77 : 45,78 : 46,79 : 47,40 : 48,41 : 49,42 : 50,43 : 51,72 : 52,73 : 53,74 : 54,75 : 55,36 : 56,37 : 57,38 : 58,39 : 59,68 : 60,69 : 61,70 : 62,71 : 63}
            if playlist.getLiveTriggerMode(padTrack + self.YOffset) == 1:
                playlist.triggerLiveClip(padTrack + self.YOffset, -1, 2) #Stop All Clips
            if playlist.getLiveTriggerMode(padTrack + self.YOffset) == 2: #Unsure on how to make it keep moving? Might be bugged in FL
                playlist.triggerLiveClip(padTrack + self.YOffset, -1, 32)
                playlist.triggerLiveClip(padTrack + self.YOffset, padNum + self.XOffset, midi.TLC_Queue)
            
            playlist.refreshLiveClips() #Refresh
            event.handled = True

    def updatePerformanceLayout(self, lastTrack):
        self.isInPerformanceMode = playlist.getPerformanceModeState()
        if self.isInPerformanceMode == 1:
            self.updateLights()
        else:
            print("yes")
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 15, 0, 247])) #Back to Default Note Mode
        #Update Direction Arrow Lights
        if self.YOffset == 0:
            device.midiOutMsg(176, 176, 91, 0)
        else:
            device.midiOutMsg(176, 176, 91, 1)
        if self.YOffset == 492:
            device.midiOutMsg(176, 176, 92, 0)
        else:
            device.midiOutMsg(176, 176, 92, 1)
        if self.XOffset == 0:
            device.midiOutMsg(176, 176, 93, 0)
        else:
            device.midiOutMsg(176, 176, 93, 1)
        device.midiOutMsg(176, 176, 94, 1)
        

    def updateLights(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 15, 1, 247]))
        displayToPad = {7 : 99,6 : 98,5 : 97,4 : 96,15 : 95,14 : 94,13 : 93,12 : 92,23 : 91,22 : 90,21 : 89,20 : 88,31 : 87,30 : 86,29 : 85,28 : 84,39 : 83,38 : 82,37 : 81,36 : 80,47 : 79,46 : 78,45 : 77,44 : 76,55 : 75,54 : 74,53 : 73,52 : 72,63 : 71,62 : 70,61 : 69,60 : 68,3 : 67,2 : 66,1 : 65,0 : 64,11 : 63,10 : 62,9 : 61,8 : 60,19 : 59,18 : 58,17 : 57,16 : 56,27 : 55,26 : 54,25 : 53,24 : 52,35 : 51,34 : 50,33 : 49,32 : 48,43 : 47,42 : 46,41 : 45,40 : 44,51 : 43,50 : 42,49 : 41,48 : 40,59 : 39,58 : 38,57 : 37,56 : 36}
        for i in range(self.YOffset + 1, self.YOffset + 9): #Tracks
            for j in range(self.XOffset, self.XOffset + 8): #Time in 4 Bars
                status = playlist.getLiveBlockStatus(i, j, 1)
                if status == 0:
                    device.midiOutMsg(152, 152, displayToPad[(((i - 1) - self.YOffset) * 8) + (j - self.XOffset)], 0)
                    continue
                elif status == 1:
                    device.midiOutMsg(152, 152, displayToPad[(((i - 1) - self.YOffset) * 8) + (j - self.XOffset)], convertColor(playlist.getLiveBlockColor(i, j)))
                elif status == 2:
                    device.midiOutMsg(152, 154, displayToPad[(((i - 1) - self.YOffset) * 8) + (j - self.XOffset)], convertColorVibrant(playlist.getLiveBlockColor(i, j)))
                else:
                    if not transport.isPlaying() or playlist.getLiveLoopMode(i) > 0:
                        device.midiOutMsg(152, 152, displayToPad[(((i - 1) - self.YOffset) * 8) + (j - self.XOffset)], convertColorVibrant(playlist.getLiveBlockColor(i, j)))
                    else:
                        device.midiOutMsg(152, 152, displayToPad[(((i - 1) - self.YOffset) * 8) + (j - self.XOffset)], convertColor(playlist.getLiveBlockColor(i, j)))
                        device.midiOutMsg(152, 153, displayToPad[(((i - 1) - self.YOffset) * 8) + (j - self.XOffset)], convertColorVibrant(playlist.getLiveBlockColor(i, j)))

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

def convertColorVibrant(color) -> int: #Convert gotten color to color in Launchpad X Color Palette, but much brighter
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
            if ((int(RGBSplit[i], 16) + 48) * 1.5) > 254:
                RGBInt[i-1] = 255
            else:
                RGBInt[i-1] = (int(RGBSplit[i], 16) + 48) * 1.5
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
        return best_palette_match + 1

palette = [ #Launchpad X Color Palette
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
    