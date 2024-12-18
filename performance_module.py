import playlist
import device
import transport
import ui
from math import floor
import midi
import helpers
import default_session_module
PerfFaderLayout = default_session_module.DefaultSessionModule()
h = helpers.Helper()



class PerformanceModule():
    def __init__(self) -> None:
        self.isInPerformanceMode = 0 #0 if False, 1 if True
        self.padsToJump = 1 # Switches between 1 and 8 for faster navigation
        self.numberPadsHeld = 0 #Checks how many arrow pads are held to switch to fastNav
        self.currTab = 0 #0: Main View (Performance Mode), 1: Faders, 2: XY Pad, 3: Tempo Picker, 4: System Commands
        self.overviewMode = False
        self.XYLayoutSelect = 0
        self.XYPads = [XYPad(), XYPad(), XYPad(), XYPad(), XYPad(), XYPad(), XYPad(), XYPad()]
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
        for XY in self.XYPads:
            XY.reset()
        self.XOffset = 0 
        self.YOffset = 0
        PerfFaderLayout.reset()

    def padToLightPad(self,pad:int,color,view:int):
        h.lightPad(floor(pad/10),pad%10,color,view)

    def toggleOverviewMode(self):
        self.overviewMode = not self.overviewMode
        self.updatePerformanceLayout()

    def updateXYCC(self):
        CC = 100
        for layout in range(0,8):
            self.XYPads[layout].XControlCC = CC
            CC += 1
            self.XYPads[layout].YControlCC = CC
            CC += 1

    def OnMidiMsg(self, event):
        if self.overviewMode:
            self.MidiMsgOverview(event)
            return
        if self.currTab == 0:
            self.MidiMsgMain(event)
            return
        midiMsgAction = {1:PerfFaderLayout.OnMidiMsg,2:self.XYPadLayout,3:self.setTransportFunctions,4:self.setTransportFunctions}
        if event.data1 in [19, 29, 39, 49, 59, 69, 79, 89]:
            if self.currTab == 2:
                self.XYLayoutSelect = 7 - floor(event.data1/10 - 1)
            midiMsgAction[self.currTab](event)
        self.updateCurrentTab(event)
        event.handled = True

    def MidiMsgOutside(self, event):
        if event.data2 == 127:
            self.padToLightPad(event.data1,"DARK_GRAY",0)
        else:
            ui.showWindow(2)
            ui.setFocused(2)

    def MidiMsgMain(self, event):
        if event.data1 in [19, 29, 39, 49, 59, 69, 79, 89]:
            if event.data2 == 127:
                self.padToLightPad(event.data1,"DARK_GRAY",0)
                event.handled = True
            else:
                padToTrack = {89:1,79:2,69:3,59:4,49:5,39:6,29:7,19:8}
                playlist.triggerLiveClip(padToTrack[event.data1] + self.YOffset, -1, 2) #Clear Row
                self.updatePerformanceLayout()
        if event.data1 == 93 and event.data2 == 0 and self.numberPadsHeld == 1:
            if self.XOffset == 0:
                self.currTab += 1
                self.numberPadsHeld -= 1
                self.updatePerformanceLayout()
                return

        if event.data1 in [91, 92, 93, 94]:
            padOperationAndLimit = {91:[self.YOffset,-1 * self.padsToJump,0,"Y"], 92:[-1 * self.YOffset, -1 * self.padsToJump,-499,"Y"],93:[self.XOffset,-1 * self.padsToJump,0,"X"],94:[-1 * self.XOffset, -1 * self.padsToJump, -99999999,"X"]}
            if event.data2 == 127:
                self.padToLightPad(event.data1,"DARK_GRAY",0)
                self.numberPadsHeld += 1
                event.handled = True
            else:
                currentSpace = padOperationAndLimit[event.data1][0]
                offsetChange = padOperationAndLimit[event.data1][1]
                limit = padOperationAndLimit[event.data1][2]
                coordinate = padOperationAndLimit[event.data1][3]
                if self.numberPadsHeld >= 4:
                    self.padsToJump = 8 if self.padsToJump == 1 else 1
                    self.numberPadsHeld = -1
                elif self.numberPadsHeld == -4:
                    self.numberPadsHeld = 1
                elif self.numberPadsHeld < 0:
                    pass
                else:
                    if currentSpace + offsetChange <= limit:
                        if coordinate == "Y":
                            self.YOffset = 0 if self.YOffset < 492 else 492
                        else:
                            self.XOffset = 0
                    else:
                        if coordinate == "Y":
                            self.YOffset += offsetChange if limit > -1 else -1 * offsetChange
                        else:
                            self.XOffset += offsetChange if limit > -1 else -1 * offsetChange

                color = "DARK_GRAY" if self.padsToJump == 1 else "DARK_RED"
                if coordinate == "Y":
                    limit = limit if self.YOffset < 492 else 492
                    if self.YOffset == limit:
                        self.padToLightPad(event.data1,"OFF",0)
                    else:
                        self.padToLightPad(event.data1,color,0)
                else:
                    if self.XOffset == limit:
                        self.padToLightPad(event.data1,"OFF",0)
                    else:
                        self.padToLightPad(event.data1,color,0)
                self.updatePerformanceLayout()
                self.numberPadsHeld -= 1
                playlist.liveDisplayZone(self.XOffset, self.YOffset + 1, self.XOffset + 8, self.YOffset + 9, 200)
                event.handled = True
            if self.XOffset == 0:
                if event.data1 != 93 and self.numberPadsHeld == 1:
                    h.lightPad(9,3,"DARK_GREEN",0)

    def MidiMsgOverview(self, event):
        # Pad 79 is LIGHT Light Green
        color = {89:"LIGHT_GREEN",79:88,69:"ORANGE",59:"CYAN"}
        if event.data1 in [89,79,69,59]:
            if event.data2 == 127:
                self.padToLightPad(event.data1,color[event.data1],0)
            else:
                self.currTab = 9-floor(event.data1/10)
                self.overviewMode = False
                self.updatePerformanceLayout()
        event.handled = True

    def updateCurrentTab(self, event):
        if event.data1 in [93,94]:
            if event.data2 == 127:
                self.padToLightPad(event.data1,"DARK_GRAY",0)
            else:
                h.clearPads(0)
                jump = 1 if event.data1 == 93 else -1
                self.currTab += jump
                if self.currTab == 5:
                    self.currTab = 0
                self.updatePerformanceLayout()

    def OnNoteOn(self, event):
        noteRoute = {0:self.OnNoteMain, 2:self.OnNoteXY, 3:self.OnNoteTempo, 4:self.OnNoteSystem}
        if self.overviewMode:
            self.OnNoteOverview(event)
            return
        if not self.currTab == 1:
            noteRoute[self.currTab](event)

    def OnNoteMain(self, event):
        if event.data2 == 0:
            event.handled = True
            return
        padToDisplay = {11 : 56,12 : 57,13 : 58,14 : 59,15 : 60,16 : 61,17 : 62,18 : 63,21 : 48,22 : 49,23 : 50,24 : 51,25 : 52,26 : 53,27 : 54,28 : 55,31 : 40,32 : 41,33 : 42,34 : 43,35 : 44,36 : 45,37 : 46,38 : 47,41 : 32,42 : 33,43 : 34,44 : 35,45 : 36,46 : 37,47 : 38,48 : 39,51 : 24,52 : 25,53 : 26,54 : 27,55 : 28,56 : 29,57 : 30,58 : 31,61 : 16,62 : 17,63 : 18,64 : 19,65 : 20,66 : 21,67 : 22,68 : 23,71 : 8,72 : 9,73 : 10,74 : 11,75 : 12,76 : 13,77 : 14,78 : 15,81 : 0,82 : 1,83 : 2,84 : 3,85 : 4,86 : 5,87 : 6,88 : 7}
        padTrack = floor(padToDisplay[event.data1]/8) + 1
        padNum = padToDisplay[event.data1] % 8
        padYOffset = padTrack + self.YOffset
        padXOffset = padNum + self.XOffset
        if event.data2 > 0:
            if playlist.getLiveTriggerMode(padYOffset) in [0, 1, 2]:
                if playlist.getLiveBlockStatus(padYOffset,padXOffset, 1) == 0:
                    playlist.triggerLiveClip(padYOffset, -1, 2) #Clear Row
                    playlist.triggerLiveClip(padYOffset,padXOffset, 32) #Release Note
                else: 
                    playlist.triggerLiveClip(padYOffset,padXOffset, 2)
                
            elif playlist.getLiveTriggerMode(padYOffset) == 3:
                if (playlist.getLiveBlockStatus(padYOffset,padXOffset, 1) != 2):
                    playlist.triggerLiveClip(padYOffset,padXOffset, 2) #Play Clip
                    playlist.triggerLiveClip(padYOffset,padXOffset, 1) #Mute Others
                else:
                    playlist.triggerLiveClip(padYOffset, -1, 2)
                    playlist.triggerLiveClip(padYOffset,padXOffset, 2) #Play Clip
                    playlist.triggerLiveClip(padYOffset, -1, 2) #Stop All Clips
                event.handled = True
            else:
                if playlist.getLiveTriggerMode(padYOffset) == 1:
                    playlist.triggerLiveClip(padYOffset, -1, 2) #Stop All Clips
                if playlist.getLiveTriggerMode(padYOffset) == 2: #Unsure on how to make it keep moving? Might be bugged in FL
                    playlist.triggerLiveClip(padYOffset, -1, 32)
                    playlist.triggerLiveClip(padYOffset, padNum + self.XOffset, midi.TLC_Queue)
            event.handled = True
        
    def OnNoteOverview(self, event):
        if event.data2 > 0:
            self.YOffset = (7 -(floor(event.data1/10)-1))* 8
            self.XOffset = ((event.data1%10)-1) * 8
            playlist.liveDisplayZone(self.XOffset, self.YOffset + 1, self.XOffset + 8, self.YOffset + 9, 200)
            self.overviewMode = False
            self.updatePerformanceLayout()
        event.handled = True
        
    def OnNoteXY(self, event):
        self.XYPads[self.XYLayoutSelect].OnNoteOn(event)
        event.handled = True
        
    def OnNoteTempo(self, event):
        globTransColorFuncVal = {63:[108,midi.FPT_Metronome,127],43:[90,midi.FPT_TapTempo,127],
                            32:[34,midi.FPT_NudgeMinus,127],34:["CYAN",midi.FPT_NudgePlus,127],
                            76:[82,midi.FPT_TempoJog,50],66:[54,midi.FPT_TempoJog,10],
                            56:[55,midi.FPT_TempoJog,1],46:[50,midi.FPT_TempoJog, -1],
                            36:["PURPLE",midi.FPT_TempoJog, -10],26:[44,midi.FPT_TempoJog, -50],
                            72:[88,transport.start],74:["RED",transport.stop]}
        try:
            color = globTransColorFuncVal[event.data1][0]
            operation = globTransColorFuncVal[event.data1][1]
            if event.data2 > 0:
                self.padToLightPad(event.data1,color,0)
            else:
                if event.data1 not in [72,74]:
                    value = globTransColorFuncVal[event.data1][2]
                    transport.globalTransport(operation,value)
                else:
                    operation()
            event.handled = True
        except KeyError:
            self.padToLightPad(event.data1,"OFF",0)
            event.handled = True
        
    def OnNoteSystem(self, event):
        globTransColorFuncVal = {82:[109,midi.FPT_ChannelJog,-1],62:[74,midi.FPT_ChannelJog,1],
                         71:[33,midi.FPT_Previous,1],72:[88,midi.FPT_Enter,1],
                         73:[29,midi.FPT_Next,1],85:[122,midi.FPT_MarkerJumpJog,-1],
                         87:[88,midi.FPT_MarkerJumpJog,1],76:[20,midi.FPT_AddMarker,1],
                         65:[84,midi.FPT_MarkerSelJog,-1],67:[108,midi.FPT_MarkerSelJog,1],
                         41:[44,2],42:[77,1],43:[88,3],44:["RED",4],45:[61,0],21:[44,midi.FPT_UndoUp,1],
                         11:[69,midi.FPT_UndoJog,1],48:[4,midi.FPT_Escape,1],37:[95,midi.FPT_WindowJog,-1],
                         23:[88,ui.snapMode,1],13:[76,ui.snapMode,-1],47:[81,ui.nextWindow]}
        try:
            color = globTransColorFuncVal[event.data1][0]
            operation = globTransColorFuncVal[event.data1][1]
            if event.data2 > 0:
                self.padToLightPad(event.data1,color,0)
            else:
                if event.data1 in range(41,46):
                    if ui.getFocused(operation):
                        ui.hideWindow(operation)
                    else:
                        ui.showWindow(operation)
                        ui.setFocused(operation)
                elif event.data1 in [23,13,47]:
                    if event.data1 == 47:
                        operation()
                    else:
                        value = globTransColorFuncVal[event.data1][2]
                        operation(value)
                else:
                    value = globTransColorFuncVal[event.data1][2]
                    transport.globalTransport(operation,value)
                self.updatePerformanceLayout()
            event.handled = True
        except KeyError:
            self.padToLightPad(event.data1,"OFF",0)
            event.handled = True

    def updatePerformanceLayout(self):
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

        for i in range(1,5):
            h.lightPad(9,i,"OFF",0)

        viewColor = {1:"OFF", 2:"OFF", 3:"OFF", 4:"OFF", 5:35, 6:"BROWN", 7:19, 8:"DARK_GREEN"}
        for i in range(1,9):
            h.lightPad(i,9,viewColor[i],0)
        
        for row in range(1,9):
            rowOffset = (8-row)*8
            for column in range(1,9):
                columnOffset = (column-1)*8
                isFilled = False
                isPlaying = False
                for track in range(1+rowOffset,9+rowOffset):
                    for blockIndex in range(0+columnOffset,8-columnOffset):
                        status = playlist.getLiveBlockStatus(track,blockIndex,midi.LB_Status_Simplest)
                        if status == 0: # Empty
                            continue
                        elif status == 1: # Filled
                            isFilled = True
                        elif status == 2: # Playing or Scheduled
                            isFilled = True
                            isPlaying = True
                padColor = "OFF"
                padMode = "STATIC"
                if isPlaying:
                    padColor = "WHITE"
                    if transport.isPlaying():
                        padMode = "PULSING"
                elif isFilled:
                    padColor = "GRAY"
                h.lightPad(row,column,padColor,0,padMode)
               
    def updateLights(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 0, 247]))
        h.lightPad(9,1,"OFF" if self.YOffset == 0 else "DARK_GRAY",0)
        h.lightPad(9,2,"OFF" if self.YOffset == 492 else "DARK_GRAY",0)
        h.lightPad(9,3,23 if self.XOffset == 0 else "DARK_GRAY",0)
        h.lightPad(9,4,"DARK_GRAY",0)
        for row in range(1,9):
            h.lightPad(row,9,"DARK_GRAY",0)
            for column in range(1,9):
                padColor = "OFF"
                padVibrancy = "NORMAL"
                padMode = "STATIC"
                track = (9-row)+self.YOffset
                blockIndex = (column-1)+self.XOffset
                status = playlist.getLiveBlockStatus(track,blockIndex,midi.LB_Status_Simple)
                if status == 0: # Empty
                    h.lightPad(row,column,padColor,0)
                elif status in [1,3]: # Filled or Scheduled
                    padColor = playlist.getLiveBlockColor(track,blockIndex)
                    padVibrancy = "VIBRANT" if status == 3 else "NORMAL"
                    if status == 3:
                        padMode = "FLASHING" if transport.isPlaying() else "STATIC"
                elif status == 2: # Playing
                    padColor = playlist.getLiveBlockColor(track,blockIndex)
                    padVibrancy = "VIBRANT"
                    padMode = "PULSING" if transport.isPlaying() else "STATIC"
                h.lightPad(row,column,padColor,0,padMode,padVibrancy)
                if padColor != "OFF":
                    h.lightPad(row,9,"GRAY",0)

    def faderBank(self):
        PerfFaderLayout.updateLayout(0)
        self.setArrowTabLights()
        

    def XYPadLayout(self, *args):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 0, 247]))
        self.setArrowTabLights()
        self.XYPads[self.XYLayoutSelect].updateLights()
        pad = {0:89,1:79,2:69,3:59,4:49,5:39,6:29,7:19}
        for i in range(1,9):
                h.lightPad(i,9,"DARK_GRAY",0)
        h.lightPad(8-self.XYLayoutSelect,9,54,0)

    def tempoPicker(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 0, 247]))
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 18, 1, 0, 0, 247]))
        self.setTransportLights()
        self.setArrowTabLights()

        h.lightPad(7,2,"LIGHT_GREEN",0,"PULSING" if transport.isPlaying() else "STATIC")
        h.lightPad(7,4,6,0)
        h.lightPad(6,3,"ORANGE" if ui.isMetronomeEnabled() else "BROWN",0)
        h.lightPad(4,3,29,0)
        h.lightPad(3,2,"BLUE",0)
        h.lightPad(3,4,"LIGHT_BLUE",0)
        for row in range(2,8):
            start = 49 if row < 5 else 59
            color = (start-2) + row if row < 5 else start-(row-5)
            h.lightPad(row,6,color,0)

    def sysCommands(self):
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 0, 247]))
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 18, 1, 0, 0, 247]))
        self.setTransportLights()
        self.setArrowTabLights()

        h.lightPad(8,2,"YELLOW",0)
        h.lightPad(7,1,"LIGHT_BLUE",0)
        h.lightPad(7,2,25,0)
        h.lightPad(7,3,37,0)
        h.lightPad(6,2,99,0)
        h.lightPad(8,5,18,0)
        h.lightPad(8,7,17,0)
        h.lightPad(7,6,87,0)
        h.lightPad(6,5,61,0)
        h.lightPad(6,7,96,0)
        h.lightPad(4,1,45,0)
        h.lightPad(4,2,78,0)
        h.lightPad(4,3,"LIGHT_GREEN",0)
        h.lightPad(4,4,60,0)
        h.lightPad(4,5,61,0)
        h.lightPad(2,1,"PURPLE",0)
        h.lightPad(1,1,51,0)
        h.lightPad(2,3,122,0)
        h.lightPad(1,3,123,0)
        h.lightPad(4,7,"MAGENTA",0)
        h.lightPad(3,7,58,0)
        h.lightPad(4,8,72,0)

    def setTransportFunctions(self, event):
        globTransColorFuncVal = {89:[72,midi.FPT_Overdub,127],79:[72,midi.FPT_LoopRecord,127],
                         69:[37,midi.FPT_WaitForInput,127],59:[25,midi.FPT_StepEdit,127],
                         49:[61,midi.FPT_CountDown,127],39:[108,midi.FPT_Metronome,127],
                         29:[109,midi.FPT_ChannelJog,-1],19:[74,midi.FPT_ChannelJog,1]}
        try:
            color = globTransColorFuncVal[event.data1][0]
            operation = globTransColorFuncVal[event.data1][1]
            value = globTransColorFuncVal[event.data1][2]
            if event.data2 > 0:
                self.padToLightPad(event.data1,color,0)
            else:
                transport.globalTransport(operation,value)
                self.setTransportLights()
            event.handled = True
        except KeyError:
            event.handled = True

    def setTransportLights(self):
        h.lightPad(8,9,7,0)        # Overdub
        h.lightPad(7,9,7,0)        # Loop Recording
        h.lightPad(6,9,38,0)       # Wait For Input
        h.lightPad(5,9,"GREEN",0)  # Step Editing
        h.lightPad(4,9,84,0)       # Countdown Before Recording
        h.lightPad(3,9,"ORANGE" if ui.isMetronomeEnabled() else "BROWN",0)
        h.lightPad(2,9,"YELLOW",0) # Chan Up
        h.lightPad(1,9,99,0)       # Chan Down

    def setArrowTabLights(self):
        arrowLights = {1:[122,69],2:[108,23],3:[68,122],4:[69,108]}
        h.lightPad(9,1,"OFF",0)
        h.lightPad(9,2,"OFF",0)
        h.lightPad(9,3,arrowLights[self.currTab][0],0)
        h.lightPad(9,4,arrowLights[self.currTab][1],0)
        
class XYPad():
    def __init__(self) -> None:
        self.selectedPad = 81
        self.XControlCC = 0
        self.YControlCC = 0

    def reset(self):
        self.selectedPad = 81

    def OnNoteOn(self, event):
        if event.data2 == 0:
            return
        color = 26 if self.selectedPad in [81,88,72,77,63,66,54,55,44,45,33,36,22,27,11,18] else 68
        h.lightPad(floor(self.selectedPad/10),self.selectedPad%10,color,0)
        h.lightPad(floor(event.data1/10),event.data1%10,54,0)
        self.selectedPad = event.data1
        # TODO: Figure out how FL MIDI CC Works Because Documentation Doesn't Explain Well
        device.forwardMIDICC(179 + (self.XControlCC << 8) + (50 << 16) + (0 << 24), 1)
        device.forwardMIDICC(179 + (self.YControlCC << 8) + (50 << 16) + (0 << 24), 1)

    def updateLights(self):
        for row in range(1,9):
            for column in range(1,9):
                if (row == column) or (row + column == 9):
                    h.lightPad(row,column,"GREEN",0)
                    continue
                h.lightPad(row,column,68,0)
        h.lightPad(floor(self.selectedPad/10),self.selectedPad%10,54,0)

    