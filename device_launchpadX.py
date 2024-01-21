# name= Novation Launchpad X MK3
# url= https://forum.image-line.com/viewtopic.php?t=321464
# github = https://github.com/MetallicAsylum/Novation-Launchpad-X-MK3/
"""
Developer: Maxwell Zentolight MaxwellZentolight@Gmail.com
Version 1.1
Date: 1/20/2024
"""

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

from mixer_module import MixerModule
import plugin_module
from performance_module import PerformanceModule
from default_session import DefaultSessionModule

mixerModule = MixerModule()
FPCModule = plugin_module.PluginFPC()
grossBeatModule = plugin_module.PluginGrossBeat()
performanceModule = PerformanceModule()
defaultSessionModule = DefaultSessionModule()

holdLengthSeconds = 0.5
timeFromDumpScoreLog = 45 #Seconds
layoutReadbackMsg = [0xF0, 0x00, 0x20, 0x29, 0x02, 0x0C, 0x00, 0xF7]

class LaunchpadX():
    def __init__(self) -> None:
        self.currentScreen = None #Initialized on OnInit, {0: Session, 1: Note Mode, [2,3 unused], 4-12: Custom Modes, 13: DAW Fader, 127: Programmer Mode}
        self.timeCalled = 0 #Helper variable for button holds

        self.FLCurrentWindow = -1 #FL Window Constants, {0: Mixer, 1: Channel Rack, 2: Playlist, 3: Piano Roll, 4: Browser, 5: Plugin (general) 6: Effect Plugin, 7: Generator Plugin
        self.isInPlugin = False
        self.channelPluginName = ""
        self.mixerPluginName = ""

    def OnInit(self):
        #Set Launchpad into DAW mode
        mode = 1
        launchpadDAWModemsg = [0xF0, 0x00, 0x20, 0x29, 0x02, 0x0C, 0x10, mode, 0xF7]
        device.midiOutSysex(bytes(launchpadDAWModemsg))
        device.midiOutSysex(bytes(layoutReadbackMsg))
        device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 18, 1, 1, 1, 247]))
        self.OnRefresh(260)
        self.updateNoteMode()

    def OnDeInit(self):
        #Set Launchpad into Standalone mode
        mode = 0
        launchpadDAWModemsg = [0xF0, 0x00, 0x20, 0x29, 0x02, 0x0C, 0x10, mode, 0xF7]
        device.midiOutSysex(bytes(launchpadDAWModemsg))

    def OnIdle(self):
        #Check if window has changed, flag tended to be pretty unreliable
        self.updateCurrentView()

    def OnMidiIn(self, event):
        if event.sysex == None:
            return
        #Get current layout
        if event.sysex[6] == 0:
            self.currentScreen = event.sysex[7]
            event.handled = True
        #See if Launchpad is in DAW Fader mode
        if event.sysex[6] == 1:
            if (self.FLCurrentWindow == 0 and not self.isInPlugin):
                mixerModule.OnMidiIn()

    def OnMidiMsg(self, event):
        if (event.data1 in [95, 96, 97]): #Session, Note, and Custom Button
            if (event.data2 == 127):
                device.midiOutSysex(bytes(layoutReadbackMsg))
                if event.data1 == 95:
                    self.currentScreen = 0
                    self.clearButtons()
                    device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 18, 1, 0, 0, 247]))
                    self.updateSession()
                if event.data1 == 96 and self.channelPluginName == "FPC": #Note Mode, FPC DAW Drumrack
                    self.currentScreen = 1
                    FPCModule.updateArrows(self.currentScreen)
            event.handled = True

        if (event.data1 == 98): #Record + Dump Score
            if (event.data2 == 127):
                self.timeCalled = time.time()
                event.handled = True
                start_new_thread(self.checkHeld, ()) #Check when to dump score

            if (event.data2 == 0): #Handle if to record or dump score
                event.handled = True
                if (time.time() - self.timeCalled < holdLengthSeconds):
                    transport.record()
                else:
                    if (transport.isRecording()):
                        colorMode = lambda recording: 146 if recording else 144
                        device.midiOutMsg(176, colorMode(transport.isPlaying()), 98, 72)
                    else:
                        device.midiOutMsg(176, 144, 98, 0)
                self.timeCalled = 0

        if (event.data1 in [19, 29, 39, 49, 59, 69, 79, 89, 91, 92, 93, 94]): #Session Arrows and Side Arrows
            if self.FLCurrentWindow == 0 and not self.isInPlugin:
                mixerModule.OnMidiMsg(event)
                return
            if self.channelPluginName == "FPC" and self.currentScreen == 1:
                FPCModule.OnMidiMsg(event)
                return
            if self.mixerPluginName == "Gross Beat" and self.currentScreen in [0, 13]:
                grossBeatModule.OnMidiMsg(event)
                return
            if playlist.getPerformanceModeState() == 1 and self.currentScreen == 1 and self.FLCurrentWindow == 2:
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
            if self.mixerPluginName == "Gross Beat":
                grossBeatModule.OnNoteOn(event)
            return
        if self.channelPluginName == "FPC": #FPC
            FPCModule.OnNoteOn(event)
            return
        if playlist.getPerformanceModeState() == 1 and self.currentScreen == 1 and self.FLCurrentWindow == 2: #Performance Mode
            performanceModule.OnNoteOn(event)
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

    def OnRefresh(self, flags):
        print(flags)
        if flags == 4: #Mixer Interaction
            mixerModule.userMixerInteraction()
        if flags == 263: #New Mixer Selected
            mixerModule.updateMixerLayout(self.currentScreen, flags)
        if (flags == 260 or flags == 256): #Record Button Change or Playing State Change
            if self.timeCalled == 0:
                if (transport.isRecording()):
                    colorMode = lambda recording: 146 if recording else 144
                    device.midiOutMsg(176, colorMode(transport.isPlaying()), 98, 72)
                else:
                    device.midiOutMsg(176, 144, 98, 0)
        if (flags == 4096 or flags == 4352):
            if ui.getFocusedPluginName() == "Gross Beat":
                grossBeatModule.updateSlots()
        if (flags == 17687) and self.FLCurrentWindow == 0 and not self.isInPlugin: #Plugin on Mixer Change
            mixerModule.updatePluginScrollArrows(0)
        if (flags == 65824):
            self.updateNoteMode()
        if flags == 91463 and self.channelPluginName == "FPC": #Preset Change
            FPCModule.updatePadsColor(channels.channelNumber())

    def OnUpdateLiveMode(self, lastTrack):
        if self.FLCurrentWindow == 2 and self.currentScreen == 1 and playlist.getPerformanceModeState() == 1: #If in Playlist and Note Mode
            performanceModule.updatePerformanceLayout(lastTrack)

    def checkHeld(self):
        while (self.timeCalled != 0):
            if time.time() - self.timeCalled > holdLengthSeconds:
                print(device.getName()) # [ISSUE] Sometimes calls wrong device? I can't reliably recreate this bug but I have noticed it multiple times
                device.midiOutMsg(176, 145, 98, 3)
                if (patterns.isPatternDefault(patterns.patternNumber())) != 1:
                    patterns.findFirstNextEmptyPat(2)
                general.dumpScoreLog(timeFromDumpScoreLog, True)
                general.clearLog()
                break
            time.sleep(holdLengthSeconds) 
    
    def clearButtons(self): 
        for button in range(11, 100):
            if button in [19, 29, 39, 49, 59, 69, 79, 89, 91, 92, 93, 94, 95, 96, 97, 98, 99]:
                input = 176 #CC Pads
            else:
                input = 144 #Note Pads
            device.midiOutMsg(input, 144, button, 0)

    def updateCurrentView(self):
        if (ui.getFocused(5) >= 1 and ((ui.getFocusedPluginName() != self.channelPluginName) and (ui.getFocusedPluginName() != self.mixerPluginName))): #Is in plugin and not in same plugin
            self.isInPlugin = True
            print()
            if ui.getFocused(6) >= 1:
                self.mixerPluginName = ui.getFocusedPluginName()
            else:
                self.mixerPluginName = ""
            if ui.getFocused(7) >= 1:
                self.channelPluginName = ui.getFocusedPluginName()
            self.FLCurrentWindow = 1000
            self.updateSession()
            self.updateNoteMode()
        if (ui.getFocused(5) < 1 and self.isInPlugin): # Isn't in plugin
            self.isInPlugin = False
            self.mixerPluginName = ""
            self.updateSession()



        if ui.getFocusedFormID() != self.FLCurrentWindow: #FL Window variable needs updating
            self.FLCurrentWindow = ui.getFocusedFormID()
            if self.FLCurrentWindow == 2 and playlist.getPerformanceModeState() == 1 and self.currentScreen == 1: #Update Note Mode for Performance Mode
                performanceModule.updatePerformanceLayout(-1)
            if self.timeCalled == 0: #Update Record Button
                if (transport.isRecording()):
                    colorMode = lambda recording: 146 if recording else 144
                    device.midiOutMsg(176, colorMode(transport.isPlaying()), 98, 72)
                else:
                    device.midiOutMsg(176, 144, 98, 0)                    
            self.updateSession()

    def updateSession(self):
        if (self.FLCurrentWindow == 0 and not self.isInPlugin): #Mixer, not in Plugin
            mixerModule.updateMixerLayout(self.currentScreen, None)
        elif self.mixerPluginName == "Gross Beat":
            grossBeatModule.updateGrossBeatLayout(self.currentScreen, mixer.getActiveEffectIndex()[0], mixer.getActiveEffectIndex()[1])
        else:
            defaultSessionModule.updateLayout(self.currentScreen) #Default Session View
        
    def updateNoteMode(self):
        self.channelPluginName = plugins.getPluginName(channels.channelNumber(), -1, False, True)
        if self.channelPluginName == "FPC":
            FPCModule.updateNoteMode(channels.channelNumber(), self.currentScreen)
            defaultSessionModule.updateLayout(self.currentScreen)
        else:
            if self.currentScreen == 1: #Is in Note Mode
                device.midiOutSysex(bytes([240, 0, 32, 41, 2, 12, 15, 0, 247])) #Change Note Mode to Scale
            else:
                defaultSessionModule.updateLayout(self.currentScreen) #Default Session View
       


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

def OnNoteOn(event):
    Launchpad.OnNoteOn(event)

def OnNoteOff(event):
    Launchpad.OnNoteOff(event)

def OnControlChange(event):
    Launchpad.OnControlChange(event)

def OnRefresh(flags):
    Launchpad.OnRefresh(flags)

def OnUpdateLiveMode(lastTrack):
    Launchpad.OnUpdateLiveMode(lastTrack)


