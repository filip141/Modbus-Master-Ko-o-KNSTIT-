
import RPi.GPIO as GPIO
import serial
import time

class UART_Obj(object):
    port = '' 
    serObj = None
    ControlPin = 18
    BaundRate = 0

    def __init__(self, brate):
        
         self.BaundRate = brate
         #Setup Control Pin
         GPIO.setmode(GPIO.BCM)
         GPIO.setup(self.ControlPin, GPIO.OUT)
         #Initialize Raspberry Serial
         self.port = '/dev/ttyAMA0'
         self.serObj = serial.Serial(self.port, brate, timeout = 1)
         self.serObj.bytesize = serial.EIGHTBITS
         self.serObj.parit = serial.PARITY_NONE
         self.serObj.stopbits = serial.STOPBITS_TWO

    def UART_SendStr(self,Message):
         #Bytes per second transmition with number of bytes
         #from cumulating start,stop and parity bits
         BytesPerSec = round(self.BaundRate/8)
         Bytes = float(len(Message))
         SnSCum = round((Bytes*4)/8)
         Bytes = Bytes + SnSCum
         #Set Half Duplex into sending mode
         GPIO.output(self.ControlPin, GPIO.HIGH)
         #Send Message
         self.serObj.write(Message)
         time.sleep(Bytes/BytesPerSec)
         #Back to Waiting for message
         GPIO.output(self.ControlPin, GPIO.LOW)
    def UART_ReceiveStr(self):
         StatusBit = 0
         RcvChar = ''
         MessageString = ''
         while True:
             try:
                #Waiting for next letter
                RcvChar = self.serObj.read()
             except:
                 return None

             if (RcvChar == ''):
                 return None
             # CR Recived Status equals 1
             elif (hex(ord(RcvChar)) == '0xd'):
                 StatusBit = 1
             #LF Recived ending transmition
             elif (StatusBit == 1 and hex(ord(RcvChar) == '0xa')):
                 return MessageString
                 MessageString = ''
             else:
                 MessageString = MessageString + RcvChar
             

if __name__ == "__main__":

    c = UART_Obj(19200)
    c.UART_SendStr("Hello World")
    print "Start Receiving"
    print c.UART_ReceiveStr()


