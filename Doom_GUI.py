"""
Needed:

"""
import numpy as np
import sys
import os
import time
from datetime import datetime, timedelta
import cv2
from collections import deque
from colour import Color
from collections import deque
import json
from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.patches as mpatches

import pyqtgraph as pg

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
import Graphing_Widgets as gw

class MainWindow(qtw.QMainWindow):

    def __init__(self, connection):
        super().__init__()
        self.widget = CentralWidget(connection)
        self.setCentralWidget(self.widget)
        launchcode(self)

class CentralWidget(qtw.QWidget):

    def __init__(self, connection):
        super().__init__()
        self.connection = connection
        self.game_timer = time.time()
        self.master_data_width = 140
        self.fast_mode = False

        self.title_font = qtg.QFont('Trebuchet MS', 30)
        self.metric_font = qtg.QFont('Trebuchet MS', 12)
        self.click_font = qtg.QFont('Trebuchet MS', 20)
        self.metric_font.setItalic(1)
        self.custom_style1 = qtg.QFont('Trebuchet MS', 16)
        self.custom_style2 = qtg.QFont('Trebuchet MS', 12)
        self.custom_style2.setItalic(1)
        self.custom_style3 = qtg.QFont('Trebuchet MS', 16)

        # Load up the graphics and put them in a dictionary.
        bitmap_dir = "Resources/Bitmaps/"
        self.up_pixmap_1 = qtg.QPixmap(bitmap_dir+'1_up.png')
        self.up_pixmap_2 = qtg.QPixmap(bitmap_dir+'2_up.png')
        self.up_pixmap_3 = qtg.QPixmap(bitmap_dir+'3_up.png')
        self.down_pixmap_1 = qtg.QPixmap(bitmap_dir+'1_down.png')
        self.down_pixmap_2 = qtg.QPixmap(bitmap_dir+'2_down.png')
        self.down_pixmap_3 = qtg.QPixmap(bitmap_dir+'3_down.png')
        self.left_pixmap_1 = qtg.QPixmap(bitmap_dir+'1_left.png')
        self.left_pixmap_2 = qtg.QPixmap(bitmap_dir+'2_left.png')
        self.left_pixmap_3 = qtg.QPixmap(bitmap_dir+'3_left.png')
        self.right_pixmap_1 = qtg.QPixmap(bitmap_dir+'1_right.png')
        self.right_pixmap_2 = qtg.QPixmap(bitmap_dir+'2_right.png')
        self.right_pixmap_3 = qtg.QPixmap(bitmap_dir+'3_right.png')
        self.circle_pixmap_1 = qtg.QPixmap(bitmap_dir+'1_circle.png')
        self.circle_pixmap_2 = qtg.QPixmap(bitmap_dir+'2_circle.png')
        self.circle_pixmap_3 = qtg.QPixmap(bitmap_dir+'3_circle.png')
        self.pixmap_dict = {0:self.up_pixmap_1, 1:self.up_pixmap_2,
                            2:self.up_pixmap_3, 3:self.down_pixmap_1,
                            4:self.down_pixmap_2, 5:self.down_pixmap_3,
                            6:self.left_pixmap_1, 7:self.left_pixmap_2,
                            8:self.left_pixmap_3, 9:self.right_pixmap_1,
                            10:self.right_pixmap_2, 11:self.right_pixmap_3,
                            12:self.circle_pixmap_1, 13:self.circle_pixmap_2,
                            14:self.circle_pixmap_3}
        self.click_set = ['null', 'color: rgb(33, 37, 43);',
                          'color: rgb(255,255,255);',
                          'color: rgb(80,167,239);']
        self.action_set = [ # All the moves the agent can make (10x)
                        'MOVE_FORWARD', 'MOVE_BACKWARD', 'MOVE_LEFT',
                        'MOVE_RIGHT', 'TURN_LEFT', 'TURN_RIGHT',
                        'ATTACK', 'SELECT_NEXT_WEAPON', 'USE',
                        'JUMP'
                        ]

        self.metrics_last = [0 for n in range(30)] #initialize empty.

        ## Plot of Total Reward
        self.g_treward_que1 = deque(maxlen=self.master_data_width)
        self.g_treward_que2 = deque(maxlen=self.master_data_width)
        self.g_treward_que3 = deque(maxlen=self.master_data_width)
        self.g_treward_que4 = deque(maxlen=self.master_data_width)
        self.g_treward_lineque = deque(maxlen=self.master_data_width)
        self.g_treward = gw.SmoothPlotWidget(self, plot_layers=2,
                                             graph_label='Total Reward Avg: -',
                                             label_1="Final Reward",
                                             label_2="Avg(25)",
                                             y_min=-5, y_max=1000, left=0.055
                                             )

        ## Plot of Avg Actor & Avg Critic Qmax
        self.g_avg_qmax_que1 = deque(maxlen=self.master_data_width)
        self.g_avg_qmax_que2 = deque(maxlen=self.master_data_width)
        self.g_avg_qmax_que3 = deque(maxlen=self.master_data_width)
        self.g_avg_qmax_que4 = deque(maxlen=self.master_data_width)
        self.g_avg_qmax = gw.SmoothPlotWidget(self, plot_layers=4,
                                        graph_label='Actor vs Critic Avg',
                                        label_1="Agent Avg Qmax",
                                        label_2="Agent Closing Qmax",
                                        label_3="Critic Avg Qmax",
                                        label_4="Critic Closing Qmax",
                                        y_min=-5, y_max=500, left=0.04
                                        )

        ## Plot Failrate of moveset
        self.g_damage_que1 = deque(maxlen=self.master_data_width)
        self.g_damage_que2 = deque(maxlen=self.master_data_width)
        self.g_damage_que3 = deque(maxlen=self.master_data_width)
        self.g_damage_que4 = deque(maxlen=self.master_data_width)
        self.g_damage = gw.SmoothPlotWidget(self, plot_layers=4,
                                      graph_label='Damage Graph',
                                      label_1="DPS In", label_2="DPS Out",
                                      label_3="DPS In Avg(25)", label_4="DPS Out Avg(25)",
                                      y_min=-5, y_max=5, left=0.04
                                      )

        ## Quickplot of the Actionspace
        num_bars = 5
        self.g_action_que1 = deque(maxlen=num_bars)
        self.g_action_que2 = deque(maxlen=num_bars)
        self.g_action_que3 = deque(maxlen=num_bars)
        self.g_action_que4 = deque(maxlen=num_bars)
        self.g_action_que5 = deque(maxlen=num_bars)
        self.g_action = gw.QuickBarWidget(self, num_bars=num_bars)

        ## Quickplot of the Agent vs Critic vs Reward
        self.g_actor_critic_que_1 = deque(maxlen=60)
        self.g_actor_critic_que_2 = deque(maxlen=60)
        self.g_actor_critic_que_3 = deque(maxlen=60)
        self.g_actor_critic = gw.QuickCurveWidget(self, minimum=-50, maximum=250)

        ## Quickplot of the Current Dataset Frame.
        #  Used here as a dummy frame for the active game window.
        self.g_image = gw.QuickImageWidget(self)

        ## Now populate all of the widgets in the main window.
        self.main_layout = qtw.QGridLayout()
        self.setLayout(self.main_layout)

        # for vertical space per row.
        self.main_layout.setRowStretch(1, 2) #row, stretch factor
        self.main_layout.setRowStretch(2, 2) #row, stretch factor
        self.main_layout.setRowStretch(3, 2)

        #(row, column, hight, width)
        self.main_layout.addWidget(self.title_module(),                         0, 0, 1, 18)
        #the image is a frame for the gamewindow
        self.main_layout.addWidget(self.img_module(self.g_image),               1, 0, 2, 5)
        self.main_layout.addWidget(self.action_module(),                        1, 5, 1, 2)
        self.main_layout.addWidget(self.bar_module(self.g_action),              1, 7, 1, 2)
        self.main_layout.addWidget(self.metrics_module(),                       1, 9, 1, 9)
        self.main_layout.addWidget(self.curve_module(self.g_actor_critic),      2, 5, 1, 4)
        self.main_layout.addWidget(self.plot_module(self.g_treward),            2, 9, 1, 9)
        self.main_layout.addWidget(self.plot_module(self.g_avg_qmax),           3, 0, 1, 9)
        self.main_layout.addWidget(self.plot_module(self.g_damage),    3, 9, 1, 9)

        self.main_layout.addWidget(self.new_button("quit_button"),              4, 6, 1, 2)
        self.main_layout.addWidget(self.new_button("fast_button"),              4, 8, 1, 2)
        self.button_click(mode="fast_button")

        self.timer = qtc.QTimer()
        self.timer.setInterval(1)
        self.timer.timeout.connect(self.update_gui)
        self.timer.start()

    # This is the mouse arrows & buttons display
    def action_module(self):
        self.up = qtw.QLabel(self)
        self.up.setPixmap(self.pixmap_dict[0])
        self.up.setAlignment(qtc.Qt.AlignCenter)
        #self.up.resize(up_pixmap.width(), up_pixmap.height()) #resize label to window.
        self.down = qtw.QLabel(self)
        self.down.setPixmap(self.pixmap_dict[3])
        self.down.setAlignment(qtc.Qt.AlignCenter)
        self.left = qtw.QLabel(self)
        self.left.setPixmap(self.pixmap_dict[6])
        self.left.setAlignment(qtc.Qt.AlignRight)
        self.right = qtw.QLabel(self)
        self.right.setPixmap(self.pixmap_dict[9])
        self.right.setAlignment(qtc.Qt.AlignLeft)
        self.circle = qtw.QLabel(self)
        self.circle.setPixmap(self.pixmap_dict[12])
        self.circle.setAlignment(qtc.Qt.AlignCenter)

        action_grid = qtw.QGridLayout()
        action_grid.addWidget(self.up,      0, 1, 1, 1)
        action_grid.addWidget(self.down,    2, 1, 1, 1)
        action_grid.addWidget(self.left,    1, 0, 1, 1)
        action_grid.addWidget(self.right,   1, 2, 1, 1)
        action_grid.addWidget(self.circle,  1, 1, 1, 1)

        action_groupbox = qtw.QGroupBox()
        action_groupbox.setLayout(action_grid)
        action_groupbox.setFont(self.custom_style2)
        action_groupbox.setStyleSheet(box_style)
        return action_groupbox

    # Tracks training metrics
    def metrics_module(self):
        self.last_move = qtw.QLabel(f' Action: -', self)
        self.last_move.setFont(self.metric_font)
        self.last_move.setStyleSheet(metric_style)
        self.reward_scan = qtw.QLabel(f' Reward Scan: -/-', self)
        self.reward_scan.setFont(self.metric_font)
        self.reward_scan.setStyleSheet(metric_style)
        self.critic_value = qtw.QLabel(f' Actor/Critic Value: -/-', self)
        self.critic_value.setFont(self.metric_font)
        self.critic_value.setStyleSheet(metric_style)
        self.fail_rate = qtw.QLabel(f' Fail Rate: -', self)
        self.fail_rate.setFont(self.metric_font)
        self.fail_rate.setStyleSheet(metric_style)
        self.lap_metrics = qtw.QLabel(f' Lap: -/-', self)
        self.lap_metrics.setFont(self.metric_font)
        self.lap_metrics.setStyleSheet(metric_style)
        self.last_reset = qtw.QLabel(f' Subcycle/Seconds: -/-', self)
        self.last_reset.setFont(self.metric_font)
        self.last_reset.setStyleSheet(metric_style)

        self.current_cycle = qtw.QLabel(f' Current Cycle: -', self)
        self.current_cycle.setFont(self.metric_font)
        self.current_cycle.setStyleSheet(metric_style)
        self.cycles_per_second = qtw.QLabel(f' Cycles/Second: -', self)
        self.cycles_per_second.setFont(self.metric_font)
        self.cycles_per_second.setStyleSheet(metric_style)
        self.avg_qmax = qtw.QLabel(f' Actor/Critic Avg Qmax: -/-', self)
        self.avg_qmax.setFont(self.metric_font)
        self.avg_qmax.setStyleSheet(metric_style)
        self.dps = qtw.QLabel(f' Time Trend: -', self)
        self.dps.setFont(self.metric_font)
        self.dps.setStyleSheet(metric_style)
        self.ai_time = qtw.QLabel(f' Time: -/-', self)
        self.ai_time.setFont(self.metric_font)
        self.ai_time.setStyleSheet(metric_style)
        self.deviance = qtw.QLabel(f' Reward/Second: -/-', self)
        self.deviance.setFont(self.metric_font)
        self.deviance.setStyleSheet(metric_style)
        

        metrics_grid = qtw.QGridLayout()
        metrics_grid.addWidget(self.last_move,          1, 0, 1, 1)
        metrics_grid.addWidget(self.reward_scan,        2, 0, 1, 2)
        metrics_grid.addWidget(self.critic_value,       3, 0, 1, 1)
        metrics_grid.addWidget(self.fail_rate,          4, 0, 1, 1)
        metrics_grid.addWidget(self.lap_metrics,        5, 0, 1, 1)
        metrics_grid.addWidget(self.last_reset,         6, 0, 1, 1)

        metrics_grid.addWidget(self.current_cycle,      1, 1, 1, 1)
        metrics_grid.addWidget(self.cycles_per_second,  2, 1, 1, 1)
        metrics_grid.addWidget(self.avg_qmax,           3, 1, 1, 1)
        metrics_grid.addWidget(self.dps,  4, 1, 1, 1)
        metrics_grid.addWidget(self.ai_time,            5, 1, 1, 1)
        metrics_grid.addWidget(self.deviance,           6, 1, 1, 1)

        metrics_groupbox = qtw.QGroupBox()
        metrics_groupbox.setLayout(metrics_grid)
        metrics_groupbox.setFont(self.custom_style2)
        metrics_groupbox.setStyleSheet(box_style)
        return metrics_groupbox

    def evo_module(self):
        self.first_place = qtw.QLabel(f' 1st: -', self)
        self.first_place.setFont(self.metric_font)
        self.first_place.setStyleSheet(metric_style)
        self.second_place = qtw.QLabel(f' 2nd: -', self)
        self.second_place.setFont(self.metric_font)
        self.second_place.setStyleSheet(metric_style)
        self.third_place = qtw.QLabel(f' 3rd: -', self)
        self.third_place.setFont(self.metric_font)
        self.third_place.setStyleSheet(metric_style)
        self.fourth_place = qtw.QLabel(f' 4th: -', self)
        self.fourth_place.setFont(self.metric_font)
        self.fourth_place.setStyleSheet(metric_style)
        self.fifth_place = qtw.QLabel(f' 5th: -', self)
        self.fifth_place.setFont(self.metric_font)
        self.fifth_place.setStyleSheet(metric_style)

        self.loaded_seed = qtw.QLabel(f' Loaded State: -/-', self)
        self.loaded_seed.setFont(self.metric_font)
        self.loaded_seed.setStyleSheet(metric_style)
        self.current_score = qtw.QLabel(f' Current Score: -/-', self)
        self.current_score.setFont(self.metric_font)
        self.current_score.setStyleSheet(metric_style)
        self.cycles_since_save = qtw.QLabel(f' Last Evo Save: -', self)
        self.cycles_since_save.setFont(self.metric_font)
        self.cycles_since_save.setStyleSheet(metric_style)
        self.standard_deviation = qtw.QLabel(f' StDev: -', self)
        self.standard_deviation.setFont(self.metric_font)
        self.standard_deviation.setStyleSheet(metric_style)
        self.finish_cycles_avg = qtw.QLabel(f' Finish Cycles Avg: -', self)
        self.finish_cycles_avg.setFont(self.metric_font)
        self.finish_cycles_avg.setStyleSheet(metric_style)

        evo_grid = qtw.QGridLayout()
        evo_grid.addWidget(self.first_place,        1, 0, 1, 1)
        evo_grid.addWidget(self.second_place,       2, 0, 1, 1)
        evo_grid.addWidget(self.third_place,        3, 0, 1, 1)
        evo_grid.addWidget(self.fourth_place,       4, 0, 1, 1)
        evo_grid.addWidget(self.fifth_place,        5, 0, 1, 1)

        evo_grid.addWidget(self.loaded_seed,        1, 1, 1, 1)
        evo_grid.addWidget(self.current_score,      2, 1, 1, 1)
        evo_grid.addWidget(self.cycles_since_save,  3, 1, 1, 1)
        evo_grid.addWidget(self.standard_deviation, 4, 1, 1, 1)
        evo_grid.addWidget(self.finish_cycles_avg,  5, 1, 1, 1)

        evo_groupbox = qtw.QGroupBox()
        evo_groupbox.setLayout(evo_grid)
        evo_groupbox.setFont(self.custom_style2)
        evo_groupbox.setStyleSheet(box_style)
        return evo_groupbox

    def update_gui(self):
        self.metrics = []
        #begin_time =time.time()
        try:
            if self.connection.poll(timeout=0.1):
                #print('********************Recieved Connection********************')
                while 1:
                    metric = self.connection.recv()
                    self.metrics.append(metric)
                    if metric == -9999:# dummy figure thrown in to singal the end.
                        break

            #Update Metrics:
            action = self.metrics[0]
            reward = self.metrics[1]
            action_space = self.metrics[2]
            total_reward = self.metrics[3]
            subcycle = self.metrics[4]

            iteration = self.metrics[6]
            total_time = self.metrics[7]
            qmax = self.metrics[8]
            reward_polarity = self.metrics[9]

            crit_val = self.metrics[11]
            cycles_per_second = self.metrics[12]
            agent_qmax_avg = self.metrics[13]
            actor_learning_rate = self.metrics[14]
            game_time = self.metrics[15]
            critic_qmax_avg = self.metrics[16]
            race_time_delta = max(round(self.metrics[17], 1), 1)
            mini_batch_size = self.metrics[18]
            
            dmg_list = self.metrics[19] #metrics_last
            dmg_in = dmg_list[0]
            dmg_out = dmg_list[1]
            dps_in = dmg_list[2]
            dps_out = dmg_list[3]
            dps_in_avg = dmg_list[4]
            dps_out_avg = dmg_list[5]

            game_count = self.metrics[20]
            reward_avg = self.metrics[21]

            fail_rate = round(reward_polarity[1]/sum(reward_polarity)*100,2) #[positive count, negative count]
            #fail_rate = 1
            self.subtitlebar.setText(f' Learning Rate: {actor_learning_rate}      Game Batch: {mini_batch_size}')

            self.last_move.setText(f' Action: {self.action_set[action]}')
            self.reward_scan.setText(f' Reward Scan: {reward}/{round(total_reward,2)}')
            self.deviance.setText(f' Available "deviance"') #reward/timeseconds
            self.critic_value.setText(f' Actor/Critic Value: {qmax}/{crit_val}')
            self.last_reset.setText(f' Subcycle/Seconds: {subcycle}/{race_time_delta}')
            self.fail_rate.setText(f' Fail Rate: {fail_rate}%')
            self.current_cycle.setText(f' Current Cycle: {iteration}/{game_count}')
            self.ai_time.setText(f' Time: {str(timedelta(seconds=total_time))}/{str(timedelta(seconds=game_time))}')
            self.lap_metrics.setText(f' Available "lap_metrics"')
            self.dps.setText(f' DPS In/Out: {dps_in}/{dps_out}')
            self.cycles_per_second.setText(f' Cycles/Second: {cycles_per_second}')
            self.avg_qmax.setText(f' Actor/Critic Avg Qmax: {agent_qmax_avg}/{self.metrics_last[16]}')

            if not self.fast_mode:
                self.reward_scan.setStyleSheet(self.color_coder(1, zero=True)) #Color Code reward_scans

                #update per-frame graphs
                action_arr = action_space[0]
                self.g_action_que1.append(action_arr[0])
                self.g_action_que2.append(action_arr[1])
                self.g_action_que3.append(action_arr[2])
                self.g_action_que4.append(action_arr[3])
                self.g_action_que5.append(action_arr[4])
                #blocky, but faster than creating a list container
                self.g_action.add_value(self.g_action_que1,
                                        self.g_action_que2,
                                        self.g_action_que3,
                                        self.g_action_que4,
                                        self.g_action_que5)

                self.g_actor_critic_que_1.append(qmax)
                self.g_actor_critic_que_2.append(crit_val)
                self.g_actor_critic_que_3.append(reward*10)

                self.g_actor_critic.add_value(self.g_actor_critic_que_1, 
                    self.g_actor_critic_que_2, self.g_actor_critic_que_3)
                
                #Actions
                color_set = [1, 1, 1, 1, 1] # All 5 actions start grey, or off state.
                color_set[action] = int(2)
                #print(f'{action}  {color_set[action]}   2')
                self.last_move.setStyleSheet(metric_style)

                #action module color coding. Notice the +/- shifts along pixmap dict selection. 
                up_pixmap = (int(color_set[0]) - 1)
                self.up.setPixmap(self.pixmap_dict[up_pixmap])
                down_pixmap = (int(color_set[2]) + 2)
                self.down.setPixmap(self.pixmap_dict[down_pixmap])
                left_pixmap = (int(color_set[3]) + 5)
                self.left.setPixmap(self.pixmap_dict[left_pixmap])
                right_pixmap = (int(color_set[4]) + 8)
                self.right.setPixmap(self.pixmap_dict[right_pixmap])
                circle_pixmap = (int(color_set[1]) + 11)
                self.circle.setPixmap(self.pixmap_dict[circle_pixmap])

            #Update per-game Graphs
            if ((game_count > self.metrics_last[20])
                and (self.metrics_last[20] > 0)):
                ## Total Reward Update
                self.g_treward_que1.append(self.metrics_last[3]) #Final Reward
                self.g_treward_que2.append(reward_avg) #avg
                graph_treward_label = f'Total Reward Avg: ({reward_avg})'
                self.g_treward.add_value(self.g_treward_que1, input_2=self.g_treward_que2,
                                         title=graph_treward_label)

                ## Qmax/Critic Avg Update
                self.g_avg_qmax_que1.append(self.metrics_last[13]) #qmax avg
                self.g_avg_qmax_que2.append(self.metrics_last[8]) #qmax closing
                self.g_avg_qmax_que3.append(self.metrics_last[16]) #critic avg
                self.g_avg_qmax_que4.append(self.metrics_last[11]) #critic closing
                graph_avg_qmax_label = f'Actor({self.metrics_last[13]}) vs Critic({self.metrics_last[16]}) Avg'
                self.g_avg_qmax.add_value(self.g_avg_qmax_que1, self.g_avg_qmax_que2,
                                                self.g_avg_qmax_que3, self.g_avg_qmax_que4, 
                                                title=graph_avg_qmax_label)
                ## Plot DPS
                dmg_list = self.metrics_last[19]
                dps_in = round(dmg_list[0]/self.metrics_last[17], 1)
                dps_out = round(dmg_list[1]/self.metrics_last[17], 1)
                self.g_damage_que1.append(dps_in)
                self.g_damage_que2.append(dps_out)
                self.g_damage_que3.append(dps_in_avg)
                self.g_damage_que4.append(dps_out_avg)
                self.g_damage.add_value(self.g_damage_que1,
                                        input_2=self.g_damage_que2,
                                        input_3=self.g_damage_que3,
                                        input_4=self.g_damage_que4)

            self.metrics_last = self.metrics
            #print('********************COMPLETED UPDATE GUI********************')
        
        except Exception as e:
            if str(e) != "'int' object has no attribute 'poll'" and str(e) != "list index out of range":
                print("Receive Failure:", e)

    def title_module(self):
        titlebox = qtw.QGroupBox()
        titlebox.setStyleSheet(box_style)
        titlebar = qtw.QLabel(' A2C/PPO Reinforcement Learning Monitor', self)
        titlebar.setFont(self.title_font)
        titlebar.setStyleSheet("color: rgb(255,255,255);border-width : 0px;")
        self.subtitlebar = qtw.QLabel('  v4', self)
        self.subtitlebar.setFont(self.custom_style2)
        self.subtitlebar.setStyleSheet("color: rgb(80,167,239);border-width : 0px;")
        titlegrid = qtw.QGridLayout()
        titlegrid.addWidget(titlebar, 0, 0)
        titlegrid.addWidget(self.subtitlebar, 1, 0)
        titlebox.setLayout(titlegrid)
        return titlebox

    def graph_module(self, graph, label='Graph'):
        graph_grid = qtw.QGridLayout()
        self.q_title = qtw.QLabel(label, self)
        self.q_title.setFont(self.metric_font)
        self.q_title.setStyleSheet(metric_style)
        self.q_title.setAlignment(qtc.Qt.AlignCenter)
        graph_grid.addWidget(self.q_title,0,0)
        graph_grid.addWidget(graph,1,0,5,1)
        graph_groupbox = qtw.QGroupBox()
        graph_groupbox.setLayout(graph_grid)
        graph_groupbox.setFont(self.custom_style2)
        graph_groupbox.setStyleSheet(box_style)
        graph_groupbox.setAlignment(qtc.Qt.AlignCenter)
        return graph_groupbox

    def plot_module(self, plot):
        last_game_groupbox = qtw.QGroupBox()
        last_game_groupbox.setLayout(plot.plot_layout)
        last_game_groupbox.setFont(self.custom_style2)
        last_game_groupbox.setStyleSheet(box_style)
        return last_game_groupbox

    def bar_module(self, plot):
        last_game_groupbox = qtw.QGroupBox()
        last_game_groupbox.setLayout(plot.plot_layout)
        last_game_groupbox.setFont(self.custom_style2)
        last_game_groupbox.setStyleSheet(box_style)
        return last_game_groupbox
    
    def curve_module(self, plot):
        curve_groupbox = qtw.QGroupBox()
        curve_groupbox.setLayout(plot.plot_layout)
        curve_groupbox.setFont(self.custom_style2)
        curve_groupbox.setStyleSheet(box_style)
        return curve_groupbox

    def img_module(self, img_plot):
        img_groupbox = qtw.QGroupBox()
        img_groupbox.setLayout(img_plot.plot_layout)
        img_groupbox.setFont(self.custom_style2)
        img_groupbox.setStyleSheet(box_style)
        return img_groupbox

    def new_button(self, button_request):
        ##Create the button and assign function
        if button_request == "fast_button":
            self.fast_button = qtw.QPushButton("Fast Mode: Off", self)
            self.fast_button.setFont(self.custom_style3)
            self.fast_button.setStyleSheet(click_style_on)
            self.fast_button.clicked.connect(lambda: self.button_click(button_request))
            return self.fast_button

        elif button_request == "quit_button":
            qbtn = qtw.QPushButton('Quit', self)
            qbtn.setFont(self.custom_style3)
            qbtn.setStyleSheet(click_style_on)
            qbtn.clicked.connect(qtw.QApplication.instance().quit)
            return qbtn

    def button_click(self, mode):
        ##Execute Button Function
        if mode == "fast_button":
            #toggle fastmode
            if self.fast_mode:
                self.fast_mode = False
                self.fast_button.setText("Fast Mode: Off")
                self.fast_button.setStyleSheet(click_style_on)
            elif not self.fast_mode:
                self.fast_mode = True
                self.fast_button.setText("Fast Mode: On")
                self.fast_button.setStyleSheet(click_style_off)

    def color_coder(self, metrics_index, distribution=0, percent_max=0, zero=False): # distribution[yellow, orange, red, purple]
        # percent_max will represent 100%, and will trigger percentage mode if provided (0 is off)
        value = self.metrics[metrics_index]
        last_value = self.metrics_last[metrics_index]

        if distribution:
            if percent_max:
                if value/percent_max < distribution[0]:
                    return 'color: rgb(255,255,255);' #Set to normal
                if  distribution[0] <= value/percent_max < distribution[1]:
                    return 'color: rgb(229,192,123);'
                if  distribution[1] <= value/percent_max < distribution[2]:
                    return 'color: rgb(206,101,53);'
                if  distribution[2] <= value/percent_max < distribution[3]:
                    return 'color: rgb(220,89,61);'
                if  value/percent_max >= distribution[3]:
                    return 'color: rgb(198,120,221);'

            elif not percent_max:
                if value < distribution[0]:
                    return 'color: rgb(255,255,255);' #Set to normal
                if  distribution[0] <= value < distribution[1]:
                    return 'color: rgb(229,192,123);'
                if  distribution[1] <= value < distribution[2]:
                    return 'color: rgb(206,101,53);'
                if  distribution[2] <= value < distribution[3]:
                    return 'color: rgb(220,89,61);'
                if  value >= distribution[3]:
                    return 'color: rgb(198,120,221);'

        elif not distribution:
            if zero: #positive/negative
                if value > 0:
                    return 'color: rgb(152,195,121);'
                elif value <= 0:
                    return 'color: rgb(220,89,61);'
            elif not zero: #improve/worsen
                if value >= last_value:
                    return 'color: rgb(152,195,121); border-style: none; text-align: left;'
                elif value < last_value:
                    return 'color: rgb(220,89,61); border-style: none; text-align: left;'

def map(x):
    result = ((x-1028)*(100-0)/(430-1028) + 0)
    return result

def launchcode(self):      #the universal 'show' protocol 
    self.setGeometry(0, 0, 3840, 2160)
    #self.setGeometry(1950, 70, 1880, 1600)
    self.setStyleSheet("background-color: rgb(40,44,52);")
    self.setWindowTitle('DRL Monitor')
    #self.show()
    self.showMaximized()

def main(connection):
    #if mode == 'Main_Window':
    app = qtw.QApplication(sys.argv)
    mw = MainWindow(connection,)   
    sys.exit(app.exec())

#margin: 1px;   <- under chunk
pbar_Style1 = """
QProgressBar{
    border: 4px solid grey;
    border-radius: 5px;
    border-color: rgb(152,195,121);
    color: rgb(152,195,121);
    text-align: center
}
QProgressBar::chunk {
    background-color: rgb(152,195,121);
    width: 10px;
}
"""
pbar_Style2 = """
QProgressBar{
    border: 4px solid grey;
    border-radius: 5px;
    border-color: rgb(152,195,121);
    color: rgb(40,44,52);
    text-align: center
}
QProgressBar::chunk {
    background-color: rgb(152,195,121);
    width: 10px;
}
"""

click_style_off ="""
border-color: rgb(255,255,255);
color: rgb(80,167,239);
border-radius: 8px;
border-width : 4px;
border-style:outset;
"""
click_style_on = """
border-color: rgb(255,255,255);
color: rgb(255,255,255);
border-radius: 8px;
border-width : 4px;
border-style:outset;
"""
click_style_random = """
border :3px solid black;
border-color: rgb(209,154,102);
color: rgb(80,167,239);
border-radius: 8px;
border-width: 4px;
"""


#color:rgb(152,195,121); green
#rgb(40,44,52) grey background.

metric_style = """
color: rgb(255,255,255);
border-width : 0px;
border-style: none;
text-align: left;
"""

metric_style_random = """
border-color: rgb(152,195,121);
color: rgb(80,167,239);
border-width : 0px;
border-style: none;
"""

box_style = """
QGroupBox {
    border :3px solid black;
    border-color: rgb(255,255,255);
    color: rgb(209,154,102);
    border-radius: 8px;
    border-width : 4px;
    }
"""

button_style = 0

if __name__ == '__main__':
    main(19)
    # main('Main_Window')