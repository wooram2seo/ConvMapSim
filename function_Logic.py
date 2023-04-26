from cgitb import lookup
import math
from os import access
from re import I
from pandas import array
import seaborn as sns # 
import matplotlib.pyplot as plt
import random
import numpy as np
import time
import main_GUI

class visualization :

  global visualizationTime
  global count_used_array


  def __init__(self):
    pass


  def lookup_table_rect(self, PW_h, PW_w, filter_size):
    n_window_w, n_window_h = PW_w - filter_size + 1, PW_h - filter_size + 1
    lookup_table = np.empty(shape = (n_window_w * n_window_h, filter_size * filter_size), dtype=int) 
    lookup_table.fill(0)
    count = 0 

    for x in range(n_window_h): 
        for y in range(n_window_w): 
            for w in range(filter_size): 
                for h in range(filter_size): 
                    lookup_table[count][filter_size * w + h] = PW_w * (x + w) + (y + h)
            count=count+1
    return lookup_table



  def visualize(self, Array, Size):
    custom_color_map = []
    for i in range(Size):
        color = "#" + "%06x" % random.randint(0, 0xFFFFFF)
        custom_color_map.append(color)
    
    max_size = 15 
    figr, axs = plt.subplots(figsize=(max_size, max_size))    

    cbar_kws = {
                "orientation":"vertical",
                "drawedges":True,
                } 
    
    axs = sns.heatmap(Array, annot=True, linewidth = 1, cbar_kws=cbar_kws, cmap=custom_color_map, fmt='g' )
    main_GUI.countHeatmap = main_GUI.countHeatmap + 1
    window = main_GUI.HeatmapWindow(Array, main_GUI.countHeatmap, axs)

    figure = axs.get_figure()    
    figure.savefig('result_heatmap.png', dpi=400)



  def generate_array_IRIS(self, kernel, n_window_w, n_window_h, IC_tiled, OC_tiled, array_row, array_col, method):
        K = int(kernel)
        n_window_w, n_window_h = int(n_window_w), int(n_window_h)
        C, M = int(IC_tiled), int(OC_tiled) 
        PW_w,PW_h = K + n_window_w -1, K + n_window_h - 1 

        total_col = M * n_window_w * n_window_h 
        total_row = PW_h * PW_w * C 

        array_row, array_col = int(array_row), int(array_col)
        
        print("SRAM SIZE : (Row: {}, Column: {})".format(array_row, array_col))
        print("TILED SIZE : (Row: {}, Column: {})".format(total_row, total_col))
        print("-"*40)
        print("="*40)

        Array = np.empty(shape=(1024,1024)) 
        Array.fill(np.nan)

        tcol = n_window_w * n_window_h
        trow = int(total_row/C) 

        convLayer_h = total_row 
        convLayer_w = total_row 
        pimArraySize_h = array_col 
        pimArraySize_w = array_row 
        reference = self.lookup_table_rect(PW_h, PW_w, K)

        count = 0
        for i in range(C): 
            for j in range(0,total_col,M): 
                for k in range(trow): 
                    for l in range(M):                         
                        Array[reference[int(j/M)][count]+PW_h*PW_w*i][j+l] = 1 + i + C*l 
                    count = count+1
                    if count > K*K-1:
                        count = 0                        
                        
        Array = Array[:array_row, :array_col]
        self.visualize(Array,C*M) 


def Get_ReadCycle_WriteCycle_im2col(image_col, image_row, filter_col, filter_row, in_channel, out_channel, array_row, array_col) : # (image, image, kernel, kernel, ic, oc, ar, ac)
    # read Cycle
    col_slide = image_col - filter_col + 1
    row_slide = image_row - filter_row + 1
    readCycle = col_slide * row_slide

    # write Cycle
    col_cycle = math.ceil(out_channel/array_col)
    row_cycle = math.ceil(in_channel *(filter_col*filter_row) / array_row)
    writeCycle = row_cycle * col_cycle
    
    return readCycle, writeCycle, row_slide, col_slide, row_cycle, col_cycle


def Get_ReadCycle_WriteCycle_SDK(image_col, image_row, filter_col, filter_row, in_channel, out_channel, \
                    array_row, array_col) :
    
    row_vector = filter_row * filter_col * in_channel
    col_vector = out_channel
    used_row = math.ceil(row_vector/array_row)
    used_col = math.ceil(col_vector/array_col)    
    new_array_row = array_row * used_row
    new_array_col = array_col * used_col

    # initialize
    cycle = []
    cycle.append(used_row*used_col*(image_row-filter_row+1)*(image_col-filter_col+1))
    
    readCycle = []
    writeCycle = []
    readCycle.append((image_row-filter_row+1)*(image_col-filter_col+1)) 
    writeCycle.append(used_row*used_col)

    i=0
    while True :
        i += 1
        pw_row = filter_row + i - 1 
        pw_col = filter_col + i - 1
        pw = pw_row * pw_col
        if pw*in_channel <= new_array_row and i * i * out_channel <= new_array_col :
            parallel_window_row = math.ceil((image_row - (filter_row + i) + 1)/i) + 1
            parallel_window_col = math.ceil((image_col - (filter_col + i) + 1)/i) + 1
            
            if parallel_window_row * parallel_window_col * used_row * used_col <= cycle[0] :
                del readCycle[0]
                del writeCycle[0]
                readCycle.append(parallel_window_row * parallel_window_col) 
                writeCycle.append(used_row * used_col)
                
        else :
            break
        
    return readCycle[0], writeCycle[0], parallel_window_row, parallel_window_col, used_row, used_col


def Get_readCycle_WriteCycle_VWSDK(image_col, image_row, filter_col, filter_row, in_channel, out_channel, \
                    array_row, array_col) :
    i = 0
    j = 1
    readCycle = [] 
    writeCycle = [] 
    reg_total_cycle = [] 
    reg_row_cycle = [] 
    reg_col_cycle = [] 
    
    while True :
        try :
            i += 1
            if (i + filter_col) > image_col : 
                i = 1
                j += 1
                if j + filter_row > image_row : 
                    break

            reg_N_parallel_window_row = math.ceil((image_row - (filter_row + i) + 1)/i) + 1
            reg_N_parallel_window_col = math.ceil((image_col - (filter_col + j) + 1)/j) + 1
            
            if in_channel == 3 :
                ICt = math.floor(array_row /((filter_row + i - 1)*(filter_col + j - 1)))
                if ICt > in_channel :
                    ICt = 3
                row_cycle = math.ceil(in_channel / ICt)
            else :
                ICt = math.floor(array_row /((filter_row + i - 1)*(filter_col + j - 1)))
                row_cycle = math.ceil(in_channel / ICt)
            
            OCt =  math.floor(array_col / (i * j))
            col_cycle = math.ceil(out_channel / OCt)
    
            reg_N_of_computing_cycle = reg_N_parallel_window_row * reg_N_parallel_window_col \
                                     * row_cycle * col_cycle
            reg_N_of_readCycle = reg_N_parallel_window_row * reg_N_parallel_window_col
            reg_N_of_writeCycle = row_cycle * col_cycle

            if i == 1 : 
                reg_total_cycle.append(reg_N_of_computing_cycle)
                readCycle.append(reg_N_of_readCycle) 
                writeCycle.append(reg_N_of_writeCycle) 
                reg_row_cycle.append(row_cycle)
                reg_col_cycle.append(col_cycle)

            if reg_total_cycle[0] > reg_N_of_computing_cycle :
                del reg_total_cycle[0]
                del readCycle[0] 
                del writeCycle[0] 
                del reg_row_cycle[0]
                del reg_col_cycle[0]

                reg_total_cycle.append(reg_N_of_computing_cycle)
                readCycle.append(reg_N_of_readCycle) 
                writeCycle.append(reg_N_of_writeCycle) 
                reg_row_cycle.append(row_cycle)
                reg_col_cycle.append(col_cycle)
   
        except ZeroDivisionError :
            continue

    return readCycle[0], writeCycle[0], reg_N_parallel_window_row, reg_N_parallel_window_col, reg_row_cycle[0], reg_col_cycle[0]

    
def im2col (image_col, image_row, filter_col, filter_row, in_channel, out_channel, array_row, array_col) :

    col_slide = image_col - filter_col + 1
    row_slide = image_row - filter_row + 1
    
    col_cycle = math.ceil(out_channel/array_col)
    
    if col_cycle > 1 :
        o_ct = array_col
    else :
        o_ct = out_channel

    i_ct = math.floor(array_row/(filter_col*filter_row)) 
    row_cycle = math.ceil(in_channel/i_ct) 
    total_cycle = col_slide * row_slide * row_cycle * col_cycle

    return total_cycle, i_ct, o_ct


def SDK (image_col, image_row, filter_col, filter_row, in_channel, out_channel, \
                    array_row, array_col) :
    
    row_vector = filter_row * filter_col * in_channel
    col_vector = out_channel
    
    used_row = math.ceil(row_vector/array_row)
    used_col = math.ceil(col_vector/array_col)
    
    new_array_row = array_row * used_row
    new_array_col = array_col * used_col

    # initialize
    cycle = []
    w = [] # pw size
    w.append(filter_row*filter_col)
    cycle.append(used_row*used_col*(image_row-filter_row+1)*(image_col-filter_col+1))
    
    i=0
    while True :
        i += 1
        pw_row = filter_row + i - 1 
        pw_col = filter_col + i - 1
        pw = pw_row * pw_col
        if pw*in_channel <= new_array_row and i * i * out_channel <= new_array_col :
            parallel_window_row = math.ceil((image_row - (filter_row + i) + 1)/i) + 1
            parallel_window_col = math.ceil((image_col - (filter_col + i) + 1)/i) + 1
            
            if parallel_window_row * parallel_window_col * used_row * used_col <= cycle[0] :
                del cycle[0]
                del w[0]
                cycle.append(parallel_window_row * parallel_window_col * used_row * used_col)
                w.append(pw)
            
        else :
            break
        
    return cycle, w


def vw_sdk (image_col, image_row, filter_col, filter_row, in_channel, out_channel, \
                    array_row, array_col) :

    i = 0 # overlap col
    j = 1 # overlap row

    reg_total_cycle = [] 
    reg_overlap_row = []
    reg_overlap_col = []
    reg_row_cycle = []
    reg_col_cycle = []
    reg_ICt = []
    reg_OCt = []
    
    while True :
        try :
            i += 1
            if (i + filter_col) > image_col : 
                i = 1
                j += 1
                if j + filter_row > image_row : 
                    break

            # for parallel_window computing
            reg_N_parallel_window_row = math.ceil((image_row - (filter_row + i) + 1)/i) + 1
            reg_N_parallel_window_col = math.ceil((image_col - (filter_col + j) + 1)/j) + 1
            
            # for cycle computing
            # Tiled IC
            if in_channel == 3 :
                ICt = math.floor(array_row /((filter_row + i - 1)*(filter_col + j - 1)))
                if ICt > in_channel :
                    ICt = 3
                row_cycle = math.ceil(in_channel / ICt)
            else :
                ICt = math.floor(array_row /((filter_row + i - 1)*(filter_col + j - 1)))
                row_cycle = math.ceil(in_channel / ICt)
            
            # Tiled OC
            OCt =  math.floor(array_col / (i * j))
            col_cycle = math.ceil(out_channel / OCt)
    
            reg_N_of_computing_cycle = reg_N_parallel_window_row * reg_N_parallel_window_col \
                                    * row_cycle * col_cycle
            
            if i == 1 : # initialize
                reg_total_cycle.append(reg_N_of_computing_cycle)
                reg_overlap_row.append(i)
                reg_overlap_col.append(j)
                reg_row_cycle.append(row_cycle)
                reg_col_cycle.append(col_cycle)
                reg_ICt.append(ICt)
                reg_OCt.append(OCt)

            if reg_total_cycle[0] > reg_N_of_computing_cycle :
                del reg_total_cycle[0]
                del reg_overlap_row[0]
                del reg_overlap_col[0]
                del reg_row_cycle[0]
                del reg_col_cycle[0]
                del reg_ICt[0]
                del reg_OCt[0]

                reg_total_cycle.append(reg_N_of_computing_cycle)
                reg_overlap_row.append(i)
                reg_overlap_col.append(j)
                reg_row_cycle.append(row_cycle)
                reg_col_cycle.append(col_cycle)
                reg_ICt.append(ICt)
                reg_OCt.append(OCt)
    
        except ZeroDivisionError :
            continue

    return reg_total_cycle[0], reg_overlap_col[0], reg_overlap_row[0], reg_row_cycle[0], reg_col_cycle[0], reg_ICt[0], reg_OCt[0] 

def result_vw (image, kernel, IC, OC, array_row, array_col, method) :

    VWSDK_height = []
    VWSDK_width = []
    AR_cycle = []
    AC_cycle = []
    VW_IC_tiled = []
    VW_OC_tiled = []

    CC=[]
    print("="*50)
    print(" RESULTS of COMPUTING CYCLES")
    print("-"*30)

    T_cycle_vw, VWSDK_h, VWSDK_w, ARC, ACC, tiled_IC, tiled_OC = vw_sdk(image, image, kernel, kernel, IC, OC, array_row, array_col)
    CC.append(T_cycle_vw)
    VWSDK_height.append(VWSDK_h)
    VWSDK_width.append(VWSDK_w)
    AR_cycle.append(ARC)
    AC_cycle.append(ACC)
    count_visualCycle = ARC * ACC 
    count_used_array = count_visualCycle 
    VW_IC_tiled.append(tiled_IC)
    VW_OC_tiled.append(tiled_OC)

    T_cycle_im, i_c, o_c = im2col(image, image, kernel, kernel, IC, OC, array_row, array_col)
    T_cycle_SDK, pw = SDK(image, image, kernel, kernel, IC, OC, array_row, array_col)
    
    SDK_w, SDK_h = math.sqrt(pw[0])-kernel+1, math.sqrt(pw[0])-kernel+1
    SDK_ict = math.floor(array_row /((kernel + SDK_w - 1)*(kernel + SDK_h - 1)))
    SDK_oct = math.floor(array_col / (SDK_w * SDK_h))

    global Im2col_ComputingCycle
    global SDK_ComputingCycle 
    global VWSDK_ComputingCycle
    Im2col_ComputingCycle = T_cycle_im
    SDK_ComputingCycle = T_cycle_SDK[0]
    VWSDK_ComputingCycle = CC[0]

    print("    Im2col = {}".format(T_cycle_im))
    print("     S D K = {}".format(T_cycle_SDK[0]))
    print("    VW-SDK = {}".format(CC[0]))
    print("      - Optimal shape of PW = {} x {} x {} x {}".format(kernel + VWSDK_width[0]-1, kernel + VWSDK_height[0]-1, VW_IC_tiled[0], VW_OC_tiled[0]))
    print("="*50)
    
    convLayer = kernel * kernel * IC * OC
    pimArraySize = AR_cycle[0] * AC_cycle[0]
        
    v = visualization()
    if method == 'im2col' :
        print("im2col")
    
        v.generate_array_IRIS(kernel, 1, 1, i_c, o_c, array_row, array_col, method)

        tiled_IC_Case, tiled_OC_case = 0, 0
        array_row = int(array_row) 
        array_col = int(array_col) 
        IC = int(IC) 
        OC = int(OC) 

        if math.ceil(i_c/array_row) <= 1 : 
            if math.ceil(o_c/array_col) <= 1 :
                v.generate_array_IRIS(kernel, VWSDK_w, VWSDK_h, IC, OC, array_row, array_col, method) 
                case = 1 
                print(case, IC, OC) 

            if math.ceil(o_c/array_col) > 1 : 
                tiled_IC_Case = tiled_IC
                tiled_OC_case = OC - tiled_OC * (ACC-1)                
                v.generate_array_IRIS(kernel, VWSDK_w, VWSDK_h, tiled_IC_Case, tiled_OC_case, array_row, array_col, method) 
                case = 2 

        if (math.ceil(i_c*kernel*kernel/array_row) != 0 & math.ceil(i_c*kernel*kernel/array_row) > 1) : 
            if (math.ceil(o_c/array_col) !=0 & math.ceil(o_c/array_col) > 1) :
                v.generate_array_IRIS(kernel, VWSDK_w, VWSDK_h, IC, OC, array_row, array_col, method) 
                tiled_IC_Case = IC - tiled_IC * (ARC-1)
                tiled_OC_case = tiled_OC
                v.generate_array_IRIS(kernel, VWSDK_w, VWSDK_h, tiled_IC_Case, tiled_OC_case, array_row, array_col, method)
                case = 3 
                print(case)

            if math.ceil(o_c/array_col) > 1 : 
                v.generate_array_IRIS(kernel, VWSDK_w, VWSDK_h, IC, OC, array_row, array_col, method) 

                tiled_IC_Case = IC - tiled_IC * (ARC-1)
                tiled_OC_case = tiled_OC
                v.generate_array_IRIS(kernel, VWSDK_w, VWSDK_h, tiled_IC_Case, tiled_OC_case, array_row, array_col, method) 

                tiled_IC_Case = tiled_IC
                tiled_OC_case = OC - tiled_OC * (ACC-1)
                v.generate_array_IRIS(kernel, VWSDK_w, VWSDK_h, tiled_IC_Case, tiled_OC_case, array_row, array_col, method) 

                tiled_IC_Case = IC - tiled_IC * (ARC-1)
                tiled_OC_case = OC - tiled_OC * (ACC-1)
                v.generate_array_IRIS(kernel, VWSDK_w, VWSDK_h, tiled_IC_Case, tiled_OC_case, array_row, array_col, method)
                case = 4 
                print(case)




    elif method == 'SDK' :
        print("SDK")
        if SDK_w == 1 and SDK_h == 1 :            
            v.generate_array_IRIS(kernel, 1, 1, i_c, o_c, array_row, array_col, 'im2col')
        else :
            v.generate_array_IRIS(kernel, SDK_w, SDK_h, SDK_ict, SDK_oct, array_row, array_col, method) 

    elif method == 'VW-SDK' :
        print("VW-SDK")
        ACC = math.ceil(OC / tiled_OC)
        ARC = math.ceil(IC / tiled_IC)

        ### vw-sdk
        tiled_IC_Case, tiled_OC_case = 0, 0
        array_row = int(array_row) 
        array_col = int(array_col) 
        tiled_IC = int(tiled_IC)
        tiled_OC = int(tiled_OC)
        if IC % tiled_IC == 0 :
            if OC % tiled_OC == 0 :
                tiled_IC_Case = tiled_IC
                tiled_OC_case = tiled_OC
                v.generate_array_IRIS(kernel, VWSDK_w, VWSDK_h, tiled_IC_Case, tiled_OC_case, array_row, array_col, method) 
                case = 1 
                print(case, tiled_IC_Case, tiled_OC_case)

            elif OC % tiled_OC != 0:
                tiled_IC_Case = tiled_IC
                tiled_OC_case = OC - tiled_OC * (ACC-1)
                v.generate_array_IRIS(kernel, VWSDK_w, VWSDK_h, tiled_IC_Case, tiled_OC_case, array_row, array_col, method) 
                case = 2 

        elif IC % tiled_IC != 0 :
            if OC % tiled_OC == 0 :
                tiled_IC_Case = tiled_IC
                tiled_OC_case = tiled_OC
                v.generate_array_IRIS(kernel, VWSDK_w, VWSDK_h, tiled_IC_Case, tiled_OC_case, array_row, array_col, method) 

                tiled_IC_Case = IC - tiled_IC * (ARC-1)
                tiled_OC_case = tiled_OC
                v.generate_array_IRIS(kernel, VWSDK_w, VWSDK_h, tiled_IC_Case, tiled_OC_case, array_row, array_col, method) 
                case = 3 
                print(case)

            elif OC % tiled_OC != 0:
                tiled_IC_Case = tiled_IC
                tiled_OC_case = tiled_OC
                v.generate_array_IRIS(kernel, VWSDK_w, VWSDK_h, tiled_IC_Case, tiled_OC_case, array_row, array_col, method) 

                tiled_IC_Case = IC - tiled_IC * (ARC-1)
                tiled_OC_case = tiled_OC
                v.generate_array_IRIS(kernel, VWSDK_w, VWSDK_h, tiled_IC_Case, tiled_OC_case, array_row, array_col, method) 

                tiled_IC_Case = tiled_IC
                tiled_OC_case = OC - tiled_OC * (ACC-1)
                v.generate_array_IRIS(kernel, VWSDK_w, VWSDK_h, tiled_IC_Case, tiled_OC_case, array_row, array_col, method) 

                tiled_IC_Case = IC - tiled_IC * (ARC-1)
                tiled_OC_case = OC - tiled_OC * (ACC-1)
                v.generate_array_IRIS(kernel, VWSDK_w, VWSDK_h, tiled_IC_Case, tiled_OC_case, array_row, array_col, method) 
                case = 4 
                print(case)

    print("Counting used PIM Array = {}".format(count_visualCycle))
    return count_visualCycle

def Print_input_data(ar_, ac_, image_, kernel_, ic_, oc_) :
    contents = ""
    contents += "\nINFORMATION\n"
    contents += "-"*30
    contents += "\n    Array   Size = {} x {}".format(ar_, ac_)
    contents += "\n    Image   Size = {} x {}".format(image_, image_)
    contents += "\n    Kernel  Size = {} x {}".format(kernel_, kernel_)
    contents += "\n    Channel Size = {} x {}".format(ic_, oc_) + "\n"
    contents += "-"*30
    return contents


def Get_lookup_table_rect(PW_h, PW_w, filter_size): 
    # reference pixel coordinate. same as input feature coordinate    
    n_window_w, n_window_h = PW_w - filter_size + 1, PW_h - filter_size + 1
    lookup_table = np.empty(shape = (n_window_w * n_window_h, filter_size * filter_size), dtype=int) 
    lookup_table.fill(0)
    count = 0 

    for x in range(n_window_h):
        for y in range(n_window_w): 
            for w in range(filter_size): 
                for h in range(filter_size):
                    lookup_table[count][filter_size * w + h] = PW_w * (x + w) + (y + h)

            count=count+1
    return lookup_table


def Get_array_IRIS_forHeatmap(kernel, n_window_w, n_window_h, IC_tiled, OC_tiled, array_row, array_col, method):
    K = int(kernel)
    n_window_w, n_window_h = int(n_window_w), int(n_window_h) 
    C, M = int(IC_tiled), int(OC_tiled) 
    PW_w,PW_h = K + n_window_w -1, K + n_window_h - 1 

    total_col = M * n_window_w * n_window_h 
    total_row = PW_h * PW_w * C 

    array_row, array_col = int(array_row), int(array_col)
    
    print("SRAM SIZE : (Row: {}, Column: {})".format(array_row, array_col))
    print("TILED SIZE : (Row: {}, Column: {})".format(total_row, total_col))
    print("-"*40)
    print("="*40)

    Array = np.empty(shape=(1024,1024)) 
    Array.fill(np.nan)

    tcol = n_window_w * n_window_h
    trow = int(total_row/C) 

    convLayer_h = total_row 
    convLayer_w = total_row 
    pimArraySize_h = array_col 
    pimArraySize_w = array_row 
    reference = Get_lookup_table_rect(PW_h, PW_w, K) 
    
    count = 0
    for i in range(C): 
        for j in range(0,total_col,M): 
            for k in range(trow): 
                for l in range(M): 
                    '''
                    horizontal: filters
                    vertical: lookup table coordinate + input order (ex. 1245, 2356, ...)
                    value: filter number (different channel, filter number)
                    reference[int(j/M)][count]: 
                    '''
                    Array[reference[int(j/M)][count]+PW_h*PW_w*i][j+l] = 1 + i + C*l 
                count = count+1
                if count > K*K-1: 
                    count = 0
                                            
    Array = Array[:array_row, :array_col]
    return array



