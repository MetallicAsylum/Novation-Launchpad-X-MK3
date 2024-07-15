import playlist
import device
import transport
import ui
from math import floor
import midi
from default_session import DefaultSessionModule
PerfFaderLayout = DefaultSessionModule()



class PerformanceModule():
    def __init__(self) -> None:
        self.isInPerformanceMode = 0 #0 if False, 1 if True
        self.padsToJump = 1 # Switches between 1 and 8 for faster navigation
        self.numberPadsHeld = 0 #Checks how many arrow pads are held to switch to fastNav
        self.currTab = 0 #0: Main View (Performance Mode), 1: Faders, 2: XY Pad, 3: Tempo Picker, 4: System Commands
        self.overviewMode = False
        self.XYLayoutSelect = 0
        self.XYPad0 = XYPad()
        self.XYPad1 = XYPad()
        self.XYPad2 = XYPad()
        self.XYPad3 = XYPad()
        self.XYPad4 = XYPad()
        self.XYPad5 = XYPad()
        self.XYPad6 = XYPad()
        self.XYPad7 = XYPad()
        self.updateXYCC()
        

        self.XOffset = 0 #Offset from Left
        self.YOffset = 0 #Offset from Track 1

    def reset(self):
        self.isInPerformanceMode = 0
        self.padsToJump = 1
        self.numberPadsHeld = 0
        self.currTab = 0
        self.overviewMode = False
        self.XYLayoutSelect = 0
        XYLayouts = {0:self.XYPad0,1:self.XYPad1,2:self.XYPad2,3:self.XYPad3,4:self.XYPad4,5:self.XYPad5,6:self.XYPad6,7:self.XYPad7}
        for i in range (0, 8):
            XYLayouts[i].reset()

        self.XOffset = 0 
        self.YOffset = 0

        PerfFaderLayout.reset()

    def updateXYCC(self):
        XYLayouts = {0:self.XYPad0,1:self.XYPad1,2:self.XYPad2,3:self.XYPad3,4:self.XYPad4,5:self.XYPad5,6:self.XYPad6,7:self.XYPad7}
        CC = 100
        for layout in range(0,8):
            XYLayouts[layout].XControlCC = CC
            CC += 1
            XYLayouts[layout].YControlCC = CC
            CC += 1

    def OnMidiMsg(self, event):
        midiRoute = {0:self.MidiMsgMain, 1:self.MidiMsgFaders, 2:self.MidiMsgXYPad, 3:self.MidiMsgTempoPicker, 4:self.MidiMsgSysCommands}
        if self.overviewMode:
            self.MidiMsgOverview(event)
            return
        midiRoute[self.currTab](event)

    def MidiMsgOutside(self, event):
        if event.data2 == 127:
            device.midiOutMsg(176, 176, event.data1, 3)
        else:
            ui.showWindow(2)
            ui.setFocused(2)
            self.updatePerformanceLayout(0, 500)

    def MidiMsgMain(self, event):
        if event.data1 in [19, 29, 39, 49, 59, 69, 79, 89]:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, event.data1, 3)
                event.handled = True
            else:
                padToTrack = {89:1,79:2,69:3,59:4,49:5,39:6,29:7,19:8}
                playlist.triggerLiveClip(padToTrack[event.data1] + self.YOffset, -1, 2) #Clear Row
                self.updatePerformanceLayout(0, 500)
        if event.data1 == 93 and event.data2 == 0 and self.numberPadsHeld == 1:
            if self.XOffset == 0:
                self.currTab += 1
                self.numberPadsHeld -= 1
                self.updatePerformanceLayout(0,500)
                return

        if event.data1 in [91, 92, 93, 94]:
            padToOperationAndLimit = {91:[self.YOffset,-1 * self.padsToJump,0,"Y"], 92:[-1 * self.YOffset, -1 * self.padsToJump,-499,"Y"],93:[self.XOffset,-1 * self.padsToJump,0,"X"],94:[-1 * self.XOffset, -1 * self.padsToJump, -99999999,"X"]}
            if event.data2 == 127:
                device.midiOutMsg(176, 176, event.data1, 3)
                self.numberPadsHeld += 1
                event.handled = True
            else:
                if self.numberPadsHeld >= 4:
                    self.padsToJump = 8 if self.padsToJump == 1 else 1
                    self.numberPadsHeld = -1
                elif self.numberPadsHeld == -4:
                    self.numberPadsHeld = 1
                elif self.numberPadsHeld < 0:
                    pass
                else:
                    if padToOperationAndLimit[event.data1][0] + padToOperationAndLimit[event.data1][1] <= padToOperationAndLimit[event.data1][2]:
                        if padToOperationAndLimit[event.data1][3] == "Y":
                            self.YOffset = padToOperationAndLimit[event.data1][2] if self.YOffset < 492 else 492
                        else:
                            self.XOffset = 0
                    else:
                        if padToOperationAndLimit[event.data1][3] == "Y":
                            self.YOffset += padToOperationAndLimit[event.data1][1] if padToOperationAndLimit[event.data1][2] > -1 else -1 * padToOperationAndLimit[event.data1][1]
                        else:
                            self.XOffset += padToOperationAndLimit[event.data1][1] if padToOperationAndLimit[event.data1][2] > -1 else -1 * padToOperationAndLimit[event.data1][1]

                color = 1 if self.padsToJump == 1 else 6
                if padToOperationAndLimit[event.data1][3] == "Y":
                    limit = padToOperationAndLimit[event.data1][2] if self.YOffset < 492 else 492
                    if self.YOffset == limit:
                        device.midiOutMsg(176, 176, event.data1, 0)
                    else:
                        device.midiOutMsg(176, 176, event.data1, color)
                else:
                    if self.XOffset == padToOperationAndLimit[event.data1][2]:
                        device.midiOutMsg(176, 176, event.data1, 0)
                    else:
                        device.midiOutMsg(176, 176, event.data1, color)
                self.updatePerformanceLayout(0, 500)
                self.numberPadsHeld -= 1
                playlist.liveDisplayZone(self.XOffset, self.YOffset + 1, self.XOffset + 8, self.YOffset + 9, 200)
                event.handled = True
            if self.XOffset == 0:
                if event.data1 != 93 and self.numberPadsHeld == 1:
                    device.midiOutMsg(176, 176, 93, 23)

    def MidiMsgOverview(self, event):
        if event.data1 == 89:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 89, 21)
            else:
                self.currTab = 1
                self.overviewMode = False
                self.updatePerformanceLayout(0, 500)
        if event.data1 == 79:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 79, 88)
            else:
                self.currTab = 2
                self.overviewMode = False
                self.updatePerformanceLayout(0, 500)
        if event.data1 == 69:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 69, 84)
            else:
                self.currTab = 3
                self.overviewMode = False
                self.updatePerformanceLayout(0, 500)
        if event.data1 == 59:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 89, 29)
            else:
                self.currTab = 4
                self.overviewMode = False
                self.updatePerformanceLayout(0, 500)
        event.handled = True


    def MidiMsgFaders(self, event):
        if event.data1 in [19, 29, 39, 49, 59, 69, 79, 89]:
            PerfFaderLayout.OnMidiMsg(event)
        if event.data1 == 93:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 93, 3)
            else:
                self.currTab += 1
                self.updatePerformanceLayout(0, 500)
        if event.data1 == 94:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 94, 3)
            else:
                self.currTab -= 1
                self.updatePerformanceLayout(0, 500)
        event.handled = True

    def MidiMsgXYPad(self, event):
        if event.data1 in [19, 29, 39, 49, 59, 69, 79, 89] and event.data2 == 0:
            self.XYLayoutSelect = 7 - floor(event.data1/10 - 1)
            self.XYPadLayout()
            for i in [19, 29, 39, 49, 59, 69, 79, 89]:
                device.midiOutMsg(176, 176, i, 1)
            device.midiOutMsg(176, 176, event.data1, 54)  
        if event.data1 == 93:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 93, 3)
            else:
                self.currTab += 1
                self.updatePerformanceLayout(0, 500)
        if event.data1 == 94:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 94, 3)
            else:
                self.currTab -= 1
                self.updatePerformanceLayout(0, 500)
        event.handled = True

    def MidiMsgTempoPicker(self, event):
        if event.data1 in [19, 29, 39, 49, 59, 69, 79, 89]:
            self.setTransportFunctions(event)
        if event.data1 == 93:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 93, 3)
            else:
                self.currTab += 1
                self.updatePerformanceLayout(0, 500)
        if event.data1 == 94:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 94, 3)
            else:
                self.currTab -= 1
                self.updatePerformanceLayout(0, 500)
        event.handled = True

    def MidiMsgSysCommands(self, event):
        if event.data1 in [19, 29, 39, 49, 59, 69, 79, 89]:
            self.setTransportFunctions(event)
        if event.data1 == 93:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 93, 3)
            else:
                self.currTab = 0
                self.updatePerformanceLayout(0, 500)
        if event.data1 == 94:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 94, 3)
            else:
                self.currTab -= 1
                self.updatePerformanceLayout(0, 500)
        event.handled = True

    def OnNoteOn(self, event):
        noteRoute = {0:self.OnNoteMain, 1:self.OnNoteFader, 2:self.OnNoteXY, 3:self.OnNoteTempo, 4:self.OnNoteSystem}
        if self.overviewMode:
            self.OnNoteOverview(event)
            return
        noteRoute[self.currTab](event)

    def OnNoteMain(self, event):
        if event.data2 == 0:
            event.handled = True
            return
        padToDisplay = {11 : 56,12 : 57,13 : 58,14 : 59,15 : 60,16 : 61,17 : 62,18 : 63,21 : 48,22 : 49,23 : 50,24 : 51,25 : 52,26 : 53,27 : 54,28 : 55,31 : 40,32 : 41,33 : 42,34 : 43,35 : 44,36 : 45,37 : 46,38 : 47,41 : 32,42 : 33,43 : 34,44 : 35,45 : 36,46 : 37,47 : 38,48 : 39,51 : 24,52 : 25,53 : 26,54 : 27,55 : 28,56 : 29,57 : 30,58 : 31,61 : 16,62 : 17,63 : 18,64 : 19,65 : 20,66 : 21,67 : 22,68 : 23,71 : 8,72 : 9,73 : 10,74 : 11,75 : 12,76 : 13,77 : 14,78 : 15,81 : 0,82 : 1,83 : 2,84 : 3,85 : 4,86 : 5,87 : 6,88 : 7}
        padTrack = floor(padToDisplay[event.data1]/8) + 1
        padNum = padToDisplay[event.data1] % 8
        if event.data2 > 0:
            if (playlist.getLiveTriggerMode(padTrack + self.YOffset) in [0, 1, 2]):
                if playlist.getLiveBlockStatus(padTrack + self.YOffset, padNum + self.XOffset, 1) == 0:
                    playlist.triggerLiveClip(padTrack + self.YOffset, -1, 2) #Clear Row
                    playlist.triggerLiveClip(padTrack + self.YOffset, padNum + self.XOffset, 32) #Release Note
                else: 
                    playlist.triggerLiveClip(padTrack + self.YOffset, padNum + self.XOffset, 2)
                
            elif (playlist.getLiveTriggerMode(padTrack + self.YOffset)) == 3:
                if (playlist.getLiveBlockStatus(padTrack + self.YOffset, padNum + self.XOffset, 1) != 2):
                    playlist.triggerLiveClip(padTrack + self.YOffset, padNum + self.XOffset, 2) #Play Clip
                    playlist.triggerLiveClip(padTrack + self.YOffset, padNum + self.XOffset, 1) #Mute Others
                else:
                    playlist.triggerLiveClip(padTrack + self.YOffset, -1, 2)
                    playlist.triggerLiveClip(padTrack + self.YOffset, padNum + self.XOffset, 2) #Play Clip
                    playlist.triggerLiveClip(padTrack + self.YOffset, -1, 2) #Stop All Clips
                event.handled = True
            else:
                padToDisplay = {11 : 56,12 : 57,13 : 58,14 : 59,15 : 60,16 : 61,17 : 62,18 : 63,21 : 48,22 : 49,23 : 50,24 : 51,25 : 52,26 : 53,27 : 54,28 : 55,31 : 40,32 : 41,33 : 42,34 : 43,35 : 44,36 : 45,37 : 46,38 : 47,41 : 32,42 : 33,43 : 34,44 : 35,45 : 36,46 : 37,47 : 38,48 : 39,51 : 24,52 : 25,53 : 26,54 : 27,55 : 28,56 : 29,57 : 30,58 : 31,61 : 16,62 : 17,63 : 18,64 : 19,65 : 20,66 : 21,67 : 22,68 : 23,71 : 8,72 : 9,73 : 10,74 : 11,75 : 12,76 : 13,77 : 14,78 : 15,81 : 0,82 : 1,83 : 2,84 : 3,85 : 4,86 : 5,87 : 6,88 : 7}
                if playlist.getLiveTriggerMode(padTrack + self.YOffset) == 1:
                    playlist.triggerLiveClip(padTrack + self.YOffset, -1, 2) #Stop All Clips
                if playlist.getLiveTriggerMode(padTrack + self.YOffset) == 2: #Unsure on how to make it keep moving? Might be bugged in FL
                    playlist.triggerLiveClip(padTrack + self.YOffset, -1, 32)
                    playlist.triggerLiveClip(padTrack + self.YOffset, padNum + self.XOffset, midi.TLC_Queue)
            
                #playlist.refreshLiveClips() #Refresh
            event.handled = True
        
    def OnNoteOverview(self, event):
        if event.data2 > 0:
            self.YOffset = (7 -(floor(event.data1/10)-1))* 8
            self.XOffset = ((event.data1%10)-1) * 8
            playlist.liveDisplayZone(self.XOffset, self.YOffset + 1, self.XOffset + 8, self.YOffset + 9, 200)
            self.overviewMode = False
            self.updatePerformanceLayout(0, 500)
        event.handled = True

    def OnNoteFader(self, event):
        print(end="")
        
    def OnNoteXY(self, event):
        XY = {0:self.XYPad0,1:self.XYPad1,2:self.XYPad2,3:self.XYPad3,4:self.XYPad4,5:self.XYPad5,6:self.XYPad6,7:self.XYPad7}
        XY[self.XYLayoutSelect].OnNoteOn(event)
        event.handled = True
        
    def OnNoteTempo(self, event):
        if event.data1 == 72:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 72, 88)
            else:
                transport.start()
        if event.data1 == 74:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 74, 5)
            else:
                transport.stop()
                device.midiOutMsg(144, 144, 74, 120)
        if event.data1 == 63:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 63, 108)
            else:
                transport.globalTransport(midi.FPT_Metronome, 127)

        if event.data1 == 43:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 43, 90)
            else:
                transport.globalTransport(midi.FPT_TapTempo, 127)
        if event.data1 == 32:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 32, 34)              
            else:
                transport.globalTransport(midi.FPT_NudgeMinus, 127)
        if event.data1 == 34:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 34, 33)
            else:
                transport.globalTransport(midi.FPT_NudgePlus, 127)

        if event.data1 == 76:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 76, 82)
            else:
                transport.globalTransport(midi.FPT_TempoJog, 50)
                device.midiOutMsg(144, 144, 76, 57)
        if event.data1 == 66:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 66, 54)
            else:
                transport.globalTransport(midi.FPT_TempoJog, 10)
                device.midiOutMsg(144, 144, 66, 58)
        if event.data1 == 56:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 56, 55)
            else:
                transport.globalTransport(midi.FPT_TempoJog, 1)
                device.midiOutMsg(144, 144, 56, 59)
        if event.data1 == 46:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 46, 46)
            else:
                transport.globalTransport(midi.FPT_TempoJog, -1)
                device.midiOutMsg(144, 144, 46, 51)
        if event.data1 == 36:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 36, 45)
            else:
                transport.globalTransport(midi.FPT_TempoJog, -10)
                device.midiOutMsg(144, 144, 36, 50)
        if event.data1 == 26:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 26, 44)
            else:
                transport.globalTransport(midi.FPT_TempoJog, -50)
                device.midiOutMsg(144, 144, 26, 49)
        
            
        event.handled = True
        
    def OnNoteSystem(self, event):
        if event.data1 == 82:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 82, 109)
            else:
                transport.globalTransport(midi.FPT_ChannelJog, -1)
                device.midiOutMsg(144, 144, 82, 13)
        if event.data1 == 62:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 62, 74)
            else:
                transport.globalTransport(midi.FPT_ChannelJog, 1)
                device.midiOutMsg(144, 144, 62, 99)
        if event.data1 == 71:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 71, 33)
            else:
                transport.globalTransport(midi.FPT_Previous, 1)
                device.midiOutMsg(144, 144, 71, 41)
        if event.data1 == 72:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 72, 88)
            else:
                transport.globalTransport(midi.FPT_Enter, 1)
                device.midiOutMsg(144, 144, 72, 25)
        if event.data1 == 73:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 73, 29)
            else:
                transport.globalTransport(midi.FPT_Next, 1)
                device.midiOutMsg(144, 144, 73, 37)
        if event.data1 == 85:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 85, 122)
            else:
                transport.globalTransport(midi.FPT_MarkerJumpJog, -1)
                device.midiOutMsg(144, 144, 85, 18)
        if event.data1 == 87:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 87, 88)
            else:
                transport.globalTransport(midi.FPT_MarkerJumpJog, 1)
                device.midiOutMsg(144, 144, 87, 17)
        if event.data1 == 76:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 76, 20)
            else:
                transport.globalTransport(midi.FPT_AddMarker, 1)
                device.midiOutMsg(144, 144, 76, 87)
        if event.data1 == 65:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 65, 84)
            else:
                transport.globalTransport(midi.FPT_MarkerSelJog, -1)
                device.midiOutMsg(144, 144, 65, 61)
        if event.data1 == 67:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 67, 108)
            else:
                transport.globalTransport(midi.FPT_MarkerSelJog, 1)
                device.midiOutMsg(144, 144, 67, 96)
        if event.data1 == 41:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 41, 44)
            else:
                if ui.getFocused(2):
                    ui.hideWindow(2)
                else:
                    ui.showWindow(2)
                    ui.setFocused(2)
                device.midiOutMsg(144, 144, 41, 45)
        if event.data1 == 42:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 42, 77)
            else:
                if ui.getFocused(1):
                    ui.hideWindow(1)
                else:
                    ui.showWindow(1)
                    ui.setFocused(1)
                device.midiOutMsg(144, 144, 42, 78)
        if event.data1 == 43:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 43, 88)
            else:
                if ui.getFocused(3):
                    ui.hideWindow(3)
                else:
                    ui.showWindow(3)
                    ui.setFocused(3)
                device.midiOutMsg(144, 144, 43, 21)
        if event.data1 == 44:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 44, 5)
            else:
                if ui.getFocused(4):
                    ui.hideWindow(4)
                else:
                    ui.showWindow(4)
                    ui.setFocused(4)
                device.midiOutMsg(144, 144, 44, 60)
        if event.data1 == 45:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 45, 96)
            else:
                if ui.getFocused(0):
                    ui.hideWindow(0)
                else:
                    ui.showWindow(0)
                    ui.setFocused(0)
                device.midiOutMsg(144, 144, 45, 61)
        if event.data1 == 21:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 21, 44)
            else:
                transport.globalTransport(midi.FPT_UndoUp, 1)
                device.midiOutMsg(144, 144, 21, 49)
        if event.data1 == 11:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 11, 69)
            else:
                transport.globalTransport(midi.FPT_UndoJog, 1)
                device.midiOutMsg(144, 144, 11, 51)
        if event.data1 == 23:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 23, 88)
            else:
                ui.snapMode(1)
                device.midiOutMsg(144, 144, 23, 122)
        if event.data1 == 13:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 13, 76)
            else:
                ui.snapMode(-1)
                device.midiOutMsg(144, 144, 13, 123)
        if event.data1 == 47:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 47, 81)
            else:
                ui.nextWindow()
                device.midiOutMsg(144, 144, 47, 53)
        if event.data1 == 48:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 48, 4)
            else:
                transport.globalTransport(midi.FPT_Escape, 1)
                device.midiOutMsg(144, 144, 48, 72)
        if event.data1 == 37:
            if event.data2 > 0:
                device.midiOutMsg(144, 144, 37, 95)
            else:
                transport.globalTransport(midi.FPT_WindowJog, -1)
                device.midiOutMsg(144, 144, 37, 58)
        event.handled = True
        

    def updatePerformanceLayout(self, currentScreen, lastTrack):
        if self.overviewMode:
            self.updateOverviewLayout()
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 20, 53, 52, 247])) #Change Session colors
            return
        else:
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 20, 49, 44, 247])) #Change Session colors
        self.isInPerformanceMode = playlist.getPerformanceModeState()
        if self.isInPerformanceMode:
            layouts = {0:self.updateLights, 1:self.faderBank, 2:self.XYPadLayout, 3:self.tempoPicker, 4:self.sysCommands}
            layouts[self.currTab]()

    def updateOverviewLayout(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 0, 247]))
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 18, 1, 0, 0, 247]))

        for i in range(91,95):
            device.midiOutMsg(176, 176, i, 0)

        viewButton = {0:89, 1:79, 2:69, 3:59, 4:49, 5:39, 6:29, 7:19}
        viewColor = {0:23, 1:122, 2:108, 3:68, 4:0, 5:0, 6:0, 7:0}
        for i in range(0,8):
            device.midiOutMsg(176, 176, viewButton[i], viewColor[i])
            
        for pad in range(11,89):
            isFilled = False
            isPlaying = False
            padColor = 0
            if pad%10 in [9,0]:
                continue
            for track in range(1,9):
                for row in range(0,8):
                    status = playlist.getLiveBlockStatus((7 -(floor(pad/10)-1))* 8 + track, ((pad%10)-1) * 8 + row, 2)
                    if status == 0:
                        continue
                    elif status == 1:
                        isFilled = True
                        if not isPlaying:
                            padColor = convertColor(playlist.getLiveBlockColor((7 -(floor(pad/10)-1))* 8 + track, ((pad%10)-1) * 8 + row))
                    else:
                        isFilled = True
                        isPlaying = True
                        padColor = convertColorVibrant(playlist.getLiveBlockColor((7 -(floor(pad/10)-1))* 8 + track, ((pad%10)-1) * 8 + row))
            if not isFilled:
                device.midiOutMsg(144, 144, pad, 0)
            elif not isPlaying:
                device.midiOutMsg(144, 144, pad, padColor)
            else:
                mode = 146 if transport.isPlaying() else 144
                device.midiOutMsg(144, mode, pad, padColor)
            
            device.midiOutMsg(144, 144, ((8 - floor(self.YOffset/8))* 10) + floor(self.XOffset/8) + 1, 2)
            


            
               
    def updateLights(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 0, 247]))
        if self.YOffset == 0:
            device.midiOutMsg(176, 176, 91, 0)
        else:
            device.midiOutMsg(176, 176, 91, 1)
        if self.YOffset == 492:
            device.midiOutMsg(176, 176, 92, 0)
        else:
            device.midiOutMsg(176, 176, 92, 1)
        if self.XOffset == 0:
            device.midiOutMsg(176, 176, 93, 23)
        else:
            device.midiOutMsg(176, 176, 93, 1)
        device.midiOutMsg(176, 176, 94, 1)


        displayToPad = {56 : 11,57 : 12,58 : 13,59 : 14,60 : 15,61 : 16,62 : 17,63 : 18,48 : 21,49 : 22,50 : 23,51 : 24,52 : 25,53 : 26,54 : 27,55 : 28,40 : 31,41 : 32,42 : 33,43 : 34,44 : 35,45 : 36,46 : 37,47 : 38,32 : 41,33 : 42,34 : 43,35 : 44,36 : 45,37 : 46,38 : 47,39 : 48,24 : 51,25 : 52,26 : 53,27 : 54,28 : 55,29 : 56,30 : 57,31 : 58,16 : 61,17 : 62,18 : 63,19 : 64,20 : 65,21 : 66,22 : 67,23 : 68,8 : 71,9 : 72,10 : 73,11 : 74,12 : 75,13 : 76,14 : 77,15 : 78,0 : 81,1 : 82,2 : 83,3 : 84,4 : 85,5 : 86,6 : 87,7 : 88}
        hasPlaying = False
        for i in range(self.YOffset + 1, self.YOffset + 9): #Tracks
            for j in range(self.XOffset, self.XOffset + 8): #Time in 4 Bars
                status = playlist.getLiveBlockStatus(i, j, 1)
                if status == 0:
                    device.midiOutMsg(144, 144, displayToPad[(((i - 1) - self.YOffset) * 8) + (j - self.XOffset)], 0)
                    continue
                elif status == 1:
                    device.midiOutMsg(144, 144, displayToPad[(((i - 1) - self.YOffset) * 8) + (j - self.XOffset)], convertColor(playlist.getLiveBlockColor(i, j)))
                elif status == 2:
                    device.midiOutMsg(144, 146, displayToPad[(((i - 1) - self.YOffset) * 8) + (j - self.XOffset)], convertColorVibrant(playlist.getLiveBlockColor(i, j)))
                    hasPlaying = True
                else:
                    if not transport.isPlaying() or playlist.getLiveLoopMode(i) > 0:
                        device.midiOutMsg(144, 144, displayToPad[(((i - 1) - self.YOffset) * 8) + (j - self.XOffset)], convertColorVibrant(playlist.getLiveBlockColor(i, j)))
                        hasPlaying = True
                    else:
                        device.midiOutMsg(144, 144, displayToPad[(((i - 1) - self.YOffset) * 8) + (j - self.XOffset)], convertColor(playlist.getLiveBlockColor(i, j)))
                        device.midiOutMsg(144, 145, displayToPad[(((i - 1) - self.YOffset) * 8) + (j - self.XOffset)], convertColorVibrant(playlist.getLiveBlockColor(i, j)))
                        hasPlaying = True
            trackToPad = {1:89,2:79,3:69,4:59,5:49,6:39,7:29,8:19}
            color = 2 if hasPlaying else 1
            device.midiOutMsg(176, 176, trackToPad[i-self.YOffset], color)
            hasPlaying = False

    def faderBank(self):
        PerfFaderLayout.updateLayout(0)
        device.midiOutMsg(176, 176, 91, 0)
        device.midiOutMsg(176, 176, 92, 0)
        device.midiOutMsg(176, 176, 93, 122)
        device.midiOutMsg(176, 176, 94, 69)
        

    def XYPadLayout(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 0, 247]))
        device.midiOutMsg(176, 176, 91, 0)
        device.midiOutMsg(176, 176, 92, 0)
        device.midiOutMsg(176, 176, 93, 108)
        device.midiOutMsg(176, 176, 94, 23)
        XYLayouts = {0:self.XYPad0,1:self.XYPad1,2:self.XYPad2,3:self.XYPad3,4:self.XYPad4,5:self.XYPad5,6:self.XYPad6,7:self.XYPad7}
        XYLayouts[self.XYLayoutSelect].updateLights()
        pad = {0:89,1:79,2:69,3:59,4:49,5:39,6:29,7:19}
        for i in [19, 29, 39, 49, 59, 69, 79, 89]:
                device.midiOutMsg(176, 176, i, 1)
        device.midiOutMsg(176, 176, pad[self.XYLayoutSelect], 54)

    def tempoPicker(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 0, 247]))
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 18, 1, 0, 0, 247]))
        device.midiOutMsg(176, 176, 91, 0)
        device.midiOutMsg(176, 176, 92, 0)
        device.midiOutMsg(176, 176, 93, 68)
        device.midiOutMsg(176, 176, 94, 122)
        self.setTransportLights()

        mode = 146 if transport.isPlaying() else 144
        device.midiOutMsg(144, mode, 72, 21)
        device.midiOutMsg(144, 144, 74, 6)
        color = 9 if ui.isMetronomeEnabled() else 11
        device.midiOutMsg(144, 144, 63, color)

        device.midiOutMsg(144, 144, 43, 29)
        device.midiOutMsg(144, 144, 32, 42)
        device.midiOutMsg(144, 144, 34, 41)

        device.midiOutMsg(144, 144, 76, 57)
        device.midiOutMsg(144, 144, 66, 58)
        device.midiOutMsg(144, 144, 56, 59)
        device.midiOutMsg(144, 144, 46, 51)
        device.midiOutMsg(144, 144, 36, 50)
        device.midiOutMsg(144, 144, 26, 49)

    def sysCommands(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 0, 247]))
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 18, 1, 0, 0, 247]))
        device.midiOutMsg(176, 176, 91, 0)
        device.midiOutMsg(176, 176, 92, 0)
        device.midiOutMsg(176, 176, 93, 69)
        device.midiOutMsg(176, 176, 94, 108)
        self.setTransportLights()

        device.midiOutMsg(144, 144, 82, 13)
        device.midiOutMsg(144, 144, 71, 41)
        device.midiOutMsg(144, 144, 72, 25)
        device.midiOutMsg(144, 144, 73, 37)
        device.midiOutMsg(144, 144, 62, 99)

        device.midiOutMsg(144, 144, 85, 18)
        device.midiOutMsg(144, 144, 87, 17)
        device.midiOutMsg(144, 144, 76, 87)
        device.midiOutMsg(144, 144, 65, 61)
        device.midiOutMsg(144, 144, 67, 96)

        device.midiOutMsg(144, 144, 41, 45)
        device.midiOutMsg(144, 144, 42, 78)
        device.midiOutMsg(144, 144, 43, 21)
        device.midiOutMsg(144, 144, 44, 60)
        device.midiOutMsg(144, 144, 45, 61)

        device.midiOutMsg(144, 144, 21, 49)
        device.midiOutMsg(144, 144, 11, 51)

        device.midiOutMsg(144, 144, 23, 122)
        device.midiOutMsg(144, 144, 13, 123)

        device.midiOutMsg(144, 144, 47, 53)
        device.midiOutMsg(144, 144, 37, 58)
        device.midiOutMsg(144, 144, 48, 72)





    def setTransportLights(self):
        device.midiOutMsg(176, 176, 89, 7) #Overdub
        device.midiOutMsg(176, 176, 79, 7) #Loop Recording
        device.midiOutMsg(176, 176, 69, 38) # Wait For Input
        device.midiOutMsg(176, 176, 59, 26) # Step Editing
        device.midiOutMsg(176, 176, 49, 84) #Countdown Before Recorrding
        color = 9 if ui.isMetronomeEnabled() else 11
        device.midiOutMsg(176, 176, 39, color) # Metronome
        device.midiOutMsg(176, 176, 29, 13) #Chan Up
        device.midiOutMsg(176, 176, 19, 99) #Chan Down

    def setTransportFunctions(self, event):
        if event.data1 == 89:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 89, 72)
            else:
                transport.globalTransport(midi.FPT_Overdub, 127)
        if event.data1 == 79:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 79, 72)
            else:
                transport.globalTransport(midi.FPT_LoopRecord, 127)
        if event.data1 == 69:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 69, 37)
            else:
                transport.globalTransport(midi.FPT_WaitForInput, 127)
        if event.data1 == 59:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 59, 25)
            else:
                transport.globalTransport(midi.FPT_StepEdit, 127)
                device.midiOutMsg(176, 176, 59, 26)
        if event.data1 == 49:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 49, 61)
            else:
                transport.globalTransport(midi.FPT_CountDown, 127)
        if event.data1 == 39:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 39, 108)
            else:
                transport.globalTransport(midi.FPT_Metronome, 127)
        if event.data1 == 29:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 29, 109)
            else:
                transport.globalTransport(midi.FPT_ChannelJog, -1)
                device.midiOutMsg(176, 176, 29, 13)
        if event.data1 == 19:
            if event.data2 == 127:
                device.midiOutMsg(176, 176, 19, 74)
            else:
                transport.globalTransport(midi.FPT_ChannelJog, 1)
                device.midiOutMsg(176, 176, 19, 99)
        event.handled = True


def convertColor(color) -> int: #Convert gotten color to color in Launchpad X Color Palette
        if color == 10462118:
             return 0
        if color > 0:
            RGBHex = hex(color)
        else:
            RGBHex = hex(16777216 + color)
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
        RGBSplit = [RGBHex[i:i+2] for i in range(0, len(RGBHex), 2)]
        RGBInt = [int, int, int]
        for i in range(1,4):
            if ((int(RGBSplit[i], 16) + 48) * 1.5) > 254:
                RGBInt[i-1] = 255
            else:
                RGBInt[i-1] = (int(RGBSplit[i], 16) + 48) * 1.5
        return getPaletteColorFromRGB([RGBInt[0], RGBInt[1], RGBInt[2]])

def getPaletteColorFromRGB(input: (int, int, int)) -> int: #Gets closest Palette Color to RGB # type: ignore
        best_palette_match = 0
        best_palette_match_distance = (0.3 * (input[0] - palette[0][0])**2) + (0.6 * (input[1] - palette[0][1])**2) + (0.1 * (input[2] - palette[0][2])**2)

        # we already checked [0]
        for i in range(1, len(palette)):
            distance = (0.3 * (input[0] - palette[i][0])**2) + (0.6 * (input[1] - palette[i][1])**2) + (0.1 * (input[2] - palette[i][2])**2)
            if distance < best_palette_match_distance:
                best_palette_match = i
                best_palette_match_distance = distance
        return best_palette_match + 1

class XYPad():
    def __init__(self) -> None:
        self.selectedPad = 81
        self.XControlCC = 0
        self.YControlCC = 0

    def reset(self):
        self.selectedPad = 81

    def OnNoteOn(self, event):
        color = 26 if self.selectedPad in [81,88,72,77,63,66,54,55,44,45,33,36,22,27,11,18] else 68
        device.midiOutMsg(144, 144, self.selectedPad, color)
        device.midiOutMsg(144, 144, event.data1, 54)
        self.selectedPad = event.data1
        device.forwardMIDICC(179 + (self.XControlCC << 8) + (50 << 16) + (0 << 24), 1)
        device.forwardMIDICC(179 + (self.YControlCC << 8) + (50 << 16) + (0 << 24), 1)

    def updateLights(self):
        line1 = 1
        line2 = 8
        for i in range(11,89):
            if i % 10 == 9:
                line1 += 1
                line2 -= 1
                continue
            if i % 10 == 0:
                continue
            if i % 10 in [line1, line2]:
                color = 26
            else:
                color = 68
            device.midiOutMsg(144, 144, i, color)
        device.midiOutMsg(144, 144, self.selectedPad, 54)


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
    