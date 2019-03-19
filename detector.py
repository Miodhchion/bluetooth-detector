# Bluetooth Signal Strength Detector
# Latest Revision by Chris Peek 2019-01-17
#
# Assumes hardware operates via relays attached to the first 5 outside General Purpose Input/Output pins.
#
# Keyboard input is used only to end operation. All interaction should be via config file and input/output pins to allow for headless operation.
#
# Three options for setting activation levels exist
#	Demo: cycles through all activation settings on 1 second intervals
#	Flicker: has a random 2% chance of flashing level 1 for half a second and a 0.2% chance of flashing level 3
#	Distance: changes activation levels based on distance to a bluetooth source


import RPi.GPIO as GPIO
import ConfigParser
import bluetooth
import bluetooth._bluetooth as bt
import random
import time
import struct
import array
import fcntl

outpins = [15, 17, 18]
onstates = [0, 0, 0]
pwm = []
target_addr = '00:00:00:00:00:00'
maxActivation = 10
minrssi = -100
maxrssi = 25
mode = 0
count = 0

def init (): #Initialize I/O hardware and random number generator
	global outpins
	global onstates
	global pwm
	global target_addr
	global minrssi
	global maxrssi
	global mode
	random.seed()
	config = ConfigParser.ConfigParser()
	try:
		#Read pin and bluetooth settings from ini file
		config.read('detector.ini')
		#Maximum level of activation, default is 10
		maxactivation = int(config.get('GPIO','MaxActivation','10'))
		#List of on/off output pins, default is 14 & 15
		outpins = [int(x) for x in config.get('GPIO','OutputPins','15 17 18').split()]
		#PWM pin, default is 21
		pwmpin = int(config.get('GPIO','PwmPin','14'))
		onstates = [int(x) for x in config.get('GPIO','OnStates','1 1 1').split()]
		GPIO.setmode(GPIO.BCM)
		if outpins:
			GPIO.setup(outpins,GPIO.OUT,initial=GPIO.LOW)
		if pwmpin:
			GPIO.setup(pwmpin,GPIO.OUT,initial=GPIO.LOW)
			pwm = GPIO.PWM(pwmpin, 1000)
			pwm.start(0)
		#Bluetooth MAC and allowed signal strength range
		target_addr = config.get('Bluetooth','Target')
		minrssi = int(config.get('Bluetooth','minRSSI'))
		maxrssi = int(config.get('Bluetooth','maxRSSI'))
		mode = int(config.get('Settings','Mode'))
	except:
		print('Invalid config file. Using defaults')
	print('Output Pins: '+','.join(map(str,outpins)))
	print('Pin On States: '+','.join(map(str,onstates)))
	print('PWN Outut Pin: '+str(pwmpin))
	print('BT Target Address: '+target_addr)
	print('Min. RSSI: '+str(minrssi))
	print('Max. RSSI: '+str(maxrssi))
	print('Mode: '+str(mode))
	print('\n\r')

def activate(level): #Activate device
	global outputs
	global onstates
	global maxActivation
	global minActivation
	#pull output pins low in increasing order
	for i in range(0,len(outpins)):
        	if level > i*maxActivation/len(outpins):
			if onstates[i]==1:
	        		GPIO.output(outpins[i],GPIO.HIGH)
			else:
				GPIO.output(outpins[i],GPIO.LOW)
        	else:
        		if onstates[i]==1:
				GPIO.output(outpins[i],GPIO.LOW)
			else:
				GPIO.output(outpins[i],GPIO.HIGH)
	#Set duty cycle on PWM pin
	if pwm:
		pwm.ChangeDutyCycle(level*100/maxActivation);

def bluetooth_rssi(addr): #Get bluetooth signal strength

    # Open hci socket
    hci_sock = bt.hci_open_dev()
    hci_fd = hci_sock.fileno()
    # Connect to device
    bt_sock = bluetooth.BluetoothSocket(bt.L2CAP)
    bt_sock.settimeout(10)
    result = bt_sock.connect_ex((addr, 1))	# PSM 1 - Service Discovery

    try:
        # Get ConnInfo
        reqstr = struct.pack("6sB17s", bt.str2ba(addr), bt.ACL_LINK, "\0" * 17)
        request = array.array("c", reqstr )
        handle = fcntl.ioctl(hci_fd, bt.HCIGETCONNINFO, request, 1)
        handle = struct.unpack("8xH14x", request.tostring())[0]

        # Get RSSI
        cmd_pkt=struct.pack('H', handle)
        rssi = bt.hci_send_req(hci_sock, bt.OGF_STATUS_PARAM,
                     bt.OCF_READ_RSSI, bt.EVT_CMD_COMPLETE, 4, cmd_pkt)
        rssi = struct.unpack('b', rssi[3])[0]

        # Close sockets
        bt_sock.close()
        hci_sock.close()

        return rssi

    except:
        return None


def demo(): #Cycle through all activation levels in 2 second increments
	global count
	global maxActivation
	count += 0.5
	if count > maxActivation:
		count = 0
	return count;


def flicker(): #Random 2% chance of activating level 1. Random 0.2% chance of activating level 2
	r = random.randInt(0,500)
	if  r==500:
		return 2
	if  r>= 490:
		return 1
	return 0


def distance(): #Increase activation levels based on distance to a bluetooth source
	global target_addr
	global maxrsssi
	global minrssi
	rssi = bluetooth_rssi(target_addr)
	print(rssi)
	if rssi == None:
                return 0
        else:
		rssi=max(rssi,0)
                return maxActivation*(rssi-minrssi)/(maxrssi-minrssi)


def mainloop():
	global mode
	act = 0
	while True:
		try:
			if mode == 1:
				act = flicker()
			elif mode == 2:
				act = distance()
			else:
				act = demo()
			activate(act)
			time.sleep(0.5)
		except KeyboardInterrupt:
			break
	GPIO.cleanup()

if __name__ == "__main__":
	init()
mainloop()
