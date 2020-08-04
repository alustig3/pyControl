from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
import re

# Custom Variable dialog
class Sequence_Variables_dialog(QtGui.QDialog):
    # Dialog for setting and getting task variables.
    def __init__(self, parent, board):
        super(QtGui.QDialog, self).__init__(parent)
        self.setWindowTitle('Set variables')
        self.layout = QtGui.QVBoxLayout(self)
        self.setWindowTitle('Sequence Variable Setter')
        self.variables_grid = Sequence_grid(self, board)
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
                            self.variables_grid.sequence_gui.update_battery_status(int(data_chunks[2]))
                        elif msg_type == 'DP':
                            left_pwr,right_pwr = data_chunks[2].split('-')
                            if self.variables_grid.sequence_gui.diode_power_left.spn.value() != int(left_pwr) or self.variables_grid.sequence_gui.diode_power_right.spn.value() != int(right_pwr):
                                self.diode_was_different = True
                                QtCore.QTimer.singleShot(500, self.variables_grid.sequence_gui.set_diode_powers)
                            else:
                                if self.diode_was_different:
                                    QtCore.QTimer.singleShot(500, self.variables_grid.sequence_gui.update_task_diode_powers)
                                    self.diode_was_different = False
                        elif msg_type == 'Wave':
                            start_delay,on_time,off_time,train_dur,ramp_dur = data_chunks[2].split('-')
                            if self.variables_grid.sequence_gui.pulse_train_radio.isChecked():
                                if self.variables_grid.sequence_gui.start_delay.mills_str() != start_delay or self.variables_grid.sequence_gui.on_time.mills_str() != on_time or  self.variables_grid.sequence_gui.off_time.mills_str() != off_time or  self.variables_grid.sequence_gui.train_dur.mills_str() != train_dur or ramp_dur != '0': 
                                    QtCore.QTimer.singleShot(2500, self.variables_grid.sequence_gui.send_waveform_parameters)
                            else:
                                if self.variables_grid.sequence_gui.start_delay.mills_str() != start_delay or self.variables_grid.sequence_gui.on_time.mills_str() != on_time or off_time != '0' or train_dur != '0' or self.variables_grid.sequence_gui.ramp_dur.mills_str() != ramp_dur: 
                                    QtCore.QTimer.singleShot(2500, self.variables_grid.sequence_gui.send_waveform_parameters)
                    except:
                        print("bad chunk {}".format(data_chunks))

class Sequence_grid(QtGui.QWidget):
    # Grid of variables to set/get, displayed within scroll area of dialog.
    def __init__(self, parent, board):
        super(QtGui.QWidget, self).__init__(parent)
        variables = board.sm_info['variables']
        self.grid_layout = QtGui.QGridLayout()
        initial_variables_dict = {v_name:v_value_str for (v_name, v_value_str) in sorted(variables.items())}
        self.sequence_gui = Sequence_GUI(self,self.grid_layout, board,initial_variables_dict)
        self.setLayout(self.grid_layout)

class Sequence_GUI(QtGui.QWidget):
   # For setting and getting a single variable.
    def __init__(self, parent, grid_layout, board,init_vars): # Should split into seperate init and provide info.
        super(QtGui.QWidget, self).__init__(parent) 
        self.board = board

        center = QtCore.Qt.AlignCenter

        ##############  Sequence Scheduler ##############
        self.sequence_group = QtGui.QGroupBox('Bout Variables')
        self.sequence_layout = QtGui.QGridLayout()
        # create widgets
        self.reward_array = sequence_text_var(init_vars,'<b>Sequence Array</b>','sequence_array_text',text_width=150)
        self.bout_mean = spin_var(init_vars,'<b>Bout distribution µ</b>', 1,500,1,'','bout_mean')
        self.bout_sd = spin_var(init_vars,'<b>Bout distribution σ</b>', 1,500,1,'','bout_sd')
        self.next_bout = spin_var(init_vars,'<b>Trials until new bout</b>', 1,500,1,'','trials_until_change')
        # place widgets
        for i,var in enumerate([self.reward_array,self.bout_mean,self.bout_sd,self.next_bout]):
            var.setBoard(board)
            var.add_to_grid(self.sequence_layout,i)
        self.sequence_group.setLayout(self.sequence_layout)

        ############## Reward Variables ##############
        self.reward_group = QtGui.QGroupBox('Reward Variables')
        self.reward_layout = QtGui.QGridLayout()
        # create widgets
        # self.reward_seq = text_var(init_vars,'<b>Reward Sequence</b>','reward_seq')
        self.reward_vol = spin_var(init_vars,'💧<b>Reward Volume</b>', 1,500,25,' µL','reward_volume')
        self.correct_rate = spin_var(init_vars,'✅<b>Correct Reward Rate</b>',0,1,.05,'','correct_reward_rate')
        self.background_rate = spin_var(init_vars,'🎲<b>Background Reward Rate</b>',0,1,.05,'','background_reward_rate')
        # place widgets
        for i,var in enumerate([self.reward_vol,self.correct_rate,self.background_rate]):
            var.setBoard(board)
            var.add_to_grid(self.reward_layout,i)
        self.reward_group.setLayout(self.reward_layout)

        ############## Center Variables ##############
        self.center_group = QtGui.QGroupBox('Center Variables')
        self.center_layout = QtGui.QGridLayout()
        
        self.center_hold_label = QtGui.QLabel('<b>Center Hold</b>')
        self.center_hold_label.setAlignment(QtCore.Qt.AlignRight)

        center_constant = eval(init_vars['center_hold_constant'])
        self.constant_center_radio = QtGui.QRadioButton('Constant')
        self.ramp_center_radio = QtGui.QRadioButton('Ramp Up')
        self.constant_center_radio.setChecked(center_constant)
        self.ramp_center_radio.setChecked(not center_constant)

        self.center_layout.addWidget(self.center_hold_label,0,0)
        self.center_layout.addWidget(self.constant_center_radio,0,1)
        self.center_layout.addWidget(self.ramp_center_radio,0,2,1,2)

        # create widgets
        self.forgive_window = spin_var(init_vars,'<b>Forgive Window</b>',1,1000,1,' ms','time_forgive')
        self.center_delay = spin_var(init_vars,'<b>Duration</b>',0,10000,100,' ms','time_hold_center')
        self.hold_start = spin_var(init_vars,'<b>Start</b>',1,5000,10,' ms','center_hold_start')
        self.hold_increment = spin_var(init_vars,'<b>Increment</b>',1,500,1,' ms','center_hold_increment')
        self.hold_max = spin_var(init_vars,'<b>Max</b>',1,10000,10,' ms','center_hold_max')
        # place widgets
        for i,var in enumerate([self.center_delay,self.hold_start,self.hold_increment,self.hold_max,self.forgive_window]):
            var.setBoard(board)
            var.add_to_grid(self.center_layout,i+1)

        self.center_group.setLayout(self.center_layout)
        self.show_center_options()
        
        ############## Side Variables ##############
        self.side_group = QtGui.QGroupBox('Side Variables')
        self.side_layout = QtGui.QGridLayout()


        self.side_delay_label = QtGui.QLabel('<b>Side Delay</b>')
        self.side_delay_label.setAlignment(QtCore.Qt.AlignRight)

        side_constant = eval(init_vars['side_delay_constant'])
        self.constant_side_radio = QtGui.QRadioButton('Constant')
        self.ramp_side_radio = QtGui.QRadioButton('Ramp Up')
        self.constant_side_radio.setChecked(side_constant)
        self.ramp_side_radio.setChecked(not side_constant)

        self.side_layout.addWidget(self.side_delay_label,0,0)
        self.side_layout.addWidget(self.constant_side_radio,0,1)
        self.side_layout.addWidget(self.ramp_side_radio,0,2,1,2)
        # create widgets
        self.blink_delay = spin_var(init_vars,'<b>Blink Delay</b>',50,200,10,' ms','time_blink')
        self.side_delay = spin_var(init_vars,'<b>Duration</b>',0,10000,100,' ms','time_side_delay')
        self.side_start = spin_var(init_vars,'<b>Start</b>',1,5000,10,' ms','side_delay_start')
        self.side_increment = spin_var(init_vars,'<b>Increment</b>',1,500,1,' ms','side_delay_increment')
        self.side_max = spin_var(init_vars,'<b>Max</b>',1,10000,10,' ms','side_delay_max')
        # place widgets
        for i,var in enumerate([self.side_delay,self.side_start,self.side_increment,self.side_max,self.blink_delay]):
            var.setBoard(board)
            var.add_to_grid(self.side_layout,i+1)
        self.side_group.setLayout(self.side_layout)
        self.show_side_options()

        ###### Place groups into layout ############
        grid_layout.addWidget(self.sequence_group,0,0,1,3)
        grid_layout.addWidget(self.reward_group,1,0,1,3)
        grid_layout.addWidget(self.center_group,2,0,1,2)
        grid_layout.addWidget(self.side_group,3,0,1,1)
        grid_layout.setColumnStretch(9,1)
        grid_layout.setRowStretch(10,1)

        self.constant_center_radio.clicked.connect(self.update_center)
        self.ramp_center_radio.clicked.connect(self.update_center)
        self.constant_side_radio.clicked.connect(self.update_side)
        self.ramp_side_radio.clicked.connect(self.update_side)

    def update_center(self):
        self.show_center_options()
        if self.board.framework_running: # Value returned later.
            self.board.set_variable('center_hold_constant',self.constant_center_radio.isChecked())

    def show_center_options(self):
        self.center_delay.setEnabled(self.constant_center_radio.isChecked())
        self.hold_start.setEnabled(not self.constant_center_radio.isChecked())
        self.hold_increment.setEnabled(not self.constant_center_radio.isChecked())
        self.hold_max.setEnabled(not self.constant_center_radio.isChecked())

    def update_side(self):
        self.show_side_options()
        if self.board.framework_running: # Value returned later.
            self.board.set_variable('side_delay_constant',self.constant_side_radio.isChecked())

    def show_side_options(self):
        self.side_delay.setEnabled(self.constant_side_radio.isChecked())
        self.side_start.setEnabled(not self.constant_side_radio.isChecked())
        self.side_increment.setEnabled(not self.constant_side_radio.isChecked())
        self.side_max.setEnabled(not self.constant_side_radio.isChecked())
class spin_var():
    def __init__(self,init_var_dict,label,min,max,step,suffix,varname=''):
        center = QtCore.Qt.AlignCenter
        Vcenter = QtCore.Qt.AlignVCenter
        right = QtCore.Qt.AlignRight
        button_width = 65
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
        self.get_btn.setMaximumWidth(button_width)
        self.get_btn.setAutoDefault(False)
        self.get_btn.clicked.connect(self.get)

        self.set_btn = QtGui.QPushButton('Set')
        self.set_btn.setMinimumWidth(button_width)
        self.set_btn.setMaximumWidth(button_width)
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

    def setVisible(self,makeVisible):
        self.label.setVisible(makeVisible)
        self.spn.setVisible(makeVisible)
        self.get_btn.setVisible(makeVisible)
        self.set_btn.setVisible(makeVisible)

class text_var():
    def __init__(self,init_var_dict,label,varname='',text_width=80):
        center = QtCore.Qt.AlignCenter
        Vcenter = QtCore.Qt.AlignVCenter
        right = QtCore.Qt.AlignRight
        button_width = 65
        self.label = QtGui.QLabel(label)
        self.label.setAlignment(right|Vcenter)
        # self.label.setToolTip(helpText)
        self.varname = varname

        self.line_edit = QtGui.QLineEdit()
        self.line_edit.setAlignment(center)
        self.line_edit.setMinimumWidth(text_width)
        self.line_edit.setMaximumWidth(text_width)
        self.line_edit.setText(eval(init_var_dict[varname]))

        self.get_btn = QtGui.QPushButton('Get')
        self.get_btn.setMinimumWidth(button_width)
        self.get_btn.setMaximumWidth(button_width)
        self.get_btn.setAutoDefault(False)
        self.get_btn.clicked.connect(self.get)

        self.set_btn = QtGui.QPushButton('Set')
        self.set_btn.setMinimumWidth(button_width)
        self.set_btn.setMaximumWidth(button_width)
        self.set_btn.setAutoDefault(False)
        self.set_btn.clicked.connect(self.set)

    def add_to_grid(self,grid,row):
        grid.addWidget(self.label,row,0)
        grid.addWidget(self.line_edit,row,1)
        grid.addWidget(self.get_btn,row,2)
        grid.addWidget(self.set_btn,row,3)

    def setEnabled(self,doEnable):
        self.label.setEnabled(doEnable)
        self.line_edit.setEnabled(doEnable)
        self.get_btn.setEnabled(doEnable)
        self.set_btn.setEnabled(doEnable)

    def setBoard(self,board):
        self.board = board

    def get(self):
        if self.board.framework_running: # Value returned later.
            self.board.get_variable(self.varname)
            QtCore.QTimer.singleShot(200, self.reload)
        else: # Value returned immediately.
            self.line_edit.setText(self.board.get_variable(self.varname))

    def set(self):
        if self.board.framework_running: # Value returned later.
            self.board.set_variable(self.varname,self.line_edit.text().upper())
            QtCore.QTimer.singleShot(200, self.reload)
        else: # Value returned immediately.
            self.line_edit.setText(self.board.get_variable(self.varname))
    
    def reload(self):
        '''Reload value from sm_info.  sm_info is updated when variables are output
        during framework run due to get/set.'''
        self.line_edit.setText(str(self.board.sm_info['variables'][self.varname]))

class sequence_text_var(text_var):
    def set(self):
        if self.board.framework_running: # Value returned later.
            # can't be blank/
            # only lrLR-
            good_letters = re.compile('[^lrLR-]')
            single_dashes = re.compile('[-]{2,}') # single dashes only
            new_sequence_string = self.line_edit.text()
            if good_letters.search(new_sequence_string) == None:
                if single_dashes.search(new_sequence_string):
                    msg = QtGui.QMessageBox()
                    msg.setIcon(QtGui.QMessageBox.Warning)
                    msg.setText("Invalid Input")
                    msg.setInformativeText("There is more than 1 \"-\" somehwere")
                    msg.setWindowTitle("Input Error")
                    msg.exec()
                else:
                    self.board.set_variable(self.varname,self.line_edit.text().upper())
                    QtCore.QTimer.singleShot(200, self.reload)
            else:
                msg = QtGui.QMessageBox()
                msg.setIcon(QtGui.QMessageBox.Warning)
                msg.setText("Invalid Input")
                msg.setInformativeText('Sequences can only be made up of letters \"L\" and \"R\" and should be separated by a single \"-\"')
                msg.setWindowTitle("Input Error")
                msg.exec()
        else: # Value returned immediately.
            self.line_edit.setText(self.board.get_variable(self.varname))