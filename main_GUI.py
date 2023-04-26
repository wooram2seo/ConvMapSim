#%%
import math
from function_Logic import * 
import matplotlib.pyplot as plt
import time
import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import *
import csv
import pandas as pd

import os
from PyQt5.QtCore import Qt
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis
import seaborn as sns
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget
from PyQt5.QtGui import QPainter
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt5.QtWidgets import QFileDialog

import pandas as pd
import seaborn as sns
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtGui import QPixmap
import pythoncom


im2Col_readCycle = 0 
sdk_readCycle = 0 
vwsdk_readCycle = 0
im2Col_CalculateTotalPower = 0
sdk_CalculateTotalPower = 0
vwsdk_CalculateTotalPower = 0

count_used_array = 0 

############################## GUI
form_class = uic.loadUiType("simulator_main.ui")[0]

global countHeatmap
countHeatmap = 0

class WindowClass(QMainWindow, form_class) :
    
    def __init__(self) :
        super().__init__()
        self.setupUi(self)                
        self.log = Log(self.textEdit_Log)
        self.log.Start()
        self.countSimulation = 0
        self.h_layout = QHBoxLayout()
        
        self.pushButton.clicked.connect(self.button1Function)
        self.pushButton_2.clicked.connect(self.button2Function)
        self.pushButton_3.clicked.connect(self.button3Function)
        
        self.radioButton_EnableDB.clicked.connect(self.RadioButton_EnableDB_Clicked)
        self.radioButton_DisableDB.clicked.connect(self.RadioButton_EnableDB_Clicked)
        
    ### UI function
    def RadioButton_EnableDB_Clicked(self):
        if self.radioButton_EnableDB.isChecked():
            readEnergy_SimDB, writeEnergy_SimDB, readLatency_SimDB, writeLatency_SimDB, MemoryDevice_SimDB = self.LoadData_SimulationDB(True)
            self.lineEdit_ReadEnergy.setText(str(readEnergy_SimDB))
            self.lineEdit_WriteEnergy.setText(str(writeEnergy_SimDB))
            self.lineEdit_ReadLatency.setText(str(readLatency_SimDB))
            self.lineEdit_WriteLatency.setText(str(writeLatency_SimDB))
            self.lineEdit_MemoryDevice.setText(MemoryDevice_SimDB)
        else:
            self.lineEdit_ReadEnergy.setText("0")
            self.lineEdit_WriteEnergy.setText("0")
            self.lineEdit_ReadLatency.setText("0")
            self.lineEdit_WriteLatency.setText("0")
            self.lineEdit_MemoryDevice.setText("SRAM")

    def LoadData_SimulationDB(self, checked):
        if checked:
            filename = 'SimulationDB.csv'
            if filename:
                global df_simulationDB
                df_simulationDB = pd.read_csv(filename, index_col = 0)
                self.create_table_widget(self.tableWidget_perCycle, df_simulationDB)            
                float_readEnergy_SimDB = float(df_simulationDB.loc['Value']['ReadEnergy'])
                float_writeEnergy_SimDB = float(df_simulationDB.loc['Value']['WriteEnergy'])
                float_readLatency_SimDB = float(df_simulationDB.loc['Value']['ReadLatency'])
                float_writeLatency_SimDB = float(df_simulationDB.loc['Value']['WriteLatency'])
                str_MemoryDevice = df_simulationDB.loc['Value']['Memory']

                readEnergy_SimDB_ = int(float_readEnergy_SimDB)
                writeEnergy_SimDB_ = int(float_writeEnergy_SimDB)
                readLatency_SimDB_ = int(float_readLatency_SimDB)
                writeLatency_SimDB_ = int(float_writeLatency_SimDB)


                return readEnergy_SimDB_, writeEnergy_SimDB_, readLatency_SimDB_, writeLatency_SimDB_, str_MemoryDevice
            else :
                QMessageBox.critical(self, 'Error', 'Please check SimulationDB.csv file to load data.', QMessageBox.Ok)

    def Init_Tables(self) :
        while self.tableWidget_TotalCycle.rowCount() > 0:
            self.tableWidget_TotalCycle.removeRow(0)        
        while self.tableWidget_perCycle.rowCount() > 0:
            self.tableWidget_perCycle.removeRow(0)

    def Save_option_csv(self, readEnergy_, writeEnergy_, readLatency_, writeLatency_, memoryDevice_):
        data = {'' : ['Value', 'Unit'],
                'ReadEnergy' : [readEnergy_, 'pJ'],
                'WriteEnergy' : [writeEnergy_, 'pJ'],
                'ReadLatency' : [readLatency_, 'ns'], 
                'WriteLatency' : [writeLatency_, 'ns'], 
                'Memory' : [memoryDevice_, 'Memory']
        }
        df = pd.DataFrame(data)

        file_name = 'SimulationDB_User.csv'
        # if file_name:
        df.to_csv(file_name, index=False)

    def button1Function(self) :
        self.Init_Tables()
        self.log.Running("Simulation")

        # Get input data
        global image
        global kernel
        global ic
        global oc
        global ar
        global ac
        global method
    
        image = int(self.lineEdit.text())
        kernel = int(self.lineEdit_2.text())
        ic = int(self.lineEdit_3.text())
        oc = int(self.lineEdit_4.text())
        ar = int(self.lineEdit_5.text())
        ac = int(self.lineEdit_6.text())
        method = self.lineEdit_7.text()
        
        # print log : input data information
        contents = Print_input_data(ar, ac, image, kernel, ic, oc)
        self.log.LogPrint(contents)      
        
        global readEnergy_SimDB
        global writeEnergy_SimDB
        global readLatency_SimDB
        global writeLatency_SimDB
        global Memory_SimDB

        if self.radioButton_DisableDB.isChecked():
            if self.lineEdit_ReadEnergy.text() == '' or self.lineEdit_WriteEnergy.text() == '' or self.lineEdit_ReadLatency.text() == '' or self.lineEdit_WriteLatency.text() == ''  :
                QMessageBox.critical(self, 'Error', 'Please fill all of data if you checked "Disable DB".', QMessageBox.Ok)
                self.lineEdit_ReadEnergy.setText(str(0))
                self.lineEdit_WriteEnergy.setText(str(0))
                self.lineEdit_ReadLatency.setText(str(0))
                self.lineEdit_WriteLatency.setText(str(0))
                self.lineEdit_MemoryDevice.setText("SRAM")
            else :
                readEnergy_SimDB = float(self.lineEdit_ReadEnergy.text())
                writeEnergy_SimDB = float(self.lineEdit_WriteEnergy.text())
                readLatency_SimDB = float(self.lineEdit_ReadLatency.text())
                writeLatency_SimDB = float(self.lineEdit_WriteLatency.text())
                Memory_SimDB = self.lineEdit_MemoryDevice.text()
                self.Save_option_csv(readEnergy_SimDB, writeEnergy_SimDB, readLatency_SimDB, writeLatency_SimDB, Memory_SimDB)

                filename = 'SimulationDB_User.csv'
                if filename:
                    df_SimulationDB_User = pd.read_csv(filename, index_col = 0)
                    self.create_table_widget(self.tableWidget_perCycle, df_SimulationDB_User)

        else :
            readEnergy_SimDB, writeEnergy_SimDB, readLatency_SimDB, writeLatency_SimDB, Memory_SimDB = self.LoadData_SimulationDB(True)
            self.lineEdit_ReadEnergy.setText(str(readEnergy_SimDB))
            self.lineEdit_WriteEnergy.setText(str(writeEnergy_SimDB))
            self.lineEdit_ReadLatency.setText(str(readLatency_SimDB))
            self.lineEdit_WriteLatency.setText(str(writeLatency_SimDB))
            self.lineEdit_MemoryDevice.setText(Memory_SimDB)


        ######### Calculate power        
        # output Read Cycle, Write Cycle, Windows_row, Windows_col, AR Cycle, AC Cycle, 
        ## get read, write cycle (image, image, kernel, kernel, IC, OC, array_row, array_col)
        # image, kernel, ic, oc, ar, ac, method

        # im2col
        im2Col_readCycle_old, im2col_writeCycle, im2col_slide_Window_row, im2col_slide_Window_col, im2col_AR_cycle, im2col_AC_cycle = Get_ReadCycle_WriteCycle_im2col(image, image, kernel, kernel, ic, oc, ar, ac)
        im2Col_windows = im2col_slide_Window_row * im2col_slide_Window_col ###
        im2Col_readCycle, i_c, o_c = im2col(image, image, kernel, kernel, ic, oc, ar, ac)
        im2col_totalCycle = im2Col_readCycle + im2col_writeCycle

        # sdk
        sdk_readCycle_old, sdk_writeCycle, sdk_parallel_window_row, sdk_parallel_Window_col, sdk_AR_Cycle, sdk_AC_Cycle = Get_ReadCycle_WriteCycle_SDK(image, image, kernel, kernel, ic, oc, ar, ac)
        sdk_windows = sdk_parallel_window_row * sdk_parallel_Window_col ###
        sdk_readCycle_arr, pw = SDK(image, image, kernel, kernel, ic, oc, ar, ac)
        sdk_readCycle = sdk_readCycle_arr[0]
        sdk_totalCycle = sdk_readCycle + sdk_writeCycle

        # vw-sdk
        vwsdk_readCycle_old, vwsdk_writeCycle, vwsdk_parallel_Window_row, vwsdk_parallel_Window_col, vwsdk_AR_Cycle, vwsdk_AC_Cycle = Get_readCycle_WriteCycle_VWSDK(image, image, kernel, kernel, ic, oc, ar, ac)
        vwsdk_windows = vwsdk_parallel_Window_row * vwsdk_parallel_Window_col ###
        vwsdk_readCycle, VWSDK_h, VWSDK_w, ARC, ACC, tiled_IC, tiled_OC = vw_sdk(image, image, kernel, kernel, ic, oc, ar, ac)
        wvsdk_totalCycle = vwsdk_readCycle + vwsdk_writeCycle

        # readEnergy * readCycle + writeEnergy * writeCycle
        im2Col_CalculateTotalPower = readEnergy_SimDB * im2Col_readCycle + writeEnergy_SimDB * im2col_writeCycle 
        sdk_CalculateTotalPower = readEnergy_SimDB * sdk_readCycle + writeEnergy_SimDB * sdk_writeCycle
        vwsdk_CalculateTotalPower = readEnergy_SimDB * vwsdk_readCycle + writeEnergy_SimDB * vwsdk_writeCycle
        
        im2Col_CalculateTotalLatency = readLatency_SimDB * im2Col_readCycle + writeLatency_SimDB * im2col_writeCycle 
        sdk_CalculateTotalLatency = readLatency_SimDB * sdk_readCycle + writeLatency_SimDB * sdk_writeCycle
        vwsdk_CalculateTotalLatency = readLatency_SimDB * vwsdk_readCycle + writeLatency_SimDB * vwsdk_writeCycle
        
        # # generate calculationDB :  
        self.Generate_Schema_CalculationDB('', 'Total Cycle', 'Read Cycle', 'Write Cycle', 'Total Energy(pJ)', 'Total Latency(ns)', 'Windows', 'AR Cycle', 'AC Cycle', 'Read Energy', 'Write Energy', 'Read Latency', 'Write Latency', 'Memory')
        self.CalculationDB_Add_Row('im2col', im2col_totalCycle, im2Col_readCycle, int(im2col_writeCycle), im2Col_CalculateTotalPower, im2Col_CalculateTotalLatency, im2Col_windows, im2col_AR_cycle, im2col_AC_cycle, readEnergy_SimDB, writeEnergy_SimDB, readLatency_SimDB, writeLatency_SimDB, Memory_SimDB)
        self.CalculationDB_Add_Row('SDK', sdk_totalCycle, sdk_readCycle, int(sdk_writeCycle), sdk_CalculateTotalPower, sdk_CalculateTotalLatency, sdk_windows, sdk_AR_Cycle, sdk_AC_Cycle, readEnergy_SimDB, writeEnergy_SimDB, readLatency_SimDB, writeLatency_SimDB, Memory_SimDB)
        self.CalculationDB_Add_Row('VW-SDK', wvsdk_totalCycle, vwsdk_readCycle, int(vwsdk_writeCycle), vwsdk_CalculateTotalPower, vwsdk_CalculateTotalLatency, vwsdk_windows, vwsdk_AR_Cycle, vwsdk_AC_Cycle, readEnergy_SimDB, writeEnergy_SimDB, readLatency_SimDB, writeLatency_SimDB, Memory_SimDB)
        ###############

        # load csv CalculationDB
        filename = 'CalculationDB.csv'
        if filename:
            global df_CalculationDB
            df_CalculationDB = pd.read_csv(filename, index_col = 0)
            self.create_table_widget(self.tableWidget_TotalCycle, df_CalculationDB)
        
######################### Chart
        # # init : Remove all existing charts from the widget
        if self.countSimulation > 0 :
            for i in reversed(range(self.widget_Chart.layout().count())):
                self.widget_Chart.layout().itemAt(i).widget().setParent(None)

        df = df_CalculationDB                
        widget = self.widget_Chart
        
        # # Create a horizontal layout to hold the chart views
        countColumn = 0 ###
        for column in df.columns: 
            countColumn = countColumn + 1 ###
            if(countColumn > 5) : break ###
            else :
                # Create the bar chart
                chart = QChart()
                chart.setTitle(f"{column}")
                # Create the series for the chart
                series = QBarSeries()
                for i in range(len(df)):
                    if i == 0:
                        column_set1 = QBarSet(df.index[i])
                        column_set1.append(df.iloc[i][column])
                        column_set1.setColor(QColor('#58FA58'))
                        series.append(column_set1)
                    elif i == 1:
                        column_set2 = QBarSet(df.index[i])
                        column_set2.append(df.iloc[i][column])
                        column_set2.setColor(QColor('#2E64FE'))
                        series.append(column_set2)
                    elif i == 2:
                        column_set3 = QBarSet(df.index[i])
                        column_set3.append(df.iloc[i][column])
                        column_set3.setColor(QColor('#FF0040'))
                        series.append(column_set3)                
            chart.addSeries(series)

            axis = QBarCategoryAxis()
            axis.append('')
            chart.legend().setAlignment(Qt.AlignBottom)#
            chart.setTheme(QChart.ChartThemeLight)# 
            chart.createDefaultAxes()
            chart.setAxisX(axis, series)

            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)

            self.h_layout.addWidget(chart_view)

        widget.setLayout(self.h_layout)
###############################

        # load output image
        qPixmapVar = QPixmap() 
        qPixmapVar.load("output.png")

        self.countSimulation = self.countSimulation + 1
        self.log.Complete("Simulation")

    def button2Function(self) :          
        self.log.Running("Weight mapping heatmap visualization")        
        self.log.LogPrint("It takes time to display. please wait...")
        pythoncom.PumpWaitingMessages()

########################################################### heatmap
        
        heatmap = Heatmap_QLabel(self.label_QPixmap)

###########################################################

        df = df_CalculationDB

        widget = QWidget()        
        widget.setWindowTitle("Simulation result")
        widget.setMinimumSize(1600, 400)

        h_layout = QHBoxLayout()

        countColumn = 0 ###
        for column in df.columns: 
            countColumn = countColumn + 1 ###
            if(countColumn > 5) : break ###
            else :
                chart = QChart()
                chart.setTitle(f"{column}")

                series = QBarSeries()
                for i in range(len(df)):                
                    if i == 0:
                        column_set1 = QBarSet(df.index[i])
                        column_set1.append(df.iloc[i][column])
                        column_set1.setColor(QColor('#58FA58'))
                        series.append(column_set1)
                    elif i == 1:
                        column_set2 = QBarSet(df.index[i])
                        column_set2.append(df.iloc[i][column])
                        column_set2.setColor(QColor('#2E64FE'))
                        series.append(column_set2)
                    elif i == 2:
                        column_set3 = QBarSet(df.index[i])
                        column_set3.append(df.iloc[i][column])
                        column_set3.setColor(QColor('#FF0040'))
                        series.append(column_set3)
                    
            chart.addSeries(series)

            axis = QBarCategoryAxis()
            axis.append('')
            chart.legend().setAlignment(Qt.AlignBottom)#
            chart.setTheme(QChart.ChartThemeLight)# 
            chart.createDefaultAxes()
            chart.setAxisX(axis, series)

            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)

            h_layout.addWidget(chart_view)

        widget.setLayout(h_layout)
        widget.show()

        # heatmap
        count_used_array = result_vw(image, kernel, ic, oc, ar, ac, method)
        self.log.LogPrint("Check out the png file for the Weight Mapping Heatmap.")
        self.log.Complete("visualization")
        pythoncom.PumpWaitingMessages()

        
    def button3Function(self) :
    # save dataframe as csv file, to export simulation result to excel file
        df = df_CalculationDB
        df.insert(0, 'Method', ['im2col', 'SDK', 'VW-SDK'])
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(options=options, filter="CSV Files (*.csv)")
        if file_name:
            df.to_csv(file_name, index=False)


    def Get_Value_SimulationDB(self, dataframe_) : 
        readEnergy_SimDB = dataframe_.loc['Value']['ReadEnergy']
        writeEnergy_SimDB = dataframe_.loc['Value']['WriteEnergy']
        readLatency_SimDB = dataframe_.loc['Value']['ReadLatency']
        writeLatency_SimDB = dataframe_.loc['Value']['Write Latency']
        MemoryDevice_SimDB = dataframe_.loc['Value']['Memory']

    def create_table_widget(self, widget, df):
        widget.setRowCount(len(df.index))
        widget.setColumnCount(len(df.columns))
        widget.setHorizontalHeaderLabels(df.columns)
        widget.setVerticalHeaderLabels(df.index)

        for row_index, row in enumerate(df.index):
            for col_index, column in enumerate(df.columns):
                value = df.loc[row][column]
                item = QTableWidgetItem(str(value))
                widget.setItem(row_index, col_index, item)
        
        
    # calculation_DB generation (write csv file)
    def Generate_Schema_CalculationDB(self, method_, totalCycle_, readCycle_, writeCycle_, totalEnergy_, totalLatency_, windows_, arCycle_, acCycle_, readEnergy_, writeEnergy_, readLatency_, writeLatency_, memory_) : 
        filename = 'CalculationDB.csv'
        if filename :
            os.remove("CalculationDB.csv")
        # else : 
        f = open('CalculationDB.csv', 'w', newline='')
        wr = csv.writer(f)
        wr.writerow([method_, totalCycle_, readCycle_, writeCycle_, totalEnergy_, totalLatency_, windows_, arCycle_, acCycle_, readEnergy_, writeEnergy_, readLatency_, writeLatency_, memory_])
        f.close()

    def CalculationDB_Add_Row(self, method_, totalCycle_, readCycle_, writeCycle_, totalEnergy_, totalLatency_, windows_, arCycle_, acCycle_, readEnergy_, writeEnergy_, readLatency_, writeLatency_, memory_):
        fields=[method_, totalCycle_, readCycle_, writeCycle_, totalEnergy_, totalLatency_, windows_, arCycle_, acCycle_, readEnergy_, writeEnergy_, readLatency_, writeLatency_, memory_]
        with open(r'CalculationDB.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow(fields)
            f.close()


    # csv load
    def GetInputData(self, image_, kernel_, ic_, oc_, ar_, ac_, method_) :
        image_ = self.lineEdit.text()
        kernel_ = self.lineEdit_2.text()
        ic_ = self.lineEdit_3.text()
        oc_ = self.lineEdit_4.text()
        ar_ = self.lineEdit_5.text()
        ac_ = self.lineEdit_6.text()
        method_ = self.lineEdit_7.text()
        return image_, kernel_, ic_, oc_, ar_, ac_, method_
                

# heatmap on QLabel(label_QPixmap)
class Heatmap_QLabel(QLabel):
    def __init__(self, QLabel_, parent=None):
        super().__init__(parent)
        self.qPixmap = QLabel_

    def SaveFig(self, data_, imgName_save):
        heatmap = sns.heatmap(data_)
        heatmap.figure.savefig(imgName_save)
    
    def Display(self, imgName):
        self.qPixmapVar = QPixmap() 
        self.qPixmapVar.load(imgName)
        self.qPixmapVar.scaledToWidth(400) 
        self.qPixmapVar.scaledToHeight(400)
        self.qPixmap.setPixmap(self.qPixmapVar)


# class : heatmap on new window
class HeatmapWindow(QMainWindow):
    def __init__(self, data, countHeatmap_, sns_heatmap_, parent=None):
        super().__init__(parent)        
        
        self.label = QLabel(self)
        self.setCentralWidget(self.label)

        # save heatmap
        sns_heatmap_.figure.savefig('WeightMapping' + str(countHeatmap_)+ '.png')        
        # sns_heatmap_.figure.savefig('WeightMapping' + str(countHeatmap_)+ '.pdf') # save as pdf as well
        pixmap = QPixmap('WeightMapping' + str(countHeatmap_) + '.png')
        
        self.label.setPixmap(pixmap)
        self.show()


class Log:    
    def __init__(self, qTextEdit_):
        self.qTextEdit = qTextEdit_

    def Start(self):
        contents = ">> Hello, simulator is ready now :)"
        self.qTextEdit.setText(contents)        

    def Complete(self, action_):
        contents = f">> {action_} is complete."
        self.qTextEdit.append(contents)
        self.qTextEdit.verticalScrollBar().setValue(self.qTextEdit.verticalScrollBar().maximum());
    
    def Running(self, action_):
        contents = f">> {action_} is running."
        self.qTextEdit.append(contents)
        self.qTextEdit.verticalScrollBar().setValue(self.qTextEdit.verticalScrollBar().maximum());
    
    def LogPrint(self, contents):
        self.qTextEdit.append(">> " + contents)
        self.qTextEdit.verticalScrollBar().setValue(self.qTextEdit.verticalScrollBar().maximum());

    def ScrollToLast(self):
        self.qTextEdit.verticalScrollBar().setValue(self.qTextEdit.verticalScrollBar().maximum());

if __name__ == "__main__" :
    
    app = QApplication(sys.argv)     
    myWindow = WindowClass()     
    myWindow.show()
    app.exec_()



# %%




# %%
