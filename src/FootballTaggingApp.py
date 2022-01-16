#!/usr/bin/env python
# coding: utf-8

# ### Basic UI Design
# Last Updated on: 2022-01-15

# In[1]:


from PIL import ImageTk,Image
# from tkvideo import tkvideo
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror
from os.path import basename, expanduser, isfile, join as joined
from pathlib import Path
import time
import vlc
import sys
import pandas as pd
import tkinter.font as tkFont


# In[2]:


# Create dataframe to store the tagging data
tagDF = pd.DataFrame(columns = ["Video_Start","Video_End","Game_Start","Game_End","Player_Start","Player_End","Event_Type","Score_Home","Score_Away","Result","Location_From","Location_To"])
# Create data fields to store tag data
data_VS = "00:00:00" #hh:mm:ss
data_VE = "00:00:00" #hh:mm:ss
data_GS = "00:00" #mm:ss
data_GE = "00:00" #mm:ss
data_PS = ""
data_PE = ""
data_ET = ""
data_SH = 0
data_SA = 0
data_Result= ""
data_LF = ""
data_LT = ""
time_diff = 0 # this stores the time difference in milliseconds between video time and game time  


# In[3]:


libtk = "N/A"
C_Key = "Control-"  # shortcut key modifier
class _Tk_Menu(tk.Menu):
    '''Tk.Menu extended with .add_shortcut method.
       Note, this is a kludge just to get Command-key shortcuts to
       work on macOS.  Other modifiers like Ctrl-, Shift- and Option-
       are not handled in this code.
    '''
    _shortcuts_entries = {}
    _shortcuts_widget  = None

    def add_shortcut(self, label='', key='', command=None, **kwds):
        '''Like Tk.menu.add_command extended with shortcut key.
           If needed use modifiers like Shift- and Alt_ or Option-
           as before the shortcut key character.  Do not include
           the Command- or Control- modifier nor the <...> brackets
           since those are handled here, depending on platform and
           as needed for the binding.
        '''
        # <https://TkDocs.com/tutorial/menus.html>
        if not key:
            self.add_command(label=label, command=command, **kwds)
        else:  # XXX not tested, not tested, not tested
            self.add_command(label=label, underline=label.lower().index(key),
                                          command=command, **kwds)
            self.bind_shortcut(key, command, label)

    def bind_shortcut(self, key, command, label=None):
        """Bind shortcut key, default modifier Command/Control.
        """
        # The accelerator modifiers on macOS are Command-,
        # Ctrl-, Option- and Shift-, but for .bind[_all] use
        # <Command-..>, <Ctrl-..>, <Option_..> and <Shift-..>,
        # <https://www.Tcl.Tk/man/tcl8.6/TkCmd/bind.htm#M6>
        if self._shortcuts_widget:
            if C_Key.lower() not in key.lower():
                key = "<%s%s>" % (C_Key, key.lstrip('<').rstrip('>'))
            self._shortcuts_widget.bind(key, command)
            # remember the shortcut key for this menu item
            if label is not None:
                item = self.index(label)
                self._shortcuts_entries[item] = key
        # The Tk modifier for macOS' Command key is called
        # Meta, but there is only Meta_L[eft], no Meta_R[ight]
        # and both keyboard command keys generate Meta_L events.
        # Similarly for macOS' Option key, the modifier name is
        # Alt and there's only Alt_L[eft], no Alt_R[ight] and
        # both keyboard option keys generate Alt_L events.  See:
        # <https://StackOverflow.com/questions/6378556/multiple-
        # key-event-bindings-in-tkinter-control-e-command-apple-e-etc>

    def bind_shortcuts_to(self, widget):
        '''Set the widget for the shortcut keys, usually root.
        '''
        self._shortcuts_widget = widget

    def entryconfig(self, item, **kwds):
        """Update shortcut key binding if menu entry changed.
        """
        tk.Menu.entryconfig(self, item, **kwds)
        # adjust the shortcut key binding also
        if self._shortcuts_widget:
            key = self._shortcuts_entries.get(item, None)
            if key is not None and "command" in kwds:
                self._shortcuts_widget.bind(key, kwds["command"])


# In[4]:


class Player(tk.Frame):
    _geometry = ''
    _stopped  = None
    def __init__(self, parent, title=None, video=''):
        tk.Frame.__init__(self, parent)
        self.parent = parent  # == root
        # self.parent.title("Football Tagging Software") # cannot add title to frame
        self.video = expanduser(video)
        # Menu Bar
        #   File Menu
        menubar = tk.Menu(self.parent)
        self.parent.config(menu=menubar)
        fileMenu = _Tk_Menu(menubar)
        fileMenu.bind_shortcuts_to(parent)  # XXX must be root?

        fileMenu.add_shortcut("Open...", 'o', self.OnOpen)
        fileMenu.add_separator()
        fileMenu.add_shortcut("Play", 'p', self.OnPlay)  # Play/Pause
        fileMenu.add_command(label="Stop", command=self.OnStop)
        fileMenu.add_separator()
        fileMenu.add_shortcut("Mute", 'm', self.OnMute)
        fileMenu.add_separator()
        fileMenu.add_shortcut("Close", 's', self.OnClose)
        menubar.add_cascade(label="File", menu=fileMenu)
        self.fileMenu = fileMenu
        self.playIndex = fileMenu.index("Play")
        self.muteIndex = fileMenu.index("Mute")
# first, top panel shows video
        self.videopanel = ttk.Frame(self.parent)
        self.canvas = tk.Canvas(self.videopanel)
#         self.canvas.grid(column=0, row = 0)
        self.canvas.pack(fill=tk.BOTH, expand=1,side = tk.LEFT)
        self.videopanel.pack(fill=tk.BOTH, expand=1, side = tk.LEFT)
#         self.videopanel.grid(column=0, row = 0)
        
        # panel to hold buttons
        self.buttons_panel = tk.Toplevel(self.parent)
        # self.parent.bind("<Configure>", self.move_me)
        self.buttons_panel.title("")
        self.is_buttons_panel_anchor_active = False

        buttons = ttk.Frame(self.buttons_panel)
        self.playButton = ttk.Button(buttons, text="Play", command=self.OnPlay)
        stop            = ttk.Button(buttons, text="Stop", command=self.OnStop)
        self.muteButton = ttk.Button(buttons, text="Mute", command=self.OnMute)
        self.playButton.pack(side=tk.LEFT)
        stop.pack(side=tk.LEFT)
        self.muteButton.pack(side=tk.LEFT)
        
        self.volMuted = False
        self.volVar = tk.IntVar()
        self.volSlider = tk.Scale(buttons, variable=self.volVar, command=self.OnVolume,
                                  from_=0, to=100, orient=tk.HORIZONTAL, length=200,
                                  showvalue=0, label='Volume')
        self.volSlider.pack(side=tk.RIGHT)
        buttons.pack(side=tk.BOTTOM, fill=tk.X)
        
        # panel to hold player time slider
        timers = ttk.Frame(self.buttons_panel)
        self.timeVar = tk.DoubleVar()
        self.timeSliderLast = 0
        self.timeSlider = tk.Scale(timers, variable=self.timeVar, command=self.OnTime,
                                   from_=0, to=1000, orient=tk.HORIZONTAL, length=500,
                                   showvalue=0)  # label='Time',
        self.timeSlider.pack(side=tk.BOTTOM, fill=tk.X, expand=1)
        self.timeSliderUpdate = time.time()
        timers.pack(side=tk.BOTTOM, fill=tk.X)
        
        # VLC player
        args = []
        self.Instance = vlc.Instance(args)
        self.player = self.Instance.media_player_new()

        self.parent.bind("<Configure>", self.OnConfigure)  # catch window resize, etc.
        self.parent.update()

        # After parent.update() otherwise panel is ignored.
        ## Set this to false in order to move around the buttons panel
        self.buttons_panel.overrideredirect(False)

        # Estetic, to keep our video panel at least as wide as our buttons panel.
        self.parent.minsize(width=502, height=0)
        self.is_buttons_panel_anchor_active = True
        self._AnchorButtonsPanel()

        self.OnTick()  # set the timer up
 
        # Move me not working
#     def move_me(self, event):
#         if self.buttons_panel != None:
#             x = self.parent.winfo_x()
#             y = self.parent.winfo_y()
#             self.buttons_panel.geometry('+{}+{}'.format(x+10, y+30))
    
    def OnClose(self, *unused):
        """Closes the window and quit.
        """
        # print("_quit: bye")
        self.player.stop()
        self.parent.quit()  # stops mainloop
        self.parent.destroy()  # this is necessary on Windows to avoid
        # ... Fatal Python Error: PyEval_RestoreThread: NULL tstate

    def _DetectButtonsPanelDragging(self, _):
        """If our last click was on the boarder
           we disable the anchor.
        """
        if self.has_clicked_on_buttons_panel:
            self.is_buttons_panel_anchor_active = False
            self.buttons_panel.unbind("<Button-1>")
            self.buttons_panel.unbind("<B1-Motion>")
            self.buttons_panel.unbind("<ButtonRelease-1>")

    def _AnchorButtonsPanel(self):
        video_height = self.parent.winfo_height()
        panel_x = self.parent.winfo_x()
        panel_y = self.parent.winfo_y() + video_height + 23 # 23 seems to put the panel just below our video.
        panel_height = self.buttons_panel.winfo_height()
        panel_width = self.parent.winfo_width()
        self.buttons_panel.geometry("%sx%s+%s+%s" % (panel_width, panel_height, panel_x, panel_y))

    def OnConfigure(self, *unused):
        """Some widget configuration changed.
        """
        # <https://www.Tcl.Tk/man/tcl8.6/TkCmd/bind.htm#M12>
        self._geometry = ''  # force .OnResize in .OnTick, recursive?

        if self.is_buttons_panel_anchor_active:
            self._AnchorButtonsPanel()

    def OnFullScreen(self, *unused):
        """Toggle full screen, macOS only.
        """
        # <https://www.Tcl.Tk/man/tcl8.6/TkCmd/wm.htm#M10>
        f = not self.parent.attributes("-fullscreen")  # or .wm_attributes
        if f:
            self._previouscreen = self.parent.geometry()
            self.parent.attributes("-fullscreen", f)  # or .wm_attributes
            self.parent.bind("<Escape>", self.OnFullScreen)
        else:
            self.parent.attributes("-fullscreen", f)  # or .wm_attributes
            self.parent.geometry(self._previouscreen)
            self.parent.unbind("<Escape>")

    def OnMute(self, *unused):
        """Mute/Unmute audio.
        """
        # audio un/mute may be unreliable, see vlc.py docs.
        self.volMuted = m = not self.volMuted  # self.player.audio_get_mute()
        self.player.audio_set_mute(m)
        u = "Unmute" if m else "Mute"
        self.fileMenu.entryconfig(self.muteIndex, label=u)
        self.muteButton.config(text=u)
        # update the volume slider text
        self.OnVolume()

    def OnOpen(self, *unused):
        """Pop up a new dialow window to choose a file, then play the selected file.
        """
        # if a file is already running, then stop it.
        self.OnStop()
        # Create a file dialog opened in the current home directory, where
        # you can display all kind of files, having as title "Choose a video".
        video = askopenfilename(initialdir = Path(expanduser("~")),
                                title = "Choose a video",
                                filetypes = (("all files", "*.*"),
                                             ("mp4 files", "*.mp4"),
                                             ("mov files", "*.mov")))
        self._Play(video)

    def _Pause_Play(self, playing):
        # re-label menu item and button, adjust callbacks
        p = 'Pause' if playing else 'Play'
        c = self.OnPlay if playing is None else self.OnPause
        self.fileMenu.entryconfig(self.playIndex, label=p, command=c)
        # self.fileMenu.bind_shortcut('p', c)  # XXX handled
        self.playButton.config(text=p, command=c)
        self._stopped = False

    def _Play(self, video):
        # helper for OnOpen and OnPlay
        if isfile(video):  # Creation
            m = self.Instance.media_new(str(video))  # Path, unicode
            self.player.set_media(m)
            self.parent.title("tkVLCplayer - %s" % (basename(video),))

            # set the window id where to render VLC's video output
            h = self.videopanel.winfo_id()  # .winfo_visualid()?
            self.player.set_hwnd(h)
            self.OnPlay()

    def OnPause(self, *unused):
        """Toggle between Pause and Play.
        """
        if self.player.get_media():
            self._Pause_Play(not self.player.is_playing())
            self.player.pause()  # toggles

    def OnPlay(self, *unused):
        """Play video, if none is loaded, open the dialog window.
        """
        # if there's no video to play or playing,
        # open a Tk.FileDialog to select a file
        if not self.player.get_media():
            if self.video:
                self._Play(expanduser(self.video))
                self.video = ''
            else:
                self.OnOpen()
        # Try to play, if this fails display an error message
        elif self.player.play():  # == -1
            self.showError("Unable to play the video.")
        else:
            self._Pause_Play(True)
            # set volume slider to audio level
            vol = self.player.audio_get_volume()
            if vol > 0:
                self.volVar.set(vol)
                self.volSlider.set(vol)

    def OnResize(self, *unused):
        """Adjust the window/frame to the video aspect ratio.
        """
        g = self.parent.geometry()
        if g != self._geometry and self.player:
            u, v = self.player.video_get_size()  # often (0, 0)
            if v > 0 and u > 0:
                # get window size and position
                g, x, y = g.split('+')
                w, h = g.split('x')
                # alternatively, use .winfo_...
                # w = self.parent.winfo_width()
                # h = self.parent.winfo_height()
                # x = self.parent.winfo_x()
                # y = self.parent.winfo_y()
                # use the video aspect ratio ...
                if u > v:  # ... for landscape
                    # adjust the window height
                    h = round(float(w) * v / u)
                else:  # ... for portrait
                    # adjust the window width
                    w = round(float(h) * u / v)
                self.parent.geometry("%sx%s+%s+%s" % (w, h, x, y))
                self._geometry = self.parent.geometry()  # actual

    def OnStop(self, *unused):
        """Stop the player, resets media.
        """
        if self.player:
            self.player.stop()
            self._Pause_Play(None)
            # reset the time slider
            self.timeSlider.set(0)
            self._stopped = True
        # XXX on macOS libVLC prints these error messages:
        # [h264 @ 0x7f84fb061200] get_buffer() failed
        # [h264 @ 0x7f84fb061200] thread_get_buffer() failed
        # [h264 @ 0x7f84fb061200] decode_slice_header error
        # [h264 @ 0x7f84fb061200] no frame!

    def OnTick(self):
        """Timer tick, update the time slider to the video time.
        """
        if self.player:
            # since the self.player.get_length may change while
            # playing, re-set the timeSlider to the correct range
            t = self.player.get_length() * 1e-3  # to seconds
            if t > 0:
                self.timeSlider.config(to=t)

                t = self.player.get_time() * 1e-3  # to seconds
                # don't change slider while user is messing with it
                if t > 0 and time.time() > (self.timeSliderUpdate + 2):
                    self.timeSlider.set(t)
                    self.timeSliderLast = int(self.timeVar.get())
        # start the 1 second timer again
        self.parent.after(1000, self.OnTick)
        # adjust window to video aspect ratio, done periodically
        # on purpose since the player.video_get_size() only
        # returns non-zero sizes after playing for a while
        if not self._geometry:
            self.OnResize()

    def OnTime(self, *unused):
        if self.player:
            t = self.timeVar.get()
            if self.timeSliderLast != int(t):
                # this is a hack. The timer updates the time slider.
                # This change causes this rtn (the 'slider has changed' rtn)
                # to be invoked.  I can't tell the difference between when
                # the user has manually moved the slider and when the timer
                # changed the slider.  But when the user moves the slider
                # tkinter only notifies this rtn about once per second and
                # when the slider has quit moving.
                # Also, the tkinter notification value has no fractional
                # seconds.  The timer update rtn saves off the last update
                # value (rounded to integer seconds) in timeSliderLast if
                # the notification time (sval) is the same as the last saved
                # time timeSliderLast then we know that this notification is
                # due to the timer changing the slider.  Otherwise the
                # notification is due to the user changing the slider.  If
                # the user is changing the slider then I have the timer
                # routine wait for at least 2 seconds before it starts
                # updating the slider again (so the timer doesn't start
                # fighting with the user).
                self.player.set_time(int(t * 1e3))  # milliseconds
                self.timeSliderUpdate = time.time()

    def OnVolume(self, *unused):
        """Volume slider changed, adjust the audio volume.
        """
        vol = min(self.volVar.get(), 100)
        v_M = "%d%s" % (vol, " (Muted)" if self.volMuted else '')
        self.volSlider.config(label="Volume " + v_M)
        if self.player and not self._stopped:
            # .audio_set_volume returns 0 if success, -1 otherwise,
            # e.g. if the player is stopped or doesn't have media
            if self.player.audio_set_volume(vol):  # and self.player.get_media():
                self.showError("Failed to set the volume: %s." % (v_M,))

    def showError(self, message):
        """Display a simple error dialog.
        """
        self.OnStop()
        showerror(self.parent.title(), message)
        


# In[5]:


_video = ''
#_video = expanduser(sys.argv.pop(1))


# In[6]:


#The rootbase of the UI and create frame1 to hold bottoms and list elements
root = tk.Tk()
root.title("Football Tagging Software") 
# Create two frame to contain UI elements
canvas1=tk.Canvas(root)
canvas1.pack(side=tk.BOTTOM,fill=tk.X)


# In[7]:


# Player Start panel: Adding Buttons to cavas1 - frame_PS
frame_PS = tk.Frame(canvas1, bg = "white",highlightbackground="black", highlightthickness=1)
frame_PS.grid(column=0, row = 0,padx=5, pady=5)
frame_PS_label = tk.Label(frame_PS, text="Player Start",bg = "white")
frame_PS_label.grid(columnspan=3, row = 0)

PS_H1 = tk.Button(frame_PS, text = "H 1", command= lambda t= "H 1 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_H1.grid(column=0, row = 1)
PS_H2 = tk.Button(frame_PS, text = "H 2", command= lambda t= "H 2 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_H2.grid(column=0, row = 2)
PS_H3 = tk.Button(frame_PS, text = "H 3", command= lambda t= "H 3 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_H3.grid(column=0, row = 3)
PS_H4 = tk.Button(frame_PS, text = "H 4", command= lambda t= "H 4 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_H4.grid(column=0, row = 4)
PS_H5 = tk.Button(frame_PS, text = "H 5", command= lambda t= "H 5 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_H5.grid(column=0, row = 5)
PS_H6 = tk.Button(frame_PS, text = "H 6", command= lambda t= "H 6 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_H6.grid(column=0, row = 6)
PS_H7 = tk.Button(frame_PS, text = "H 7", command= lambda t= "H 7 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_H7.grid(column=0, row = 7)
PS_H8 = tk.Button(frame_PS, text = "H 8", command= lambda t= "H 8 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_H8.grid(column=0, row = 8)
PS_H9 = tk.Button(frame_PS, text = "H 9", command= lambda t= "H 9 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_H9.grid(column=0, row = 9)
PS_H10 = tk.Button(frame_PS, text = "H 10", command= lambda t= "H 10 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_H10.grid(column=0, row = 10)
PS_H11 = tk.Button(frame_PS, text = "H 11", command= lambda t= "H 11 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_H11.grid(column=0, row = 11)

PS_A1 = tk.Button(frame_PS, text = "A 1", command= lambda t= "A 1 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_A1.grid(column=2, row = 1)
PS_A2 = tk.Button(frame_PS, text = "A 2", command= lambda t= "A 2 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_A2.grid(column=2, row = 2)
PS_A3 = tk.Button(frame_PS, text = "A 3", command= lambda t= "A 3 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_A3.grid(column=2, row = 3)
PS_A4 = tk.Button(frame_PS, text = "A 4", command= lambda t= "A 4 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_A4.grid(column=2, row = 4)
PS_A5 = tk.Button(frame_PS, text = "A 5", command= lambda t= "A 5 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_A5.grid(column=2, row = 5)
PS_A6 = tk.Button(frame_PS, text = "A 6", command= lambda t= "A 6 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_A6.grid(column=2, row = 6)
PS_A7 = tk.Button(frame_PS, text = "A 7", command= lambda t= "A 7 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_A7.grid(column=2, row = 7)
PS_A8 = tk.Button(frame_PS, text = "A 8", command= lambda t= "A 8 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_A8.grid(column=2, row = 8)
PS_A9 = tk.Button(frame_PS, text = "A 9", command= lambda t= "A 9 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_A9.grid(column=2, row = 9)
PS_A10 = tk.Button(frame_PS, text = "A 10", command= lambda t= "A 10 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_A10.grid(column=2, row = 10)
PS_A11 = tk.Button(frame_PS, text = "A 11", command= lambda t= "A 11 Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_A11.grid(column=2, row = 11)

PS_CustomEntry = tk.Entry(frame_PS,width=4)
PS_CustomEntry.grid(column=2, row = 12)
PS_CustomEntry.insert(4, 0)
PS_Add = tk.Button(frame_PS, text = "Add", command= lambda t= " Clicked": [PS_lastClicked(t),PS_setValue(t)])
PS_Add.grid(column=0, row = 12)
           
def PS_lastClicked(t): # Use this function to update label text
    if t == " Clicked":
        t = PS_CustomEntry.get()+" Clicked"
    frame_PS_lastClicked.config(text=t)
def PS_setValue(t):
    global data_PS
    if t == " Clicked":
        t = PS_CustomEntry.get()+" Clicked"
    data_PS = t.replace(" Clicked","")
frame_PS_lastClicked = tk.Label(frame_PS, text="Unclicked",bg = "white") # Use this label to show the last text clicked
frame_PS_lastClicked.grid(columnspan=3, row = 13)


# In[8]:


# Player End panel: Adding Buttons to cavas1 - frame_PE
frame_PE = tk.Frame(canvas1, bg = "white",highlightbackground="black", highlightthickness=1)
frame_PE.grid(column=1, row = 0,padx=5, pady=5)
frame_PE_label = tk.Label(frame_PE, text="Player End",bg = "white")
frame_PE_label.grid(columnspan=3, row = 0)
PE_H1 = tk.Button(frame_PE, text = "H 1", command= lambda t= "H 1 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_H1.grid(column=0, row = 1)
PE_H2 = tk.Button(frame_PE, text = "H 2", command= lambda t= "H 2 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_H2.grid(column=0, row = 2)
PE_H3 = tk.Button(frame_PE, text = "H 3", command= lambda t= "H 3 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_H3.grid(column=0, row = 3)
PE_H4 = tk.Button(frame_PE, text = "H 4", command= lambda t= "H 4 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_H4.grid(column=0, row = 4)
PE_H5 = tk.Button(frame_PE, text = "H 5", command= lambda t= "H 5 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_H5.grid(column=0, row = 5)
PE_H6 = tk.Button(frame_PE, text = "H 6", command= lambda t= "H 6 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_H6.grid(column=0, row = 6)
PE_H7 = tk.Button(frame_PE, text = "H 7", command= lambda t= "H 7 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_H7.grid(column=0, row = 7)
PE_H8 = tk.Button(frame_PE, text = "H 8", command= lambda t= "H 8 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_H8.grid(column=0, row = 8)
PE_H9 = tk.Button(frame_PE, text = "H 9", command= lambda t= "H 9 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_H9.grid(column=0, row = 9)
PE_H10 = tk.Button(frame_PE, text = "H 10", command= lambda t= "H 10 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_H10.grid(column=0, row = 10)
PE_H11 = tk.Button(frame_PE, text = "H 11", command= lambda t= "H 11 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_H11.grid(column=0, row = 11)

PE_A1 = tk.Button(frame_PE, text = "A 1", command= lambda t= "A 1 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_A1.grid(column=2, row = 1)
PE_A2 = tk.Button(frame_PE, text = "A 2", command= lambda t= "A 2 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_A2.grid(column=2, row = 2)
PE_A3 = tk.Button(frame_PE, text = "A 3", command= lambda t= "A 3 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_A3.grid(column=2, row = 3)
PE_A4 = tk.Button(frame_PE, text = "A 4", command= lambda t= "A 4 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_A4.grid(column=2, row = 4)
PE_A5 = tk.Button(frame_PE, text = "A 5", command= lambda t= "A 5 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_A5.grid(column=2, row = 5)
PE_A6 = tk.Button(frame_PE, text = "A 6", command= lambda t= "A 6 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_A6.grid(column=2, row = 6)
PE_A7 = tk.Button(frame_PE, text = "A 7", command= lambda t= "A 7 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_A7.grid(column=2, row = 7)
PE_A8 = tk.Button(frame_PE, text = "A 8", command= lambda t= "A 8 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_A8.grid(column=2, row = 8)
PE_A9 = tk.Button(frame_PE, text = "A 9", command= lambda t= "A 9 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_A9.grid(column=2, row = 9)
PE_A10 = tk.Button(frame_PE, text = "A 10", command= lambda t= "A 10 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_A10.grid(column=2, row = 10)
PE_A11 = tk.Button(frame_PE, text = "A 11", command= lambda t= "A 11 Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_A11.grid(column=2, row = 11)

PE_CustomEntry = tk.Entry(frame_PE,width=4)
PE_CustomEntry.grid(column=2, row = 12)
PE_CustomEntry.insert(4, 0)
PE_Add = tk.Button(frame_PE, text = "Add", command= lambda t= " Clicked": [PE_lastClicked(t),PE_setValue(t)])
PE_Add.grid(column=0, row = 12)

def PE_lastClicked(t): # Use this function to update label text
    if t == " Clicked":
        t = PE_CustomEntry.get()+" Clicked"
    frame_PE_lastClicked.config(text=t)
def PE_setValue(t):
    global data_PE
    if t == " Clicked":
        t = PE_CustomEntry.get()+" Clicked"
    data_PE = t.replace(" Clicked","")
frame_PE_lastClicked = tk.Label(frame_PE, text="Unclicked",bg = "white") # Use this label to show the last text clicked
frame_PE_lastClicked.grid(columnspan=3, row = 13)


# In[9]:


# Event Type panel: Adding Buttons to cavas1 - frame_ET
frame_ET = tk.Frame(canvas1, bg = "white",highlightbackground="black", highlightthickness=1)
frame_ET.grid(column=2, row = 0,padx=5, pady=5)
frame_ET_label = tk.Label(frame_ET, text="Event Type",bg = "white")
frame_ET_label.grid(columnspan=1, row = 0)

Pass = tk.Button(frame_ET, text = "Pass", command= lambda t= "Pass Clicked": [ET_lastClicked(t),ET_setValue(t)])
Pass.grid(column=0, row = 1)
Dribble = tk.Button(frame_ET, text = "Dribble", command= lambda t= "Dribble Clicked": [ET_lastClicked(t),ET_setValue(t)])
Dribble.grid(column=0, row = 2)
Shot = tk.Button(frame_ET, text = "Shot", command= lambda t= "Shot Clicked": [ET_lastClicked(t),ET_setValue(t)])
Shot.grid(column=0, row = 3)
Assist = tk.Button(frame_ET, text = "Assist", command= lambda t= "Assist Clicked": [ET_lastClicked(t),ET_setValue(t)])
Assist.grid(column=0, row = 4)
Cross = tk.Button(frame_ET, text = "Cross", command= lambda t= "Cross Clicked": [ET_lastClicked(t),ET_setValue(t)])
Cross.grid(column=0, row = 5)
Clear = tk.Button(frame_ET, text = "Clear", command= lambda t= "Clear Clicked": [ET_lastClicked(t),ET_setValue(t)])
Clear.grid(column=0, row = 6)
Throw = tk.Button(frame_ET, text = "Throw", command= lambda t= "Throw Clicked": [ET_lastClicked(t),ET_setValue(t)])
Throw.grid(column=0, row = 7)
Corner = tk.Button(frame_ET, text = "Corner", command= lambda t= "Corner Clicked": [ET_lastClicked(t),ET_setValue(t)])
Corner.grid(column=0, row = 8)

def ET_lastClicked(t): # Use this function to update label text
    frame_ET_lastClicked.config(text=t)
def ET_setValue(t):
    global data_ET
    data_ET = t.replace(" Clicked","")
frame_ET_lastClicked = tk.Label(frame_ET, text="Unclicked",bg = "white") # Use this label to show the last text clicked
frame_ET_lastClicked.grid(columnspan=1, row = 9)


# In[10]:


# Other panel: Adding Buttons to cavas1 - frame_other
frame_other = tk.Frame(canvas1, bg = "white",highlightbackground="black", highlightthickness=1)
frame_other.grid(column=3, row = 0,padx=5, pady=5)
frame_other_label = tk.Label(frame_other, text="Other",bg = "white")
frame_other_label.grid(columnspan=2, row = 0)
ScoreH_label = tk.Label(frame_other, text="Score H: ",bg = "white")
ScoreH_label.grid(column = 0, row = 1)
ScoreA_label = tk.Label(frame_other, text="Score A: ",bg = "white")
ScoreA_label.grid(column = 0, row = 2)
ScoreH_Entry = tk.Entry(frame_other,width=2)
ScoreA_Entry = tk.Entry(frame_other,width=2)
ScoreH_Entry.grid(row=1, column=1)
ScoreA_Entry.grid(row=2, column=1)
ScoreH_Entry.insert(2, 0)
ScoreA_Entry.insert(2, 0)

CurrentGameTime_label = tk.Label(frame_other, text="Game Time: ",bg = "white")
CurrentGameTime_label.grid(columnspan=2, row = 3)
CurrentGameTime_Entry = tk.Entry(frame_other,width=5)
CurrentGameTime_Entry.grid(row=4, column=0)
CurrentGameTime_Entry.insert(5, 0)
CurrentGameTime_Button = tk.Button(frame_other, text = "Sync", command=lambda: CurrentGameTime_sync())
CurrentGameTime_Button.grid(column=1, row = 4)

def CurrentGameTime_sync():
    current_gametime_str = CurrentGameTime_Entry.get()
    current_gametime_m = int(current_gametime_str.split(":")[0].strip())
    current_gametime_s =  int(current_gametime_str.split(":")[1].strip())
    current_gametime_ms = current_gametime_s*1000 + current_gametime_m*60*1000
    video_time_ms = frame2.player.get_time()
    global time_diff
    time_diff = video_time_ms - current_gametime_ms
    CurrentGameTime_label.config(text="Game Time Synced: ")

frame_result_label = tk.Label(frame_other, text="Result: ",bg = "white")
frame_result_label.grid(column=0, row = 5)

Pass_C = tk.Button(frame_other, text = "Pass Completed", command= lambda t= "Pass Completed": [Other_lastClicked(t),result_setValue(t)])
Pass_C.grid(columnspan=2, row = 6)
Pass_F = tk.Button(frame_other, text = "Pass Failed", command= lambda t= "Pass Failed": [Other_lastClicked(t),result_setValue(t)])
Pass_F.grid(columnspan=2, row = 7)
Pass_I = tk.Button(frame_other, text = "Pass Intercepted", command= lambda t= "Pass Intercepted": [Other_lastClicked(t),result_setValue(t)])
Pass_I.grid(columnspan=2, row = 8)
Shot_S = tk.Button(frame_other, text = "Shot Scored", command= lambda t= "Shot Scored": [Other_lastClicked(t),result_setValue(t)])
Shot_S.grid(columnspan=2, row = 9)
Shot_B = tk.Button(frame_other, text = "Shot Blocked", command= lambda t= "Shot Blocked": [Other_lastClicked(t),result_setValue(t)])
Shot_B.grid(columnspan=2, row = 10)
Shot_SV = tk.Button(frame_other, text = "Shot Saved", command= lambda t= "Shot Saved": [Other_lastClicked(t),result_setValue(t)])
Shot_SV.grid(columnspan=2, row = 11)
Shot_C = tk.Button(frame_other, text = "Shot Corner", command= lambda t= "Shot Corner": [Other_lastClicked(t),result_setValue(t)])
Shot_C.grid(columnspan=2, row = 12)
Shot_OT = tk.Button(frame_other, text = "Shot Off Target", command= lambda t= "Shot Off Target": [Other_lastClicked(t),result_setValue(t)])
Shot_OT.grid(columnspan=2, row = 13)
Dribble_C = tk.Button(frame_other, text = "Dribble Completed", command= lambda t= "Dribble Completed": [Other_lastClicked(t),result_setValue(t)])
Dribble_C.grid(columnspan=2, row = 14)
Dribble_F = tk.Button(frame_other, text = "Dribble Failed", command= lambda t= "Dribble Failed": [Other_lastClicked(t),result_setValue(t)])
Dribble_F.grid(columnspan=2, row = 15)
Foul = tk.Button(frame_other, text = "Foul", command= lambda t= "Foul": [Other_lastClicked(t),result_setValue(t)])
Foul.grid(columnspan=2, row = 16)

def Other_lastClicked(t): # Use this function to update label text
    frame_Other_lastClicked.config(text=t)
def result_setValue(t):
    global data_Result
    data_Result = t
frame_Other_lastClicked = tk.Label(frame_other, text="Unclicked",bg = "white") # Use this label to show the last text clicked
frame_Other_lastClicked.grid(columnspan=2, row = 17)


# In[11]:


frame_Table = tk.Frame(canvas1, bg = "white",highlightbackground="black", highlightthickness=1)
frame_Table.grid(column=4, row = 0,padx=10, pady=5)
frame_Table_label = tk.Label(frame_Table, text="Data Table",bg = "white")
frame_Table_label.grid(column=0, row = 0)

frame_Table_VS_label = tk.Label(frame_Table, text="Video_Start",bg = "white",highlightbackground="black", highlightthickness=0.5)
frame_Table_VS_label.grid(column = 0, row = 1)
frame_Table_VE_label = tk.Label(frame_Table, text="Video_End",bg = "white",highlightbackground="black", highlightthickness=0.5)
frame_Table_VE_label.grid(column = 1, row = 1)
frame_Table_GS_label = tk.Label(frame_Table, text="Game_Start",bg = "white",highlightbackground="black", highlightthickness=0.5)
frame_Table_GS_label.grid(column = 2, row = 1)
frame_Table_GE_label = tk.Label(frame_Table, text="Game_End",bg = "white",highlightbackground="black", highlightthickness=0.5)
frame_Table_GE_label.grid(column = 3, row = 1)
frame_Table_PS_label = tk.Label(frame_Table, text="Player_Start",bg = "white",highlightbackground="black", highlightthickness=0.5)
frame_Table_PS_label.grid(column = 4, row = 1)
frame_Table_PE_label = tk.Label(frame_Table, text="Player_End",bg = "white",highlightbackground="black", highlightthickness=0.5)
frame_Table_PE_label.grid(column = 5, row = 1)
frame_Table_ET_label = tk.Label(frame_Table, text="Event_Type",bg = "white",highlightbackground="black", highlightthickness=0.5)
frame_Table_ET_label.grid(column = 6, row = 1)
frame_Table_SH_label = tk.Label(frame_Table, text="Score_Home",bg = "white",highlightbackground="black", highlightthickness=0.5)
frame_Table_SH_label.grid(column = 7, row = 1)
frame_Table_SA_label = tk.Label(frame_Table, text="Score_Away",bg = "white",highlightbackground="black", highlightthickness=0.5)
frame_Table_SA_label.grid(column = 8, row = 1)
frame_Table_RE_label = tk.Label(frame_Table, text="           Result           ",bg = "white",highlightbackground="black", highlightthickness=0.5)
frame_Table_RE_label.grid(column = 9, row = 1)
frame_Table_LF_label = tk.Label(frame_Table, text="Location_From",bg = "white",highlightbackground="black", highlightthickness=0.5)
frame_Table_LF_label.grid(column = 10, row = 1)
frame_Table_LT_label = tk.Label(frame_Table, text="Location_To",bg = "white",highlightbackground="black", highlightthickness=0.5)
frame_Table_LT_label.grid(column = 11, row = 1)

frame_Table_02_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_02_label.grid(column = 0, row = 2)
frame_Table_12_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_12_label.grid(column = 1, row = 2)
frame_Table_22_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_22_label.grid(column = 2, row = 2)
frame_Table_32_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_32_label.grid(column = 3, row = 2)
frame_Table_42_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_42_label.grid(column = 4, row = 2)
frame_Table_52_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_52_label.grid(column = 5, row = 2)
frame_Table_62_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_62_label.grid(column = 6, row = 2)
frame_Table_72_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_72_label.grid(column = 7, row = 2)
frame_Table_82_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_82_label.grid(column = 8, row = 2)
frame_Table_92_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_92_label.grid(column = 9, row = 2)
frame_Table_102_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_102_label.grid(column = 10, row = 2)
frame_Table_112_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_112_label.grid(column = 11, row = 2)
frame_Table_122_Button_delete = tk.Button(frame_Table, text = "delete",command= lambda t = 1 :delete_row(t))
frame_Table_122_Button_delete.grid(column=12, row = 2)

frame_Table_03_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_03_label.grid(column = 0, row = 3)
frame_Table_13_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_13_label.grid(column = 1, row = 3)
frame_Table_23_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_23_label.grid(column = 2, row = 3)
frame_Table_33_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_33_label.grid(column = 3, row = 3)
frame_Table_43_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_43_label.grid(column = 4, row = 3)
frame_Table_53_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_53_label.grid(column = 5, row = 3)
frame_Table_63_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_63_label.grid(column = 6, row = 3)
frame_Table_73_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_73_label.grid(column = 7, row = 3)
frame_Table_83_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_83_label.grid(column = 8, row = 3)
frame_Table_93_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_93_label.grid(column = 9, row = 3)
frame_Table_103_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_103_label.grid(column = 10, row = 3)
frame_Table_113_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_113_label.grid(column = 11, row = 3)
frame_Table_123_Button_delete = tk.Button(frame_Table, text = "delete",command= lambda t = 2 :delete_row(t))
frame_Table_123_Button_delete.grid(column=12, row = 3)

frame_Table_04_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_04_label.grid(column = 0, row = 4)
frame_Table_14_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_14_label.grid(column = 1, row = 4)
frame_Table_24_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_24_label.grid(column = 2, row = 4)
frame_Table_34_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_34_label.grid(column = 3, row = 4)
frame_Table_44_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_44_label.grid(column = 4, row = 4)
frame_Table_54_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_54_label.grid(column = 5, row = 4)
frame_Table_64_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_64_label.grid(column = 6, row = 4)
frame_Table_74_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_74_label.grid(column = 7, row = 4)
frame_Table_84_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_84_label.grid(column = 8, row = 4)
frame_Table_94_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_94_label.grid(column = 9, row = 4)
frame_Table_104_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_104_label.grid(column = 10, row = 4)
frame_Table_114_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_114_label.grid(column = 11, row = 4)
frame_Table_124_Button_delete = tk.Button(frame_Table, text = "delete",command= lambda t = 3 :delete_row(t))
frame_Table_124_Button_delete.grid(column=12, row = 4)

frame_Table_05_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_05_label.grid(column = 0, row = 5)
frame_Table_15_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_15_label.grid(column = 1, row = 5)
frame_Table_25_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_25_label.grid(column = 2, row = 5)
frame_Table_35_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_35_label.grid(column = 3, row = 5)
frame_Table_45_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_45_label.grid(column = 4, row = 5)
frame_Table_55_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_55_label.grid(column = 5, row = 5)
frame_Table_65_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_65_label.grid(column = 6, row = 5)
frame_Table_75_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_75_label.grid(column = 7, row = 5)
frame_Table_85_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_85_label.grid(column = 8, row = 5)
frame_Table_95_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_95_label.grid(column = 9, row = 5)
frame_Table_105_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_105_label.grid(column = 10, row = 5)
frame_Table_115_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_115_label.grid(column = 11, row = 5)
frame_Table_125_Button_delete = tk.Button(frame_Table, text = "delete",command= lambda t = 4 :delete_row(t))
frame_Table_125_Button_delete.grid(column=12, row = 5)

frame_Table_06_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_06_label.grid(column = 0, row = 6)
frame_Table_16_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_16_label.grid(column = 1, row = 6)
frame_Table_26_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_26_label.grid(column = 2, row = 6)
frame_Table_36_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_36_label.grid(column = 3, row = 6)
frame_Table_46_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_46_label.grid(column = 4, row = 6)
frame_Table_56_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_56_label.grid(column = 5, row = 6)
frame_Table_66_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_66_label.grid(column = 6, row = 6)
frame_Table_76_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_76_label.grid(column = 7, row = 6)
frame_Table_86_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_86_label.grid(column = 8, row = 6)
frame_Table_96_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_96_label.grid(column = 9, row = 6)
frame_Table_106_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_106_label.grid(column = 10, row = 6)
frame_Table_116_label = tk.Label(frame_Table, text="",bg = "white")
frame_Table_116_label.grid(column = 11, row = 6)
frame_Table_126_Button_delete = tk.Button(frame_Table, text = "delete",command= lambda t = 5 :delete_row(t))
frame_Table_126_Button_delete.grid(column=12, row = 6)

FT_row1 = [frame_Table_02_label,frame_Table_12_label,frame_Table_22_label,frame_Table_32_label,frame_Table_42_label,frame_Table_52_label,frame_Table_62_label,frame_Table_72_label,frame_Table_82_label,frame_Table_92_label,frame_Table_102_label,frame_Table_112_label]
FT_row2 = [frame_Table_03_label,frame_Table_13_label,frame_Table_23_label,frame_Table_33_label,frame_Table_43_label,frame_Table_53_label,frame_Table_63_label,frame_Table_73_label,frame_Table_83_label,frame_Table_93_label,frame_Table_103_label,frame_Table_113_label]
FT_row3 = [frame_Table_04_label,frame_Table_14_label,frame_Table_24_label,frame_Table_34_label,frame_Table_44_label,frame_Table_54_label,frame_Table_64_label,frame_Table_74_label,frame_Table_84_label,frame_Table_94_label,frame_Table_104_label,frame_Table_114_label]
FT_row4 = [frame_Table_05_label,frame_Table_15_label,frame_Table_25_label,frame_Table_35_label,frame_Table_45_label,frame_Table_55_label,frame_Table_65_label,frame_Table_75_label,frame_Table_85_label,frame_Table_95_label,frame_Table_105_label,frame_Table_115_label]
FT_row5 = [frame_Table_06_label,frame_Table_16_label,frame_Table_26_label,frame_Table_36_label,frame_Table_46_label,frame_Table_56_label,frame_Table_66_label,frame_Table_76_label,frame_Table_86_label,frame_Table_96_label,frame_Table_106_label,frame_Table_116_label]
FT_rowlist = [FT_row5,FT_row4,FT_row3,FT_row2,FT_row1]


# In[12]:


# Add button commad to add data row
def add_tag_row():
    new_row_index = tagDF.shape[0]
    data_SH = ScoreH_Entry.get()
    data_SA =ScoreA_Entry.get()
    data_VS = convertMillis(max(0,frame2.player.get_time()-2000))
    data_VE = convertMillis(min(frame2.player.get_time()+2000,frame2.player.get_length()))
    data_GS = convertMillis(max(0,frame2.player.get_time()-2000 - time_diff))
    data_GE = convertMillis(min(frame2.player.get_time()+3000-time_diff,frame2.player.get_length()))
    tagDF.loc[new_row_index] = [data_VS, data_VE, data_GS,data_GE,data_PS,data_PE,data_ET,data_SH,data_SA,data_Result,data_LF,data_LT]
    update_frameTable()

# add function for delete button to remove current data row
def delete_row(t):
    row_id = 5 - int(t)
    if FT_rowlist[row_id][0].cget("text") != "":
        if tagDF.shape[0] == int(t):
            tagDF.drop([int(t)-1],inplace = True)
        elif tagDF.shape[0] > int(t) and tagDF.shape[0] < 5:
            tagDF.drop([int(t)-1],inplace = True)
        elif tagDF.shape[0] > int(t) and tagDF.shape[0] >= 5:
            tagDF.drop([tagDF.shape[0] - 5 + int(t) - 1],inplace = True)
        for label in FT_rowlist[row_id]:
             label.config(text = "")
        tagDF.reset_index(drop=True,inplace = True)

# add function to convert video time from miliseconds to hours minutes seconds
def convertMillis(millis):
    seconds=int((millis/1000)%60)
    minutes=int((millis/(1000*60))%60)
    hours=int((millis/(1000*60*60))%24)
    result = str(hours)+":"+str(minutes)+":"+str(seconds)
    return result

# update Data tabel with data fields in tagDF
def update_frameTable():
    if tagDF.shape[0] > 0:
        row_count  = tagDF.shape[0]
        label = 0
        while row_count >=1 and label <= 4:
            update_labelrow(FT_rowlist[label],row_count-1)
            row_count -=1
            label+=1
        
def update_labelrow(label_list,row_index):
    column_names = tagDF.columns.values.tolist()
    for i in range(12):
        label_list[i].config(text=tagDF.at[row_index, column_names[i]])

# function used in clear button to clear label and data fields
def clear_location():
    Lf_value_label.config(text = "")
    Lf_value_label.config(font=default_font)
    Lt_value_label.config(text = "")
    Lt_value_label.config(font=default_font)
    global data_LF, data_LT
    data_LF = ""
    data_LT = ""
    
def export_data():
    global tagDF
    tagDF.to_csv("Tagging_Export.csv",index = False, encoding = 'utf-8')
    Export_label.config(text = "Export Success!")

Button_Add = tk.Button(frame_Table, text = "Add",command= lambda :add_tag_row())
Button_Add.grid(column=1, row = 0)
Lf_label = tk.Label(frame_Table, text="LocaFrom:",bg = "white")
Lf_label.grid(column = 2, row = 0)
Lf_value_label = tk.Label(frame_Table, text="",bg = "white")
Lf_value_label.grid(column = 3, row = 0,columnspan=2)
Lt_label = tk.Label(frame_Table, text="LocaTo:",bg = "white")
Lt_label.grid(column = 6, row = 0)
Lt_value_label = tk.Label(frame_Table, text="",bg = "white")
Lt_value_label.grid(column = 7, row = 0,columnspan=2)
Button_clearLocation = tk.Button(frame_Table, text = "Clean",command= lambda :clear_location())
Button_clearLocation.grid(column=9, row = 0)
Button_export = tk.Button(frame_Table, text = "Export",command= lambda :export_data())
Button_export.grid(column=10, row = 0)
Export_label = tk.Label(frame_Table, text="",bg = "white")
Export_label.grid(column = 11, row = 0,columnspan=2)

# stores default_font for conversion
default_font = tkFont.Font(font=Lf_label['font'])


# In[13]:


#Add video player to frame2 left side
frame2 = Player(root, video=_video)
frame2.pack(fill=tk.X, expand=True,side = tk.BOTTOM)
# player.grid(column=0, row = 0)
root.protocol("WM_DELETE_WINDOW", frame2.OnClose)


# In[14]:


#Create image canvas to store the image and collect mouse position
image_canvas = tk.Canvas(frame2,width = 500, height = 300, background = 'white')
image_canvas.pack(fill=tk.X, expand=True,side = tk.RIGHT)


# In[15]:


#Add image to image_canvas as a reference for clicking
field_image = Image.open('Field.jpg')
field_image = field_image.resize((500,300)) #resize image
field_image = ImageTk.PhotoImage(field_image)
image_canvas.create_image(1,1,image = field_image, anchor=tk.NW)

# field_image_label=tk.Label(image_canvas,image = field_image)
# field_image_label.Image = field_image
# field_image_label.grid(column=2, row = 2)
# field_image_label.pack(fill=tk.X, expand=True)


# In[16]:


# create function to capture location data based on mouse click position
def assign_location(event):
    global data_LF, data_LT, click_number
    if click_number == 0:
        x1 = event.x
        y1 = event.y
        data_LF = ' '.join([str(max(0,x1/4-8.75)),str(max((300-y1)/4-5,0))])
        Lf_value_label.config(text = data_LF,font='underline')
        Lt_value_label.config(font=default_font)
        click_number = 1
    else:
        x2 = event.x
        y2 = event.y
        data_LT = ' '.join([str(max(0,x2/4-8.75)),str(max((300-y2)/4-5,0))])
        Lt_value_label.config(text = data_LT,font='underline')
        Lf_value_label.config(font=default_font)
        click_number = 0
image_canvas.bind('<Button-1>',assign_location)
click_number = 0


# In[17]:


#Add Video to tk using tkvideo
# video_label = tk.Label(root)
# player = tkvideo("C:\\Users\\yingy\\Desktop\\中国vs沙特.mp4", video_label,loop = 1, size = (1280,720))
# video_label.grid(column=0, row = 0)


# In[18]:


#Add Video Play Button 
# def play():
#     player.play()
# play_button = tk.Button(root, text = "Play",command = play)
# play_button.grid(column=2, row = 0)


# In[19]:


# Add Video to tk using VLC
# root.video = expanduser(video)
# media = vlc.MediaPlayer("C:\\Users\\yingy\\Desktop\\中国vs沙特.mp4")
# media.play()


# In[20]:


#all UI elements must be before this
root.mainloop()


# ### Reference
# https://www.youtube.com/watch?v=itRLRfuL_PQ
# 
# https://www.askpython.com/python-modules/tkinter/python-tkinter-grid-example
# 
# https://www.youtube.com/watch?v=yQSEXcf6s2I&list=PLCC34OHNcOtoC6GglhF3ncJ5rLwQrLGnV
# 
# Identifying mouse click position:
# https://youtu.be/XC4eJQCem_0
# 
# Drawing a line between two mouse click: https://www.youtube.com/watch?v=fj-SIM9nXOw
