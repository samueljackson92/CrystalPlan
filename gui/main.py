"""CrystalPlan GUI Main file.
Includes GUI launcher, logger, error handler."""
#Boa:App:CrystalPlanApp

# Author: Janik Zikovsky, zikovskyjl@ornl.gov
# Version: $Id: CrystalPlan.py 1127 2010-04-01 19:28:43Z 8oz $
#print "CrystalPlan.gui.launch_gui is being imported. __name__ is", __name__
#print "CrystalPlan.gui.launch_gui __file__ is", __file__


#--- General Imports ---
from __future__ import with_statement
import sys
import os
import traceback
import datetime

if __name__=="__main__":
    #Manipulate the PYTHONPATH to put model directly in view of it
    #   This way, "import model" works.
    sys.path.insert(0, "..")

#--- GUI Imports ---
import frame_main
import frame_qspace_view
import display_thread
import wx
import model
import CrystalPlan_version
   


#-------------------------------------------------------------------------
# The following is generated by BOA Constructor IDE
modules ={u'detector_views': [0, '', u'detector_views.py'],
 u'dialog_preferences': [0, '', u'dialog_preferences.py'],
 u'dialog_startup': [0, '', u'dialog_startup.py'],
 u'display_thread': [0, '', u'display_thread.py'],
 u'experiment': [0, '', u'model/experiment.py'],
 u'frame_main': [1, 'Main frame of Application', u'frame_main.py'],
 u'frame_qspace_view': [0, '', u'frame_qspace_view.py'],
 u'frame_reflection_info': [0, '', u'frame_reflection_info.py'],
 u'frame_test': [0, '', u'frame_test.py'],
 u'goniometer': [0, '', u'model/goniometer.py'],
 u'gui_utils': [0, '', u'gui_utils.py'],
 u'instrument': [0, '', u'model/instrument.py'],
 u'messages': [0, '', u'model/messages.py'],
 u'panel_add_positions': [0, '', u'panel_add_positions.py'],
 u'panel_detectors': [0, '', u'panel_detectors.py'],
 u'panel_experiment': [0, '', u'panel_experiment.py'],
 u'panel_goniometer': [0, '', u'panel_goniometer.py'],
 u'panel_positions_select': [0, '', u'panel_positions_select.py'],
 u'panel_qspace_options': [0, '', u'panel_qspace_options.py'],
 u'panel_reflection_info': [0, '', u'panel_reflection_info.py'],
 u'panel_reflection_measurement': [0, '', u'panel_reflection_measurement.py'],
 u'panel_reflections_view_options': [0,'',u'panel_reflections_view_options.py'],
 u'panel_sample': [0, '', u'panel_sample.py'],
 u'plot_panel': [0, '', u'plot_panel.py'],
 u'scd_old_code': [0, '', u'scd_old_code.txt'],
 u'slice_panel': [0, '', u'slice_panel.py']}


#The background display thread
global background_display
background_display = None


#-------------------------------------------------------------------------
#-------------------- LOGGING AND ERROR HANDLING -------------------------
#-------------------------------------------------------------------------
#(with is in python 2.6)

#-------------------------------------------------------------------------
class OutWrapper(object):
    """Class wraps the standard output and logs it to a file."""
    def __init__(self, realOutput, logFileName):
        self._realOutput = realOutput
        self._logFileName = logFileName
        print "Logging standard output to", logFileName

    def _log(self, text):
        """Add a line of text to the log file."""
        with open(self._logFileName, 'a') as logFile:
            logFile.write(text)

    def flush(self):
        """Flush out stdout."""
        self._realOutput.flush()

    def write(self, text):
        """Log and output to stdout the text to print out."""
        self._log(text)
        self._realOutput.write(text)

    def write_error(self, text):
        """Log and output error message."""
        self._log(text)
        sys.stderr.write(text)


#-------------------------------------------------------------------------
def excepthook(type, value, tb, thread_information="Main Loop"):
    """Uncaught exception hook. Will log the exception and display it
    as a message box to the user."""
    global out_wrapper
    message = 'Uncaught exception (from %s):\n-----------------------\n' % thread_information
    message += ''.join(traceback.format_exception(type, value, tb))
    message += '-----------------------\n\n'
    #Also log the exception (and output to stdout)
    out_wrapper.write_error("\n"+message)
    #And show a messagebox for the user.
    extra_message = "This exception has been logged to " + out_wrapper._logFileName
    extra_message += "\n\nYou can attempt to continue your work, but you may run into other errors/problems if you do."
    #TODO: Make into a nicer dialog, maybe submit a bug report directly?
    wx.CallAfter(wx.MessageBox, message + extra_message,
        caption="Unhandled Exception from %s" % thread_information, style=wx.OK | wx.ICON_ERROR)




#-------------------------------------------------------------------------
class CrystalPlanApp(wx.App):
    def OnInit(self):
        #Create the main GUI frame
        self.main = frame_main.create(None)
        self.main.Show()
        #Set it on top
        self.SetTopWindow(self.main)
        #Also, we show the q-space coverage window
        frame_qspace_view.get_instance(self.main).Show()
        return True


#-------------------------------------------------------------------------
#if __name__ == '__main__':
def launch_gui():
    print "-------------- %s %s GUI is starting -----------------" % (CrystalPlan_version.package_name, CrystalPlan_version.version)

    #Create a StdOut wrapper
    global out_wrapper
    out_wrapper = OutWrapper(sys.stdout, r'/tmp/CrystalPlan_Log_' + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt" )
    sys.stdout = out_wrapper

    #Attach our exception hook
    sys.excepthook = excepthook

    
    #TODO: Here pick the latest instrument, load other configuration
    #Make the goniometers
    model.goniometer.initialize_goniometers()

    #Ok, create the instrument
    model.instrument.inst = model.instrument.Instrument(model.config.cfg.default_detector_filename)
    model.instrument.inst.make_qspace()

    #Initialize the instrument and experiment
    model.experiment.exp = model.experiment.Experiment(model.instrument.inst)
    model.experiment.exp.crystal.point_group_name = model.crystals.get_point_group_names(long_name=True)[0]

    #Some initial calculations
    if False:
        import numpy as np
        for i in np.deg2rad([-5, 0, 5]):
            model.instrument.inst.simulate_position(list([i,i,i]))
        pd = dict()
        for pos in model.instrument.inst.positions:
            pd[ id(pos) ] = True
        display_thread.NextParams[model.experiment.PARAM_POSITIONS] = model.experiment.ParamPositions(pd)
        #Do some reflections
        model.experiment.exp.initialize_reflections()
        model.experiment.exp.recalculate_reflections(model.experiment.ParamPositions(pd))
    else:
        model.experiment.exp.initialize_reflections()
        model.experiment.exp.recalculate_reflections(None)

    #Initialize the application
    application = CrystalPlanApp(0)

    #Start the thread that monitors changes to the q-space coverage calculation.
    if True: #To try it with and without
        background_display = display_thread.DisplayThread()
        display_thread.thread_exists = True
    else:
        display_thread.thread_exists = False


    try:
        #Start the GUI loop
        application.MainLoop()
    except:
        #Catch the latest error and report it
        xc = traceback.format_exception(*sys.exc_info())
        wx.MessageBox("Exception caught in MainLoop!\n\n" + ''.join(xc))


    #Exit the program and do all necessary clean-up.
    print "Exiting CrystalPlan. Have a nice day!"
    background_display.abort()




if __name__=="__main__":
    #For launching from source

    launch_gui()