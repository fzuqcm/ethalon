import serial
import serial.tools.list_ports
import time
import numpy as np
import os
from datetime import datetime    #for folder naming
import csv        #for data saving
from pathlib import Path
import re

freq_vect = []

# SET UP THE PATH HERE
now = datetime.now()
dt_string = now.strftime("%Y-%m-%d_%H-%M")
current_dir = Path.cwd()     #return current directory
newdir = os.path.join(current_dir,dt_string)
os.makedirs(newdir)

#keep the old directory for getting access to the .txt file
os.chdir(current_dir)
print("Folder created. Path: " + str(Path.cwd()))


#READ REQUIRED FREQUENCIES FROM THE SETTINGS FILE CSV
with open('settings_data.csv','r') as csvfile:
    csvreader = csv.reader(csvfile,delimiter=',')
    for row in csvreader:
        if len(row) > 0:
            if not(row[0] == "" or row[0] == "\n"):
                f1 = int(row[0])
                f2 = int(row[1])
                f3 = int(row[2])
                f = np.arange(f1,f2,f3)
                for j in f:
                    freq_vect.append(str(j))

print("First frequency: " + freq_vect[0])
print("Last frequency: " + freq_vect[len(freq_vect)-1])
print("Sample count: " + str(len(freq_vect)))
print()
os.chdir(newdir)


# now open ports
ports = serial.tools.list_ports.comports()
for p in ports:
    print('Connected device:\n______________')
    print("name: {} \ndescription: {}\nhardware: {}\n______________\n".format(p.name, p.description, p.hwid))

#go through all ports - add QCMs to the array, create file for each, open their SERIAL
count = 0
portarray = []
portser = []
portnames = []
for p in ports:
    hw = p.hwid
    a = hw.partition('SER=')
    n = -1
    if len(a[2]) < 7:
        continue
    else:
        act = a[2]
        nums = re.findall(r'\d+',str(act[0:10]))  #extract the HWID number after SER into a string
        n = int(nums[0])
    if (n > 0 and n < 10000000):  #if SER within this bound, add it to the array
        portarray.append(p)
        portnames.append(str(n))
        count += 1
        portser.append(serial.Serial('/dev/'+p.name, 115200, write_timeout = 2, timeout = 10))   #open its port
        # and create a file for it
        with open(str(n) + ".csv",'w',newline='') as csvfile:
            filewriter = csv.writer(csvfile,delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL )
            filewriter.writerow(['Frequency','Median amplitude','Mean Ampitude','Standard deviation of data'])

# NOW ALL PORTS IN THE ARRAY AND ALL FILES WERE CREATED

#send first request for data
for i in range(len(ports)):
    m = freq_vect[0]
    portser[i].flush()
    #print(m)
    time.sleep(0.1)
    portser[i].write(m.encode())
    print("First freq: " + m + " requested for port " + portser[i].name)

time.sleep(1)
t_prev = round(time.time(),2)
t_new = round(time.time(),2)

#now go through all the frequencies
print(len(freq_vect))
for freq in freq_vect:
   
    #send new value as a request for measurement
    f = freq
    for num,p in enumerate(portser):
        #print(f.encode())
        p.write(f.encode())
    print()
    print("Wrote " + f + " to all ports")    
    #wait until first data arrived
    while not(portser[0].in_waiting > 0):
        pass

    #wait a bit more for all to arrive
    time.sleep(0.05)

    #read ports one by one, extract all 3 pieces of data
    for i,p in enumerate(portser):
        fr = p.readline().decode()
        med = p.readline().decode()
        mea = p.readline().decode()
        std = p.readline().decode()
        n = re.findall(r'\d+',fr)
        nums = re.findall(r'\d+',med)
        nums2 = re.findall(r'\d+',mea)
        nums3 = re.findall(r'\d+',std)
        print(i,str(n[0]),str(nums[0]),str(nums2[0]),str(nums3[0]))

        with open(portnames[i] + ".csv",'a',newline='') as csvfile:  #save as a new line to the file
            filewriter = csv.writer(csvfile,delimiter=',')
            filewriter.writerow([f,str(nums[0]),str(nums2[0]),str(nums3[0])])

    t_new = round(time.time(),2)
    print("Time taken: " + str(t_new - t_prev))
    t_prev = t_new

