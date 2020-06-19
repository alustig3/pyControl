import time
import numpy as np
from datetime import timedelta
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtWidgets
from PyQt5.QtCore import Qt

from config.gui_settings import event_history_len, state_history_len, analog_history_dur, markov_history_len,markov_plot_window
from gui.utility import detachableTabWidget

# ----------------------------------------------------------------------------------------
# Task_plot 
# ----------------------------------------------------------------------------------------

class Task_plot(QtGui.QWidget):
    ''' Widget for plotting the states, events and analog inputs output by a state machine.'''

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        # Create widgets

        self.choice_plot = Choice_plot(self, data_len=markov_history_len)
        self.states_plot = States_plot(self, data_len=state_history_len)
        self.events_plot = Events_plot(self, data_len=event_history_len)
        self.analog_plot = Analog_plot(self, data_dur=analog_history_dur)
        self.run_clock   = Run_clock(self.states_plot.axis)

        self.choice_update_checkbox = QtWidgets.QCheckBox('Keep last {} trials in view'.format(markov_plot_window))
        self.choice_update_checkbox.setChecked(True)
        self.choice_update_checkbox.setEnabled(False)
        self.choice_update_checkbox.clicked.connect(self.choice_plot.toggle_update)

        self.zoom_fit_btn = QtGui.QPushButton('Past 10 minutes')
        self.zoom_medium_btn = QtGui.QPushButton('Past 90 seconds')
        self.zoom_close_btn = QtGui.QPushButton('Past 15 Seconds')
        self.zoom_fit_btn.clicked.connect(self.fit_zoom)
        self.zoom_medium_btn.clicked.connect(self.medium_zoom)
        self.zoom_close_btn.clicked.connect(self.close_zoom)

        # Setup plots
        self.pause_button = QtGui.QPushButton('Pause plots')
        self.pause_button.setEnabled(False)
        self.pause_button.setCheckable(True)
        self.events_plot.axis.setXLink(self.states_plot.axis)
        self.analog_plot.axis.setXLink(self.states_plot.axis)
        self.analog_plot.axis.setVisible(False)
        self.choice_plot.axis.setVisible(False)
        self.choice_update_checkbox.setVisible(False)

        # create layout
        self.vertical_layout = QtGui.QVBoxLayout()
        self.vertical_layout.addWidget(self.choice_plot.axis,1)
        self.vertical_layout.addWidget(self.states_plot.axis,1)
        self.vertical_layout.addWidget(self.events_plot.axis,1)
        self.vertical_layout.addWidget(self.analog_plot.axis,1)
        self.vertical_layout = QtGui.QGridLayout()
        self.vertical_layout.addWidget(self.choice_plot.axis,0,0,1,3)
        self.vertical_layout.addWidget(self.choice_update_checkbox,1,0,1,3,Qt.AlignCenter)
        self.vertical_layout.addWidget(self.states_plot.axis,2,0,1,3)
        self.vertical_layout.addWidget(self.events_plot.axis,3,0,1,3)
        self.vertical_layout.addWidget(self.analog_plot.axis,4,0,1,3)
        self.vertical_layout.addWidget(self.pause_button,5,0,1,3,Qt.AlignCenter)
        
        # x-axis range buttons
        self.vertical_layout.addWidget(self.zoom_fit_btn,6,0,1,1)
        self.vertical_layout.addWidget(self.zoom_medium_btn,6,1,1,1)
        self.vertical_layout.addWidget(self.zoom_close_btn,6,2,1,1)
        self.setLayout(self.vertical_layout)

    def set_state_machine(self, sm_info):
        # Initialise plots with state machine information.
        self.choice_plot.set_state_machine(sm_info)
        self.states_plot.set_state_machine(sm_info)
        self.events_plot.set_state_machine(sm_info)
        self.analog_plot.set_state_machine(sm_info)

        if sm_info['analog_inputs']:
            self.analog_plot.axis.setVisible(True)
            self.events_plot.axis.getAxis('bottom').setLabel('')
        else:
            self.analog_plot.axis.setVisible(False)
            self.events_plot.axis.getAxis('bottom').setLabel('Time (seconds)')

        if self.choice_plot.is_markov_task:
            self.choice_plot.axis.setVisible(True)
            self.choice_update_checkbox.setVisible(True)
        else:
            self.choice_plot.axis.setVisible(False)
            self.choice_update_checkbox.setVisible(False)

    def run_start(self, recording):
        self.pause_button.setChecked(False)
        self.pause_button.setEnabled(True)
        self.choice_update_checkbox.setChecked(True)
        self.choice_update_checkbox.setEnabled(True)
        self.start_time = time.time()
        self.choice_plot.run_start()
        self.states_plot.run_start()
        self.events_plot.run_start()
        self.analog_plot.run_start()
        if recording:
            self.run_clock.recording()

    def run_stop(self):
        self.pause_button.setEnabled(False)
        self.run_clock.run_stop()

    def process_data(self, new_data):
        '''Store new data from board.'''
        self.choice_plot.process_data(new_data)
        self.states_plot.process_data(new_data)
        self.events_plot.process_data(new_data)
        self.analog_plot.process_data(new_data)

    def update(self):
        '''Update plots.'''
        if not self.pause_button.isChecked():
            run_time = time.time() - self.start_time
            self.states_plot.update(run_time)
            self.events_plot.update(run_time)
            self.analog_plot.update(run_time)
            self.run_clock.update(run_time)

    # functions for quickly changing x-axis ranges
    def fit_zoom(self):
        try:
            run_time = time.time() - self.start_time
            self.states_plot.axis.setRange(xRange=[-600*1.02, 0], padding=0)
        except:
            self.states_plot.axis.setRange(xRange=[-15*1.02, 0], padding=0)
    def medium_zoom(self):
        self.states_plot.axis.setRange(xRange=[-90*1.02, 0], padding=0)
    def close_zoom(self):
        self.states_plot.axis.setRange(xRange=[-15*1.02, 0], padding=0)   

# States_plot --------------------------------------------------------

class States_plot():

    def __init__(self, parent=None, data_len=100):
        self.data_len = data_len
        self.axis = pg.PlotWidget(title='States')
        self.axis.showAxis('right')
        self.axis.hideAxis('left')
        self.axis.setRange(xRange=[-10.2, 0], padding=0)
        self.axis.setMouseEnabled(x=True,y=False)
        self.axis.showGrid(x=True,alpha=0.75)
        self.axis.setLimits(xMax=0)

    def set_state_machine(self, sm_info):
        self.state_IDs = list(sm_info['states'].values())
        self.axis.clear()
        max_len = max([len(n) for n in list(sm_info['states'])+list(sm_info['events'])])
        self.axis.getAxis('right').setTicks([[(i, n) for (n, i) in sm_info['states'].items()]])
        self.axis.getAxis('right').setWidth(5*max_len)
        self.axis.setYRange(min(self.state_IDs), max(self.state_IDs), padding=0.1)
        self.n_colours = len(sm_info['states'])+len(sm_info['events'])
        self.plots = {ID: self.axis.plot(pen=pg.mkPen(pg.intColor(ID, self.n_colours), width=3))
                      for ID in self.state_IDs}

    def run_start(self):
        self.data = np.zeros([self.data_len*2, 2], int)
        for plot in self.plots.values():
            plot.clear()
        self.cs = self.state_IDs[0]
        self.updated_states = []

    def process_data(self, new_data):
        '''Store new data from board'''
        new_states = [nd for nd in new_data if nd[0] == 'D' and nd[2] in self.state_IDs]
        self.updated_states = [self.cs]
        if new_states:
            n_new =len(new_states)
            self.data = np.roll(self.data, -2*n_new, axis=0)
            for i, ns in enumerate(new_states): # Update data array.
                timestamp, ID = ns[1:]
                self.updated_states.append(ID)
                j = 2*(-n_new+i)  # Index of state entry in self.data
                self.data[j-1:,0] = timestamp
                self.data[j:  ,1] = ID  
            self.cs = ID

    def update(self, run_time):
        '''Update plots.'''
        self.data[-1,0] = 1000*run_time # Update exit time of current state to current time.
        for us in self.updated_states: # Set data for updated state plots.
            state_data = self.data[self.data[:,1]==us,:]
            timestamps, ID = (state_data[:,0]/1000, state_data[:,1])
            self.plots[us].setData(x=timestamps, y=ID, connect='pairs')
        # Shift all state plots.
        for plot in self.plots.values():
            plot.setPos(-run_time, 0)

# Events_plot--------------------------------------------------------

class Events_plot():

    def __init__(self, parent=None, data_len=100):
        self.axis = pg.PlotWidget(title='Events')
        self.axis.showAxis('right')
        self.axis.hideAxis('left')
        self.axis.setRange(xRange=[-10.2, 0], padding=0)
        self.axis.setMouseEnabled(x=True,y=False)
        self.axis.showGrid(x=True,alpha=0.75)
        self.axis.setLimits(xMax=0)
        self.data_len = data_len

    def set_state_machine(self, sm_info):
        self.event_IDs = list(sm_info['events'].values())
        self.axis.clear()
        if not self.event_IDs: return # State machine can have no events.
        max_len = max([len(n) for n in list(sm_info['states'])+list(sm_info['events'])])
        self.axis.getAxis('right').setTicks([[(i, n) for (n, i) in sm_info['events'].items()]])
        self.axis.getAxis('right').setWidth(5*max_len)
        self.axis.setYRange(min(self.event_IDs), max(self.event_IDs), padding=0.1)
        self.n_colours = len(sm_info['states'])+len(sm_info['events'])
        self.plot = self.axis.plot(pen=None, symbol='o', symbolSize=6, symbolPen=None)

    def run_start(self):
        if not self.event_IDs: return # State machine can have no events.
        self.plot.clear()
        self.data = np.zeros([self.data_len, 2])

    def process_data(self, new_data):
        '''Store new data from board.'''
        if not self.event_IDs: return # State machine can have no events.
        new_events = [nd for nd in new_data if nd[0] == 'D' and nd[2] in self.event_IDs]
        if new_events:
            n_new = len(new_events)
            self.data = np.roll(self.data, -n_new, axis=0)
            for i, ne in enumerate(new_events):
                timestamp, ID = ne[1:]
                self.data[-n_new+i,0] = timestamp / 1000
                self.data[-n_new+i,1] = ID

    def update(self, run_time):
        '''Update plots'''
        # Should not need to setData but setPos does not cause redraw otherwise.
        if not self.event_IDs: return
        self.plot.setData(self.data, symbolBrush=[pg.intColor(ID) for ID in self.data[:,1]])
        self.plot.setPos(-run_time, 0)

# Choice Plot --------------------------------------------------------

class Choice_plot():

    def __init__(self, parent=None, data_len=100):
        self.axis = pg.PlotWidget(title='Markov Plot')
        self.axis.hideAxis('right')
        self.axis.showAxis('left')
        self.axis.setRange(xRange=[-1,markov_plot_window+5], padding=0)
        self.axis.setMouseEnabled(x=True,y=False)
        self.axis.showGrid(x=True,alpha=0.75)
        self.axis.setLimits(xMin=-1)
        reward_color = pg.mkColor(0,255,0) # green
        no_reward_color = pg.mkColor(0,0,0) # black
        reject_color = pg.mkColor(255,255,0) # yellow
        error_color = pg.mkColor(255,0,0) # red
        self.my_colors = (reward_color,no_reward_color,error_color,reject_color)
        self.my_symbols = ('o','+','s') # circle, plus, square
        self.is_markov_task = False
        self.do_update = True
        self.data_len = data_len
        self.left_prob  = None
        self.right_prob = None
        self.next_block_start = 0
        self.last_arrow = None
        
    def set_state_machine(self,sm_info):
        self.is_markov_task = sm_info['name'] == 'markov'
        if not self.is_markov_task: return
        self.axis.clear()
        self.axis.getAxis('bottom').setLabel('Trial')
        self.axis.getAxis('right').setWidth(75)
        self.axis.getAxis('left').setWidth(50)

        self.axis.setYRange(5,6.5, padding=0.1)
        self.plot = self.axis.plot(pen=None, symbol='o', symbolSize=6, symbolPen=None)
        self.plot2 = self.axis.plot(pen=pg.mkPen(color = (255,154,0,), width=2))
        self.plot3 = self.axis.plot(pen=pg.mkPen(color  = (0,222,255,128), width=2))

    def run_start(self):
        if not self.is_markov_task: return
        self.plot.clear()
        self.plot2.clear()
        self.plot3.clear()
        self.axis.removeItem(self.last_arrow)
        self.trial_num = -1
        self.axis.setTitle('Choices and Outcomes')
        self.axis.getAxis('left').setTicks([[(6.5,'Left'),(6.25,'Right'),(5.0,'0'),(5.2,'.2'),(5.4,'.4'),(5.6,'.6'),(5.8,'.8'),(6,'1')]])
        self.data = np.zeros([self.data_len,6])

    def process_data(self, new_data):
        if not self.is_markov_task: return
        '''Store new data from board.'''
        outcome_msgs = [nd for nd in new_data if nd[0] == 'P' and nd[2].split(',')[0]=='rslt'] 
        new_block_msgs = [nd for nd in new_data if nd[0] == 'P' and nd[2].split(',')[0]=='NB']
        probability_var_update_msgs = [nd for nd in new_data if nd[0] == 'V' and nd[2].split(' ')[0].find('reward_probability')>-1] 
        newBlock_var_update_msgs = [nd for nd in new_data if nd[0] == 'V' and nd[2].split(' ')[0].find('trial_new_block')>-1] 
        if outcome_msgs:
            n_new = len(outcome_msgs)
            self.data = np.roll(self.data, -n_new, axis=0)
            for i, ne in enumerate(outcome_msgs):
                trial_num_string,left_prob_string,right_prob_string,choice,outcome,isLaserTrial= ne[-1].split(',')[1:]
                self.left_prob = float(left_prob_string)
                self.right_prob = float(right_prob_string)
                self.trial_num = int(trial_num_string)
                if choice == 'L': 
                    side = 6.5
                elif choice == 'R':
                    side = 6.25
                else:
                    side = 0
                if outcome == 'Y': # was rewarded
                    color = 0
                    symbol = 0
                elif outcome == 'N': # was not rewarded
                    color = 1
                    symbol = 0
                elif outcome == 'X': # error
                    color = 2
                    symbol = 2
                elif outcome == 'R': # rejected tone
                    color = 3
                    symbol = 1
            
                self.data[-n_new+i,0] = self.trial_num
                self.data[-n_new+i,1] = side
                self.data[-n_new+i,2] = color
                self.data[-n_new+i,3] = symbol
                self.data[-n_new+i,4] = self.left_prob + 5
                self.data[-n_new+i,5] = self.right_prob + 5
                if self.trial_num < 2:
                    self.data[:,4] = self.left_prob + 5
                    self.data[:,5] = self.right_prob + 5
 
            self.plot.setData(self.data[:,0],self.data[:,1],symbol=[self.my_symbols[int(ID)] for ID in self.data[:,3]],symbolSize=10,symbolPen=[pg.mkPen('y') if symbol == 1 else pg.mkPen('w') for symbol in self.data[:,3]],symbolBrush=[self.my_colors[int(ID)] for ID in self.data[:,2]])
            self.plot2.setData(self.data[:,0],self.data[:,4])
            self.plot3.setData(self.data[:,0],self.data[:,5])
            self.update_title()
            if self.do_update:
                self.axis.setRange(xRange=[self.trial_num-markov_plot_window,self.trial_num+5], padding=0)
        if new_block_msgs:
            for nb_msg in new_block_msgs:
                content = nb_msg[2].split(',')
                self.next_block_start = int(content[2])
                if self.trial_num>0: # remove old marker and place marker where probability change actually occured. This takes into account instances where the new bout was scheduled for a trial that already occured.
                    self.axis.removeItem(self.last_arrow)
                    self.update_block_marker(self.trial_num+1)
                self.update_block_marker(self.next_block_start)
                self.update_title()
        if probability_var_update_msgs:
            for prob_update in probability_var_update_msgs:
                content = prob_update[2].split(' ')
                if content[0].find('right') > -1:
                    self.right_prob = content[1]
                elif content[0].find('left') > -1:
                    self.left_prob = content[1]
                self.update_title()
        if newBlock_var_update_msgs:
            for block_start_update in newBlock_var_update_msgs:
                content = block_start_update[2].split(' ')
                self.next_block_start = int(content[1])
                self.update_block_marker(self.next_block_start)
                self.update_title()

    def toggle_update(self):
        self.do_update = not self.do_update
        if self.do_update:
            self.axis.setRange(xRange=[self.trial_num-markov_plot_window,self.trial_num+5], padding=0)

    def update_title(self):
        self.axis.setTitle('<font size="4"><span>Completed {} trials---Current Probabilities: </span><span style="color: #FF9A00;">Left={}</span><span style="color: #00DEFF;"> Right={}</span>---New Block in {} trials (@ trial <span style="color:#FF1FE6;">{}</span></font>)'.format(
            self.trial_num,self.left_prob,self.right_prob,self.next_block_start-self.trial_num,self.next_block_start))

    def update_block_marker(self,xpos):
        self.axis.removeItem(self.last_arrow)
        self.last_arrow = pg.ArrowItem(pos=(xpos,4.85),angle=-90,brush='#FF1FE6',pen='#FF1FE6',headLen=18)
        self.axis.addItem(self.last_arrow)
    
# ------------------------------------------------------------------------------------------
class Analog_plot():

    def __init__(self, parent=None, data_dur=10):
        self.data_dur = data_dur
        self.axis = pg.PlotWidget(title='Analog')
        self.axis.showAxis('right')
        self.axis.hideAxis('left')
        self.axis.setRange(xRange=[-10.2, 0], padding=0)
        self.axis.setMouseEnabled(x=True,y=False)
        self.axis.showGrid(x=True,alpha=0.75)
        self.axis.setLimits(xMax=0)
        self.legend = None 

    def set_state_machine(self, sm_info):
        self.inputs = sm_info['analog_inputs']
        if not self.inputs: return # State machine may not have analog inputs.
        if self.legend:
            self.legend.close()
        self.legend = self.axis.addLegend(offset=(10, 10))
        self.axis.clear()
        self.plots = {ai['ID']: self.axis.plot(name=name, 
                      pen=pg.mkPen(pg.intColor(ai['ID'],len(self.inputs)))) for name, ai in sorted(self.inputs.items())}
        self.axis.getAxis('bottom').setLabel('Time (seconds)')
        max_len = max([len(n) for n in list(sm_info['states'])+list(sm_info['events'])])
        self.axis.getAxis('right').setWidth(5*max_len)
        
    def run_start(self):
        if not self.inputs: return # State machine may not have analog inputs.
        for plot in self.plots.values():
            plot.clear()
        self.data = {ai['ID']: np.zeros([ai['Fs']*self.data_dur, 2])
                     for ai in self.inputs.values()}
        self.updated_inputs = []

    def process_data(self, new_data):
        '''Store new data from board.'''
        if not self.inputs: return # State machine may not have analog inputs.
        new_analog = [nd for nd in new_data if nd[0] == 'A']
        self.updated_inputs = [na[1] for na in new_analog]
        for na in new_analog:
            ID, sampling_rate, timestamp, data_array = na[1:]
            new_len = len(data_array)
            t = timestamp/1000 + np.arange(new_len)/sampling_rate
            self.data[ID] = np.roll(self.data[ID], -new_len, axis=0)
            self.data[ID][-new_len:,:] = np.vstack([t,data_array]).T

    def update(self, run_time):
        '''Update plots.'''
        if not self.inputs: return # State machine may not have analog inputs.
        for ID in self.updated_inputs:
            self.plots[ID].setData(self.data[ID])
        for plot in self.plots.values():
            plot.setPos(-run_time, 0)   

# -----------------------------------------------------

class Run_clock():
    # Class for displaying the run time.

    def __init__(self, axis):
        self.clock_text = pg.TextItem(text='')
        self.clock_text.setFont(QtGui.QFont('arial',11, QtGui.QFont.Bold))
        axis.getViewBox().addItem(self.clock_text, ignoreBounds=True)
        self.clock_text.setParentItem(axis.getViewBox())
        self.clock_text.setPos(10,-5)
        self.recording_text = pg.TextItem(text='', color=(255,0,0))
        self.recording_text.setFont(QtGui.QFont('arial',12,QtGui.QFont.Bold))
        axis.getViewBox().addItem(self.recording_text, ignoreBounds=True)
        self.recording_text.setParentItem(axis.getViewBox())
        self.recording_text.setPos(80,-5)

    def update(self, run_time):
        self.clock_text.setText(str(timedelta(seconds=run_time))[:7])

    def recording(self):
        self.recording_text.setText('Recording')

    def run_stop(self):
        self.clock_text.setText('')
        self.recording_text.setText('')

# --------------------------------------------------------------------------------
# Experiment plotter
# --------------------------------------------------------------------------------

class Experiment_plot(QtGui.QMainWindow):
    '''Window for plotting data during experiment run where each subjects plots
    are displayed in a seperate tab.'''

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)
        self.setWindowTitle('Experiment plot')
        self.setGeometry(720, 30, 700, 800) # Left, top, width, height.       
        self.subject_tabs = QtGui.QTabWidget(self)
        self.setCentralWidget(self.subject_tabs)
        self.subject_plots = []
        self.active_plots = []

    def setup_experiment(self, experiment):
        '''Create task plotters in seperate tabs for each subject.'''
        subject_dict = experiment['subjects']
        subjects = subject_dict.keys()
        setup_subject_pairs = {}
        for subject in subjects:
            setup_subject_pairs[subject_dict[subject]['Setup']] = subject
        # Add plot tabs in order of setup name
        for key in sorted(setup_subject_pairs.keys()):
            self.subject_plots.append(Task_plot(self))
            self.subject_tabs.addTab(self.subject_plots[-1],
                '{} ---- {}'.format(key, setup_subject_pairs[key]))

    def set_state_machine(self, sm_info):
        '''Provide the task plotters with the state machine info.'''
        for subject_plot in self.subject_plots:
            subject_plot.set_state_machine(sm_info)

    def start_experiment(self,rig):
        self.subject_plots[rig].run_start(False)
        self.active_plots.append(rig)

    def close_experiment(self):
        '''Remove and delete all subject plot tabs.'''
        while len(self.subject_plots) > 0:
            subject_plot = self.subject_plots.pop() 
            subject_plot.setParent(None)
            subject_plot.deleteLater()
        self.close()
        
    def update(self):
        '''Update the plots of the active tab.'''
        for i,subject_plot in enumerate(self.subject_plots):
            if not subject_plot.visibleRegion().isEmpty() and i in self.active_plots:
                subject_plot.update()