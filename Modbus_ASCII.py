
from UART_Obj import *
import threading




#Modbus ASCII Object contain Modbus Querries
#and other practical functions
class Modbus_Ascii(object):
    UART_mod = None
    InputRegisters = {}
    OutputRegisters = {}
    
    #Daemon States
    ForceCoilState = False    
    PresetRegState = False
    PresetMulState = False
    
    #Errors
    TimeoutError = False
    DataAddressError = False
    DataValueError = False
    BadLRC = False

    #Global temporary for Coil function
    StartReg = 0
    StartBit = 0


    #Init function
    def __init__(self,UART):
        self.UART_mod = UART
        self.OutputRegisters = {str(x): [('0' * 16) for y in range(0,10)] for x in range(1,33)}
        self.InputRegisters = {str(x): [('0' * 16) for y in range(0,10)] for x in range(1,33)}
    
    #Wait 1s for message is we don't recieve anything function return None whitch equals TIMEOUT
    def Receive(self):
        Text = None
        t0 = time.time()
        t1 = t0
        while(t1 - t0 <= 1.23):
            Text = self.UART_mod.UART_ReceiveStr()
            t1 = time.time()
            if (Text != None):
                try:
                    if(Text[1] == ':'):
                        return Text
                except:
                    continue
        return None
    
    #Return dictionary with Error values
    def ErrorRet(self):
        Errors = {}
        Errors["Timeout"] = self.TimeoutError
        Errors["DataAddress"] = self.DataAddressError
        Errors["DataValue"] = self.DataValueError
        Errors["BadLRC"] = self.BadLRC
        self.TimeoutError = False
        self.DataAddressError = False
        self.DataValueError - False
        self.BadLRC = False
        return Errors

    #Check last call Preset Multiple Registers function efficiency
    def CheckMulReg(self):
        if (self.PresetMulState == True):
            self.PresetMulState = False
            return True
        else:
            return False

    #Check last call Preset Register function efficiency
    def CheckReg(self):
        if (self.PresetRegState == True):
            self.PresetRegState = False
            return True
        else:
            return False

    #Check last call Froce Single Coil function efficiency
    def CheckCoil(self):
        if ( self.ForceCoilState == True):
            self.ForceCoilState = False
            return True
        else:
            return False

    #Converts Number(8 bit recommended) to Modbus ASCII String
    def BytetoHex(self,Byte):
        if(Byte >=  0):
            HexString = hex(Byte)[2:]
        else:
            HexString = hex(Byte)[3:]
        if (len(HexString) == 1):
            HexString = "0" + HexString
        HexString = HexString.upper()
        return HexString

    #Converts Number(16bit recommended) to Modbus ASCII String
    def BytetoHex_4(self,Byte):
        HexString = self.BytetoHex(Byte)
        NumofLetters = len(HexString)
        if ( NumofLetters <= 2):
            HexString = "00" + HexString
        elif (NumofLetters == 3):
            HexString = "0" + HexString
        return HexString

    #Converts Modbus ASCII String to Number
    def HextoByte(self, Hex):
        return int(Hex,16)

    #Fill 8 bit register with zeros
    def bin_8(self, Data):
        BData = bin(Data)[2:]
        N = 8 - len(BData)
        return (N*"0" + BData)

    #Fill 16 bit register with zeros
    def bin_16(self, Data):
        BData = bin(Data)[2:]
        N = 16 - len(BData)
        return (N*"0" + BData)

    #Function to set correct bit in Registers
    def SetCoil(self, Addr, Data):
        BData = self.bin_8(Data)
        Register = list(self.OutputRegisters[Addr][self.StartReg])
        i = self.StartBit
        for x in reversed(BData):
            if ( i < 0 ):
                self.OutputRegisters[Addr][self.StartReg] = "".join(Register)
                self.StartReg = self.StartReg + 1
                Register = list(self.OutputRegisters[Addr][self.StartReg])
                i = 15
            Register[i] = x
            i = i - 1
        self.OutputRegisters[Addr][self.StartReg] = "".join(Register)
        self.StartBit = i

    #Looking for errors
    def CheckError(self, word):
        ExcCode = self.HextoByte(word[5:7])
        if (ExcCode == 2):
            self.DataAddressError = True
        elif (ExcCode == 3):
            self.DataValueError = True

    #Calculate LRC sum
    def GetLRC(self, Frame):
        LRCsum = 0
        TempStr = ''
        Temp = 0
        NFrame = len(Frame)-1
        i = 0
        while (i<NFrame):
            TempStr = Frame[i] + Frame[i+1]
            Temp = self.HextoByte(TempStr)
            LRCsum = LRCsum + Temp
            i= i + 2
        LRCsum = (~(LRCsum) & 0xFF)
        LRCsum = LRCsum + 1
        return LRCsum


    ##############################################################
    ##############################################################
    ########################QUERRIES##############################
    ##############################################################
    ##############################################################


    #Read Coils(bits) from slave OutputRegisters array and insert it in
    #Master OutputRegisters dictionary
    def ReadCoilStatus(self, SlaveAddr, StartAddr, NumCoils):
        OutputFrame = ":"
        OutputFrame = OutputFrame + self.BytetoHex(SlaveAddr)
        OutputFrame = OutputFrame + self.BytetoHex(1)
        OutputFrame = OutputFrame + self.BytetoHex_4(StartAddr)
        OutputFrame = OutputFrame + self.BytetoHex_4(NumCoils)
        OutputFrame = OutputFrame + self.BytetoHex(self.GetLRC(OutputFrame[1:]))
        OutputFrame = OutputFrame + '\r\n'
        ReadCoilDaemon = threading.Thread(target = self.ReadCoilDaemon, args = (SlaveAddr, StartAddr,))
        self.UART_mod.UART_SendStr(OutputFrame)
        ReadCoilDaemon.start()

    #Read Input bits from slave InputRegisters array and insert it in 
    #Master Input Registers dictionary
    def ReadInputStatus(self, SlaveAddr, StartAddr, NumCoils):
        OutputFrame = ":"
        OutputFrame = OutputFrame + self.BytetoHex(SlaveAddr)
        OutputFrame = OutputFrame + self.BytetoHex(2)
        OutputFrame = OutputFrame + self.BytetoHex_4(StartAddr)
        OutputFrame = OutputFrame + self.BytetoHex_4(NumCoils)
        OutputFrame = OutputFrame + self.BytetoHex(self.GetLRC(OutputFrame[1:]))
        OutputFrame = OutputFrame + '\r\n'
        self.UART_mod.UART_SendStr(OutputFrame)
        ReadInputDaemon = threading.Thread(target = self.ReadInputDaemon, args = (SlaveAddr, StartAddr,))
        ReadInputDaemon.start()

    #Read Output register from slave OutputRegisters array and insert it in
    #Master Output Registers dictionary
    def ReadHoldingRegisters(self, SlaveAddr, StartAddr, NumRegs):
        OutputFrame = ":"
        OutputFrame = OutputFrame + self.BytetoHex(SlaveAddr)
        OutputFrame = OutputFrame + self.BytetoHex(3)
        OutputFrame = OutputFrame + self.BytetoHex_4(StartAddr)
        OutputFrame = OutputFrame + self.BytetoHex_4(NumRegs)
        OutputFrame = OutputFrame + self.BytetoHex(self.GetLRC(OutputFrame[1:]))
        OutputFrame = OutputFrame + '\r\n'
        self.UART_mod.UART_SendStr(OutputFrame)
        ReadHoldingDaemon = threading.Thread(target = self.ReadHoldingDaemon, args = (SlaveAddr, StartAddr,))
        ReadHoldingDaemon.start()

    #Read Input registers from slave InputRegisters array and insert it in
    #Master Input Registers dictionary
    def ReadInputRegisters(self, SlaveAddr, StartAddr, NumRegs):
        OutputFrame = ":"
        OutputFrame = OutputFrame + self.BytetoHex(SlaveAddr)
        OutputFrame = OutputFrame + self.BytetoHex(4)
        OutputFrame = OutputFrame + self.BytetoHex_4(StartAddr)
        OutputFrame = OutputFrame + self.BytetoHex_4(NumRegs)
        OutputFrame = OutputFrame + self.BytetoHex(self.GetLRC(OutputFrame[1:]))
        OutputFrame = OutputFrame + '\r\n'
        self.UART_mod.UART_SendStr(OutputFrame)
        ReadInputRDaemon = threading.Thread(target = self.ReadInputRDaemon, args = (SlaveAddr, StartAddr,))
        ReadInputRDaemon.start()

    #Change bit in slave device memory
    def ForceSingleCoil(self, SlaveAddr, CoilAddr, State):
        OutputFrame = ":"
        OutputFrame = OutputFrame + self.BytetoHex(SlaveAddr)
        OutputFrame = OutputFrame + self.BytetoHex(5)
        OutputFrame = OutputFrame + self.BytetoHex_4(CoilAddr)
        if (State == True):
            OutputFrame = OutputFrame + self.BytetoHex_4(0xFF00)
        else:
            OutputFrame = OutputFrame + self.BytetoHex_4(0x0000)
        OutputFrame = OutputFrame + self.BytetoHex(self.GetLRC(OutputFrame[1:]))
        OutputFrame = OutputFrame + '\r\n'
        self.UART_mod.UART_SendStr(OutputFrame)
        ForceSingleDaemon = threading.Thread(target = self.ForceSingleDaemon, args = (OutputFrame,))
        ForceSingleDaemon.start()

    #Change Register value in slave device memory
    def PresetSingleRegister(self, SlaveAddr, RegisterAddr, Data):
        OutputFrame = ":"
        OutputFrame = OutputFrame + self.BytetoHex(SlaveAddr)
        OutputFrame = OutputFrame + self.BytetoHex(6)
        OutputFrame = OutputFrame + self.BytetoHex_4(RegisterAddr)
        OutputFrame = OutputFrame + self.BytetoHex_4(Data)
        OutputFrame = OutputFrame + self.BytetoHex(self.GetLRC(OutputFrame[1:]))
        OutputFrame = OutputFrame + '\r\n'
        self.UART_mod.UART_SendStr(OutputFrame)
        PresetSingleDaemon = threading.Thread(target = self.PresetSingleDaemon, args = (OutputFrame,))
        PresetSingleDaemon.start()
    
    #Change Multiple Registers value in slave device memory
    def PresetMultipleRegisters(self, SlaveAddr, StartAddr, NumRegs, *args):
        OutputFrame = ":"
        OutputFrame = OutputFrame + self.BytetoHex(SlaveAddr)
        OutputFrame = OutputFrame + self.BytetoHex(16)
        OutputFrame = OutputFrame + self.BytetoHex_4(StartAddr)
        OutputFrame = OutputFrame + self.BytetoHex_4(NumRegs)
        OutputFrame = OutputFrame + self.BytetoHex(2*NumRegs)
        for i in range(0,NumRegs):
            OutputFrame = OutputFrame + self.BytetoHex_4(args[i])
        OutputFrame = OutputFrame + self.BytetoHex(self.GetLRC(OutputFrame[1:]))
        OutputFrame = OutputFrame + '\r\n'
        self.UART_mod.UART_SendStr(OutputFrame)
        PresetMultipleDaemon = threading.Thread(target = self.PresetMultipleDaemon, args = (SlaveAddr, StartAddr, NumRegs,))
        PresetMultipleDaemon.start()

    ##############################################
    ####Daemons waiting for answer from slave#####
    ##############################################

    def ReadCoilDaemon(self, SlaveAddr, StartAddr):

        Data = 0
        
        #Receiving message
        word = self.Receive()
        if word == None:
            self.TimeoutError = True
            return
        #Preventing empty spaces
        word = word.replace(" ", "")
        word = word.replace(":", "")

        #Extracting Function Code
        FunCod = self.HextoByte(word[3:5])
        
        #Checking for Errors
        if FunCod > 80:
            self.CheckError(word)
            return

        #Address Field
        Addr = self.HextoByte(word[1:3])
        if (SlaveAddr == Addr or SlaveAddr == 0):

            #Number of Bytes Field
            ByteNum = self.HextoByte(word[5:7])
            N = 2*ByteNum + 6

            #Calculating LRC
            LRC = self.GetLRC(word[1:N+1])
            RcvLRC =  self.HextoByte(word[N+1:N+3])

            if (LRC != RcvLRC):
                self.BadLRC = True
                return

            #Setting Coils
            #Start address and start bit are used as global class variables
            #becouse function need them in next calls 
            self.StartReg = StartAddr/16
            self.StartBit = 15 - StartAddr%16
            for i in range(7, N, 2):
                Data = self.HextoByte(word[i:i+2])
                self.SetCoil(str(Addr), Data)

    def ReadInputDaemon(self, SlaveAddr, StartAddr):

        Data = 0

        #Receiving message
        word = self.Receive()
        if word == None:
            self.TimeoutError = True
            return

        word = word.replace(" ","")
        word = word.replace(":","")

        #Extracting Function Code
        FunCod = self.HextoByte(word[3:5])
        
        #Checking for Errors
        if FunCod > 80:
            self.CheckError(word)
            return

        Addr = self.HextoByte(word[1:3])
        if (SlaveAddr == Addr or SlaveAddr == 0):
            ByteNum = self.HextoByte(word[5:7])
            N = 2*ByteNum + 6

            #Calculating LRC
            LRC = self.GetLRC(word[1:N+1])
            RcvLRC =  self.HextoByte(word[N+1:N+3])

            if (LRC != RcvLRC):
                self.BadLRC = True
                return

            self.StartReg = StartAddr/16
            self.StartBit = 15 - StartAddr%16
            for i in range(7,N,2):
                Data = self.HextoByte(word[i:i+2])
                self.SetCoil(str(Addr), Data)
    
    def ReadHoldingDaemon(self, SlaveAddr, StartAddr):

        #Variables
        RegVal = 0
        k = 0
        Register = ""
        
        #Receiving message
        word = self.Receive()
         
        if word == None:
            self.TimeoutError = True
            return

        #Preventing Empty Spaces
        word = word.replace(" ","")
        word = word.replace(":","")
        
        #Extracting Function Code
        FunCod = self.HextoByte(word[3:5])
        
        #Checking for Errors
        if FunCod > 80:
            self.CheckError(word)
            return
        
        #Address Field
        Addr = self.HextoByte(word[1:3])
        if (SlaveAddr == Addr or SlaveAddr == 0):

            #Byte Number Field
            ByteNum = self.HextoByte(word[5:7])
            N = 7 + 2*ByteNum

            #Calculate LRC
            RcvLRC = self.HextoByte(word[N:N+4])
            LRC = self.GetLRC(word[1:N])
            if (RcvLRC != LRC):
                self.BadLRC = True

            #Save registers value 
            for i in range(7,N,4):
                RegVal = self.HextoByte(word[i:i+4])
                Register = self.bin_16(RegVal)
                self.OutputRegisters[str(Addr)][StartAddr + k] = Register
                k = k + 1

    def ReadInputRDaemon(self, SlaveAddr, StartAddr):
        
        #Variables
        RegVal = 0
        k = 0
        Register = ""

        #Receiving message
        word = self.Receive()
        if word == None:
            self.TimeoutError = True
            return

        #Preventing Empty Spaces
        word = word.replace(" ","")
        word = word.replace(":","")

        #Extracting Function Code
        FunCod = self.HextoByte(word[3:5])
        
        #Checking for Errors
        if FunCod > 80:
            self.CheckError(word)
            return

        #Address Field
        Addr = self.HextoByte(word[1:3])
        if (SlaveAddr == Addr or SlaveAddr == 0):
            #Byte Number Field
            ByteNum = self.HextoByte(word[5:7])
            N = 7 + 2*ByteNum

            #Calculate LRC
            RcvLRC = self.HextoByte(word[N:N+4])
            LRC = self.GetLRC(word[1:N])
            if (RcvLRC != LRC):
                self.BadLRC = True


            #Save registers value 
            for i in range(7,N,4):
                RegVal = self.HextoByte(word[i:i+4])
                Register = self.bin_16(RegVal)
                self.InputRegisters[str(Addr)][StartAddr + k] = Register
                k = k + 1 

    def ForceSingleDaemon(self, OutputFrame):
        
        #Receiving message
        word = self.Receive()
        if word == None:
            self.TimeoutError = True
            return
        
        word = word[1:]
        N = len(word)

        #Calculating LRC
        RcvLRC = self.HextoByte(word[13:15])
        LRC = self.GetLRC(word[1:13])
        if (RcvLRC != LRC):
            self.BadLRC = True
            return

        #Extracting Function Code
        FunCod = self.HextoByte(word[3:5])
        
        #Checking for Errors
        if FunCod > 80:
            self.CheckError(word)
            return

        OutputFrame = OutputFrame[:N]
    
        #If Echoes ok return true or false
        if(OutputFrame == word):
            self.ForceCoilState = True
        else:
            self.FoceCoilState = False

    def PresetSingleDaemon(self, OutputFrame):
        
        #Receiving message
        word = self.Receive()
        if word == None:
            self.TimeoutError = True
            return

        word = word[1:]
        N = len(word)

        #Calculating LRC
        RcvLRC = self.HextoByte(word[13:15])
        LRC = self.GetLRC(word[1:13])
        if (RcvLRC != LRC):
            self.BadLRC = True
            return

        #Extracting Function Code
        FunCod = self.HextoByte(word[3:5])

        #Checking for Errors
        if FunCod > 80:
            self.CheckError(word)
            return

        OutputFrame = OutputFrame[:N]

        #If Echoes ok return true or false
        if(OutputFrame == word):
            self.PresetRegState = True
        else:
            self.PresetRegState = False

    def PresetMultipleDaemon(self, SlaveAddr, StartAddr, NumRegs):
        
        #Receiving message
        word = self.Receive()
        if word == None:
            self.TimeoutError = True
            return
        word = word.replace(":","")
        word = word.replace(" ","")
        
        #Calculating LRC
        RcvLRC = self.HextoByte(word[13:15])
        LRC = self.GetLRC(word[1:13])
        if (RcvLRC != LRC):
            self.BadLRC = True
            return

        #Extracting Function Code
        FunCod = self.HextoByte(word[3:5])

        #Checking for Errors
        if FunCod > 80:
            self.CheckError(word)
            return

        #ASCII fields to bytes
        Addr = self.HextoByte(word[1:3])
        STAddr = self.HextoByte(word[5:9])
        NumRg = self.HextoByte(word[9:13])

        #Check Corectness
        if (SlaveAddr == Addr and StartAddr == STAddr and NumRegs == NumRg):
            self.PresetMulState = True
        else:
            self.PresetMulState = False




if __name__ == "__main__":

    c = UART_Obj(19200)
    d = Modbus_Ascii(c)
    print d.BytetoHex(0x07)
    print d.HextoByte('CD6BB20E')
    print d.BytetoHex_4(0x0001)
    print d.BytetoHex_4(4)

    d.PresetMultipleRegisters(17,0,2,40,59)
    time.sleep(0.2)
    d.ReadHoldingRegisters(17,0,2)
    time.sleep(3)
    print d.OutputRegisters["17"]
    time.sleep(0.2)
    print d.ErrorRet()
      
