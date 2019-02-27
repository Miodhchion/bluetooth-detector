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
import configparser
import bluetooth as bt

global outpins
global pwm
global target_addr 
global maxactivation
global minrssi
global maxrssi
global mode

def init (): #Initialize I/O hardware and random number generator
	random.seed()
	config = configparser.ConfigParser()
	#Read pin and bluetooth settings from ini file
	config.read('detector.ini')
	gpioconfig = config['GPIO']
	#Maximum level of activation, default is 10
	maxactivation = int(gpioconfig.get('MaxActivation','10'))
	#List of on/off output pins, default is 14 & 15
	outpins = [int(x) for x in gpioconfig.get('OutputPins','14 15').split()]
	#PWM pin, default is 21
	pwmpin = int(gpioconfig.get('PwmPin','21'))
	GPIO.setmode(GPIO.BCM)
	if outpins:
		GPIO.setup(outpins,GPIO.OUT,initial=GPIO.HIGH)
	if pwm:
		GPIO.setup(pwmpin,GPIO.OUT,initial=GPIO.HIGH)
		pwm = GPIO.PWM(pwmpin, 100)
		pwm.start(0) 
	bluetooth = config['Bluetooth']
	#Bluetooth MAC and allowed signal strength range
	target_addr = bluetooth.get('Target','00:00:00:00:00:00')
	minrssi = bluetooth.get('minRSSI','0')
	maxrssi = bluetooth.get('maxRSSI','100')
	settings = config['Settings']
	mode = int(settings.get('Mode',0))
	
def activate(level): #Activate device
	#pull output pins low in increasing order
	for i in range(0,len(outpins)):
        if level > i*maxActivation/len(outpins):
        	GPIO.output(outpins[i],GPIO.LOW)
        else
        	GPIO.output(outpins[i],GPIO.HIGH)
	#Set duty cycle on PWM pin	
	if pwm:
		pwm.ChangeDutyCycle(level*100/maxActivation);
        
def bluetooth_rssi(addr): #Get bluetooth signal strength
    # Open hci socket
    hci_sock = bt.hci_open_dev()
    hci_fd = hci_sock.fileno()

    # Connect to device
    bt_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
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

		
def demo(_count=[0]): #Cycle through all activation levels in 1 second increments
	count[0] += 0.5
	if count[0] > maxActivation:
		count[0] = 0
	return count[0];
		
def flicker(): #Random 2% chance of activating level 1. Random 0.2% chance of activating level 2
	r = random.randInt(0,500)
	if  r==500:
		return 2
	if r>= 490
		return 1
	return 0 
	
	
def distance(): #Increase activation levels based on distance to a bluetooth source
	rssi = bluetooth_rssi(target_addr)
	if rssi = None:
                activate(0)
        else
                activate(maxActivation*(rssi-minrssi)/(maxrssi-minrssi)
	
def mainloop():
		while True:
			try:
				if mode == 1:
					activate(flicker())
				elif mode == 2:
					activate(distance())
				else
					activate(demo())
				sleep(0.5)
			except KeyboardInterrupt:
				break
		GPIO.cleanup()

if __name__ == "__main__":
	init()
	mainloop()
	
