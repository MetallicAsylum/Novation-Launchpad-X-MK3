# name= Novation Launchpad X MK3
# url= https://forum.image-line.com/viewtopic.php?t=321464
# github = https://github.com/MetallicAsylum/Novation-Launchpad-X-MK3/
"""
Developer: Maxwell Zentolight MaxwellZentolight@Gmail.com
Version 1.7
Date: 1/12/2025
"""

from math import floor
import playlist
import channels
import patterns
import ui
import transport
import device
import mixer
import general
import plugins
import time
from _thread import start_new_thread

import helpers
import mixer_module
import fpc_module
import grossbeat_module
import performance_module
import default_session_module

h = helpers.Helper()
mixerModule = mixer_module.MixerModule()
FPCModule = fpc_module.PluginFPC()
grossBeatModule = grossbeat_module.PluginGrossBeat()
performanceModule = performance_module.PerformanceModule()
defaultSessionModule = default_session_module.DefaultSessionModule()

holdLengthSeconds = 0.5
timeFromDumpScoreLog = 45 #Seconds
layoutReadbackMsg = [0xF0, 0x00, 0x20, 0x29, 0x02, 0x0C, 0x00, 0xF7]

class LaunchpadX():
    def __init__(self) -> None:
        self.currentScreen = None #Initialized on OnInit, {0: Session, 1: Note Mode/DAW Drum Rack, [2,3 unused], 4-12: Custom Modes, 13: DAW Fader, 127: Programmer Mode}
        self.timeCalled = 0 #Helper variable for button holds

        self.FLCurrentWindow = -1 #FL Window Constants, {0: Mixer, 1: Channel Rack, 2: Playlist, 3: Piano Roll, 4: Browser, 5: Plugin (general) 6: Effect Plugin, 7: Generator Plugin
        self.isInPerformanceMode = False
        self.isInPlugin = False
        self.channelPluginName = "NONE"
        self.mixerPluginName = "NONE"

    def reset(self):
        self.currentScreen = None
        self.timeCalled = 0
        self.FLCurrentWindow = -1 #FL Window Constants, {0: Mixer, 1: Channel Rack, 2: Playlist, 3: Piano Roll, 4: Browser, 5: Plugin (general) 6: Effect Plugin, 7: Generator Plugin
        self.isInPerformanceMode = False
        self.isInPlugin = False
        self.channelPluginName = "NONE"
        self.mixerPluginName = "NONE"
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 0, 1, 247]))        # Set View To Note Mode
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 15, 0, 247]))       # Set Note Mode To Scale
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 18, 1, 1, 1, 247])) # Clear Session, Drum, and CC
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 23, 0, 247]))       # Change Note Active color
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 20, 0, 0, 247]))    # Change Session colors
        self.updateNovationLogo()

    def OnInit(self):
        #Set Launchpad into DAW mode
        mode = 1
        launchpadDAWModemsg = [0xF0, 0x00, 0x20, 0x29, 0x02, 0x0C, 0x10, mode, 0xF7]
        device.midiOutSysex(bytes(launchpadDAWModemsg))
        device.midiOutSysex(bytes(layoutReadbackMsg))
        self.OnRefresh(260)
        self.reset()
        print("Launchpad X Script loaded successfully!")

    def OnDeInit(self):
        #Set Launchpad into Standalone mode
        mode = 0
        launchpadDAWModemsg = [0xF0, 0x00, 0x20, 0x29, 0x02, 0x0C, 0x10, mode, 0xF7]
        device.midiOutSysex(bytes(launchpadDAWModemsg))

    def OnIdle(self):
        if self.timeCalled == 0: #Update Record Button
            self.updateRecordingButton()
        #Check if window has changed, flag tended to be pretty unreliable
        self.updatePluginView()
        self.updateFlWindowView()
        #Update Gross Beat Slots
        if self.mixerPluginName == "Gross Beat" and self.currentScreen == 0:
            grossBeatModule.updateSlots()
        #CheckHeld
        if self.timeCalled > 0:
            self.checkHeld()

    def OnMidiIn(self, event):
        if event.sysex == None:
            return
        #Get current layout
        if event.sysex[6] == 0:
            if event.sysex[7] != self.currentScreen:
                self.updateNoteMode()
                self.updateSession()
            self.currentScreen = event.sysex[7]
            event.handled = True
        #See if Launchpad is in DAW Fader mode
        if event.sysex[6] == 1:
            if (self.FLCurrentWindow == 0 and not self.isInPlugin):
                mixerModule.OnMidiIn()

    def OnMidiMsg(self, event):
        if (event.data1 in [95, 96, 97] and event.status == 176): #Session, Note, and Custom Button
            if (event.data2 == 127):
                device.midiOutSysex(bytes(layoutReadbackMsg))
                if event.data1 == 95:
                    if helpers.Helper().isAnimationMode:
                        helpers.Helper().toggleAnimationMode()
                        performanceModule.updatePerformanceLayout()
                        return
                    if self.currentScreen in [0, 13] and self.isInPerformanceMode and self.FLCurrentWindow != 0 and self.mixerPluginName != "Gross Beat":
                        performanceModule.toggleOverviewMode()
                    self.currentScreen = 0
                    h.clearPads(0)
                    device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 18, 1, 0, 0, 247]))
                    self.updateNovationLogo()
                    self.updateSession()
                if event.data1 == 96:
                    self.currentScreen = 1
                    self.updateNoteMode()
                    if self.channelPluginName == "FPC": #Note Mode, FPC DAW Drum Rack
                        FPCModule.updateArrows(self.currentScreen)
                if event.data1 == 97:
                    self.currentScreen = 4
                    self.updateNovationLogo()
                    device.midiOutSysex(bytes(layoutReadbackMsg))
                    self.updateSession()
            event.handled = True

        if (event.data1 == 98 and event.status == 176): #Record + Dump Score
            if (event.data2 == 127):
                self.timeCalled = time.time()
                event.handled = True
                try: # Raises Traceback, but Error doesn't effect anything and works fine.
                    start_new_thread(self.checkHeld, ()) #Check when to dump score
                except Exception:
                    pass

            if (event.data2 == 0): #Handle if to record or dump score
                event.handled = True
                if (time.time() - self.timeCalled < holdLengthSeconds):
                    transport.record()
                    self.timeCalled = 0
                else:
                    self.updateRecordingButton()

        if (event.data1 in [19, 29, 39, 49, 59, 69, 79, 89,] or (event.data1 in [91, 92, 93, 94] and event.status == 176)): #Session Arrows and Side Arrows
            if self.FLCurrentWindow == 0 and not self.isInPlugin:
                if playlist.getPerformanceModeState() == 1 and self.currentScreen in [0,13]:
                    if event.data1 == 91:
                        performanceModule.MidiMsgOutside(event)
                    else:
                        mixerModule.OnMidiMsg(event)
                else:
                    mixerModule.OnMidiMsg(event)
                return
            if self.channelPluginName == "FPC" and self.currentScreen == 1:
                FPCModule.OnMidiMsg(event)
                return
            if self.mixerPluginName == "Gross Beat" and self.currentScreen in [0, 13]:
                if playlist.getPerformanceModeState() == 1 and self.currentScreen in [0,13]:
                    if event.data1 == 94:
                        performanceModule.MidiMsgOutside(event)
                    else:
                        grossBeatModule.OnMidiMsg(event)
                else:
                    grossBeatModule.OnMidiMsg(event)
                return
            if playlist.getPerformanceModeState() == 1 and self.currentScreen in [0,13] and self.FLCurrentWindow != 0:
                performanceModule.OnMidiMsg(event)
                return
            if self.currentScreen in [0, 13]:
                defaultSessionModule.OnMidiMsg(event)
                return

    def OnNoteOn(self, event):
        if self.currentScreen in [0, 13]: #Session Mode
            if self.FLCurrentWindow == 0 and not self.isInPlugin: #Mixer
                mixerModule.OnControlChange(event)
                event.handled = True
                return
            if playlist.getPerformanceModeState() == 1 and not self.mixerPluginName == "Gross Beat": #Performance Mode 
                performanceModule.OnNoteOn(event)
                return
            if self.mixerPluginName == "Gross Beat" and event.midiChan != 8: #Gross Beat
                grossBeatModule.OnNoteOn(event)
                return
        if self.channelPluginName == "FPC" and event.midiChan == 8: #FPC
            FPCModule.OnNoteOn(event)
            return

    def OnNoteOff(self, event):
        if self.currentScreen == 0: #Session Mode
            if self.FLCurrentWindow == 0 and not self.isInPlugin: #Mixer
                mixerModule.OnControlChange(event)
            event.handled = True
            return

    def OnControlChange(self, event):
        if (event.midiChan == 4): #DAW Fader Channel
            if (self.FLCurrentWindow == 0 and not self.isInPlugin):
                mixerModule.OnControlChange(event)
                return
            if self.currentScreen in [0, 13]: #Session or DAW Fader
                defaultSessionModule.OnControlChange(event, channels.channelNumber(True))

    def OnProjectLoad(self, status):
        if status in [0,100]:
            self.reset()
            mixerModule.reset()
            FPCModule.reset()
            grossBeatModule.reset()
            performanceModule.reset()
            defaultSessionModule.reset()
            h.reset()

    def OnMidiOutMsg(self, event):
        helpers.Helper.toggleAnimationMode()
        event.data1 = event.data1-1
        if event.midiId == 128:
            event.data2 = 0
        h.lightPad(floor(event.data1/10),event.data1%10,event.data2,0)
        if event.data1 == 95:
            if event.data2 == 0:
                event.data2 = 1
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 20, event.data2, 49, 247])) #Change Session colors

        helpers.Helper.toggleAnimationMode()
        event.handled = True

    def OnRefresh(self, flags):
        if flags == 4: #Mixer Interaction
            if self.FLCurrentWindow == 0 and not self.isInPlugin:
                mixerModule.userMixerInteraction()
        if flags in [64, 320]:
            if self.isInPerformanceMode != playlist.getPerformanceModeState():
                self.updateSession()
        if flags == 256: #Metronome/Transport update
            self.updateRecordingButton()
            if self.currentScreen in [0,13]:
                self.updateNovationLogo()
            if self.isInPerformanceMode and self.FLCurrentWindow != 0 and self.mixerPluginName != "Gross Beat" and performanceModule.currTab == 3:
                performanceModule.tempoPicker()
        if flags == 263 or flags == 4359: #New Mixer Selected
            if self.FLCurrentWindow == 0 and not self.isInPlugin:
                mixerModule.updateMixerLayout(self.currentScreen, flags)
        if (flags == 260): #Record Button Change or Playing State Change
            if self.timeCalled == -1:
                self.updateRecordingButton()
        if (flags == 17687) and self.FLCurrentWindow == 0 and not self.isInPlugin: #Plugin on Mixer Change
            mixerModule.updatePluginScrollArrows(0)
        if (flags in [288, 32768, 65824, 66848, 65792, 98560, 65847]): #Channel Slot Change
            self.updateNoteMode()
        if flags == 91463 or flags == 24871 or 16384 and self.channelPluginName == "FPC": #Preset Change, Color Update, or Note Select Update
            FPCModule.updatePadsColor(channels.channelNumber())

    def OnUpdateLiveMode(self, lastTrack):   
        self.updatePerformanceMode()

    def checkHeld(self):
        if time.time() - self.timeCalled > holdLengthSeconds:
            h.lightPad(9,8,"WHITE",self.currentScreen,"FLASHING")
            if (patterns.isPatternDefault(patterns.patternNumber())) != 1:
                patterns.findFirstNextEmptyPat(2)
            general.dumpScoreLog(timeFromDumpScoreLog, True)
            general.clearLog()
            self.timeCalled = -time.time()
            return

    def updatePluginView(self):
        pluginFocus = ui.getFocused(5)
        if not pluginFocus:
            self.isInPlugin = False
            self.mixerPluginName = ""
            return
        pluginName = ui.getFocusedPluginName()
        if pluginName == "":
            return
        effectFocus = ui.getFocused(6)
        if effectFocus:
            effectLocation = mixer.getActiveEffectIndex()
        if channels.channelNumber(True) == -1 or not plugins.isValid(channels.channelNumber(),-1,True):
            self.channelPluginName = "-1"
        if effectFocus and not plugins.isValid(effectLocation[0], effectLocation[1],True):
            self.mixerPluginName = ""
            return
        if pluginName in [self.channelPluginName, self.mixerPluginName]:
            return
        
        self.isInPlugin = True
        self.FLCurrentWindow = 1000
        if channels.channelNumber() != 1 and self.channelPluginName != "-1":
            self.channelPluginName = pluginName
            self.mixerPluginName = ""
        if effectFocus:
            self.mixerPluginName = pluginName
        self.updateSession()
        self.updateNoteMode()
 
    def updateFlWindowView(self):
        performanceModeState = playlist.getPerformanceModeState()
        if performanceModeState != self.isInPerformanceMode:
            self.isInPerformanceMode = performanceModeState
            self.updatePerformanceMode()
        pluginFocus = ui.getFocused(5)
        if pluginFocus:
            return
        focusedWindow = ui.getFocusedFormID()
        if focusedWindow == self.FLCurrentWindow:
            return
        self.FLCurrentWindow = focusedWindow
        self.updateSession()
        self.updateNoteMode()

    def updateSession(self):
        if playlist.getPerformanceModeState() and self.FLCurrentWindow != 0 and self.mixerPluginName != "Gross Beat":
           self.updatePerformanceMode()
           return
        elif (self.FLCurrentWindow == 0 and ui.getFocused(5) < 1): #Mixer, not in Plugin
            mixerModule.updateMixerLayout(self.currentScreen, None)
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 20, 9, 8, 247])) #Change Session colors
            return
        elif self.mixerPluginName == "Gross Beat":
            grossBeatModule.updateGrossBeatLayout(self.currentScreen, mixer.getActiveEffectIndex()[0], mixer.getActiveEffectIndex()[1])
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 20, 25, 16, 247])) #Change Session colors
            return
        else:
            if not playlist.getPerformanceModeState():
                defaultSessionModule.updateLayout(self.currentScreen) #Default Session View
                device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 20, 0, 0, 247])) #Change Session colors
                return
        
    def updateNoteMode(self):
        if channels.channelNumber(True) == -1:
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 15, 0, 247])) #Change to regular note mode
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 23, 0, 247])) #Change Note Active color
            return
        if not plugins.isValid(channels.channelNumber(True),-1,True):
            #Switch note mode to scale
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 15, 0, 247])) #Called for when prev channel was FPC and switches to non-plugin
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 23, 0, 247])) #Change Note Active color
            return
        self.channelPluginName = plugins.getPluginName(channels.channelNumber(), -1, False, True)
        if self.channelPluginName == "FPC":
            FPCModule.updateNoteMode(channels.channelNumber(), self.currentScreen)
            device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 23, 84, 247])) #Change Note Active color
        else:
            if self.currentScreen == 1: #Is in Note Mode
                device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 15, 0, 247])) #Change Note Mode to Scale
                device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 23, 0, 247])) #Change Note Active color
    
    def updatePerformanceMode(self):
        if self.currentScreen in [0, 13] and self.isInPerformanceMode:
            performanceModule.updatePerformanceLayout()
        else:
            if self.isInPerformanceMode:
                device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 20, 49, 44, 247])) #Change Session colors

    def updateRecordingButton(self):
        if (transport.isRecording()):
            colorMode = "PULSING" if transport.isPlaying() else "STATIC"
            h.lightPad(9,8,"RED",self.currentScreen,colorMode)
        else:
            h.lightPad(9,8,"OFF",self.currentScreen)
        self.timeCalled = -1
    
    def updateNovationLogo(self):
        mode = "PULSING" if transport.isPlaying() else "STATIC"
        h.lightPad(9,9,"PURPLE",mode,self.currentScreen)
       


Launchpad = LaunchpadX()

def OnInit():
    Launchpad.OnInit()

def OnDeInit():
    Launchpad.OnDeInit()

def OnIdle():
   Launchpad.OnIdle()

def OnMidiIn(event):
    Launchpad.OnMidiIn(event)

def OnMidiMsg(event):
    Launchpad.OnMidiMsg(event)

def OnMidiOutMsg(event):
    Launchpad.OnMidiOutMsg(event)

def OnNoteOn(event):
    Launchpad.OnNoteOn(event)

def OnNoteOff(event):
    Launchpad.OnNoteOff(event)

def OnControlChange(event):
    Launchpad.OnControlChange(event)

def OnProjectLoad(status):
    Launchpad.OnProjectLoad(status)

def OnRefresh(flags):
    Launchpad.OnRefresh(flags)

def OnUpdateLiveMode(lastTrack):
    Launchpad.OnUpdateLiveMode(lastTrack)


