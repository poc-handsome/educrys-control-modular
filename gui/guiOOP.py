import time
from threading import Thread
import sys
import logging   
import os

#import democz_recipe as self.rec

from tkinter import *
from PIL import ImageTk, Image
import numpy as np
import matplotlib as mpl
mpl.use("TkAgg")
#from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from matplotlib.widgets import CheckButtons
import matplotlib.pyplot as plt
import matplotlib.backends.backend_tkagg as tkagg
#import matplotlib.colors as mcolors

from interfaceGui import InterfaceGui


class Gui:
    def __init__(self):
        self.link = InterfaceGui()
        #time.sleep(0.5)
        #self.config = self.link.getConfig()

        self.skipWeight = True
        self.skipCam    = True
        self.skipIr     = True

        # root window
        self.root = Tk()
        self.root.title("Prof. Cz")
        # root.resizable(width=False, height=False)
        self.start = False
        self.stop_threads = False
        self.sampletime = 2000
        # Sensor
        self.kwh_val = 0

        # Heating/PID
        self.pid_mode = 0
        self.chkselv = BooleanVar()
        self.chksel = False
        self.rbselv = IntVar()
        self.rbselv.set(0)

        self.pid_out_man    =     0
        self.pid_out_period = 10000
        self.pid_out_min    =   250
        self.pid_out_max    =  5000
        self.chkctrpv = BooleanVar()

        self.pid_set_min = 0
        self.pid_set_max = 250
        self.pid_set     = 0
        self.chkctrtv = BooleanVar()

        # Motor
        ## Lin
        self.lin_val     = 0
        self.lin_val_min = -100
        self.lin_val_max = 100
        self.lin_z       = 100
        self.lin_z_min   = 0
        self.lin_z_max   = 260
        self.chkmotlv    = BooleanVar()

        ## Rot
        self.rot_val     =   0
        self.rot_val_min = -12
        self.rot_val_max =  12
        self.chkmotrv    = BooleanVar()

        ## Fan
        self.fan_val     =  0
        self.fan_val_min =  0
        self.fan_val_max = 70
        self.chkmotfv    = BooleanVar()

        # Device
        ## LED
        self.led_on = False
        
        ## Sound
        self.sound_on = False
        self.ttalarm              = 0
        self.time_startalarm      = 0
        self.time_startalarmtimer = 0
        self.planalarm            = False
        self.chkalv               = BooleanVar()

        # Camera

        # Set cells with non-zero weight, so that they expand with sticky
        # root.rowconfigure(tuple(range(4)),weight=1)
        self.root.rowconfigure(1,weight=1)
        self.root.columnconfigure(0,weight=1) # pictures expand horizontally

        # ---------- Canvas for camera
        
        # Vis
        
        self.cnv_cam = Canvas(self.root, width=400, height=300)
        self.cnv_cam.configure()
        self.cnv_cam.grid(column=0, row=0, sticky='w')
        
        self.frm_img = Frame(self.root) 
        self.frm_img.grid(column=1, row=1, padx=5, pady=2)
        
        self.frm_exp = Frame(self.root) # bg='green')
        self.frm_exp.grid(column=0, row=1, padx=5, pady=2)
        
        # Ir
        self.cnv_img = Canvas(self.root, width=400, height=300)
        self.cnv_img.configure()
        self.cnv_img.grid(column=1, row=0, sticky='w')
        
        # ---------- Plot

        # Label, visibility, y axis, scale factor, linestyle, line/labelcolor, if updated in loop
        # Axes: x1, y1, y2 or none 
        self.plot_params = [
            ['Time[s]',         True,  'x1', 1.0, 'solid',  'black',     True],
            ['T_PT_1[C]',       True,  'y1', 1.0, 'solid',  'gold',      True],
            ['T_TC_1[C]',       True,  'y1', 1.0, 'solid',  'fuchsia',   True],
            ['T_TC_2[C]',       True,  'y1', 1.0, 'solid',  'sienna',    True],
            ['T_air[C]',        True,  'y1', 1.0, 'solid',  'yellow',    True],
            ['H_air[%]',        True,  'y1', 1.0, 'solid',  'skyblue',   True],
            ['Weight[g]',       True,  'y2', 1.0, 'dashed', 'green',     True],
            ['Energy[kWh]',     True,  'y2', 1.0, 'dashed', 'teal',      True],
            ['5V-I[mA]',        False, 'y2', 1.0, 'dashed', 'darkgreen', True],
            ['Mot_Lin[mm/s]',   True,  'y2', 1.0, 'dashed', 'blue',      True],
            ['Mot_Rot[rpm]',    True,  'y2', 1.0, 'dashed', 'cyan',      True],
            ['Mot_Fan[%]',      True,  'y2', 1.0, 'dashed', 'steelblue', True],
            ['z[mm]',           True,  'y1', 1.0, 'solid',  'black',     True],
            ['pid_out[%]',      True,  'y1', 1.0, 'solid',  'lime',      True],
            ['pid_set[C]',      True,  'y1', 1.0, 'solid',  'red',       True],
            ]

        self.plot_list = []
        for i in range(len(self.plot_params)):
            newlist = []
            self.plot_list.append(newlist)

        self.plot_xaxis = 0 
        self.plot_ylist = []
        for i in range(len(self.plot_params)):
            if self.plot_params[i][2] == 'x1': self.plot_xaxis = i  
            if self.plot_params[i][2] == 'y1': self.plot_ylist.append(i)
            if self.plot_params[i][2] == 'y2': self.plot_ylist.append(i)

        my_dpi=96
        self.figDAT, self.axDAT = plt.subplots(sharey=True, figsize=(800/my_dpi, 400/my_dpi), dpi=my_dpi)
        self.figDAT.subplots_adjust(left=0.27, bottom=0.1, right=0.92, top=0.95, wspace=0, hspace=0)
        self.axDAT.grid(True, 'major', 'both', ls='--', lw=.5, c='k', alpha=.3)
        self.axDAT.set_xlabel('Time, s')

        # cm = plt.get_cmap('tab20')
        # plot_colors=[cm(1.*i/len(self.plot_ylist)) for i in range(len(self.plot_ylist))]    
        
        self.axDAT2 = self.axDAT.twinx()
        self.axDAT2.format_coord = self.make_format()
                
        self.figDATi = []

        for j in range(len(self.plot_ylist)):
            i = self.plot_ylist[j]
            if (self.plot_params[i][2]=='y1'):
                li, =  self.axDAT.plot(self.plot_list[self.plot_xaxis], self.plot_list[i], visible=self.plot_params[i][1], label=self.plot_params[i][0], color=self.plot_params[i][5], linestyle=self.plot_params[i][4])
                self.figDATi.append( li )
            if (self.plot_params[i][2]=='y2'):
                li, =  self.axDAT2.plot(self.plot_list[self.plot_xaxis], self.plot_list[i], visible=self.plot_params[i][1], label=self.plot_params[i][0], color=self.plot_params[i][5], linestyle=self.plot_params[i][4])
                self.figDATi.append( li )

        # Make checkbuttons 
            
        rax = plt.axes([0.02, 0.02, 0.17, 0.98]) # left, bottom, width, height for Buttons
        self.labels = [str(line.get_label()) for line in self.figDATi]
        visibility = [line.get_visible() for line in self.figDATi]
        check = CheckButtons(rax, self.labels, visibility)     
        
        #for i, c in enumerate(plot_colors):
        #    check.self.labels[i].set_color(c)
            
        for j in range( len(self.figDATi) ):
            self.pl = self.figDATi[j]
            check.labels[j].set_color( self.pl.get_color() )

        # Resizing of Checkboxes
        try:
            scx = 3.0 
            scy = 1.2 
            for rect in check.rectangles: 
                rect.set_width(rect.get_width()*scx)
                rect.set_height(rect.get_height()*scy)
            for l in check.lines:
                l[0].set_xdata([ l[0].get_xdata()[0], l[0].get_xdata()[0]+(l[0].get_xdata()[1]-l[0].get_xdata()[0])*scx ])
                l[1].set_xdata([ l[1].get_xdata()[0], l[1].get_xdata()[0]+(l[1].get_xdata()[1]-l[1].get_xdata()[0])*scx ]) 
                l[0].set_ydata([ l[0].get_ydata()[1]+(l[0].get_ydata()[0]-l[0].get_ydata()[1])*scy, l[0].get_ydata()[1] ])
                l[1].set_ydata([ l[1].get_ydata()[0], l[1].get_ydata()[0]+(l[1].get_ydata()[1]-l[1].get_ydata()[0])*scy ])
        except:
            logging.error("resizing of checkboxes failed. Matplotlib Version must be 3.6.3 or lower!")

        check.on_clicked(self.func)

        plot = tkagg.FigureCanvasTkAgg(self.figDAT, master=self.root) # FigureCanvasTkAgg object
        plot.get_tk_widget().grid(column=0, columnspan=2, row=2, sticky='news')

        frm_bot = Frame(self.root)
        frm_bot.grid(column=0, columnspan=2, row=3, sticky='news')
        self.toolbar = tkagg.NavigationToolbar2Tk(plot, frm_bot)
        self.toolbar.update()
        self.toolbar.pack(side='left', padx=10)


        btnauto = Button(frm_bot, text="Autoscale", command=self.btnauto_run)
        btnauto.pack(side='right', padx=10)

        # ---------- Buttons and self.labels

        # All buttons and inputs are on a new frame!!
        self.frame1=Frame(self.root) # bg='green')
        self.frame1.grid(column=2, row=0, rowspan=4, padx=10, pady=10, sticky='news')

        self.rowi = 0
        
        # --- self.start time

        self.lbltt = Label(self.frame1, text='Log time [s]:')
        self.lbltt.grid(column=0, row=self.rowi, sticky='w')

        self.lblttv = Label(self.frame1, text='0')
        self.lblttv.grid(column=2, row=self.rowi, sticky='w')          
                
        self.btnstart = Button(self.frame1, text="Start", width=4, command=self.btnstart_run)
        self.btnstart.grid(column=4, row=self.rowi, sticky='w')

        # --- Measurements incl. PID input selection
        self.rowi += 1
        self.lblsens = Label(self.frame1, text='MEASUREMENTS')
        self.lblsens.grid(column=0, columnspan=6, row=self.rowi, sticky='s')
        
        self.rowi += 1
        self.chksel = Checkbutton(self.frame1, text='Switch PID Input :', variable=self.chkselv, command=self.chksel_change)
        self.chksel.grid(column=4, columnspan=2, row=self.rowi, sticky='e')    

        self.rowi += 1
        self.lblpt1 = Label(self.frame1, text='T_PT_1 [°C]:')
        self.lblpt1.grid(column=0, row=self.rowi, sticky='w')

        self.lblpt1v = Label(self.frame1, text='0')
        self.lblpt1v.grid(column=2, row=self.rowi, sticky='w')

        self.rbselpt1 = Radiobutton(self.frame1, text='', variable=self.rbselv, value=0, command=self.rbsel_change)
        self.rbselpt1.grid(column=5, row=self.rowi, sticky='w')
        self.rbselpt1.config(state='disabled')

        self.rowi += 1
        self.lbltc1 = Label(self.frame1, text='T_TC_1 [°C]:')
        self.lbltc1.grid(column=0, row=self.rowi, sticky='w')

        self.lbltc1v = Label(self.frame1, text='0')
        self.lbltc1v.grid(column=2, row=self.rowi, sticky='w')
        
        self.rbseltc1 = Radiobutton(self.frame1, text='', variable=self.rbselv, value=1, command=self.rbsel_change)
        self.rbseltc1.grid(column=5, row=self.rowi, sticky='w')
        self.rbseltc1.config(state='disabled')

        self.rowi += 1
        self.lbltc2 = Label(self.frame1, text='T_TC_2 [°C]:')
        self.lbltc2.grid(column=0, row=self.rowi, sticky='w')

        self.lbltc2v = Label(self.frame1, text='0')
        self.lbltc2v.grid(column=2, row=self.rowi, sticky='w')
        
        self.rbseltc2 = Radiobutton(self.frame1, text='', variable=self.rbselv, value=2, command=self.rbsel_change)
        self.rbseltc2.grid(column=5, row=self.rowi, sticky='w')
        self.rbseltc2.config(state='disabled')

        self.rowi += 1
        self.lblshtt = Label(self.frame1, text='T_air [°C]:')
        self.lblshtt.grid(column=0, row=self.rowi, sticky='w')

        self.lblshttv = Label(self.frame1, text='0')
        self.lblshttv.grid(column=2, row=self.rowi, sticky='w')
        
        self.rowi += 1
        self.lblshth = Label(self.frame1, text='H_air [%]:')
        self.lblshth.grid(column=0, row=self.rowi, sticky='w')

        self.lblshthv = Label(self.frame1, text='0')
        self.lblshthv.grid(column=2, row=self.rowi, sticky='w')

        self.rowi += 1
        self.lblpow = Label(self.frame1, text='Energy [kWh]:')
        self.lblpow.grid(column=0, row=self.rowi, sticky='w')

        self.lblpowv = Label(self.frame1, text='0')
        self.lblpowv.grid(column=2, row=self.rowi, sticky='w')

        btnpow = Button(self.frame1, text='Reset', command=self.btnpow_run)
        btnpow.grid(column=4, row=self.rowi, sticky='w')

        self.rowi += 1
        self.lblina = Label(self.frame1, text='5V Current [mA]:')
        self.lblina.grid(column=0, row=self.rowi, sticky='w')

        self.lblinav = Label(self.frame1, text='0')
        self.lblinav.grid(column=2, row=self.rowi, sticky='w')

        self.rowi += 1
        self.lblwei = Label(self.frame1, text='Weight [g]:')
        self.lblwei.grid(column=0, row=self.rowi, sticky='w')

        self.lblweiv = Label(self.frame1, text='0')
        self.lblweiv.grid(column=2, row=self.rowi, sticky='w')

        btnwei = Button(self.frame1, text='Tare', command=self.btnwei_run)
        btnwei.grid(column=4, row=self.rowi, sticky='w')
        if self.skipWeight == False : btnwei.config(state='disabled')

        # ---- 

        self.rowi += 1
        lblheat = Label(self.frame1, text='HEATING CONTROL')
        lblheat.grid(column=0, columnspan=6, row=self.rowi, sticky='s')

        # --- Heating control radiobutton
        """
        # Selection between PID and Manual temperature regulation
        
        self.rowi += 1
        lblctr = Label(self.frame1, text='Control:')
        lblctr.grid(column=0, row=self.rowi, sticky='w')

        self.rbctrv = IntVar()
        self.rbctrv.set(1)
                
        self.rbctr0 = Radiobutton(self.frame1, text='PID', variable=self.rbctrv, value=1, command=self.rbctr_change)
        self.rbctr0.grid(column=2, row=self.rowi, sticky='w')
        
        
        self.rowi += 1
        self.rbctr1 = Radiobutton(self.frame1, text='Manual', variable=self.rbctrv, value=0, command=self.rbctr_change)
        self.rbctr1.grid(column=2, row=self.rowi, sticky='w')
        """
        
        self.rowi += 1
        lblrec = Label(self.frame1, text='Start/Stop recipe :')
        lblrec.grid(column=4, columnspan=2, row=self.rowi, sticky='e')

        # Target temperature
        self.inpctrtv, self.inpctrt, self.btnctrt, self.chkctrt = self.createRowWithInput(
            labelText      = 'Target T [°C]:',
            varType        = DoubleVar(),
            varStart       = 0,
            runFunction    = self.btnctrt_run,
            changeFunction = self.chkctrt_change)
        """
        # Manual temperature regulation 
        # Not needed during regular operations
        
        self.inpctrpv, self.inpctrp, self.btnctrp, self.chkctrp = self.createRowWithInput(
            labelText      = 'Target P [%]:',
            varType        = DoubleVar(),
            varStart       = 0,
            runFunction    = self.btnctrp_run,
            changeFunction = self.chkctrp_change)
        """
        ### Motors ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 

        self.rowi += 1
        lblmot = Label(self.frame1, text='MOTOR CONTROL')
        lblmot.grid(column=0, columnspan=6, row=self.rowi, sticky='s')
        
        # LinSpeed
        self.inpmotlv, self.inpmotl, self.btnmotl, self.chkmotl = self.createRowWithInput(
            labelText      = 'Lin. vel. [mm/min]:',
            varType        = DoubleVar(),
            varStart       = 0,
            runFunction    = self.btnmotl_run,
            changeFunction = self.chkmotl_change)

        # LinPos
        self.inpmotzv, self.inpmotz, self.btnmotz = self.createRowWithInput(
            labelText      = 'Coord. Z [mm]:',
            varType        = DoubleVar(),
            varStart       = self.lin_z,
            runFunction    = self.btnmotz_run,
            changeFunction = False)

        # Rot
        self.inpmotrv, self.inpmotr, self.btnmotr, self.chkmotr = self.createRowWithInput(
            labelText      = 'Rot. vel. [rpm]:',
            varType        = DoubleVar(),
            varStart       = 0,
            runFunction    = self.btnmotr_run,
            changeFunction = self.chkmotr_change)

        # Fan
        self.inpmotfv, self.inpmotf, self.btnmotf, self.chkmotf = self.createRowWithInput(
            labelText      = 'Fan vel. [%]:',
            varType        = DoubleVar(),
            varStart       = 0,
            runFunction    = self.btnmotf_run,
            changeFunction = self.chkmotf_change)
        
        
        ### Alarm ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### 

        self.inpalv, self.inpal, self.btnal, self.chkal = self.createRowWithInput(
            labelText      = 'Alarm [s]:',
            varType        = IntVar(),
            varStart       = 0,
            runFunction    = self.btnal_run,
            changeFunction = self.chkal_change)

        # ---

        lblspace1 = Label(self.frame1, text=' ')
        lblspace1.grid(column=1, row=self.rowi)

        lblspace2 = Label(self.frame1, text=' ')
        lblspace2.grid(column=3, row=self.rowi)

        self.frame1.rowconfigure(tuple(range(self.rowi)),weight=1)
        
        # ---------- Take camera picture and LED on/off
        
        frm_exp = Frame(self.root) # bg='green')
        frm_exp.grid(column=0, row=1, padx=5, pady=2)

        lblexp = Label(frm_exp, text='Cam. exp. [us]:')
        lblexp.pack(side='left', padx=3)

        self.inpexpv = IntVar()
        self.inpexpv.set(100000)
        inpexp = Entry(frm_exp, textvariable=self.inpexpv, width=8)
        inpexp.pack(side='left', padx=3)

        
        btnexp = Button(frm_exp, text='Set/Photo', command=self.btnexp_run)
        btnexp.pack(side='left', padx=3)
        if self.skipCam == False : btnexp.config(state='disabled')


        self.btnled = Button(frm_exp, text='LED on', width=4, command=self.btnled_run)
        self.btnled.pack(side='left', padx=3)
                
        # ---------- Load previous camera picture

        frm_img = Frame(self.root) 
        frm_img.grid(column=1, row=1, padx=5, pady=2)

        if self.skipIr == False :
            btnimg = Button(frm_img, text='Load', command=self.btnimg_run)
            btnimg.pack(side='left', padx=10)
        else:
            btnir = Button(frm_img, text='Get IR', command=self.btnir_run)
            btnir.pack(side='left', padx=10)
    
        # RUN
        self.root.protocol("WM_DELETE_WINDOW", self.close_event) 
        self.update_gui() # call first time, then loop
        self.root.mainloop()

### Functions ##############################################################################
    # 
    def createRowWithInput(self, labelText, varType, varStart, runFunction, changeFunction):
        self.rowi += 1

        label = Label(self.frame1, text=labelText)
        label.grid(column=0, row=self.rowi, sticky='w')

        var = varType
        var.set(varStart)

        entry = Entry(self.frame1, textvariable=var, width=5)
        entry.grid(column=2, row=self.rowi, sticky='w')

        btn = Button(self.frame1, text='Set', width=4, command=runFunction)
        btn.grid(column=4, row=self.rowi, sticky='w')

        if changeFunction != False:
            chk = Checkbutton(self.frame1, text='0 s', width=6, anchor='w', background='grey', variable=var, command=changeFunction)
            chk.grid(column=5, row=self.rowi, sticky='w')
            chk.config(state='disabled')
            return var, entry, btn, chk
        else:
            return var, entry, btn

# Plot
    def btnstart_run(self) :
        if self.start == False :
            logging.info('Start time\n')
            self.time_start = time.time_ns()
            self.start = True
            self.btnstart.config(background='lime', text='Stop')
            """
            self.fname = time.strftime("%Y%m%d-%H%M%S")
            self.fdatanamestr = "datafile_{:s}.txt".format(self.fname)
            
            with open(self.fdatanamestr, "a") as fileDAT:
                fileDAT.write('Time[s] RecipeTime[s] T_TC_1[C] T_TC_2[C] T_PT_1[C] T_air[C] H_air[%] Weight[g] Energy[kWh] I_5V[mA] self.pid_out[%] PID_Inp[C] self.pid_set[C] PID_P[ms] PID_I[ms] PID_D[ms] z[mm] Mot_Lin[mm/min] Mot_Rot[rpm] Mot_Fan[%]\n')
            """
            self.reset_plots()
            
            self.chkctrt.config(state='normal')
            #self.chkctrp.config(state='normal') # Only needed to change powercycle directly. 
            self.chkmotl.config(state='normal')
            self.chkmotr.config(state='normal')
            self.chkmotf.config(state='normal')
            self.chkal.config(state='normal')
            
        else :
            logging.info('Stop time\n')
            self.start = False
            self.tt = 0
            self.btnstart.config(background='lightgrey', text='Start')
            
            self.chkctrtv.set(False);  self.chkctrt_change();  self.chkctrt.config(state='disabled')
            #self.chkctrpv.set(False);  self.chkctrp_change();  self.chkctrp.config(state='disabled') # Only needed to change powercycle directly. 
            self.chkmotlv.set(False);  self.chkmotl_change();  self.chkmotl.config(state='disabled')
            self.chkmotrv.set(False);  self.chkmotr_change();  self.chkmotr.config(state='disabled')
            self.chkmotfv.set(False);  self.chkmotf_change();  self.chkmotf.config(state='disabled')
            self.chkalv.set(False);    self.chkal_change();    self.chkal.config(state='disabled')  

    # Display cursor coordinates for both y axes
    def make_format(self):
        def format_coord(x, y):
            display_coord = self.axDAT2.transData.transform((x,y))
            inv = self.axDAT.transData.inverted()
            ax_coord = inv.transform(display_coord)
            coords = [ax_coord, (x, y)]
            return ('Left: {:<20}    Right: {:<}'.format(*['({:.1f}, {:.2f})'.format(x, y) for x,y in coords]))
        return format_coord

    def func(self, label):
        index = self.labels.index(label)
        self.figDATi[index].set_visible(not self.figDATi[index].get_visible())
        # Add and show new points, but no autoscale
        self.figDAT.canvas.draw_idle()
        self.figDAT.canvas.flush_events()
        # set_autoscale(True)

    def set_autoscale(self, auto) :
            self.axDAT.autoscale(enable=auto, axis='both', tight=None) 
            self.axDAT.relim(visible_only=auto)
            self.axDAT2.autoscale(enable=auto, axis='both', tight=None)
            self.axDAT2.relim(visible_only=auto)
            self.toolbar.update() # Reset home state to current state
            if auto == True :
                self.axDAT.autoscale_view()
                self.axDAT2.autoscale_view()
                self.figDAT.canvas.draw_idle()
                self.figDAT.canvas.flush_events()

    def reset_plots(self) :
        for i in range(len(self.plot_params)):
            self.plot_list[i].clear()
        for i in range(len(self.figDATi)):
            self.pl = self.figDATi[i]
            self.pl.set_data(self.plot_list[self.plot_xaxis], self.plot_list[self.plot_ylist[i]])
        self.figDAT.canvas.draw_idle()


    def btnauto_run(self):
        self.set_autoscale(True)
        logging.info("autoscale")

# Sensors
    def rbsel_change(self) :
        self.link.setInputSensor(self.rbselv.get())
        self.pid_sel = self.rbselv.get()
        logging.info('Switch PID Input: pid_sel = '+str(self.pid_sel)+'\n')

    def chksel_change(self) :
        if self.chkselv.get() == True :
            self.rbselpt1.config(state='normal')
            self.rbseltc1.config(state='normal')
            self.rbseltc2.config(state='normal')
        else :
            self.rbselpt1.config(state='disabled')
            self.rbseltc1.config(state='disabled')
            self.rbseltc2.config(state='disabled')

    def btnwei_run(self):
        self.link.setTare(True)
        logging.info('Tare'+'\n')

    def btnpow_run(self):
        self.link.setPowerReset(True)
        logging.info('Reset: kwh_val = '+str(self.kwh_val)+'\n')


# Heating/PID
    def rbctr_change(self) :
        self.link.setPidMode(self.rbctrv.get())
        self.pid_mode = self.rbctrv.get()

        if self.pid_mode == 0 :
            if self.chkctrpv.get() == False : self.inpctrp.config(state='normal')
            if self.chkctrpv.get() == False : self.btnctrp.config(state='normal')
            self.inpctrt.config(state='readonly')
            self.btnctrt.config(state='disabled')
        else :
            self.inpctrp.config(state='readonly')
            self.btnctrp.config(state='disabled')
            if self.chkctrtv.get() == False : self.inpctrt.config(state='normal')
            if self.chkctrtv.get() == False : self.btnctrt.config(state='normal')            
        if self.chkctrtv.get() == False and self.chkctrpv.get() == False : 
            logging.info('Heating control: self.pid_mode = '+str(self.pid_mode)+'\n')

    def btnctrt_run(self):
        if self.inpctrtv.get() >= self.pid_set_min and self.inpctrtv.get() <= self.pid_set_max :        
            self.pid_set = self.inpctrtv.get()
            self.link.setTargetTemp(self.pid_set)
            self.inpctrt.config(background='white')
            self.inpctrt.config(readonlybackground='lightgrey')
        else :
            self.inpctrt.config(background='tomato')
            self.inpctrt.config(readonlybackground='coral')
        if self.chkctrtv.get() == False: logging.info('Set: pid_set = '+str(self.pid_set)+'\n')

    def chkctrt_change(self) :
        pass
        """if self.chkctrtv.get() == True :
            self.inpctrt.config(state='readonly')
            self.btnctrt.config(state='disabled')
            self.rbctr0.config(state='disabled')
            self.rbctr1.config(state='disabled')
            self.chkctrt.config(background='lime')
            tt_startctrt = self.tt
            self.rec.set_sp(self.tt)
            if len(self.rec.sptime2)>0 : self.figDATi[15].set_data(self.rec.sptime2, self.rec.spvalu2)
            logging.info('Start recipe: '+'tt_startctrt = '+str(tt_startctrt)+'\n')
        else :
            rbctr_change() 
            if self.chkctrpv.get() == False : self.rbctr0.config(state='normal')
            if self.chkctrpv.get() == False : self.rbctr1.config(state='normal')
            self.chkctrt.config(background='grey', text='0 s')
            logging.info('Stop recipe: ctrt'+'\n')"""


    def btnctrp_run(self):
        self.val_ms = self.pid_out_period * self.inpctrpv.get() / 100 # % to ms
        if self.val_ms >= 0 and self.val_ms <= self.pid_out_max:
            self.pid_out_man = self.val_ms
            self.link.setPidOutMan(self.pid_out_man)   
            self.inpctrp.config(background='white')
            self.inpctrp.config(readonlybackground='lightgrey')
        else :
            self.inpctrp.config(background='tomato')
            self.inpctrp.config(readonlybackground='coral')           
        if self.chkctrpv.get() == False : logging.info('Set: self.pid_out_man = '+str(self.pid_out_man)+'\n')

    def chkctrp_change(self):
        pass
        """if self.chkctrpv.get() == True :
            self.inpctrp.config(state='readonly')
            self.btnctrp.config(state='disabled')
            self.rbctr0.config(state='disabled')
            self.rbctr1.config(state='disabled')
            self.chkctrp.config(background='lime')
            self.tt_startctrp = self.tt
            self.rec.set_pp(self.tt)
            if len(self.rec.pptime2)>0 : self.figDATi[16].set_data(self.rec.pptime2, self.rec.ppvalu2)
            logging.info('Start recipe: '+'tt_startctrp = '+str(self.tt_startctrp)+'\n')
        else :
            self.rbctr_change() 
            if self.chkctrtv.get() == False : self.rbctr0.config(state='normal')
            if self.chkctrtv.get() == False : self.rbctr1.config(state='normal')
            self.chkctrp.config(background='grey', text='0 s')  
            logging.info('Stop recipe: ctrp'+'\n')"""

# Motors
    # LinSpeed
    def btnmotl_run(self):      
        self.lin_val = self.inpmotlv.get()
        if self.lin_val >= self.lin_val_min and self.lin_val <= self.lin_val_max :
            self.link.setLinSpeed(self.lin_val)
            self.inpmotl.config(background='white')
            self.inpmotl.config(readonlybackground='lightgrey')

            if self.lin_val == 0 :
                self.inpmotz.config(state='normal')
                self.btnmotz.config(state='normal')
            else :
                self.inpmotz.config(state='readonly')
                self.btnmotz.config(state='disabled')
        else:
            self.inpmotl.config(background='tomato')
            self.inpmotl.config(readonlybackground='coral') 
        if self.chkmotlv.get() == False : logging.info('Set: self.lin_val = '+str(self.lin_val)+'\n')

    # linPos
    def btnmotz_run(self):     
        self.lin_z = self.inpmotzv.get()
        if self.lin_z >= self.lin_z_min and self.lin_z <= self.lin_z_max :
            self.link.setPos(self.lin_z)
            self.inpmotz.config(background='white')
            self.inpmotz.config(readonlybackground='lightgrey')
            logging.info('Set: self.lin_z = '+str(self.lin_z)+'\n')
        else:
            self.inpmotz.config(background='tomato')
            self.inpmotz.config(readonlybackground='coral') 

    def chkmotl_change(self):
        pass
        """
        global tt_startmotl
        # global self.tt
        if self.chkmotlv.get() == True :
            self.inpmotl.config(state='readonly')
            self.btnmotl.config(state='disabled')
            self.chkmotl.config(background='lime')
            tt_startmotl = self.tt
            self.rec.set_ml(self.tt)
            if len(self.rec.mltime2)>0 : self.figDATi[17].set_data(self.rec.mltime2, self.rec.mlvalu2)
            logging.info('Start recipe: '+'tt_startmotl = '+str(tt_startmotl)+'\n')
        else :
            self.inpmotl.config(state='normal')
            self.btnmotl.config(state='normal')
            self.chkmotl.config(background='grey', text='0 s')
            logging.info('Stop recipe: motl'+'\n')
        """
    # RotMotor
    def btnmotr_run(self):
        if abs(self.inpmotrv.get()) >= self.rot_val_min and abs(self.inpmotrv.get()) <= self.rot_val_max :        
            self.rot_val = self.inpmotrv.get()
            self.link.setRotSpeed(self.rot_val)
            self.inpmotr.config(background='white')
            self.inpmotr.config(readonlybackground='lightgrey')
        else :
            self.inpmotr.config(background='tomato')
            self.inpmotr.config(readonlybackground='coral')
        if self.chkmotrv.get() == False : logging.info('Set: rot_val = '+str(self.rot_val)+'\n')
        
    def chkmotr_change(self):
        pass
        """global tt_startmotr
        # global self.tt
        if self.chkmotrv.get() == True :
            self.inpmotr.config(state='readonly')
            self.btnmotr.config(state='disabled')
            self.chkmotr.config(background='lime')
            tt_startmotr = self.tt
            self.rec.set_mr(self.tt)
            if len(self.rec.mrtime2)>0 : self.figDATi[18].set_data(self.rec.mrtime2, self.rec.mrvalu2)
            logging.info('Start recipe: '+'tt_startmotr = '+str(tt_startmotr)+'\n')
        else :
            self.inpmotr.config(state='normal')
            self.btnmotr.config(state='normal')  
            self.chkmotr.config(background='grey', text='0 s')
            logging.info('Stop recipe: motr'+'\n')
    self.chkmotr = Checkbutton(self.frame1, text='0 s', width=6, anchor='w', background='grey', variable=self.chkmotrv, command=chkmotr_change)
    self.chkmotr.grid(column=5, row=self.rowi, sticky='w')
    self.chkmotr.config(state='disabled')"""

    # Fan
    def btnmotf_run(self):
        if abs(self.inpmotfv.get()) >= self.fan_val_min and abs(self.inpmotfv.get()) <= self.fan_val_max :        
            self.fan_val = self.inpmotfv.get()
            self.link.setFanSpeed(self.fan_val)
            self.inpmotf.config(background='white')
            self.inpmotf.config(readonlybackground='lightgrey')
        else :
            self.inpmotf.config(background='tomato')
            self.inpmotf.config(readonlybackground='coral')
        if self.chkmotfv.get() == False : logging.info('Set: fan_val = '+str(self.fan_val)+'\n')
        
    def chkmotf_change(self) :
        pass
        """global tt_startmotf
        # global self.tt
        if self.chkmotfv.get() == True :
            self.inpmotf.config(state='readonly')
            self.btnmotf.config(state='disabled')
            self.chkmotf.config(background='lime')
            tt_startmotf = self.tt
            self.rec.set_mf(self.tt)
            if len(self.rec.mftime2)>0 : self.figDATi[19].set_data(self.rec.mftime2, self.rec.mfvalu2)
            logging.info('Start recipe: '+'tt_startmotf = '+str(tt_startmotf)+'\n')
        else :
            self.inpmotf.config(state='normal')
            self.btnmotf.config(state='normal') 
            self.chkmotf.config(background='grey', text='0 s')
            logging.info('Stop recipe: motf'+'\n')
    self.chkmotf = Checkbutton(self.frame1, text='0 s', width=6, anchor='w', background='grey', variable=self.chkmotfv, command=chkmotf_change)
    self.chkmotf.grid(column=5, row=self.rowi, sticky='w')
    self.chkmotf.config(state='disabled')"""

#Devices
    # LED
    def btnled_run(self):
        if  self.led_on == False :
            self.led_on = True
            self.link.setToggleLED(True)
            logging.info('LED On'+'\n')
            self.btnled.config(background='lime', text='LED off')
        else :
            self.led_on = False
            self.link.setToggleLED(True)
            logging.info( 'LED Off' + '\n' )
            self.btnled.config(background='lightgrey', text='LED on')

    # ALARM
    def btnal_run(self):
        if self.inpalv.get()>0 and self.planalarm == False :
            self.link.setAlarmIn(self.inpalv.get())
            self.planalarm = True
            self.inpal.config(state='readonly')
            logging.info('Set alarm'+'\n')
            self.btnal.config(background='lime', text='Reset')
        else :
            self.link.setToggleBuzzer(True)
            self.planalarm = False
            #self.time_startalarmtimer = 0
            #self.time_startalarm = 0
            #self.ttalarm = 0
            #self.sound_on = False
            self.inpal.config(state='normal')
            logging.info('Reset alarm'+'\n')
            self.btnal.config(background='lightgrey', text='Set')
    
    def chkal_change(self) :
        if self.chkalv.get() == True :
            self.inpal.config(state='readonly')
            self.btnal.config(state='disabled')
            self.chkal.config(background='lime')
            self.tt_startal = self.tt
            #self.rec.set_al(self.tt)
            logging.info('Start recipe: '+'tt_startal = '+str(self.tt_startal)+'\n')
        else :
            self.inpal.config(state='normal')
            self.btnal.config(state='normal') 
            self.chkal.config(background='grey', text='0 s')
            logging.info('Stop recipe: al'+'\n')

# Cameras
    # same as btnimg_run for leagcy reasons
    def btnexp_run(self):
        self.btnimg_run()

    def btnimg_run(self):
        self.link.setExp(self.inpexpv.get())
        self.link.setTakePicVis(True)
        logging.info('Get Vis'+'\n')
        
        # Show Pic
        try :
            time.sleep(2)
            imgimg = ImageTk.PhotoImage(Image.open('latestVis.png'))#.resize((400,300), Image.LANCZOS))
            #self.panel = Label(self.root, image = imgimg)
            self.cnv_cam.create_image(400, 300, image=imgimg, anchor='se') # x, y
            logging.info(f'New picture set')
        except Exception as e:
            logging.error(f'Error in setting Picture\n{e}')
    # IR
    def btnir_run(self):
        self.link.setTakePicIr(True)
        logging.info('Get IR'+'\n')
        
        # Show Pic
        try :
            time.sleep(2)
            imgimg = ImageTk.PhotoImage(Image.open('latestIr.jpg').resize((400,300), Image.LANCZOS))
            self.cnv_img.create_image(400, 300, image=imgimg, anchor='se') # x, y
            logging.info(f'New picture set')
        except Exception as e:
            logging.error(f'Error in setting Picture\n{e}')

# Update Gui
    def update_gui(self):
        now = time.time_ns()

        # --- Update sensor data in GUI
        try:
            tempData = self.link.getGuiData()
            self.guiData = dict(tempData)
            self.lblttv.config(text   = str(round(self.guiData.get("tt") ,1)))
            self.lblpt1v.config(text  = str(round(self.guiData.get("pt1"),1)))
            self.lbltc1v.config(text  = str(round(self.guiData.get("tc1"),1)))
            self.lbltc2v.config(text  = str(round(self.guiData.get("tc2"),1)))
            self.lblshttv.config(text = str(round(self.guiData.get("env"),1)))
            self.lblshthv.config(text = str(round(self.guiData.get("hum"),1)))        
            self.lblpowv.config(text  = str(round(self.guiData.get("kwh"),2)))
            self.lblinav.config(text  = str(round(self.guiData.get("current"),2)))
            self.lblweiv.config(text  = str(round(self.guiData.get("weight"),1)))
            self.inpalv.set(str(self.guiData.get("alarmIn")))
            #self.inpal.config(text    = 
            
            if self.lin_val != 0:
                self.inpmotzv.set(round(self.guiData.get("linPos"),1))
        except Exception as e:
            logging.error(f"Updating Gui with new Data not possoblie\n{e}")
        
        
        if self.lin_z < self.lin_z_min or self.lin_z > self.lin_z_max :
            self.inpmotlv.set(0)
            self.btnmotl_run()
            self.inpmotz.config(background='tomato')
            self.inpmotz.config(readonlybackground='coral')
        else :
            self.inpmotz.config(background='white')
            self.inpmotz.config(readonlybackground='lightgrey')
            
        # Alarm countdown:
        #if self.planalarm == True:
            
                
        
        # --- Plot data
        serdata = []
        for entry in self.guiData:
            serdata.append(self.guiData.get(entry))
            
        serdata = serdata[:-1]
        
        for i in range(len(serdata)):
            if self.plot_params[i][6] == True : # Skip recipe plots
                self.plot_list[i].append(float(serdata[i])*self.plot_params[i][3])
        
        if self.start == True :
            for i in range(len(self.figDATi)):
                self.pl = self.figDATi[i]
                # print(self.pl.get_linestyle())
                if self.pl.get_linestyle() != ':' : # Skip recipe plots
                    self.pl.set_data(self.plot_list[self.plot_xaxis], self.plot_list[self.plot_ylist[i]])
            
            # TODO: If recipe is running, add a vertical line for current time
            
            # No autoscale here. Use the button
            self.figDAT.canvas.draw_idle()
            # self.figDAT.canvas.flush_events()
        
    
        now2 = time.time_ns() - now
        logging.debug('GUI update time [ms] = ' + str(now2/1000000) )
        # 1 ms without plot, 400 ms with plot & autoscale
        
        if self.stop_threads == False :
            self.root.after(self.sampletime, self.update_gui)

# Close
    def close_event(self):
        self.link.setClosingEvent(True)
        time.sleep(1)
        self.link.setClosingEventInternal(True)
        self.stop_threads = True
        logging.info("Program closing")
        time.sleep(1)
        exit()
    

### Main ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###
fname = time.strftime("%Y%m%d-%H%M%S")
flognamestr = "./data/logfile_{:s}.txt".format(fname)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    #format="%(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(flognamestr, 'w+'),
    ]
)

logging.info('Starting at ' + time.strftime("%y-%m-%d-%H:%M:%S") + '\n')

Gui()
