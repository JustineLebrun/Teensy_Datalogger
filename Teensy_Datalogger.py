# -*- coding: utf-8 -*-

""" Teensy GUI """
##############################################################################

import tkinter as tk
import tkinter.ttk as ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
import serial
import matplotlib.animation as animation
import matplotlib.figure
import os
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import matplotlib.dates as mdates


##############################################################################
""" FUNCTIONS """
def layout(ax):
    ax.xaxis.grid(True, which="both", color="#cccccc", alpha=0.8, lw=0.5)
    ax.yaxis.grid(True, which="both", color="#cccccc", alpha=0.8, lw=0.5)
    ax.patch.set_visible(False)
    ax.tick_params( length=0, pad=8.0)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines['bottom'].set_color('gray')

    handles, labels = ax.get_legend_handles_labels()
    if labels:
        common_legend_params = {
            'bbox_to_anchor': (1.0, 1.15),
            'loc' : 'upper right',
            'ncol': 1,
            'frameon': True,
            'fontsize': 13,
            'borderpad': 0.5
        }
        ax.legend(handles, labels, **common_legend_params)
        
def update_plot():
    global data
    ax.clear()
    layout(ax)
    ax.plot(time, [row[0] for row in data], color='blue')
    #ax.legend()
    canvas.draw()
    
def close():    
    try:
        ani.event_source.stop()
        if serCon and ser.is_open:
            ser.flush()
            ser.close()  # close the serial port if it's open
        window.destroy()
    except Exception as e:
        print("An error occurred while closing:", e)
        
def stop():
    global continue_animation
    if continue_animation:
        continue_animation = False
        ani.event_source.stop()
        if serCon and ser.is_open:
            ser.flush()
            ser.close()  # close the serial port if it's open
    else:
        continue_animation = True


def start():
    global continue_animation, ani, serCon, ser
    
    if continue_animation:
        continue_animation = False
        ani.event_source.stop()
        ser.flush()
        ser.close()  # close the serial port
    else:
        continue_animation = True
        try:
            ser = serial.Serial('COM8', 9600) # CHANGE PORT COM IF NECESSARY
            serCon = True
                
        except serial.serialutil.SerialException:
            print("Warning: Teensy not connected")
            serCon = False
        
        ani.event_source.start()

# This function is called periodically from FuncAnimation
def animate(i, x, y):
    if serCon:
        try:
            # Read and decode the incoming line from the serial connection
            line = ser.readline().decode('utf-8')
            parts = list(map(float, line.split()))
            
            # Extract the timestamp components
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            hour = int(parts[3])
            minute = int(parts[4])
            second = int(parts[5])
            millisecond = int(parts[6])
            
            # Create a timestamp object
            timestamp = dt.datetime(year, month, day, hour, minute, second, millisecond * 1000)
            
            # Append the timestamp to the time list
            time.append(timestamp)
            
            # Extract data for each channel (Channel 1 = parts[7], Channel 2 = parts[8], etc.)
            data_line = parts[7:17]  # Assuming up to 10 channels: parts[7] to parts[16]
            data.append(data_line)
            
            # Update the subplots based on the current checkbox states
            update_subplots()
        
        except Exception as e:
            print("An error occurred:", e)


def update_subplots():
    fig.clear()
    # Find which channels are ticked
    ticked_channels = [i for i, var in enumerate(channel_vars) if var.get()]
    
    colors = ['darkred', 'red', 'orange', 'goldenrod', 'chartreuse', 'forestgreen', 'teal', 'blue', 'mediumpurple', 'magenta']
    
    if ticked_channels:
        num_channels = len(ticked_channels)
        
        for idx, channel_idx in enumerate(ticked_channels):
            subplot_ax = fig.add_subplot(num_channels, 1, idx + 1)
            layout(subplot_ax)
            
            subplot_ax.plot(time, [row[channel_idx] for row in data], label=f"Channel {channel_idx + 1}", color=colors[channel_idx % len(colors)])
            
            #subplot_ax.set_title(f"Channel {channel_idx + 1}", loc='left')
            
            subplot_ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
            subplot_ax.xaxis.set_major_locator(mdates.AutoDateLocator())
           
            plt.setp(subplot_ax.xaxis.get_majorticklabels(), rotation=30, ha='right')
            
            # Add a legend for the channel
            subplot_ax.legend()
    
        fig.tight_layout()
    # Redraw the canvas to reflect the changes
    canvas.draw()

            
def save_data_to_file():
    global filename, now_format, file_save
    file_save = True
    now = dt.datetime.now()
    now_format = now.strftime("%Y__%m__%d__%H__%M") 

    # Create the filename with timestamp
    filename = f"{save_dir}/TEENSY_DATALOG_{now_format}.txt"
                
    try:
        with open(filename, "w") as file:
            # Write header
            file.write(f"# Teensy acquisition \n")
            file.write(f"# Date: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
            file.write("# YYYY__MM__DD__HH__MM__SS__Signal Value\n")
            
    except Exception as e:
        print(f"Error while creating file: {e}")
    
save_counter = 1

def save_plot():
    global save_counter

    filename_plot = f"{save_dir}/TEENSY_PLOT_{save_counter:03d}.svg"
    try:
        fig.savefig(filename_plot, format='svg')
        #print(f"Figure saved as: {filename_plot}")
        save_counter += 1  # Increment the counter for the next save
    except Exception as e:
        print(f"Error while saving the figure: {e}")

##############################################################################
continue_animation = False
serCon = False
file_save = False

time = []
data = []

now = dt.datetime.now()
now_file = now.strftime("%Y__%m__%d__%H__%M") 
save_dir = f"{now_file}_Results"
os.makedirs(save_dir, exist_ok=True)
    
##############################################################################
""" WINODW """

### create a window
window = tk.Tk()
window.title("Teensy DataLogger")

### frames
frame_dashboard = tk.Frame(master=window)
frame_dashboard.pack(fill=tk.BOTH, side=tk.LEFT) #fills automatically in both directions

frame_exit = tk.Frame(master=window)
frame_exit.pack(fill=tk.BOTH, side=tk.RIGHT) #fills automatically in both directions

frame_plot = tk.Frame(master=window)
frame_plot.pack(fill=tk.BOTH, expand=True)

# Plot for base signal
fig = matplotlib.figure.Figure()
ax = fig.add_subplot()
layout(ax)
canvas = FigureCanvasTkAgg(fig, master=frame_plot)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

toolbar = NavigationToolbar2Tk(canvas, frame_plot)
toolbar.update()
toolbar.pack(side=tk.BOTTOM, fill=tk.X)

exit_button = ttk.Button(frame_exit, text="Exit", command=close)
exit_button.pack()

start_button = ttk.Button(frame_dashboard, text="START ACQUISITION", command=start)
start_button.pack()

stop_button = ttk.Button(frame_dashboard, text="STOP ANIMATION", command=stop)
stop_button.pack()

save_button = ttk.Button(frame_dashboard, text="SAVE current figure", command=save_plot)
save_button.pack()

save_txt_button = ttk.Button(frame_dashboard, text="Start saving data to file", command=save_data_to_file)
save_txt_button.pack()

### Channels selection
label_amp = tk.Label(text="Choose channel", fg="black", master=frame_dashboard, font = ("Arial",13), padx=5, pady=5)
label_amp.pack()
channel_vars = [tk.BooleanVar(value=False) for _ in range(10)]
checkboxes = []
for i in range(10):
    cb = tk.Checkbutton(frame_dashboard, text=f"Channel {i+1}", variable=channel_vars[i], command=lambda: update_subplots())
    cb.pack(anchor='w', padx=5, pady=2)
    checkboxes.append(cb)

ani = animation.FuncAnimation(fig, animate, fargs=(time, data), interval=100, cache_frame_data=False)

window.mainloop()