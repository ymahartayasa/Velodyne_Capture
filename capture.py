'''
This is a script to capture live packets with pcap
Yoga Mahartayasa
Parsing code from Karthik Kulkanari
Parser code: https://github.com/kkulkarni32/LidarParser/blob/master/Velodyne_Parser.py
Following https://www.binarytides.com/code-a-packet-sniffer-in-python-with-pcapy-extension/
'''

import pcapy
import socket
import numpy as np

# Initializing empty matrix and other necessary variables 
data = np.zeros((80000,5), dtype=np.float32)
iterator = 0
azimuth_value_prev = 0
counter = 0




# Vertical angles for each laser
V_angles = np.array([-30.67,-9.33,-29.33,-8.00,-28.00,-6.67,-26.67,
	-5.33,-25.33,-4.00,-24.00,-2.67,-22.67,-1.33,-21.33,0.00,-20.00,
	1.33,-18.67,2.67,-17.33,4.00,-16.00,5.33,-14.67,6.67,-13.33,8.00,
	-12.00,9.33,-10.67,10.67])

devices = pcapy.findalldevs()
dev = 'eth1'

cap = pcapy.open_live(dev, 1248, 1, 0)


for i in range (0, 100):

	(header, packet) = cap.next()
	print(len(packet))

	if(len(packet)==1248):
		f=open("packet_info/data_"+str(i)+".txt", "w+")
		dumper = cap.dump_open('packets_from_capture/pcapy_test_'+str(i)+'.pcap')
		dumper.dump(header, packet)

		for block_index in range(0,12):

				# obtain azimuth angle of the LiDAR beam stack 
				# during a given firing cycle
			firecycle_start = 42+block_index*100
			azimuth = packet[firecycle_start + 2:firecycle_start +4]
				
				# convert binary azimuth angle value to float 
				# Note: azimuths are in deg not rads
			azimuth_value = int.from_bytes(azimuth, byteorder='little', signed=False)/100
			azimuth_value = azimuth_value*np.pi/180


				# Obtain distance and intensity data from each laser 
				# channel in the block. There are 32 channels per block, 
				# one for each laser.
				
			for channel_index in range(32):
					
					# obtain distance in mm
				channel_start = firecycle_start + 4 + 3*channel_index
				channel_distance = packet[channel_start:channel_start+2]
				distance = int.from_bytes(channel_distance, byteorder='little', signed=False)/1000

					# obtain intensity of returing laser pulse
				channel_intensity = packet[channel_start+2:channel_start+3]
				intensity = int.from_bytes(channel_intensity, byteorder='little', signed=False)

					# obtain vertical angle from channel index and convert it into radians
				vertical_angle = V_angles[channel_index]*np.pi/180


				X = distance*np.cos(vertical_angle)*np.sin(azimuth_value)
				Y = distance*np.cos(vertical_angle)*np.cos(azimuth_value)
				Z = distance*np.sin(vertical_angle)

				data[iterator,0]=X
				data[iterator,1]=Y
				data[iterator,2]=Z
				data[iterator,3]=distance
				data[iterator,4]=intensity

				print(X)
				f.write('X: '+str(X)+'\n')
				print(Y)
				f.write('Y: '+str(Y)+'\n')
				print(Z)
				f.write('Z: '+str(Z)+'\n')
				print(distance)
				f.write('distance: '+str(distance)+'\n')
				print(azimuth_value)
				f.write('azimuth: '+str(azimuth_value)+'\n')
				print(channel_index)
				f.write('channel: '+str(channel_index)+'\n')
				print()
				f.write(' '+'\n')

				iterator+=1


				# Checking if one rotaion is completed, azimuth_value reaches its maximum and then starts decreasing  
			if (azimuth_value<=azimuth_value_prev):

				np.save('np_files/' + "data" + str(counter), data)
				print("writing npy:",counter)


					# Removing extra rows
				data = data[~np.all(data==0,axis=1)]


					# Reinitializing variables 
				data = np.zeros((80000,5))
				azimuth_value_prev = 0
				iterator = 0

					# Incrementing counter
				counter += 1


			else:
					# If the new azimuth value is larger than previous, assign it to the azimuth_value_prev variable 
				azimuth_value_prev=azimuth_value
