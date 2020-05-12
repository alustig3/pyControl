from pyqtgraph.Qt import QtGui, QtCore, QtWidgets

# Custom Variable dialog
class Markov_Variables_dialog(QtGui.QDialog):
    # Dialog for setting and getting task variables.
    def __init__(self, parent, board):
        super(QtGui.QDialog, self).__init__(parent)
        self.setWindowTitle('Set variables')
        self.layout = QtGui.QVBoxLayout(self)
        # if board.sm_info['name'] == 'markov':
        self.setWindowTitle('Markov Variable Setter')
        self.variables_grid = Markov_grid(self, board)
        self.layout.addWidget(self.variables_grid)
        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)
        self.diode_was_different=False

    def process_data(self, new_data):
        for data_array in new_data:
            if data_array[0]=='P': # printed miessage
                data_chunks = data_array[2].split(',')
                if data_chunks[0][0]=='[' and data_chunks[0][-1]==']': # is an incoming message from cerebro
                    try:
                        msg_type = data_chunks[1]
                        if msg_type == 'Btry':
                            self.variables_grid.markov_gui.update_battery_status(int(data_chunks[2]))
                        elif msg_type == 'DP':
                            left_pwr,right_pwr = data_chunks[2].split('-')
                            if self.variables_grid.markov_gui.diode_power_left.spn.value() != int(left_pwr) or self.variables_grid.markov_gui.diode_power_right.spn.value() != int(right_pwr):
                                self.diode_was_different = True
                                QtCore.QTimer.singleShot(500, self.variables_grid.markov_gui.set_diode_powers)
                            else:
                                if self.diode_was_different:
                                    QtCore.QTimer.singleShot(500, self.variables_grid.markov_gui.update_task_diode_powers)
                                    self.diode_was_different = False
                        elif msg_type == 'Wave':
                            start_delay,on_time,off_time,train_dur,ramp_dur = data_chunks[2].split('-')
                            if self.variables_grid.markov_gui.pulse_train_radio.isChecked():
                                if self.variables_grid.markov_gui.start_delay.mills_str() != start_delay or self.variables_grid.markov_gui.on_time.mills_str() != on_time or  self.variables_grid.markov_gui.off_time.mills_str() != off_time or  self.variables_grid.markov_gui.train_dur.mills_str() != train_dur or ramp_dur != '0': 
                                    QtCore.QTimer.singleShot(2500, self.variables_grid.markov_gui.send_waveform_parameters)
                            else:
                                if self.variables_grid.markov_gui.start_delay.mills_str() != start_delay or self.variables_grid.markov_gui.on_time.mills_str() != on_time or off_time != '0' or train_dur != '0' or self.variables_grid.markov_gui.ramp_dur.mills_str() != ramp_dur: 
                                    QtCore.QTimer.singleShot(2500, self.variables_grid.markov_gui.send_waveform_parameters)
                    except:
                        print("bad chunk {}".format(data_chunks))

class Markov_grid(QtGui.QWidget):
    # Grid of variables to set/get, displayed within scroll area of dialog.
    def __init__(self, parent, board):
        super(QtGui.QWidget, self).__init__(parent)
        variables = board.sm_info['variables']
        self.grid_layout = QtGui.QGridLayout()
        # if  board.sm_info['name'] == 'markov':
        initial_variables_dict = {v_name:v_value_str for (v_name, v_value_str) in sorted(variables.items())}
        self.markov_gui = Markov_GUI(self,self.grid_layout, board,initial_variables_dict)
        self.setLayout(self.grid_layout)

class Markov_GUI(QtGui.QWidget):
   # For setting and getting a single variable.
    def __init__(self, parent, grid_layout, board,init_vars): # Should split into seperate init and provide info.
        super(QtGui.QWidget, self).__init__(parent) 
        self.board = board

        center = QtCore.Qt.AlignCenter
        ###### Left and Right Group #######
        # create widgets 
        self.left_right_box = QtGui.QGroupBox('Left and Right Variables')
        self.left_right_layout = QtGui.QGridLayout()
        self.left_lbl = QtGui.QLabel('<b>Left</b>')
        self.left_lbl.setAlignment(center)
        self.right_lbl = QtGui.QLabel('<b>Right</b>')
        self.right_lbl.setAlignment(center)
        self.reward_probability = left_right_vars(init_vars,'🎲 <b>Reward Prob</b>',0,1,.1,'','reward_probability')
        self.req_presses = left_right_vars(init_vars,'👇 <b>Presses</b>',1,100,1,'','required_presses')
        self.reward_volume = left_right_vars(init_vars,'💧 <b>Reward Vol</b>',1,500,25,' µL','reward_volume')

        # place widgets in layout
        self.left_right_layout.addWidget(self.left_lbl,0,1)
        self.left_right_layout.addWidget(self.right_lbl,0,2)
        for i,var in enumerate([self.reward_probability, self.req_presses, self.reward_volume]):
            var.setBoard(board)
            row = i+1
            var.add_to_grid(self.left_right_layout,row)
        self.left_right_box.setLayout(self.left_right_layout)
        

        ###### Other Variables Group #######
        # create widgets 
        self.other_box = QtGui.QGroupBox('Other Variables')
        self.other_layout = QtGui.QGridLayout()
        self.speaker_volume = single_var(init_vars,'🔈 <b>Speaker Volume</b>',1,31,1,'','speaker_volume')
        self.error_duration = single_var(init_vars,'❌ <b>Error Duration</b>', .5,120,.5,' s','time_error_freeze_seconds')
        self.tone_duration = single_var(init_vars,'<b>Tone Duration</b>', 1,10,.5,' s','time_tone_duration_seconds')
        self.tone_repeats = single_var(init_vars,'<b>Maximum Repeats</b>',0,20,1,'','max_tone_repeats')
        self.trial_new_block = single_var(init_vars,'<b>New Block on Trial...',0,5000,1,'','trial_new_block')
        self.continuous_tone_lbl = QtGui.QLabel('<b>Continuous Tone</b>')
        self.continuous_tone_lbl.setAlignment(QtCore.Qt.AlignRight)
        self.other_layout.addWidget(self.continuous_tone_lbl,0,0)
        self.tone_checkbox = QtGui.QCheckBox()
        self.tone_checkbox.setChecked(eval(init_vars['continuous_tone']))
        # place widgets
        self.other_layout.addWidget(self.tone_checkbox,0,1)
        self.tone_duration.setEnabled(not eval(init_vars['continuous_tone']))
        for i,var in enumerate([self.tone_duration,self.error_duration,self.tone_repeats,self.trial_new_block,self.speaker_volume]):
            var.setBoard(board)
            var.add_to_grid(self.other_layout,i+1)
        self.other_box.setLayout(self.other_layout)
        self.tone_checkbox.clicked.connect(self.update_tone)

        ###### Laser Group #######
        # create widgets 
        self.laser_group = QtGui.QGroupBox('Laser Variables')
        self.laser_layout = QtGui.QGridLayout()
        self.laser_enabled_lbl = QtGui.QLabel('<b>Laser Enabled</b>')
        self.laser_enabled_lbl.setAlignment(QtCore.Qt.AlignRight)
        self.laser_checkbox = QtGui.QCheckBox()
        withToneChecked,withCollectionChecked = eval(init_vars['laser_with_tone']), eval(init_vars['laser_with_collection'])
        if  withToneChecked or withCollectionChecked:
            laserIsChecked = True
        else:
            laserIsChecked = False
        self.laser_checkbox.setChecked(laserIsChecked)
        self.laser_onset_lbl = QtGui.QLabel('<b>Laser Onset</b>')
        self.laser_onset_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.laser_onset_lbl.setEnabled(laserIsChecked)
        self.with_tone = QtGui.QRadioButton('With Tone')
        self.with_tone.setEnabled(laserIsChecked)
        self.with_tone.setChecked(withToneChecked)
        self.with_collection = QtGui.QRadioButton('With Collection')
        self.with_collection.setEnabled(laserIsChecked)
        self.with_collection.setChecked(withCollectionChecked)
        self.laser_probability = single_var(init_vars,'<b>Laser Probability</b>',0,1,.05,'','laser_probability')
        self.laser_probability.setBoard(board)
        self.laser_probability.setEnabled(laserIsChecked)
        # place widgets
        self.laser_layout.addWidget(self.laser_enabled_lbl,0,0)
        self.laser_layout.addWidget(self.laser_onset_lbl,1,0)
        self.laser_layout.addWidget(self.laser_checkbox,0,1)
        self.laser_layout.addWidget(self.with_tone,1,1)
        self.laser_layout.addWidget(self.with_collection,1,2,1,2)
        self.laser_probability.add_to_grid(self.laser_layout,2)
        self.laser_group.setLayout(self.laser_layout)

        ###### Cerebro Group #######
        # create widgets 
        self.cerebro_group = QtGui.QGroupBox('Cerebro')
        self.cerebro_layout = QtGui.QGridLayout()
        self.cerebro_channel = wave_var(init_vars,'<b>Cerebro Channel</b>',0,120,1,'')
        self.diode_power_left = wave_var(init_vars,'<b>Left Power</b>',0,1023,1,'','diode_power_left')
        self.diode_power_right = wave_var(init_vars,'<b>Right Power</b>',0,1023,1,'','diode_power_right')
        self.cerebro_connect_btn = QtGui.QPushButton('Connect To Cerebro')
        self.cerebro_refresh_btn = QtGui.QPushButton('Refresh')
        self.battery_indicator = QtGui.QProgressBar()
        self.battery_indicator.setRange(0,100)
        self.battery_indicator.setValue(0)
        self.battery_indicator.setFormat("%p%")
        self.single_shot_radio = QtGui.QRadioButton('Single Shot')
        self.pulse_train_radio = QtGui.QRadioButton('Pulse Train')
        self.start_delay = wave_var(init_vars,'<b>Start Delay</b>',0,65.535,0.05,' s', 'start_delay')
        self.on_time = wave_var(init_vars,'<b>On Time</b>',0,65.535,0.05,' s', 'on_time')
        self.off_time = wave_var(init_vars,'<b>Off Time</b>',0,65.535,0.05,' s', 'off_time')
        self.train_dur = wave_var(init_vars,'<b>Train Duration</b>',0,9999.999,0.250,' s', 'train_dur')
        self.ramp_dur = wave_var(init_vars,'<b>Ramp Down</b>',0,65.5,0.1,' s', 'ramp_dur')
        self.send_waveform_btn = QtGui.QPushButton('Send New Waveform Parameters')
        self.test_btn = QtGui.QPushButton('Click=Trigger       Shift+Click=Stop')
        # place widgets
        self.cerebro_channel.add_to_grid(self.cerebro_layout,0)
        self.cerebro_layout.addWidget(self.cerebro_connect_btn,0,2,1,2)
        self.diode_power_left.add_to_grid(self.cerebro_layout,1)
        self.diode_power_right.add_to_grid(self.cerebro_layout,1,2)
        self.cerebro_layout.addWidget(self.cerebro_refresh_btn,2,3)
        self.cerebro_layout.addWidget(self.battery_indicator,2,0,1,3)
        self.cerebro_layout.addWidget(self.single_shot_radio,3,1)
        self.cerebro_layout.addWidget(self.pulse_train_radio,3,2)
        self.start_delay.add_to_grid(self.cerebro_layout,4,1)
        self.on_time.add_to_grid(self.cerebro_layout,5)
        self.off_time.add_to_grid(self.cerebro_layout,5,2)
        self.ramp_dur.add_to_grid(self.cerebro_layout,6,1)
        self.train_dur.add_to_grid(self.cerebro_layout,7,1)
        self.cerebro_layout.addWidget(self.send_waveform_btn,8,1,1,2)
        self.cerebro_layout.addWidget(self.test_btn,9,0,1,4)
        self.cerebro_group.setLayout(self.cerebro_layout)

        is_pulse_train = (eval(init_vars['pulse_train']))
        self.single_shot_radio.setChecked(not is_pulse_train)
        self.pulse_train_radio.setChecked(is_pulse_train)
        if is_pulse_train:
            self.ramp_dur.setVisible(False)
        else:
            self.off_time.setVisible(False)
            self.train_dur.setVisible(False)

        grid_layout.addWidget(self.left_right_box,0,0,1,4)
        grid_layout.addWidget(self.other_box,1,0,1,3)
        grid_layout.addWidget(self.laser_group,2,0,1,2)
        grid_layout.addWidget(self.cerebro_group,3,0)
        grid_layout.setColumnStretch(9,1)
        grid_layout.setRowStretch(10,1)

        self.laser_checkbox.clicked.connect(self.update_laser)
        self.with_tone.clicked.connect(self.update_laser)
        self.with_collection.clicked.connect(self.update_laser)
        self.cerebro_connect_btn.clicked.connect(self.connect_to_cerebro)
        self.cerebro_refresh_btn.clicked.connect(self.get_battery)
        self.single_shot_radio.clicked.connect(self.update_cerebro_input)
        self.pulse_train_radio.clicked.connect(self.update_cerebro_input)
        self.send_waveform_btn.clicked.connect(self.send_waveform_parameters)
        self.test_btn.clicked.connect(self.test_trigger_stop)

    def update_laser(self):
        self.with_collection.setEnabled(self.laser_checkbox.isChecked())
        self.with_tone.setEnabled(self.laser_checkbox.isChecked())
        self.laser_probability.setEnabled(self.laser_checkbox.isChecked())
        self.laser_onset_lbl.setEnabled(self.laser_checkbox.isChecked())
        if self.laser_checkbox.isChecked():
            if self.board.framework_running: # Value returned later.
                self.board.set_variable('laser_with_tone',self.with_tone.isChecked())
                self.board.set_variable('laser_with_collection',self.with_collection.isChecked())
        else:
            if self.board.framework_running:
               self.board.set_variable('laser_with_tone',False)
               self.board.set_variable('laser_with_collection',False) 

    def update_tone(self):
        self.tone_duration.setEnabled(not self.tone_checkbox.isChecked())
        if self.board.framework_running:
            self.board.set_variable('continuous_tone',self.tone_checkbox.isChecked())

    def connect_to_cerebro(self):
        if self.board.framework_running:
            self.board.initialize_cerebro_connection(self.cerebro_channel.spn.value())

    def set_diode_powers(self):
        if self.board.framework_running:
            self.board.set_diode_powers(self.diode_power_left.spn.value(),self.diode_power_right.spn.value())

    def update_task_diode_powers(self):
        if self.board.framework_running:
            self.board.set_variable('diode_power_left',self.diode_power_left.spn.value())
            self.board.set_variable('diode_power_right',self.diode_power_right.spn.value())

    def get_battery(self):
        if self.board.framework_running:
            self.board.get_cerebro_battery()

    def test_trigger_stop(self):
        if self.board.framework_running:
            modifiers = QtWidgets.QApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.ShiftModifier:
                self.board.test_base_stop()
            else:
                self.board.test_base_trigger()

    def update_cerebro_input(self):
        if self.pulse_train_radio.isChecked():
            self.off_time.setVisible(True)
            self.train_dur.setVisible(True)
            self.ramp_dur.setVisible(False)
        else:
            self.off_time.setVisible(False)
            self.train_dur.setVisible(False)
            self.ramp_dur.setVisible(True)

    def send_waveform_parameters(self):
        if self.board.framework_running: # Value returned later.
            if self.pulse_train_radio.isChecked():
                self.board.set_waveform(self.start_delay.mills_str(),
                                        self.on_time.mills_str(),
                                        self.off_time.mills_str(),
                                        self.train_dur.mills_str(),
                                        '0' 
                                        )
            else:
                self.board.set_waveform(self.start_delay.mills_str(),
                                        self.on_time.mills_str(),
                                        '0',
                                        '0',
                                        self.ramp_dur.mills_str()
                                        )

            self.board.set_variable('pulse_train',self.pulse_train_radio.isChecked())
            self.board.set_variable('start_delay',self.start_delay.spn.value())
            self.board.set_variable('on_time',self.on_time.spn.value())
            self.board.set_variable('off_time',self.off_time.spn.value())
            self.board.set_variable('train_dur',self.train_dur.spn.value())
            self.board.set_variable('ramp_dur',self.ramp_dur.spn.value())

    def update_battery_status(self,battery_percentage):
        self.battery_indicator.setValue(battery_percentage)

class left_right_vars():
    def __init__(self,initial_vars_dict,label,min,max,step,suffix,varname=''):
        center = QtCore.Qt.AlignCenter
        Vcenter = QtCore.Qt.AlignVCenter
        right = QtCore.Qt.AlignRight
        button_width = 35
        spin_width = 70
        self.label = QtGui.QLabel(label)
        self.label.setAlignment(right|Vcenter)
        self.leftVar = varname+'_left'
        self.rightVar = varname+'_right'
        
        if isinstance(min,float) or isinstance(max,float) or isinstance(step,float):
            self.left_spn, self.right_spn = QtGui.QDoubleSpinBox(),QtGui.QDoubleSpinBox()
        else:
            self.left_spn, self.right_spn = QtGui.QSpinBox(), QtGui.QSpinBox()

        for spn in [self.left_spn,self.right_spn]:
            spn.setRange(min,max)
            spn.setSingleStep(step)
            spn.setSuffix(suffix)
            spn.setAlignment(center)

        self.left_spn.setValue(eval(initial_vars_dict[self.leftVar]))
        self.right_spn.setValue(eval(initial_vars_dict[self.rightVar]))
        
        self.left_spn.setMaximumSize(100,100)
        self.right_spn.setMaximumSize(100,100)

        self.get_btn = QtGui.QPushButton('Get')
        self.get_btn.setMinimumWidth(button_width)
        self.get_btn.setAutoDefault(False)
        self.get_btn.clicked.connect(self.get)

        self.set_btn = QtGui.QPushButton('Set')
        self.set_btn.setMinimumWidth(button_width)
        self.set_btn.setAutoDefault(False)
        self.set_btn.clicked.connect(self.set)
        
        # self.left_spn.editingFinished.connect(self.set)
        # self.right_spn.editingFinished.connect(self.set)
    
    def setBoard(self,board):
        self.board = board

    def add_to_grid(self,grid,row):
        grid.addWidget(self.label,row,0)
        grid.addWidget(self.left_spn,row,1)
        grid.addWidget(self.right_spn,row,2)
        grid.addWidget(self.get_btn,row,3)
        grid.addWidget(self.set_btn,row,4)

    def get(self):
        if self.board.framework_running: # Value returned later.
            self.board.get_variable(self.leftVar)
            self.board.get_variable(self.rightVar)
            QtCore.QTimer.singleShot(200, self.reload)
        else: # Value returned immediately.
            self.left_spn.setValue(self.board.get_variable(self.leftVar))
            self.right_spn.setValue(self.board.get_variable(self.rightVar))

    def set(self):
        if self.board.framework_running: # Value returned later.
            self.board.set_variable(self.leftVar,round(self.left_spn.value(),2))
            self.board.set_variable(self.rightVar,round(self.right_spn.value(),2))
            QtCore.QTimer.singleShot(200, self.reload)
        else: # Value returned immediately.
            self.left_spn.setValue(self.board.get_variable(self.leftVar))
            self.right_spn.setValue(self.board.get_variable(self.rightVar))

    def reload(self):
        '''Reload value from sm_info.  sm_info is updated when variables are output
        during framework run due to get/set.'''
        self.left_spn.setValue(eval(str(self.board.sm_info['variables'][self.leftVar])))
        self.right_spn.setValue(eval(str(self.board.sm_info['variables'][self.rightVar])))


class single_var():
    def __init__(self,init_var_dict,label,min,max,step,suffix,varname=''):
        center = QtCore.Qt.AlignCenter
        Vcenter = QtCore.Qt.AlignVCenter
        right = QtCore.Qt.AlignRight
        button_width = 35
        spin_width = 80
        self.label = QtGui.QLabel(label)
        self.label.setAlignment(right|Vcenter)
        # self.label.setToolTip(helpText)
        self.varname = varname

        if isinstance(min,float) or isinstance(max,float) or isinstance(step,float):
            self.spn = QtGui.QDoubleSpinBox()
        else:
            self.spn = QtGui.QSpinBox() 

        self.spn.setRange(min,max)
        self.spn.setValue(eval(init_var_dict[varname]))
        self.spn.setSingleStep(step)
        self.spn.setSuffix(suffix)
        self.spn.setAlignment(center)
        self.spn.setMaximumWidth(spin_width)

        self.get_btn = QtGui.QPushButton('Get')
        self.get_btn.setMinimumWidth(button_width)
        self.get_btn.setAutoDefault(False)
        self.get_btn.clicked.connect(self.get)

        self.set_btn = QtGui.QPushButton('Set')
        self.set_btn.setMinimumWidth(button_width)
        self.set_btn.setAutoDefault(False)
        self.set_btn.clicked.connect(self.set)

    def add_to_grid(self,grid,row):
        grid.addWidget(self.label,row,0)
        grid.addWidget(self.spn,row,1)
        grid.addWidget(self.get_btn,row,2)
        grid.addWidget(self.set_btn,row,3)

    def setEnabled(self,doEnable):
        self.label.setEnabled(doEnable)
        self.spn.setEnabled(doEnable)
        self.get_btn.setEnabled(doEnable)
        self.set_btn.setEnabled(doEnable)

    def setBoard(self,board):
        self.board = board

    def get(self):
        if self.board.framework_running: # Value returned later.
            self.board.get_variable(self.varname)
            QtCore.QTimer.singleShot(200, self.reload)
        else: # Value returned immediately.
            self.spn.setValue(self.board.get_variable(self.varname))

    def set(self):
        if self.board.framework_running: # Value returned later.
            self.board.set_variable(self.varname,round(self.spn.value(),2))
            QtCore.QTimer.singleShot(200, self.reload)
        else: # Value returned immediately.
            self.spn.setValue(self.board.get_variable(self.varname))
    
    def reload(self):
        '''Reload value from sm_info.  sm_info is updated when variables are output
        during framework run due to get/set.'''
        self.spn.setValue(eval(str(self.board.sm_info['variables'][self.varname])))

class wave_var():
    def __init__(self,init_var_dict,label,min,max,step,suffix,varname=''):
        center = QtCore.Qt.AlignCenter
        Vcenter = QtCore.Qt.AlignVCenter
        right = QtCore.Qt.AlignRight
        button_width = 35
        spin_width = 80
        self.label = QtGui.QLabel(label)
        self.label.setAlignment(right|Vcenter)
        # self.label.setToolTip(helpText)
        self.varname = varname

        if isinstance(min,float) or isinstance(max,float) or isinstance(step,float):
            self.spn = QtGui.QDoubleSpinBox()
        else:
            self.spn = QtGui.QSpinBox() 

        self.spn.setRange(min,max)
        if varname != '':
            self.spn.setValue(eval(init_var_dict[varname]))
        self.spn.setSingleStep(step)
        self.spn.setSuffix(suffix)
        self.spn.setAlignment(center)
        self.spn.setMaximumWidth(spin_width)

    def mills_str(self):
            return str(1000*round(self.spn.value(),3))[:-2]

    def add_to_grid(self,grid,row,col_offset=0):
        grid.addWidget(self.label,row,0+col_offset)
        grid.addWidget(self.spn,row,1+col_offset)

    def setVisible(self,makeVisible):
        self.label.setVisible(makeVisible)
        self.spn.setVisible(makeVisible)

    def setBoard(self,board):
        self.board = board

    def get(self):
        if self.board.framework_running: # Value returned later.
            self.board.get_variable(self.varname)
            QtCore.QTimer.singleShot(200, self.reload)
        else: # Value returned immediately.
            self.spn.setValue(self.board.get_variable(self.varname))

    def set(self):
        if self.board.framework_running: # Value returned later.
            self.board.set_variable(self.varname,round(self.spn.value(),2))
            QtCore.QTimer.singleShot(200, self.reload)
        else: # Value returned immediately.
            self.spn.setValue(self.board.get_variable(self.varname))
    
    def reload(self):
        '''Reload value from sm_info.  sm_info is updated when variables are output
        during framework run due to get/set.'''
        self.spn.setValue(eval(str(self.board.sm_info['variables'][self.varname])))