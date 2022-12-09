from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

import os
import platform #identifies OS

#Graph Stuff
import numpy as np
import math
from scipy.interpolate import interp1d
from collections import deque
from colour import Color
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
import pyqtgraph as pg

#Fonts on Linux
#https://stackoverflow.com/questions/42097053/matplotlib-cannot-find-basic-fonts
#python -m pyqtgraph.examples

#//// Matplot Graphing Widgets /////////////////////////////////////////////#
class GraphWidget(qtw.QWidget):
    'A widget to display a runnning graph of information'

    def __init__(self, *args, data_width=100, minimum=0, maximum=100, 
                warn_val=50, crit_val=75, scale=10, **kwargs):
        super().__init__(*args, **kwargs)

        self.maximum, self.minimum  = maximum, minimum
        self.warn_val = warn_val
        self.crit_val = crit_val
        self.scale = scale

        self.bad_color = qtg.QColor(255, 0, 0) #Red
        self.medium_color = qtg.QColor(255, 255, 0) #Yellow
        self.good_color = qtg.QColor(0, 255, 0) #Green

        self.red = Color("red")
        self.lime = Color("lime")
        self.gradient = list(self.red.range_to(self.lime, (self.maximum-self.minimum)))

        self.values = deque([self.minimum]* data_width, maxlen=data_width)
        self.setFixedWidth(data_width * scale)
    
    def add_value(self, value):
        '''
        This method begins by constraining our values between our min and max,
        and then appending it to the deque object
        '''
        value = max(value, self.minimum)
        #value = min(value, self.maximum)
        
        #Dynamic Maximum
        self.maximum-=0.01 #decay the value to keep it dynamic.
        if value > self.maximum:
            self.maximum = value
            self.gradient = list(self.red.range_to(self.lime, (self.maximum-self.minimum)))
        if self.maximum%10==0:
            self.gradient = list(self.red.range_to(self.lime, (self.maximum-self.minimum)))
        
        self.values.append(value)
        self.update()
    
    def paintEvent(self, paint_event):
        painter = qtg.QPainter(self)
        brush = qtg.QBrush(qtg.QColor(48,48,48))
        painter.setBrush(brush)
        painter.drawRect(0, 0, self.width(), self.height())

        pen = qtg.QPen()
        pen.setDashPattern([1,0])

        warn_y = self.val_to_y(self.warn_val)
        pen.setColor(self.good_color)
        painter.setPen(pen)
        painter.drawLine(0, warn_y, self.width(), warn_y)

        crit_y = self.val_to_y(self.crit_val)
        pen.setColor(self.bad_color)
        painter.setPen(pen)
        painter.drawLine(0, crit_y, self.width(), crit_y)

        '''
        gradient = qtg.QLinearGradient(qtc.QPointF(0, self.height()), qtc.QPointF(0, 0))
        gradient.setColorAt(0, self.bad_color)
        gradient.setColorAt(self.warn_val/(self.maximum-self.minimum), self.good_color)
        gradient.setColorAt(self.crit_val/(self.maximum-self.minimum), self.medium_color)

        brush = qtg.QBrush(gradient)
        painter.setBrush(brush)
        painter.setPen(qtc.Qt.NoPen)
        '''

        self.start_value = getattr(self, 'start_value', self.minimum)
        last_value = self.start_value
        self.start_value = self.values[0]

        for i, value in enumerate(self.values):
            local_color = self.gradient[min(int(value),len(self.gradient)-1)]
            local_color = [int(item*255) for item in local_color.rgb]
            #brush = qtg.QBrush(qtg.QColor(str(local_color)))
            brush = qtg.QBrush(qtg.QColor(local_color[0], local_color[1], local_color[2], 150))
            painter.setBrush(brush)
            painter.setPen(qtc.Qt.NoPen)

            x = (i + 1) * self.scale
            last_x = i * self.scale
            y = self.val_to_y(value)
            last_y = self.val_to_y(last_value)

            path = qtg.QPainterPath()
            path.moveTo(x, self.height())
            path.lineTo(last_x, self.height())
            path.lineTo(last_x, last_y)
            #path.lineTo(x, y) #this will draw rectagles, which is more jagged.
            c_x = round(self.scale * 0.5) + last_x
            c1 = (c_x, last_y)
            c2 = (c_x, y)
            path.cubicTo(*c1, *c2, x, y)
            
            painter.drawPath(path)
            last_value = value

    def val_to_y(self, value):
        data_range = self.maximum - self.minimum
        value_fraction = value / data_range
        y_offset = round(value_fraction * self.height())
        y = self.height() - y_offset
        return y

class PlotWidget(qtw.QWidget): #generic plot module

    def __init__(self, *args,
                plot_layers, graph_label, 
                label_1, label_2='blank', label_3='blank', label_4='blank',
                y_min, y_max, left,
                **kwargs):
        super().__init__(*args, **kwargs)
        
        self.graph_label = graph_label
        self.plot_layers = plot_layers
        self.label_1 = label_1
        self.label_2 = label_2
        self.label_3 = label_3
        self.label_4 = label_4
        self.y_min = y_min
        self.y_max = y_max

        #left=0.6, right=0.985, top=0.935, bottom=0.065 Defaults
        self.canvas = MplCanvas(self, width=1, height=1, dpi=180, left=left, right=0.98,top=0.9, bottom =0.095)
        self.xdata = []
        self.ydata1 = []
        self.ydata2 = []
        self.ydata3 = []
        self.ydata4 = []

        # Create toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        toolbar = NavigationToolbar(self.canvas, self)

        self.add_value([0],[0],[0],[0], self.graph_label)
        
        self.plot_layout = qtw.QVBoxLayout()
        #self.plot_layout.addWidget(toolbar)
        self.plot_layout.addWidget(self.canvas)

    def add_value(self, input_1, input_2=[0], input_3=[0], input_4=[0], title=""):
        self.ydata1 =[float(x) for x in input_1]
        self.ydata2 =[float(x) for x in input_2]
        self.ydata3 =[float(x) for x in input_3]
        self.ydata4 =[float(x) for x in input_4]
        if len(self.ydata1)==1:
            self.ydata1.append(self.ydata1[0])
            self.ydata2.append(self.ydata2[0])
            self.ydata3.append(self.ydata3[0])
            self.ydata4.append(self.ydata4[0])

        self.y_max = round(max( max(self.ydata1), max(self.ydata2), max(self.ydata3), max(self.ydata4) )*1.1) #adjust the limit, with a little space.
        self.y_min = round(min( min(self.ydata1), min(self.ydata2), min(self.ydata3), min(self.ydata4) )*0.9) #adjust the limit, with a little space.
        if int(self.y_max) == int(self.y_min):
            self.y_max+=1
            self.y_min-=1
        #self.xdata.reverse() #we need to do this for label reasons.

        '''
        if len(self.ydata1) < self.n_data: #if our lists arent full (len less than data length)
            self.ydata1 = self.ydata1 + [input_1] 
            self.ydata2 = self.ydata2 + [input_2] 
            self.ydata3 = self.ydata3 + [input_3] 
            self.xdata = list(range(len(self.ydata1))) #x axis will be a list of indexies equal to len(y_axis)
            #self.xdata.reverse() #we need to do this for label reasons.
        elif len(self.ydata1) >= self.n_data: #if we've filled our list que.
            self.ydata1 = self.ydata1[1:] + [input_1] # Drop off the first y element, append a new one.
            self.ydata2 = self.ydata2[1:] + [input_2]
            self.ydata3 = self.ydata3[1:] + [input_3]
            self.xdata = list(range(len(self.ydata1))) #x axis will be a list of indexies equal to len(y_axis)
            #self.xdata.reverse() #we need to do this for label reasons.
        '''
        self.xdata = list(range(len(self.ydata1))) #x axis will be a list of indexies equal to len(y_axis)
        #This is where we set the plot specific style parameters.
        axes = self.canvas.axes
        axes.cla() #clear axis.
        axes.set_facecolor((0.12, 0.12, 0.12))
        axes.set_xlim([0, len(self.ydata1)-1]) #This overwrites the automatic x axis label range.
        #axes.invert_xaxis() #since new values are appended at the end...
        axes.set_ylim([self.y_min, self.y_max]) #This overwrites the automatic y axis label range.
        axes.grid(True)
        axes.tick_params(labelcolor='white')
        axes.set_title(title, color=(1, 1, 1)) #This is how to set title within module
        
        if self.plot_layers == 1:
            axes.plot(self.xdata, self.ydata1, color=colors_mpl["magenta"], label=self.label_1)

        elif self.plot_layers == 2:
            legend_1 = mpatches.Patch(color=colors_mpl["magenta"], label=self.label_1)
            legend_2 = mpatches.Patch(color=colors_mpl["light_blue"], label=self.label_2)
            axes.legend(handles=[legend_1, legend_2])

            axes.plot(self.xdata, self.ydata2, color=colors_mpl["light_blue"])
            axes.plot(self.xdata, self.ydata1, color=colors_mpl["magenta"]) #tuple is rgb val

        elif self.plot_layers == 3:
            legend_1 = mpatches.Patch(color=colors_mpl["magenta"], label=self.label_1)
            legend_2 = mpatches.Patch(color=colors_mpl["light_blue"], label=self.label_2)
            legend_3 = mpatches.Patch(color=colors_mpl["green"], label=self.label_3)
            axes.legend(handles=[legend_1, legend_2, legend_3])

            axes.plot(self.xdata, self.ydata3, color=colors_mpl["green"], linestyle='--')
            axes.plot(self.xdata, self.ydata2, color=colors_mpl["light_blue"])
            axes.plot(self.xdata, self.ydata1, color=colors_mpl["magenta"]) #tuple is rgb val

        elif self.plot_layers == 4:
            legend_1 = mpatches.Patch(color=colors_mpl["magenta"], label=self.label_1)
            legend_2 = mpatches.Patch(color=colors_mpl["light_blue"], label=self.label_2)
            legend_3 = mpatches.Patch(color=colors_mpl["green"], label=self.label_3)
            legend_4 = mpatches.Patch(color=colors_mpl["soft_yellow"], label=self.label_4)
            axes.legend(handles=[legend_1, legend_2, legend_3, legend_4])

            axes.plot(self.xdata, self.ydata4, color=colors_mpl["soft_yellow"], linestyle='--')
            axes.plot(self.xdata, self.ydata3, color=colors_mpl["green"])
            axes.plot(self.xdata, self.ydata2, color=colors_mpl["light_blue"], linestyle='--')
            axes.plot(self.xdata, self.ydata1, color=colors_mpl["magenta"]) #tuple is rgb val

        # Trigger the canvas to update and redraw.
        self.canvas.draw()

class SmoothPlotWidget(qtw.QWidget): #smooth plot module
    #https://www.geeksforgeeks.org/how-to-plot-a-smooth-curve-in-matplotlib/
    """ Vertical Tick Lines

    this widget will manage a que containing the ticks for vertical lines.
    When a value is added, if the ticks value is True, we add a 1, else add
    a 0. 

    The len of the que will have to be adjusted to be equal to the len of the
    data.
    """

    def __init__(self, *args,
                plot_layers, graph_label="", 
                label_1, label_2='blank', label_3='blank',
                label_4='blank', label_5='blank',
                label_6='blank', y_min, y_max,
                left=0.6, right=0.985,
                top=0.935, bottom=0.065,
                **kwargs):
        super().__init__(*args, **kwargs)
        
        self.color_1 = colors_mpl["soft_red"]
        self.color_2 = colors_mpl["light_blue"]
        self.color_3 = colors_mpl["green"]
        self.color_4 = colors_mpl["magenta"]
        self.color_5 = colors_mpl["yellow"]
        self.color_6 = colors_mpl["white"]

        """
        font = mpl_font
        #'Seven Segment', 'DSEG14 Classic'
        segment_font = 'Seven Segment'
        self.title_font ={'fontname':font,
                            'fontsize': 20}
        self.sub_font ={'fontname':font,
                            'fontsize': 12}
        self.y_font ={'fontname':segment_font,
                            'fontsize': 16}
        """
        self.graph_label = graph_label
        self.plot_layers = plot_layers
        self.label_1 = label_1
        self.label_2 = label_2
        self.label_3 = label_3
        self.label_4 = label_4
        self.label_5 = label_5
        self.label_6 = label_6
        self.y_min = y_min
        self.y_max = y_max

        #left=0.6, right=0.985, top=0.935, bottom=0.065 Defaults
        self.canvas = MplCanvas(self, width=1, height=1, dpi=180,
                                left=left, right=right,
                                top=top, bottom=bottom)
        self.xdata = []
        self.ydata1 = []
        self.ydata2 = []
        self.ydata3 = []
        self.ydata4 = []

        # Create toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        #toolbar = NavigationToolbar(self.canvas, self)

        dummy = [0 for n in range(y_max)]
        #dummy = [np.random.randint(-100,100) for n in range(y_max)]
        self.add_value(dummy, dummy, dummy,
                       dummy, dummy, dummy,
                       title=self.graph_label)

        self.plot_layout = qtw.QVBoxLayout()
        #self.plot_layout.addWidget(toolbar)
        self.plot_layout.addWidget(self.canvas)

    def add_value(self, input_1, input_2=[], input_3=[],
                  input_4=[], input_5=[], input_6=[],
                  x_labels="", title="", tick_list=[]):

        self.ydata1 = [float(x) for x in input_1]
        self.ydata2 = [float(x) for x in input_2]
        self.ydata3 = [float(x) for x in input_3]
        self.ydata4 = [float(x) for x in input_4]
        self.ydata5 = [float(x) for x in input_5]
        self.ydata6 = [float(x) for x in input_6]

        if len(self.ydata1) == 1:
            self.ydata1.append(self.ydata1[0])
            self.ydata2.append(self.ydata2[0])
            self.ydata3.append(self.ydata3[0])
            self.ydata4.append(self.ydata4[0])
            self.ydata5.append(self.ydata5[0])
            self.ydata6.append(self.ydata6[0])

        self.xdata = list(range(len(self.ydata1))) #x axis will be a list of indexies equal to len(y_axis)

        if len(tick_list) != len(self.xdata): #we're not using vertical ticks.
            tick_list = [0 for n in self.xdata]

        #Convert to NP array
        xdata = np.array(self.xdata)
        ydata1 = np.array(self.ydata1)
        ydata2 = np.array(self.ydata2)
        ydata3 = np.array(self.ydata3)
        ydata4 = np.array(self.ydata4)
        ydata5 = np.array(self.ydata5)
        ydata6 = np.array(self.ydata6)

        #Used to find the min max across all entries.
        complete = np.concatenate((ydata1, ydata2, ydata3, ydata4, ydata5, ydata6))
        #adjust the limits, with a little space.
        self.y_max = round(max(complete)*1.1)
        temp_min = min(complete)
        if temp_min >= 0:
            self.y_min = round(temp_min*0.9)
        elif temp_min < 0:
            self.y_min = round(temp_min*1.1)

        if int(self.y_max) == int(self.y_min):
            self.y_max+=1
            self.y_min-=1

        curve_x = np.linspace(xdata.min(), xdata.max(), 500)

        X_Y_Spline_1 = interp1d(xdata, ydata1, kind="cubic")
        curve_y1 = X_Y_Spline_1(curve_x)
        #curve_y1[curve_y1 > 99] = 99 #set ceiling

        if input_2 != []:
            X_Y_Spline_2 = interp1d(xdata, ydata2, kind="cubic")
            curve_y2 = X_Y_Spline_2(curve_x)
            #curve_y2[curve_y2 > 99] = 99 #set ceiling

        if input_3 != []:
            X_Y_Spline_3 = interp1d(xdata, ydata3, kind="cubic")
            curve_y3 = X_Y_Spline_3(curve_x)
            #curve_y3[curve_y3 > 99] = 99 #set ceiling

        if input_4 != []:
            X_Y_Spline_4 = interp1d(xdata, ydata4, kind="cubic")
            curve_y4 = X_Y_Spline_4(curve_x)
            #curve_y4[curve_y4 > 99] = 99 #set ceiling

        if input_5 != []:
            X_Y_Spline_5 = interp1d(xdata, ydata5, kind="cubic")
            curve_y5 = X_Y_Spline_5(curve_x)
            #curve_y5[curve_y5 > 99] = 99 #set ceiling

        if input_6 != []:
            X_Y_Spline_6 = interp1d(xdata, ydata6, kind="cubic")
            curve_y6 = X_Y_Spline_6(curve_x)
            #curve_y6[curve_y6 > 99] = 99 #set ceiling

        #This is where we set the plot specific style parameters.
        axes = self.canvas.axes
        axes.cla() #clear axis.
        axes.set_facecolor((0.12, 0.12, 0.12))
        axes.set_xlim([0, len(self.ydata1)-1]) #This overwrites the automatic x axis label range.
        #axes.invert_xaxis() #since new values are appended at the end...
        axes.set_ylim([self.y_min, self.y_max]) #This overwrites the automatic y axis label range.
        axes.grid(True,color=colors_mpl['grid_color'], linestyle='-', linewidth=1)#True,color='r', linestyle='-', linewidth=2

        #force it to show all days on x axis.
        #x_ticks = [n for n in range(len(x_labels))]
        #axes.set_xticks(x_ticks)
        #axes.set_xticklabels(x_labels) #(rotation=45,ha='right', fontdict=self.sub_font)

        #force it to showby 5's in the y axis.
        #y_max = round(self.y_max/10)
        #y_limit = [n*10 for n in range(y_max)]
        #axes.set_yticks(y_limit)
        #axes.set_yticklabels(y_limit) #fontdict=self.y_font)
        axes.tick_params(labelleft=True, labelcolor='white')

        #https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.set_title.html
        if title != "":
            axes.set_title(title, color=(1, 1, 1)) #fontdict=title_font) #This is how to set title within module

        if self.plot_layers == 1:
            axes.plot(curve_x, curve_y1, color=self.color_1, label=self.label_1)

        elif self.plot_layers == 2:
            legend_1 = mpatches.Patch(color=self.color_1, label=self.label_1)
            legend_2 = mpatches.Patch(color=self.color_2, label=self.label_2)
            leg = axes.legend(handles=[legend_1, legend_2])

            axes.plot(curve_x, curve_y2, color=self.color_2)
            axes.plot(curve_x, curve_y1, color=self.color_1) #tuple is rgb val

        elif self.plot_layers == 3:
            legend_1 = mpatches.Patch(color=self.color_1, label=self.label_1)
            legend_2 = mpatches.Patch(color=self.color_2, label=self.label_2)
            legend_3 = mpatches.Patch(color=self.color_3, label=self.label_3)
            leg = axes.legend(handles=[legend_1, legend_2, legend_3])

            axes.plot(curve_x, curve_y3, color=self.color_3, linestyle='--')
            axes.plot(curve_x, curve_y2, color=self.color_2)
            axes.plot(curve_x, curve_y1, color=self.color_1) #tuple is rgb val

        elif self.plot_layers == 4:
            legend_1 = mpatches.Patch(color=self.color_1, label=self.label_1)
            legend_2 = mpatches.Patch(color=self.color_2, label=self.label_2)
            legend_3 = mpatches.Patch(color=self.color_3, label=self.label_3)
            legend_4 = mpatches.Patch(color=self.color_4, label=self.label_4)
            leg = axes.legend(handles=[legend_1, legend_2, legend_3, legend_4],
                                 loc='upper right', fancybox=True,
                                 framealpha=0)

            axes.plot(curve_x, curve_y4, color=self.color_4, linestyle='--')
            axes.plot(curve_x, curve_y3, color=self.color_3)
            axes.plot(curve_x, curve_y2, color=self.color_2, linestyle='--')
            axes.plot(curve_x, curve_y1, color=self.color_1) #tuple is rgb val

        elif self.plot_layers == 6:
            legend_1 = mpatches.Patch(color=self.color_1, label=self.label_1)
            legend_2 = mpatches.Patch(color=self.color_2, label=self.label_2)
            legend_3 = mpatches.Patch(color=self.color_3, label=self.label_3)
            legend_4 = mpatches.Patch(color=self.color_4, label=self.label_4)
            legend_5 = mpatches.Patch(color=self.color_5, label=self.label_5)
            legend_6 = mpatches.Patch(color=self.color_6, label=self.label_6)
            leg = axes.legend(handles=[legend_1, legend_2, legend_3,
                                 legend_4, legend_5, legend_6],
                                 loc='upper right', fancybox=True,
                                 framealpha=0)

            axes.plot(curve_x, curve_y6, color=self.color_6, linestyle='--')
            axes.plot(curve_x, curve_y5, color=self.color_5)
            axes.plot(curve_x, curve_y4, color=self.color_4, linestyle='--')
            axes.plot(curve_x, curve_y3, color=self.color_3)
            axes.plot(curve_x, curve_y2, color=self.color_2, linestyle='--')
            axes.plot(curve_x, curve_y1, color=self.color_1) #tuple is rgb val

            #draw the ticks line.
            ticks_temp = []
            for index, tick in enumerate(tick_list):
                if tick == 1:
                    ticks_temp.append(index)

            axes.vlines(x=ticks_temp, ymin=0, ymax=self.y_max,
                        colors=colors_mpl['gray'],
                        linestyle='--')

        for text in leg.get_texts():
            text.set_color(colors_mpl['gray'])
            text.set_fontfamily(mpl_font)
            #text.set_fontstyle("italic")
            #text.set_fontweight("bold")
            #text.set_fontsize(14)

        # Trigger the canvas to update and redraw.
        self.canvas.draw()

class RewardPlotWidget(qtw.QWidget): #bespoke module for reward graph.

    def __init__(self, *args,
                plot_layers, graph_label, 
                label_1, label_2='blank', label_3='blank', label_4='blank',
                y_min, y_max, left,
                **kwargs):
        super().__init__(*args, **kwargs)
        
        self.graph_label = graph_label
        self.plot_layers = plot_layers
        self.label_1 = label_1
        self.label_2 = label_2
        self.label_3 = label_3
        self.label_4 = label_4
        self.y_min = y_min
        self.y_max = y_max

        self.canvas = MplCanvas(self, width=1, height=1, dpi=180, left=left, right=0.98, top=0.92, bottom=0.07)
        self.xdata = []
        self.ydata1 = []
        self.ydata2 = []
        self.ydata3 = []
        self.ydata4 = []

        # Create toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        toolbar = NavigationToolbar(self.canvas, self)
        self.add_value([0],[0],[0],[0], self.graph_label)
        
        self.plot_layout = qtw.QVBoxLayout()
        #self.plot_layout.addWidget(toolbar)

        self.plot_layout.addWidget(self.canvas)

    def add_value(self, input_1, input_2='empty', input_3='empty', input_4='empty', title=""):
        self.ydata1 =[float(x) for x in input_1]
        self.ydata2 =[float(x) for x in input_2]
        #need min of 2 values for function.
        if len(self.ydata1)==1:
            self.ydata1.append(self.ydata1[0])
            self.ydata2.append(self.ydata2[0])

        self.y_max = round(max(self.ydata1)*1.05) #adjust the limit, with a little space.
        self.y_min = round(min(self.ydata1)*0.95) #adjust the limit, with a little space.
        if int(self.y_max) == int(self.y_min):
            self.y_max+=1
            self.y_min-=1

        #this contains 1&0. We want lines where there are 1's.
        self.ydata3 = list(input_3)
        temp = []
        for index, val in enumerate(self.ydata3):
            if val == 1:
                temp.append(index)
        self.ydata3 = temp

        self.ydata4 = list(input_4)
        self.xdata = list(range(len(self.ydata1))) #x axis will be a list of indexies equal to len(y_axis)

        #This is where we set the plot specific style parameters.
        axes = self.canvas.axes
        axes.cla() #clear axis.
        axes.set_facecolor((0.12, 0.12, 0.12))
        axes.set_xlim([0, len(self.ydata1)-1]) #This overwrites the automatic x axis label range.
        #axes.invert_xaxis() #since new values are appended at the end...
        axes.set_ylim([self.y_min, self.y_max]) #This overwrites the automatic y axis label range.
        axes.grid(True)
        axes.tick_params(labelcolor='white')
        axes.set_title(title, color=(1, 1, 1)) #This is how to set title within module
        
        if self.plot_layers == 1:
            axes.plot(self.xdata, self.ydata1, color=colors_mpl["magenta"], label=self.label_1)

        elif self.plot_layers == 2:
            legend_1 = mpatches.Patch(color=colors_mpl["magenta"], label=self.label_1)
            legend_2 = mpatches.Patch(color=colors_mpl["light_blue"], label=self.label_2)
            axes.legend(handles=[legend_1, legend_2])

            axes.plot(self.xdata, self.ydata2, color=colors_mpl["light_blue"])
            axes.plot(self.xdata, self.ydata1, color=colors_mpl["magenta"]) #tuple is rgb val

        #y3 is for yellow vertical lines
        elif self.plot_layers == 3:
            legend_1 = mpatches.Patch(color=colors_mpl["magenta"], label=self.label_1)
            legend_2 = mpatches.Patch(color=colors_mpl["light_blue"], label=self.label_2)
            legend_3 = mpatches.Patch(color=colors_mpl["soft_yellow"], label=self.label_3)
            axes.legend(handles=[legend_1, legend_2, legend_3])

            for vline in self.ydata3:
                axes.axvline(x=vline,  color=colors_mpl["soft_yellow"], linestyle=':')
            #axes.plot(self.xdata, self.ydata3, color=colors_mpl["soft_yellow"], linestyle='--')
            axes.plot(self.xdata, self.ydata2, color=colors_mpl["light_blue"])
            axes.plot(self.xdata, self.ydata1, color=colors_mpl["magenta"]) #tuple is rgb val

        elif self.plot_layers == 4:
            legend_1 = mpatches.Patch(color=colors_mpl["magenta"], label=self.label_1)
            legend_2 = mpatches.Patch(color=colors_mpl["light_blue"], label=self.label_2)
            legend_3 = mpatches.Patch(color=colors_mpl["green"], label=self.label_3)
            legend_4 = mpatches.Patch(color=(0.8, 0.3, 0.3), label=self.label_4)
            axes.legend(handles=[legend_1, legend_2, legend_3, legend_4])

            axes.plot(self.xdata, self.ydata4, color=(0.8, 0.3, 0.3))
            axes.plot(self.xdata, self.ydata3, color=colors_mpl["green"], linestyle='--')
            axes.plot(self.xdata, self.ydata2, color=colors_mpl["light_blue"])
            axes.plot(self.xdata, self.ydata1, color=colors_mpl["magenta"]) #tuple is rgb val

        # Trigger the canvas to update and redraw.
        self.canvas.draw()

class DaylightBar(qtw.QWidget):
    #https://www.geeksforgeeks.org/how-to-plot-a-smooth-curve-in-matplotlib/
    """ Vertical Tick Lines
    This class will make a complex horizontal plot using tick lines to
    fill in colors. Inputs must be the edges of the blocks, with values
    on a 0-100 scale.
    """

    def __init__(self, *args, graph_label="",
                left=0.6, right=0.985,
                top=0.935, bottom=0.065,
                mini_text=False,
                **kwargs):
        super().__init__(*args, **kwargs)
        
        self.color_1 = colors_mpl["soft_red"]
        self.color_2 = colors_mpl["light_blue"]
        self.color_3 = colors_mpl["green"]
        self.color_4 = colors_mpl["magenta"]
        self.color_5 = colors_mpl["yellow"]
        self.color_6 = colors_mpl["white"]

        font = mpl_font
        if not mini_text:
            self.title_font ={'fontname':font,
                              'fontsize': 20}
            self.sub_font ={'fontname':font,
                              'fontsize': 12}
        elif mini_text:
            self.title_font ={'fontname':font,
                              'fontsize': 14}
            self.sub_font ={'fontname':font,
                              'fontsize': 10}

        self.graph_label = graph_label
        self.y_min = 0
        self.y_max = 2

        #left=0.6, right=0.985, top=0.935, bottom=0.065 Defaults
        self.canvas = MplCanvas(self, width=1, height=1, dpi=180,
                                left=left, right=right,
                                top=top, bottom=bottom)
        self.xdata = []

        # Create toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        #toolbar = NavigationToolbar(self.canvas, self)

        dummy = [33,66]
        dummy_labels = ["Dawn","Dusk"]
        self.add_value(input_1=dummy,title=self.graph_label,x_labels=dummy_labels)
        
        self.plot_layout = qtw.QVBoxLayout()
        #self.plot_layout.addWidget(toolbar)
        self.plot_layout.addWidget(self.canvas)

    def add_value(self, input_1, x_labels, title="", slider=""):

        """
        Slider is used to indicate a value on the plot, e.g. the current
        time of day.

        example input:
        input_1 = [num_am,num_pm]

        """
        l1 = input_1[0]
        l2 = input_1[1]-input_1[0]
        l3 = 100-input_1[1]

        box_1 = [n for n in range(l1)]
        box_2 = [n+input_1[0] for n in range(l2)]
        box_3 = [n+input_1[1] for n in range(l3)]

        #Insert the labels in the correct place.
        temp_labels = ["" for n in range (100)]

        temp_labels[0] = "Midnight"
        temp_labels[input_1[0]] = x_labels[0]
        temp_labels[input_1[1]] = x_labels[1]
        temp_labels[50] = "Noon"
        temp_labels[-1] = "Midnight"

        #This is where we set the plot specific style parameters.
        axes = self.canvas.axes
        axes.cla() #clear axis.
        axes.set_facecolor((0.12, 0.12, 0.12))
        axes.set_xlim([0, 99]) #This overwrites the automatic x axis label range.
        axes.set_ylim([self.y_min, self.y_max]) #This overwrites the automatic y axis label range.
        axes.grid(True,color=colors_mpl['grid_color'], linestyle='-', linewidth=1)#True,color='r', linestyle='-', linewidth=2
        axes.tick_params(labelcolor='white')
        #https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.set_title.html
        if title != "":
            #treb_font = {'fontname':'Trebuchet MS'} #set the font
            axes.set_title(title, fontdict=self.title_font, color=(1, 1, 1))#,**treb_font) #This is how to set title within module

        dummy_x = [n for n in range(100)]
        dummy_y = [0 for n in range(100)]
        axes.plot(dummy_x, dummy_y, color=colors_mpl['grid_color'])

        lw = 15
        axes.vlines(x=box_1, ymin=0, ymax=self.y_max,
                    colors=colors_mpl['dark_gray'],
                    linewidth=lw)
        axes.vlines(x=box_2, ymin=0, ymax=self.y_max,
                    colors=colors_mpl['soft_yellow'],
                    linewidth=lw)
        axes.vlines(x=box_3, ymin=0, ymax=self.y_max,
                    colors=colors_mpl['dark_gray'],
                    linewidth=lw)

        #add a line to the middle
        axes.vlines(x=50, ymin=0, ymax=self.y_max,
                    colors=colors_mpl['dark_gray'],
                    linewidth=3)

        #add the slider line
        if slider != "":
            slider=min(slider,99)
            axes.vlines(x=slider, ymin=0, ymax=self.y_max,
                        colors=colors_mpl['soft_red'],
                        linewidth=3)
            #Top ticks seperate from bottom ticks.
            secax = axes.secondary_xaxis('top')
            tl_1 = ["" for n in range (100)]
            tl_1[slider] = "Now"
            x_ticks = [n for n in range(100)]
            secax.set_xticks(x_ticks)
            secax.set_xticklabels(tl_1,fontdict=self.sub_font)
            secax.tick_params(labelcolor='white')

        #force it to show all days on x axis.
        x_ticks = [n for n in range(100)]
        axes.set_xticks(x_ticks)
        #rotation=45,ha='right'
        axes.set_xticklabels(temp_labels,fontdict=self.sub_font)

        #axes.set_ylabel('Daylight',rotation=0,color="white")
        axes.set_yticklabels([]) #Blanks

        # Trigger the canvas to update and redraw.
        self.canvas.draw()

class RainBar(qtw.QWidget):
    #https://www.geeksforgeeks.org/how-to-plot-a-smooth-curve-in-matplotlib/
    """ Vertical Tick Lines
    This class will make a complex horizontal plot using tick lines to
    fill in colors. Inputs must be the edges of the blocks, with values
    on a 0-100 scale.
    """

    def __init__(self, *args, graph_label="",
                left=0.6, right=0.985,
                top=0.935, bottom=0.065,
                mini_text=False,
                **kwargs):
        super().__init__(*args, **kwargs)

        self.color_1 = colors_mpl["soft_red"]
        self.color_2 = colors_mpl["light_blue"]
        self.color_3 = colors_mpl["green"]
        self.color_4 = colors_mpl["magenta"]
        self.color_5 = colors_mpl["yellow"]
        self.color_6 = colors_mpl["white"]

        font = mpl_font
        if not mini_text:
            self.title_font ={'fontname':font,
                              'fontsize': 20}
            self.sub_font ={'fontname':font,
                              'fontsize': 12}
        elif mini_text:
            self.title_font ={'fontname':font,
                              'fontsize': 14}
            self.sub_font ={'fontname':font,
                              'fontsize': 10}

        self.graph_label = graph_label
        self.y_min, self.y_max= 0, 2

        #left=0.6, right=0.985, top=0.935, bottom=0.065 Defaults
        self.canvas = MplCanvas(self, width=1, height=1, dpi=180,
                                left=left, right=right,
                                top=top, bottom=bottom)
        self.xdata = []

        # Create toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        #toolbar = NavigationToolbar(self.canvas, self)

        dummy = [9,9]
        dummy_labels = ["Initializing","Initializing"]
        self.add_value(input_1=dummy,title=self.graph_label,x_labels=dummy_labels)
        
        self.plot_layout = qtw.QVBoxLayout()
        #self.plot_layout.addWidget(toolbar)
        self.plot_layout.addWidget(self.canvas)

    def add_value(self, input_1, x_labels, title=""):
        #example input, two boxes:
        #[9,7]

        start = input_1[0]
        end = input_1[1]
        override_bool = False

        if start+end == 0:
            override_bool = True
            print("No Data to Plot; Start=End")
            start,end = 1,1

        sum_len = start+end
        #Insert the labels in the correct place.
        temp_labels = ["" for n in range(sum_len+1)] #account for the zero.
        temp_labels[0] = x_labels[0]
        temp_labels[-1] = x_labels[1]

        #This is where we set the plot specific style parameters.
        axes = self.canvas.axes
        axes.clear() #clear axis.

        #https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.set_title.html
        if title != "":
            #treb_font = {'fontname':'Trebuchet MS'} #set the font
            axes.set_title(title, fontdict=self.title_font, color=(1, 1, 1))#,**treb_font) #This is how to set title within module

        axes.set_facecolor((0.12, 0.12, 0.12))
        axes.set_xlim([start*-1, end]) #This overwrites the automatic x axis label range.
        axes.set_ylim([self.y_min, self.y_max]) #This overwrites the automatic y axis label range.
        axes.grid(True,color=colors_mpl['grid_color'], linestyle='-', linewidth=1)#True,color='r', linestyle='-', linewidth=2
        axes.tick_params(labelcolor='white')
                                #start xy; width, height
        axes.add_patch(Rectangle((start*-1, 0), start, 2,color=colors_mpl['purple']))
        axes.add_patch(Rectangle((0, 0), end, 2,color=colors_mpl['soft_blue']))

        #add a line to the middle
        axes.vlines(x=0, ymin=0, ymax=self.y_max,
                    colors=colors_mpl["soft_red"],
                    linewidth=3)

        #Top ticks seperate from bottom ticks.
        secax = axes.secondary_xaxis('top')
        #secax.set_xlabel('Today')
        tl_1 = ["" for n in range(sum_len+1)] #account for the zero.
        if not override_bool:
            tl_1[input_1[0]] = "Today"
        elif override_bool:
            tl_1[1] = "Today"
        x_tks = [n-start for n in range(sum_len+1)] #account for the zero.
        secax.set_xticks(x_tks)
        secax.set_xticklabels(tl_1,fontdict=self.sub_font)
        secax.tick_params(labelcolor='white')

        #force it to show all days on x axis.
        x_ticks = [n-start for n in range(sum_len+1)] #account for the zero.
        axes.set_xticks(x_ticks)
        #rotation=45,ha='right'
        axes.set_xticklabels(temp_labels,fontdict=self.sub_font)

        #axes.set_ylabel('Daylight',rotation=0,color="white")
        axes.set_yticklabels([]) #Blanks

        # Trigger the canvas to update and redraw.
        self.canvas.draw()

class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=1, height=4, dpi=100,
                 left=0.6, right=0.985, top=0.935, bottom=0.065):
        
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.set_facecolor((0.16, 0.17, 0.20,0))
        self.fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)

#//// pyQtGraph Widgets ///////////////////////////////////////////////////#
class QuickBarWidget(qtw.QWidget):

    def __init__(self, *args, num_bars=5, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.win = pg.PlotWidget()

        label = 'Action Space'
        title = qtw.QLabel(label, self)
        title.setFont(qtg.QFont('Trebuchet MS', 11))
        title.setStyleSheet(metric_style)
        title.setAlignment(qtc.Qt.AlignCenter)

        sub_label = f"F({5})     P({4})      B({3})     L({2})      R({1})    "
        self.sub_title = qtw.QLabel(sub_label, self)
        self.sub_title.setFont(qtg.QFont('Trebuchet MS', 11))
        self.sub_title.setStyleSheet(metric_style)
        self.sub_title.setAlignment(qtc.Qt.AlignRight)
        self.maximum = 0

        self.red = Color("red")
        self.lime = Color("lime")
        self.gradient = list(self.red.range_to(self.lime, (255)))

        data2 = [[-1],
        [1],
        [-1],
        [1],
        [-1]]

        data3 = [[-1 for n in range(num_bars)],
        [1 for n in range(num_bars)],
        [-1 for n in range(num_bars)],
        [1 for n in range(num_bars)],
        [-1 for n in range(num_bars)]]

        data = [[(np.random.randint(-99,99)/100) for n in range(num_bars)],
        [(np.random.randint(-99,99)/100) for n in range(num_bars)],
        [(np.random.randint(-99,99)/100) for n in range(num_bars)],
        [(np.random.randint(-99,99)/100) for n in range(num_bars)],
        [(np.random.randint(-99,99)/100) for n in range(num_bars)]]


        self.num_bars = num_bars
        #self.bar_line_list = np.array([0,4,8,12,16]) #spaced by 4
        #self.bar_line_list = np.array([0,7,14,21,28]) #spaced by 7
        #self.bar_line_list = np.array([0,1,2,3,4]) #spaced by 7 #Original Tuning, this version yields 5 bar+plots per move
        self.bar_line_list = np.array([n for n in range(num_bars)]) #This will generate dynaic set.

        self.add_value(data[0], data[1], data[2], data[3], data[4])
        
        self.plot_layout = qtw.QVBoxLayout()
        #self.plot_layout = qtw.QGridLayout()
        #self.plot_layout.addWidget(toolbar)
        self.plot_layout.addWidget(title)
        self.plot_layout.addWidget(self.sub_title)
        self.plot_layout.addWidget(self.win)

        self.groupbox = qtw.QGroupBox()
        self.groupbox.setLayout(self.plot_layout)
        self.groupbox.setFont(custom_font2)
        self.groupbox.setStyleSheet(box_style)

    def add_value(self, y1, y2, y3, y4, y5):
        yset = [y1, y2, y3, y4, y5]
        ##Catch condition for when the input array is shorter than the bar count per race
        for sub_list in yset:
            while len(sub_list) < self.num_bars:
                #sub_list[:0] = [0] #append to the beggining of the list
                sub_list.insert(0, 0) # second arg is number being inserted

        averages = []
        color_adjust = [1, 0.9, 0.8, 0.7, 0.6]
        self.win.clear()

        averages.append(np.mean(yset[0]))
        averages.append(np.mean(yset[1]))
        averages.append(np.mean(yset[2]))
        averages.append(np.mean(yset[3]))
        averages.append(np.mean(yset[4]))
        places = averages.copy()

        #Dynamic Maximum
        self.maximum-=0.1 #decay the value to keep it dynamic.
        if max(averages) > self.maximum:
            self.maximum = max(averages)

        def color_generator(avg_val, place=None):
            avg_norm = max(avg_val,0) #set zero floor.
            avg_norm = np.interp(avg_norm,[0, self.maximum],[0,254]) #like c map function:(input val, [inrange_min,inrange_max],[outrange_min,outrange_max]
            #avg_norm = avg_norm * color_adjust[place-1]
            color = self.gradient[int(avg_norm)]
            color = [int(item*255) for item in color.rgb]
            ## if value is negative, we darken
            if avg_val<0:
                dark_factor = np.interp(abs(avg_val),[0, self.maximum],[0,254]) #maps from one range to another
                color[0] = max(color[0]-dark_factor,0) #cant be lower than 0
                color[1] = max(color[1]-dark_factor,0)
                color[2] = max(color[2]-dark_factor,0)
 
            return color

        def array_rank(inx):
            # Copy input array into newArray
            input_array = inx
            new_array = input_array.copy()
            # Sort newArray[] in ascending order
            new_array.sort()
            # Dictionary to store the rank of
            # the array element
            ranks = {}
            rank = len(new_array)
            for index in range(len(new_array)):
                element = new_array[index];
                # Update rank of element
                if element not in ranks:
                    ranks[element] = rank
                    rank -= 1
            # Assign ranks to elements
            for index in range(len(input_array)):
                element = input_array[index]
                input_array[index] = ranks[input_array[index]]
            return input_array

        places = array_rank(places)
        y1_color = color_generator(averages[0],places[0])
        y2_color = color_generator(averages[1],places[1])
        y3_color = color_generator(averages[2],places[2])
        y4_color = color_generator(averages[3],places[3])
        y5_color = color_generator(averages[4],places[4])
        self.sub_title.setText(f"F({places[0]})    P({places[1]})     B({places[2]})     L({places[3]})      R({places[4]})    ")

        base = len(self.bar_line_list)

        #Note: the added constant determines the spacing between bar sub-graphs.
        """ Original Calibration
        bg1 = pg.BarGraphItem(x=w,          height=y1, width=1, brush=y1_color)
        bg2 = pg.BarGraphItem(x=w+base+2,   height=y2, width=1, brush=y2_color)
        bg3 = pg.BarGraphItem(x=w+base*2+4, height=y3, width=1, brush=y3_color)
        bg4 = pg.BarGraphItem(x=w+base*3+6, height=y4, width=1, brush=y4_color)
        bg5 = pg.BarGraphItem(x=w+base*4+8, height=y5, width=1, brush=y5_color)
        """

        ##In this version we are trying to increase the plots per move from 5 to 10
        bg1 = pg.BarGraphItem(x=self.bar_line_list,          height=yset[0], width=1, brush=y1_color)
        bg2 = pg.BarGraphItem(x=self.bar_line_list+base+2,   height=yset[1], width=1, brush=y2_color)
        bg3 = pg.BarGraphItem(x=self.bar_line_list+base*2+4, height=yset[2], width=1, brush=y3_color)
        bg4 = pg.BarGraphItem(x=self.bar_line_list+base*3+6, height=yset[3], width=1, brush=y4_color)
        bg5 = pg.BarGraphItem(x=self.bar_line_list+base*4+8, height=yset[4], width=1, brush=y5_color)

        self.win.addItem(bg1)
        self.win.addItem(bg2)
        self.win.addItem(bg3)
        self.win.addItem(bg4)
        self.win.addItem(bg5)

        #self.win.setBackground((30, 30, 30))
        self.win.setBackground((48,48,48))
        self.win.hideAxis('bottom')

class QuickCurveWidget(qtw.QWidget):

    def __init__(self, *args, minimum=0, maximum=250, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.win = pg.PlotWidget()

        label = 'Actor vs Critic'
        self.title = qtw.QLabel(label, self)
        self.title.setFont(qtg.QFont('Trebuchet MS', 11))
        self.title.setStyleSheet(metric_style)
        self.title.setAlignment(qtc.Qt.AlignCenter)

        self.maximum, self.minimum = maximum, minimum

        self.actor_pen = pg.mkPen((0, 235, 212), width=3) #blue
        self.critic_pen = pg.mkPen((255, 102, 255), width=3) #violet
        self.reward_pen = pg.mkPen((230, 217, 122), width=3) #yellow
        self.zero_pen = pg.mkPen((175, 175, 175), width=3, style=qtc.Qt.DotLine) #grey dotted

        data = [[10, 20, 30, 40, 50],
        [50, 40, 30, 20, 10],
        [-10, 10, -10, 10, -10]
        ]

        self.add_value(data[0], data[1], data[2])
        
        self.plot_layout = qtw.QVBoxLayout()
        #self.plot_layout = qtw.QGridLayout()
        #self.plot_layout.addWidget(toolbar)
        self.plot_layout.addWidget(self.title)
        self.plot_layout.addWidget(self.win)

        self.groupbox = qtw.QGroupBox()
        self.groupbox.setLayout(self.plot_layout)
        self.groupbox.setFont(custom_font2)
        self.groupbox.setStyleSheet(box_style)

    def add_value(self, input_1, input_2, input_3=[]):
        ydata1 = list(input_1)
        ydata2 = list(input_2)
        ydata3 = list(input_3)
        xdata = list(range(len(input_1))) #x axis will be a list of indexies equal to len(y_axis)
        zero_line = [0 for n in xdata]

        label = f'Actor({ydata1[-1]}) vs Critic({ydata2[-1]})'
        self.title.setText(label)

        self.win.clear()

        actor_plot = pg.PlotCurveItem(x=xdata, y=ydata1, pen=self.actor_pen, name="Agent")
        critic_plot =  pg.PlotCurveItem(x=xdata, y=ydata2, pen=self.critic_pen, name="Critic")
        reward_plot =  pg.PlotCurveItem(x=xdata, y=ydata3, pen=self.reward_pen, name="Reward")
        zero_plot =  pg.PlotCurveItem(x=xdata, y=zero_line, pen=self.zero_pen, name="Zero")

        self.win.addItem(actor_plot)
        self.win.addItem(critic_plot)
        self.win.addItem(reward_plot)
        self.win.addItem(zero_plot)

        #self.win.setBackground((30, 30, 30))
        self.win.setBackground((48,48,48))
        self.win.hideAxis('bottom')

class QuickPieWidget(qtw.QWidget):

    def __init__(self, *args, title="", **kwargs):
        super().__init__(*args, **kwargs)
    
        self.win = pg.PlotWidget()

        self.title = qtw.QLabel(title, self)
        self.title.setFont(system_font)
        self.title.setStyleSheet(metric_style)
        self.title.setAlignment(qtc.Qt.AlignCenter)

        self.red = Color("red")
        self.lime = Color("lime")
        self.soft_blue = colors_pg['soft_blue']
        self.gradient = list(self.red.range_to(self.lime, (255)))

        self.add_value(percent=100)
        self.win.setAspectLocked(lock=True, ratio=1)
        #square_size = 10
        #self.win.setRange(qtc.QRectF(0, 0, square_size, square_size)) ## Set initial view bounds
        #self.win.setGeometry(0, 0, square_size, square_size)


        self.plot_layout = qtw.QVBoxLayout()
        #self.plot_layout = qtw.QGridLayout()
        #self.plot_layout.addWidget(toolbar)
        #self.plot_layout.addWidget(self.title)
        self.plot_layout.addWidget(self.win)
        self.plot_layout.addWidget(self.title)

        self.groupbox = qtw.QGroupBox()
        self.groupbox.setLayout(self.plot_layout)
        self.groupbox.setFont(custom_font2)
        self.groupbox.setStyleSheet(borderless_style)

    def add_value(self,percent, label=""):

        self.win.clear()

        """
        https://www.copperspice.com/docs/cs_api/class_qgraphicsellipseitem.html
        setSpanAngle() Sets the span angle for an ellipse segment to angle, which is in 16ths
        of a degree. This angle is used together with startAngle() to represent an ellipse
        segment (a pie). By default, the span angle is 5760 (360 * 16, a full ellipse).
        """

        if label != "":
            self.title.setText(label)

        angle = round(np.interp(percent, [0, 100],[0, 360]))

        v1 = self.soft_blue[0]
        v2 = self.soft_blue[1]
        v3 = self.soft_blue[2]

        outline = qtw.QGraphicsEllipseItem(-51, -51, 102, 102)  # x, y, width, height
        outline.setPen(pg.mkPen((v1, v2, v3, 100)))
        outline.setBrush(pg.mkBrush(self.soft_blue))

        #negative
        outline_n = qtw.QGraphicsEllipseItem(-50, -50, 100, 100)  # x, y, width, height
        outline_n.setPen(pg.mkPen((v1, v2, v3, 100)))
        outline_n.setBrush(pg.mkBrush((40,44,52)))

        filling = qtw.QGraphicsEllipseItem(-50, -50, 100, 100)  # x, y, width, height
        filling.setStartAngle(270*16)
        filling.setSpanAngle(angle*16)

        filling.setPen(pg.mkPen((v1, v2, v3, 100)))
        filling.setBrush(pg.mkBrush(self.soft_blue))
        
        self.win.addItem(outline)
        self.win.addItem(outline_n)
        self.win.addItem(filling)

        #(40,44,52), (48,48,48), (30, 30, 30)
        self.win.setBackground((40,44,52,0))
        self.win.hideAxis('left')
        self.win.hideAxis('bottom')

class QuickImageWidget(qtw.QWidget):

    def __init__(self, *args, minimum=0, maximum=250, **kwargs):
        super().__init__(*args, **kwargs)

        """
        For speed reasons, we are given the dataset directory through the pipeline, and then load the dataset like the training
        procror does. We tick through "frames" where the index=subcycle in the dataset.
        """
        self.home_dir = os.getcwd()
        square_size= 1000

        ## Create window with GraphicsView widget
        self.win = pg.GraphicsLayoutWidget()
        self.image_object = pg.ImageItem(border='w')
       
        label = '                        Game View'
        self.title = qtw.QLabel(label, self)
        self.title.setFont(qtg.QFont('Trebuchet MS', 16))
        self.title.setStyleSheet(metric_style)
        self.title.setAlignment(qtc.Qt.AlignBottom)

        view = self.win.addViewBox()
        view.setAspectLocked(True) # lock the aspect ratio so pixels are always square
        view.addItem(self.image_object)
        view.setRange(qtc.QRectF(0, 0, square_size, square_size)) ## Set initial view bounds
        view.setGeometry(0, 0, square_size, square_size)
        self.win.setBackground((40,44,52))

        ##Load in the default image.
        #starter_img = cv2.imread("Resources\screenshot_big.png", cv2.IMREAD_UNCHANGED) #cv2.IMREAD_GRAYSCALE
        #self.frame_buffer = []
        #self.frame_buffer.append(starter_img)
        #self.tick_frame(0)

        self.plot_layout = qtw.QVBoxLayout()
        self.plot_layout.addWidget(self.win)
        self.plot_layout.addWidget(self.title)

        self.groupbox = qtw.QGroupBox()
        self.groupbox.setLayout(self.plot_layout)
        self.groupbox.setFont(custom_font2)
        self.groupbox.setStyleSheet(box_style)

    #This loads the dataset  
    def change_dataset(self, directory):
        #subfunction for natural sorting of file names.
        import re
        def natural_sorter(data):
            convert = lambda text: int(text) if text.isdigit() else text.lower()
            alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
            return sorted(data, key=alphanum_key)

        #now we're in the folder loading the file list
        os.chdir(self.home_dir)#home first
        os.chdir("Dataset")
        os.chdir(directory)
        self.file_list = os.listdir()
        self.file_list = natural_sorter(self.file_list)

        #preload all the images:
        self.frame_buffer = []
        for file_name in self.file_list:
            sub_frame = cv2.imread(file_name, cv2.IMREAD_UNCHANGED) #cv2.IMREAD_GRAYSCALE
            self.frame_buffer.append(sub_frame)

    #This updates the frame
    def tick_frame(self, subcycle):
        image = self.frame_buffer[subcycle]
        image = np.flip(np.rot90(image))
        self.image_object.setImage(image, autoLevels=None)

class QuickDaylightBar(qtw.QWidget):

    def __init__(self, *args, title="", **kwargs):
        super().__init__(*args, **kwargs)
    
        self.win = pg.PlotWidget()

        self.title = qtw.QLabel(title, self)
        self.title.setFont(system_font)
        self.title.setStyleSheet(metric_style)
        self.title.setAlignment(qtc.Qt.AlignCenter)

        self.soft_yellow = colors_pg['soft_yellow']
        self.dark_gray = colors_pg['dark_gray']
        self.soft_red = colors_pg['soft_red']

        self.y_min, self.y_max = 0, 10

        dummy = [33,66]
        dummy_labels = ["Dawn","Dusk"]
        self.add_value(dummy,dummy_labels)
        self.win.setAspectLocked(lock=True, ratio=1)

        self.plot_layout = qtw.QVBoxLayout()
        #self.plot_layout = qtw.QGridLayout()
        #self.plot_layout.addWidget(toolbar)
        self.plot_layout.addWidget(self.title)
        self.plot_layout.addWidget(self.win)

        self.groupbox = qtw.QGroupBox()
        self.groupbox.setLayout(self.plot_layout)
        self.groupbox.setFont(custom_font2)
        self.groupbox.setStyleSheet(borderless_style)

    def add_value(self, input_1, x_labels, title="", slider=""):

        self.win.clear()

        if title != "":
            self.title.setText(label)

        #Insert the labels in the correct place.
        temp_labels = [(n+1,"") for n in range(100)]
        
        dawn_i = input_1[0]
        dusk_i = input_1[1]

        temp_labels[0] = (0,"Midnight")
        temp_labels[dawn_i] = (dawn_i,x_labels[0])
        temp_labels[dusk_i] = (dusk_i,x_labels[1])
        temp_labels[50] = (50,"Noon")
        temp_labels[-1] = (100,"Midnight")

        #x_dict = dict(enumerate(temp_labels))
        temp_x = [n+1 for n in range(100)]
        temp_y = [0 for n in range(100)]

        #Axis Labels
        #https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/axisitem.html
        self.win.plot(temp_x,temp_y)
        ax=self.win.getAxis('bottom')
        ax.setTicks([temp_labels]) 
        ax.setGrid(False)# Dsiable bottom axis grid
        ax.setStyle(tickLength=0)
        ax.setTickFont(mini_font)
        
        #example input:
        #input_1 = [num_am,num_pm]
        #24hrs = 100%

        dawn = input_1[0]
        dusk = input_1[1]
        light_range = dusk-dawn

        dark_list = [50]
        dark_bar = pg.BarGraphItem(x=dark_list, height=self.y_max, width=100,brush=self.dark_gray)

        light_list = [round(dawn+(0.5*light_range))] #center it.
        light_bar = pg.BarGraphItem(x=light_list, height=self.y_max, width=light_range,brush=self.soft_yellow)

        noon_list = [50]
        noon_bar = pg.BarGraphItem(x=noon_list, height=self.y_max, width=0.5,brush=(0,0,0,50))

        #Blanks make space for the label "Midnight"
        blank_left_list = [-5]
        blank_left_bar = pg.BarGraphItem(x=blank_left_list, height=0, width=0.01 ,brush=(0,0,0,0))
        blank_right_list = [105]
        blank_right_bar = pg.BarGraphItem(x=blank_right_list, height=0, width=0.01 ,brush=(0,0,0,0))

        self.win.addItem(dark_bar)
        self.win.addItem(light_bar)
        self.win.addItem(noon_bar)
        self.win.addItem(blank_left_bar)
        self.win.addItem(blank_right_bar)

        if slider != "":
            slider_list = [slider]
            slider_bar = pg.BarGraphItem(x=slider_list, height=self.y_max, width=0.5,brush=self.soft_red)
            self.win.addItem(slider_bar)

        #(40,44,52), (48,48,48), (30, 30, 30)
        self.win.setBackground((40,44,52,0))
    
        self.win.hideAxis('left')
        #self.win.hideAxis('bottom')
        return

class QuickDaylightPie(qtw.QWidget):

    def __init__(self, *args, title="", **kwargs):
        super().__init__(*args, **kwargs)
    
        self.win = pg.PlotWidget()

        self.title = qtw.QLabel(title, self)
        self.title.setFont(system_font)
        self.title.setStyleSheet(metric_style)
        self.title.setAlignment(qtc.Qt.AlignCenter)

        self.soft_yellow = colors_pg['soft_yellow']
        self.dark_gray = colors_pg['dark_gray']
        self.soft_red = colors_pg["soft_red"]
        self.light_blue = colors_pg["light_blue"]
        self.green = colors_pg["green"]
        self.magenta = colors_pg["magenta"]
        self.yellow = colors_pg["yellow"]
        self.white = colors_pg["white"]

        self.add_value([0,100])
        self.win.setAspectLocked(lock=True, ratio=1)
  
        self.plot_layout = qtw.QVBoxLayout()
        #self.plot_layout = qtw.QGridLayout()
        #self.plot_layout.addWidget(toolbar)
        self.plot_layout.addWidget(self.win)
        self.plot_layout.addWidget(self.title)

        self.groupbox = qtw.QGroupBox()
        self.groupbox.setLayout(self.plot_layout)
        self.groupbox.setFont(custom_font2)
        self.groupbox.setStyleSheet(borderless_style)

    def add_value(self, input_1, x_labels="", label="", slider=""):
        self.win.clear()

        """
        https://www.copperspice.com/docs/cs_api/class_qgraphicsellipseitem.html
        setSpanAngle() Sets the span angle for an ellipse segment to angle, which is in 16ths
        of a degree. This angle is used together with startAngle() to represent an ellipse
        segment (a pie). By default, the span angle is 5760 (360 * 16, a full ellipse).
        """

        if label != "":
            self.title.setText(label)

        dawn_i = input_1[0]
        dusk_i = input_1[1]
        dawn_i = round(np.interp(dawn_i, [0, 100],[0, 360]))
        dusk_i = round(np.interp(dusk_i, [0, 100],[0, 360]))
        light_range = dusk_i-dawn_i

        opacity = 255
        pc1 = (self.yellow[0], self.yellow[1],
                  self.yellow[2], opacity)
        pc2 = (self.dark_gray[0], self.dark_gray[1],
                  self.dark_gray[2], opacity)

        offset = 90*16 #Degree offset
        graph_width = 6
        node_size = 0
        node_symbols = ['o','+'] #'o','t','+'

        #Darnkess
        darkness = qtw.QGraphicsEllipseItem(-51, -51, 102, 102)  # x, y, width, height
        darkness.setPen(pg.mkPen(pc2))
        darkness.setBrush(pg.mkBrush(self.dark_gray))

        daylight = qtw.QGraphicsEllipseItem(-48, -48, 96, 96)  # x, y, width, height
        daylight.setStartAngle(dawn_i*16+offset)#dusk_i,dawn_i
        daylight.setSpanAngle(light_range*16)
        daylight.setPen(pg.mkPen(pc1))
        daylight.setBrush(pg.mkBrush(self.soft_yellow))
        
        #Noon Line
        opacity_noon = round(0.3*255)
        x,y = pol2cart(50,270)#(rho, phi)
        noon_line = pg.GraphItem()
        pos = np.array([[0,0],[x,y]]) # Define nodes
        adj = np.array([[0,1]]) # Define connections
        v1 = (self.dark_gray[0], self.dark_gray[1],
                self.dark_gray[2], opacity_noon, graph_width)
        pc4 = np.array([v1],dtype=[('red',np.ubyte),
                                   ('green',np.ubyte),
                                   ('blue',np.ubyte),
                                   ('alpha',np.ubyte),
                                   ('width',float)])
        noon_line.setData(pos=pos, adj=adj, pen=pc4, size=node_size, symbol=node_symbols, pxMode=False)

        self.win.addItem(darkness)
        self.win.addItem(daylight)
        self.win.addItem(noon_line)

        #Now Line
        if slider != "":
            """
            now_line = qtw.QGraphicsEllipseItem(-50, -50, 100, 100)  # x, y, width, height
            slider_i = round(np.interp(slider, [0, 100],[0, 360]))
            slider_i = max(slider_i-4,0)
            now_line.setStartAngle(slider_i*16+offset)
            now_line.setSpanAngle(4*16)
            now_line.setPen(pg.mkPen(pc3))
            now_line.setBrush(pg.mkBrush(self.soft_red))
            self.win.addItem(now_line)
            """

            slider = round(np.interp(slider, [0, 100],[0, 360]))
            slider = (slider+90)%360
            x,y = pol2cart(50,slider)#(rho, phi)
            now_line = pg.GraphItem()
            pos = np.array([[0,0],[x,y]]) # Define nodes
            adj = np.array([[0,1]]) # Define connections
            v1 = (self.soft_red[0], self.soft_red[1],
                  self.soft_red[2], opacity, graph_width)
            pc4 = np.array([v1],dtype=[('red',np.ubyte),
                                       ('green',np.ubyte),
                                       ('blue',np.ubyte),
                                       ('alpha',np.ubyte),
                                       ('width',float)])
            now_line.setData(pos=pos, adj=adj, pen=pc4, size=node_size,
                              symbol=node_symbols, pxMode=False)
            self.win.addItem(now_line)

        #(40,44,52), (48,48,48), (30, 30, 30)
        self.win.setBackground((40,44,52,0))
        self.win.hideAxis('left')
        self.win.hideAxis('bottom')

class QuickVericalBar(qtw.QWidget):

    def __init__(self, *args, title="", palette=0, double=True,
                short_bars=False,**kwargs):
        super().__init__(*args, **kwargs)
        #double=2bars, else 1bar
        #Short bars=slider effect.

        self.win = pg.PlotWidget()

        self.title = qtw.QLabel(title, self)
        self.title.setFont(system_font)
        self.title.setStyleSheet(metric_style)
        self.title.setAlignment(qtc.Qt.AlignCenter)
        
        self.soft_yellow = colors_pg['soft_yellow']
        self.dark_gray = colors_pg['dark_gray']
        self.soft_red = colors_pg["soft_red"]
        self.light_blue = colors_pg["light_blue"]
        self.soft_blue = colors_pg["soft_blue"]
        self.purple = colors_pg["purple"]
        self.green = colors_pg["green"]
        self.magenta = colors_pg["magenta"]
        self.yellow = colors_pg["yellow"]
        self.white = colors_pg["white"]

        if palette == 0:
            self.bc_1 = self.magenta
            self.bc_2 = self.yellow

        elif palette == 1:
            self.bc_1 = self.purple
            self.bc_2 = self.soft_blue

        self.double = double
        self.short_bars = short_bars
        self.y_min, self.y_max = 0, 100

        if self.double:
            dummy = [25,75]
            dummy_label = ["Last","Next"]
            self.add_value(dummy[0],dummy[1],dummy_label)
        
        if not self.double:
            dummy = 50
            dummy_label = "Initializing"
            self.add_value(dummy,dummy_label)

        self.win.setAspectLocked(lock=True, ratio=1)
        #self.win.setRange(rect=qtc.QRectF(-75,0,150,100))
        self.plot_layout = qtw.QVBoxLayout()
        self.plot_layout.addWidget(self.win)
        self.plot_layout.addWidget(self.title)

        self.groupbox = qtw.QGroupBox()
        self.groupbox.setLayout(self.plot_layout)
        self.groupbox.setFont(custom_font2)
        self.groupbox.setStyleSheet(borderless_style)

    def add_value(self, input_1, input_2="", labels="",title=""):

        #Zero will show no bar, however we want a little bar
        #so we set a min.
        min_val, max_val = 5,100
        input_1 = max(min(input_1,max_val),min_val)
        input_2 = max(min(input_2,max_val),min_val)
        title = title
        
        self.win.clear()

        if title != "":
            self.title.setText(title)

        #example input:
        #input_1 = [min,max]
        opacity = 255

        """
        horz_height = 1
        horz_width = 150
        horz_col = (self.dark_gray[0], self.dark_gray[1],
                    self.dark_gray[2], 50)
        x1,y1 = (horz_width*0.5)*-1, 0
        width,height = horz_width, horz_height
        horz_bar = RectItem(qtc.QRectF(x1, y1, width, height),color=horz_col)
        self.win.addItem(horz_bar)
        """

#////// Bar Draw ////////////////////////////////////////////////////////////#
        if not self.double:
            offset = 10
            bar_w = 10
            bar1_col = (self.bc_1[0], self.bc_1[1],
                        self.bc_1[2], opacity)
            x1,y1 = (offset*-1)+(bar_w*0.5), 0
            height, width = input_1,(offset*-1)-(bar_w*0.5)
            bar1 = RectItem(qtc.QRectF(x1, y1, width, height),color=bar1_col)
            #rect_item = RectItem(qtc.QRectF(0, 0, 4.5, 4.5))
            self.win.addItem(bar1)

        if self.double:
            offset = 0.5
            bar_w = 10

            bar1_col = (self.bc_1[0], self.bc_1[1],
                        self.bc_1[2], opacity)
            bar1_mid = (offset+(bar_w*0.5))*-1
            x1,y1 = -1*(bar_w*0.5)+bar1_mid, 0
            width,height = bar_w, input_1
            bar1 = RectItem(qtc.QRectF(x1, y1, width, height),color=bar1_col)
            self.win.addItem(bar1)

            bar2_col = (self.bc_2[0], self.bc_2[1],
                        self.bc_2[2], opacity)
            bar2_mid = (offset+(bar_w*0.5))
            x1,y1 = -1*(bar_w*0.5)+bar2_mid, 0
            width,height = bar_w, input_2
            bar2 = RectItem(qtc.QRectF(x1, y1, width, height),color=bar2_col)
            self.win.addItem(bar2)

        ## Labels
        if ((labels!="") and not self.double):
            # top = -0.5, bottom = -9
            y_1 = round(np.interp(input_1, [0, 100],[0.28, 9]),1)
            #rotateAxis=(0, 1), angle=0
            label_1 = pg.TextItem(text=labels[0], color=self.white, html=None, anchor=((1.2,y_1)),#(-1.6,x_1)
                                  border=None, fill=None, angle=-90, rotateAxis=(0, 1))
            label_1.setFont(system_font)
            label_1.setParentItem(bar1)

        elif ((labels!="") and self.double):
            # top = -0.5, bottom = -9
            y_1 = round(np.interp(input_1, [0, 100],[0.28, 9]),1)
            #rotateAxis=(0, 1), angle=0
            label_1 = pg.TextItem(text=labels[0], color=self.white, html=None, anchor=((1.25,y_1)),#(-1.6,x_1)
                                  border=None, fill=None, angle=-90, rotateAxis=(0, 1))
            label_1.setFont(system_font)
            #label_1.setTextWidth(len(labels[0]))
            label_1.setPos(0, 0)
            label_1.setParentItem(bar1)
            
            y_2 = round(np.interp(input_2, [0, 100],[0.28, 9]),1)
            #rotateAxis=(0, 1), angle=0
            label_2 = pg.TextItem(text=labels[1], color=self.white, html=None, anchor=((-0.3,y_2)),#(-1.6,x_1)
                                  border=None, fill=None, angle=-90, rotateAxis=(0, 1))
            label_2.setFont(system_font)
            label_2.setPos(0, 0)
            #label_2.setParentItem(bar2)
            label_2.setParentItem(bar2)

#////// Bagckground Vert Draw ///////////////////////////////////////////////#
        vert_height = 100
        vert_width = 1
        vert_col = (self.dark_gray[0], self.dark_gray[1],
                    self.dark_gray[2], opacity)
        x1,y1 = (vert_width*0.5)*-1, 0
        width,height = vert_width, vert_height
        vert_bar = RectItem(qtc.QRectF(x1, y1, width, height),color=vert_col)
        self.win.addItem(vert_bar)

#////// Tick Vert Draw //////////////////////////////////////////////////////#
        for tick in range(11):
            offset = 0
            tick_height = 1
            tick_width = 16
            if tick%2 !=0:
                #evens are smaller bars
                tick_width*=0.5
            if (tick==0 or tick==10):
                #evens are smaller bars
                tick_width*=1.5
                tick_height = 2
            tick*=10 #scale to 100
            tick_col = (self.dark_gray[0], self.dark_gray[1],
                        self.dark_gray[2], opacity)
            x1,y1 = (tick_width*0.5)*-1, tick-tick_height*0.5
            width,height = tick_width, tick_height
            tick_bar = RectItem(qtc.QRectF(x1, y1, width, height),color=tick_col)
            self.win.addItem(tick_bar)

        #(40,44,52), (48,48,48), (30, 30, 30)
        self.win.setBackground((40,44,52,0))
        #self.win.getPlotItem().getAxis('left').setWidth(80)
        self.win.hideAxis('left')
        self.win.hideAxis('bottom')
        return

#Use to draw rectangles.
class RectItem(pg.GraphicsObject):
    def __init__(self, rect, parent=None,color=""):
        # rect = qtc.QRectF(x, y, width, height)
        super().__init__(parent)
        self._rect = rect
        self.picture = qtg.QPicture()
        self.color = color
        if self.color == "":
            self.color = colors_pg["white"]
        self._generate_picture()

    @property
    def rect(self):
        return self._rect

    def _generate_picture(self):
        painter = qtg.QPainter(self.picture)
        painter.setPen(pg.mkPen(self.color))
        painter.setBrush(pg.mkBrush(self.color))
        painter.drawRect(self.rect)
        painter.end()

    def paint(self, painter, option, widget=None):
        painter.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return qtc.QRectF(self.picture.boundingRect())

#//// Loading Bar Widgets //////////////////////////////////////////////////#
class SensorWidget():
    def __init__(self,sensor_num, sensor_labels):

        #initialize styles.
        self.styles()
        self.threshold_percent = 20 #val below this triggers warn color.
        self.raw_wet, self.raw_dry = 600, 1028 #Floor and ceiling
        self.timecheck = ""

        rawVal = 0
        pbarVal = min(max(rawVal, self.raw_wet),self.raw_dry) #bounds
        pbarVal = round(np.interp(rawVal,
                                    [self.raw_wet, self.raw_dry],
                                    [100, 0]))

        self.pbar = qtw.QProgressBar()
        self.pbar.setFont(system_font)
        if int(pbarVal) >= 50:
            self.pbar.setStyleSheet(self.pbar_style_full)
        elif int(pbarVal) <= self.threshold_percent:
            self.pbar.setStyleSheet(self.pbar_style_low)
        elif int(pbarVal) < 50:
            self.pbar.setStyleSheet(self.pbar_style_middle)
        self.pbar.setValue(pbarVal)

        #Labels
        self.s_label = qtw.QLabel(f"S{sensor_num}")
        self.s_label.setAlignment(qtc.Qt.AlignVCenter) #AlignVCenter
        self.s_label.setFont(subtitle_font)
        self.s_label.setStyleSheet(self.sensor_style)
        s_label_grid = qtw.QGridLayout()
        s_label_grid.addWidget(self.s_label)
        self.s_label_groupbox = qtw.QGroupBox()
        self.s_label_groupbox.setLayout(s_label_grid)
        self.s_label_groupbox.setStyleSheet(self.sensor_style)
        s_label_gb = self.s_label_groupbox

        self.raw = qtw.QLabel(f"Raw: {rawVal}")
        self.raw.setFont(mini_font)
        self.raw.setAlignment(qtc.Qt.AlignCenter)
        self.raw.setStyleSheet(self.raw_style)
        
        self.sublabel = qtw.QLabel("Timestamp: -")
        self.sublabel.setFont(mini_font)
        self.sublabel.setStyleSheet(self.avg_style)

        self.common_name = sensor_labels[sensor_num]["Name"]
        plant = qtw.QLabel(self.common_name)
        plant.setFont(subtitle_font)       
        plant.setStyleSheet(self.plant_style)

        latin_name = sensor_labels[sensor_num]["Taxon"]
        planttaxon = qtw.QLabel("-"+latin_name) #space for aesthetic
        planttaxon.setFont(eight_bit_italic)
        planttaxon.setStyleSheet(self.taxon_style)

        gridsensor = qtw.QGridLayout()
        gridsensor.addWidget(self.pbar,    1,0,1,8)
        gridsensor.addWidget(self.raw,     2,7)
        gridsensor.addWidget(self.sublabel,2,0)
        gridsensor.addWidget(plant,        3,0,1,8)
        gridsensor.addWidget(s_label_gb,   3,7,2,1)
        gridsensor.addWidget(planttaxon,   4,0,1,8)
        
        self.sub_groupbox = qtw.QGroupBox()
        self.sub_groupbox.setLayout(gridsensor)
        self.sub_groupbox.setFont(self.custom_font2)
        self.sub_groupbox.setStyleSheet(self.subbox_style)

    def update_sensor(self, sensor_num, sensor_vals):

        ##[source, sensor, raw_val, timestamp,
        #  [time_string, stale_bool]]
        sensor_entry = sensor_vals[sensor_num-1]
        #print(sensor_entry)
        rawVal = sensor_entry[2]
        time_string = sensor_entry[4][0]
        stale = sensor_entry[4][1]

        self.raw.setText(f"Raw: {rawVal}")
        pbarVal = min(max(rawVal, self.raw_wet),self.raw_dry) #bounds
        pbarVal = round(np.interp(pbarVal,
                                  [self.raw_wet, self.raw_dry],
                                  [100, 0]))
        
        self.pbar.setValue(pbarVal)
        self.sublabel.setText(f"Timestamp: {time_string}")

        if not stale:
            self.s_label.setStyleSheet(self.sensor_style)
            self.s_label_groupbox.setStyleSheet(self.sensor_style)

        elif stale and self.common_name!="Available":
            self.s_label.setStyleSheet(self.warning_style)
            self.s_label_groupbox.setStyleSheet(self.warning_style)

        if int(pbarVal) >= 50:
            self.pbar.setStyleSheet(self.pbar_style_full)
        elif int(pbarVal) <= self.threshold_percent:
            self.pbar.setStyleSheet(self.pbar_style_low)
        elif int(pbarVal) < 50:
            self.pbar.setStyleSheet(self.pbar_style_middle)

        #self.pbar.repaint()
        return

    def styles(self):
        #Set up the styles
        self.win1_font = qtg.QFont('Arial', 12)
        self.title_font= qtg.QFont('Trebuchet MS', 30)
        self.subtitle_font= qtg.QFont('Trebuchet MS', 18)
        self.metric_font = qtg.QFont('Trebuchet MS', 12)
        self.click_font = qtg.QFont('Trebuchet MS', 20)
        self.metric_font.setItalic(1)
        self.custom_font1 = qtg.QFont('Trebuchet MS', 20)
        self.custom_font2 = qtg.QFont('Trebuchet MS', 16)
        self.custom_font2.setItalic(1)
        self.custom_font3 = qtg.QFont('Trebuchet MS', 16)
        self.mini_style = qtg.QFont('Trebuchet MS', 12)
        self.mini_style.setItalic(1)

        self.metric_style = """
            color: rgb(255,255,255);
            border-width : 0px;
            border-style: none;
        """
        self.box_style = """
        QGroupBox {
            border :3px solid black;
            border-color: rgb(255,255,255);
            color: rgb(209,154,102);
            border-radius: 8px;
            border-width : 4px;
            }
        """
        self.subbox_style = """
        QGroupBox {
            color: rgb(209,154,102);
            border-width : 0px;
            }
        """
        self.pbar_style_low = """
        QProgressBar{
            border: 4px solid grey;
            border-radius: 5px;
            border-color: rgb(152,195,121);
            color: rgb(152,195,121);
            text-align: center
        }
        QProgressBar::chunk {
            background-color: rgb(255,166,0;
            width: 10px;
        }
        """
        self.pbar_style_full = """
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
        self.pbar_style_middle= """
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

        self.sensor_style = """
        QLabel{
            background-color: rgb(209,154,102);
            color: rgb(40,44,52);
            border-radius: 0px;
            text-align: vcenter
        }
        QGroupBox {
            background-color: rgb(209,154,102);
            color: rgb(40,44,52);
            border-radius: 0px;
            text-align: vcenter
            }
        """
        self.warning_style = """
            background-color: rgb(255,15,15);
            color: rgb(40,44,52);
            border-radius: 0px;
            """

        self.raw_style = """
                border-color: rgb(152,195,121);
                color: rgb(152,195,121);
                border-width : 0px;
                border-style:inset;
                """
        self.avg_style = """
                border-color: rgb(152,195,121);
                color: rgb(152,195,121);
                border-width : 0px;
                border-style:inset;
                """
        self.plant_style = """
            border-color: rgb(40,44,52);
            color: white;
            border-width : 0px;
            border-style:inset;
            """
        self.taxon_style = """
            border-color: rgb(40,44,52);
            color: rgb(80,167,239);
            border-width : 0px;
            border-style:inset;
            """

class SimpleBarWidget():
    def __init__(self, title="", min_x=0, max_x=100, threshold=20):
        #initialize styles.
        self.styles()
        self.threshold_percent = threshold #val below this triggers warn color.
        self.min_x, self.max_x  = min_x, max_x #Floor and ceiling

        rawVal = 0
        pbarVal = min(max(rawVal, self.min_x),self.max_x) #bounds
        pbarVal = round(np.interp(pbarVal,
                                    [self.min_x, self.max_x],
                                    [0,100]))

        #self.pbar = qtw.QProgressBar(self)
        self.pbar_1 = qtw.QProgressBar()
        self.pbar_1.setFont(system_font)

        #Labels
        if title != "":
            self.title = qtw.QLabel(title)
            self.title.setAlignment(qtc.Qt.AlignCenter)
            self.title.setFont(system_font)       
            self.title.setStyleSheet(self.plant_style)

            gridsensor = qtw.QGridLayout()
            gridsensor.addWidget(self.title,0,0,1,2)
            gridsensor.addWidget(self.pbar_1,1,0,1,2)
        elif title == "":  
            gridsensor = qtw.QGridLayout()
            gridsensor.addWidget(self.pbar_1,0,0,1,2)

        self.sub_groupbox = qtw.QGroupBox()
        self.sub_groupbox.setLayout(gridsensor)
        self.sub_groupbox.setFont(self.custom_font2)
        self.sub_groupbox.setStyleSheet(self.subbox_style)

        self.update_bar(pbarVal)

    def update_bar(self, val):
        pbarVal = min(max(val, self.min_x),self.max_x) #bounds
        pbarVal = round(np.interp(pbarVal,
                                    [self.min_x, self.max_x],
                                    [0,100]))
        self.pbar_1.setValue(pbarVal)

        if int(pbarVal) >= 50:
            self.pbar_1.setStyleSheet(self.pbar_style_full)
        elif int(pbarVal) <= self.threshold_percent:
            self.pbar_1.setStyleSheet(self.pbar_style_low)
        elif int(pbarVal) < 50:
            self.pbar_1.setStyleSheet(self.pbar_style_middle)
        #self.pbar.repaint()
        return

    def styles(self):
        #Set up the styles
        self.win1_font = qtg.QFont('Arial', 12)
        self.title_font= qtg.QFont('Trebuchet MS', 30)
        self.subtitle_font= qtg.QFont('Trebuchet MS', 16)
        self.metric_font = qtg.QFont('Trebuchet MS', 12)
        self.click_font = qtg.QFont('Trebuchet MS', 20)
        self.metric_font.setItalic(1)
        self.custom_font1 = qtg.QFont('Trebuchet MS', 22)
        self.custom_font2 = qtg.QFont('Trebuchet MS', 16)
        self.custom_font2.setItalic(1)
        self.custom_font3 = qtg.QFont('Trebuchet MS', 16)
        self.mini_style = qtg.QFont('Trebuchet MS', 12)
        self.mini_style.setItalic(1)

        self.metric_style = """
            color: rgb(255,255,255);
            border-width : 0px;
            border-style: none;
            text-align: left;
        """
        self.box_style = """
        QGroupBox {
            border :3px solid black;
            border-color: rgb(255,255,255);
            color: rgb(209,154,102);
            border-radius: 8px;
            border-width : 4px;
            }
        """
        self.subbox_style = """
        QGroupBox {
            color: rgb(209,154,102);
            border-style: none;
            border-width : 0px;
            }
        """
        
        self.pbar_style_full = """
        QProgressBar{
            border: 4px solid grey;
            border-radius: 5px;
            border-color: rgb(51,153,214);
            color: rgb(40,44,52);
            text-align: center
        }
        QProgressBar::chunk {
            background-color: rgb(51,153,214);
            width: 10px;
        }
        """
        self.pbar_style_middle= """
        QProgressBar{
            border: 4px solid grey;
            border-radius: 5px;
            border-color: rgb(51,153,214);
            color: rgb(51,153,214);
            text-align: center
        }
        QProgressBar::chunk {
            background-color: rgb(51,153,214);
            width: 10px;
        }
        """
        self.pbar_style_low= """
        QProgressBar{
            border: 4px solid grey;
            border-radius: 5px;
            border-color: rgb(51,153,214);
            color: rgb(51,153,214);
            text-align: center
        }
        QProgressBar::chunk {
            background-color: rgb(51,153,214);
            width: 10px;
        }
        """
        
        self.sensor_style = """
            border :8px solid black;
            border-color: rgb(40,44,52);
            background-color: rgb(209,154,102);
            color: rgb(40,44,52);
            border-radius: 12px;
            """
        self.raw_style = """
                border-color: rgb(152,195,121);
                color: rgb(152,195,121);
                border-width : 0px;
                border-style:inset;
                """
        self.avg_style = """
                border-color: rgb(152,195,121);
                color: rgb(152,195,121);
                border-width : 0px;
                border-style:inset;
                """
        self.plant_style = """
            border-color: rgb(40,44,52);
            color: white;
            border-width : 0px;
            border-style:inset;
            """
        self.taxon_style = """
            border-color: rgb(40,44,52);
            color: rgb(80,167,239);
            border-width : 0px;
            border-style:inset;
            """

#//// Other Widgets /////////////////////////////////////////////////////////#
class Seven_Segment(qtw.QWidget):
    #https://doc.qt.io/qt-5/qlcdnumber.html

    """ Seven Segment Display using QLCDNumber
    """

    def __init__(self, *args,**kwargs):
        super().__init__(*args, **kwargs)
        
        color = colors_pg['green']

        self.lcd = qtg.QLCDNumber(self)
        self.lcd.setSegmentStyle(2)#Outline, Filled, Flat
        
        #generate the style sheet.
        v1 = "QLCDNumber{ color: rgb"
        v2 = "; border-width : 0px;}"
        lcd_style = v1+str(color)+v2
        
        self.lcd.setStyleSheet(lcd_style)

        v1="--:--"
        self.add_value(v1)

        self.plot_layout = qtw.QVBoxLayout()
        #self.plot_layout.addWidget(toolbar)
        self.plot_layout.addWidget(self.lcd)

        self.groupbox = qtw.QGroupBox()
        self.groupbox.setLayout(self.plot_layout)
        self.groupbox.setStyleSheet(borderless_style)

    def add_value(self, val):
        self.lcd.setDigitCount(len(str(val)))
        self.lcd.display(val)

#///////STYLE SETTINGS//////////////////////////////////////////////////////#
colors_pg = {'white': (255, 255, 255),
          'yellow': (255, 240, 31),
          'soft_yellow': (230, 217, 122),
          'orange': (255, 166, 0),
          'purple': (102, 0, 204),
          'magenta': (255, 102, 255),
          'pink': (255, 15, 240),
          'black': (0, 0, 0),
          'soft_red': (214, 51, 79),
          'red': (255, 0, 0),
          'green': (0, 255, 0),
          'soft_green':(152,195,121),
          'soft_blue': (51, 153, 214),
          'blue': (0, 0, 255),
          'light_blue': (0, 235, 212),
          'grid_color': (76, 76, 76),
          'light_gray': (153, 153, 153),
          'gray': (128, 128, 128),
          'dark_gray': (102, 102, 102)}
colors_mpl = {} #in decimal format vs RGB
for key, item in colors_pg.items():
    v1 = [round(n/255,2) for n in item]
    v2 = (v1[0],v1[1],v1[2])
    colors_mpl[key] = v2

#//// Load Fonts ////////////////////////////////////////////////////////////#
"""  LOAD FONTS
Linux does not support loading fonts locally.
https://raspberrytips.com/install-fonts-raspberry-pi/

cd ~/Downloads/
cp *.otf ~/.fonts/
cp *.ttf ~/.fonts/
fc-cache -v -f

if platform.system() == "Windows":
    dir_list = []
    dir_list.append(r'Resources\Fonts\lcd_font_1.ttf')#'DSEG14 Classic'
    dir_list.append(r'Resources\Fonts\lcd_font_2.ttf')#'Seven Segment'
    dir_list.append(r'Resources\Fonts\PennStation.ttf')#'Penn Station'
    dir_list.append(r'Resources\Fonts\8bitOperator.ttf')#'8-bit Operator+ 8'

    for dir in dir_list:
        qtg.QFontDatabase.addApplicationFont(dir)

"""

#for matplotlib
cwd = os.getcwd()
font_path = cwd+"/Resources/Fonts"
import matplotlib.font_manager as font_manager

font_dir = [font_path]
for font in font_manager.findSystemFonts(font_dir):
    font_manager.fontManager.addfont(font)

win1_font = qtg.QFont('Arial', 12)
metric_font = qtg.QFont('Trebuchet MS', 12)
click_font = qtg.QFont('Trebuchet MS', 20)
metric_font.setItalic(1)
metric_title_font= qtg.QFont('Trebuchet MS', 30)
custom_font1 = qtg.QFont('Trebuchet MS', 20)
custom_font2 = qtg.QFont('Trebuchet MS', 16)
custom_font2.setItalic(1)
custom_font3 = qtg.QFont('Trebuchet MS', 16)

#"""Custom loaded fonts.
lcd_font1_big = qtg.QFont('DSEG14 Classic', 24)
lcd_font1_small = qtg.QFont('DSEG14 Classic', 12)
lcd_font2 = qtg.QFont('Seven Segment', 16)
penn_font = qtg.QFont('Penn Station', 20)

eight_bit_mini_font = qtg.QFont('8-bit Operator+ 8', 12)
eight_bit_font = qtg.QFont('8-bit Operator+ 8', 20)
eight_bit_font_big = qtg.QFont('8-bit Operator+ 8', 22)
eight_bit_title_font= qtg.QFont('8-bit Operator+ 8', 40)
eight_bit_subtitle_font= qtg.QFont('8-bit Operator+ 8', 30)
eight_bit_italic= qtg.QFont('8-bit Operator+ 8', 18)
eight_bit_italic.setItalic(1)

#Main simple font used throughout the script.
system_font = eight_bit_font
title_font = eight_bit_title_font
subtitle_font = eight_bit_subtitle_font
mini_font = eight_bit_mini_font
mpl_font = '8-bit Operator+ 8'#'Trebuchet MS'
#"""

metric_style = """
    color: rgb(255,255,255);
    border-width : 0px;
    border-style: none;
    text-align: left;
"""
box_style = """
QGroupBox {
    border-color: rgb(255,255,255);
    color: rgb(209,154,102);
    border-radius: 4px;
    }
"""
borderless_style = """
QGroupBox {
    color: rgb(209,154,102);
    border-width : 0px;
    }
"""

def dec2int(triplet):
    #converts a decminal to rgb255 equiv.
    l3 = [round(n/255,2) for n in triplet]
    #l3 = [round(n*255) for n in triplet]
    output = (l3[0],l3[1],l3[2])
    return output

def cart2pol(x, y):
    """
    Interprets the x,y into degrees around the center.
    Note: less degrees means faster.
    y values are goofy in array notation.
    """
    phi = np.arctan2(y, x)
    phi = math.degrees(phi) #phi is in raidans, we want degrees.
    if phi < 0:
        phi = 360-abs(phi)
    return phi #rho

def pol2cart(rho, phi):
    phi = round(np.interp(phi, [0, 360],[360, 0]))#gotta invert
    phi = math.radians(phi)#phi is in degrees, we want raidans.
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    x = round(x)
    y = round(y)
    return(x, y)

if __name__ == "__main__":
    print(dec2int((40,44,52)))