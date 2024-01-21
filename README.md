### Novation Launchpad X MK3 Integration with FL Studio 
# Support:
* Performance Mode
* Mixer
* FPC
* Gross Beat
* Default Session Layout with 1 Pitch Bend, one Mod Wheel, and **62** different faders to control different parameters you assign to
your heart's content

# How To Install:
1. Drop the MIDI Script in the hardware folder, usually found in ...\Documents\Image-Line\FL Studio\Settings\Hardware\
2. Refresh the scripts and click on "LPX MIDI", keep "MIDIIN2 (LPX MIDI)" set to generic controller.
3. In the dropdown under Controller Type, set "LPX MIDI" to "Novation Launchpad X MK3" and set it to a port number
4. You know the script will be active if the "Session" button is now lit!

# Known Issues:
* For some odd reason, the button flashing when dumping the score log doesn't work due to it getting the device exactly 5 ports ahead,
weird bug but I haven't found a direct fix.
* Default Mixer Track colors are not accurate for Users using Themes that have a shift in the Hue Knob, this seems to be an FL API error
when getting a color that I have not found a workaround for.
* In performance mode, the "Press" category "Hold and Motion" doesn't seem to work as expected, so it works the same as "Retrigger"
until I can understand the undocumented way most of the flags work
* FL Crashes when turning off the device sometimes, supposedly just an FL Bug with things running in the background, so hoping for it
to be fixed.


# Other Information:
* Press and Hold the "Capture Midi" button to dump score to next empty pattern. Duration of how long to hold (Default: 0.5 seconds) and duration of score (Default: 45 seconds.)
* Note Mode will switch from the default scale mode you have selected into a DAW Drum Rack with the FPC Pad Colors when selecting FPC in the Channel Rack.
* In order to use performance mode, make sure to go to Tools -> Macros -> "Prepare for Performance Mode." This will allow the Launchpad to detect different clips.
* The Gross Beat Session layout will only appear when inside the plugin, as to not conflict with generators.
* The "Default" Session layout appears in any window besides Gross Beat and the Mixer.
