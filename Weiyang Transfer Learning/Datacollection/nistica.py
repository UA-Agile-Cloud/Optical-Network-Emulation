import time
import sys

import serial

class Nistica(object):
    """Control Nistica Switch

    Writing bytearrays are complex for Nistica. Add more functions later
    dd 01 MID(1) LENGTH(1) CMD(1) OBJID(1) Table(1) Row(1) INSTANCE(2) PARAMETER(1) DATA(n) checksum(1) dd 02
    if both table rows are needed , 0x60 should be or'ed into 

    MID: Message ID 1-255
    Length: length from Cmd to Checksum
    CMD: Operation to be performed
        1.Write 2.Read 3.Abort Firmware Download 4.Checksum Verify
        5.Switch 6.Commit 7.Start FW Download 16.Array Write
        17.Array Read 18.Multi-object Write. 19.Multi-object Read

    ObjID: Identifiers for different objects (switch,attenuation,etc)/
    Table: Switch Identifier, OCM Identifier
    Row: Port (Usually used in Perportatten)
    Instance: Instance of the object to be read/written(e.g. channel number)
    Parameter: Parameter associated with instance
         0.Measured Value
         1.Setpoint
         2.Degrade_Low alarm threshold
         3.Degrade-High alarm threshold
         ....
    Data: Additional data associated with specific commands
    Checksum: Calculated by the XOR of the bytes starting from the MID field to
    the last data parameter byte,inclusive.

    Response: MID Result-Code Value

    Array Message:
    MID,LENGTH,CMD,OBJID,INSTANCE1,PARAMETER,INSTANCEN,DATA,CHECKSUM

    Response:
    MID LENGTH RESULT SUCCESS COUNT DATA CHECKSUM
    
    """
    
    count = 0
    def __init__ (self,port,timeout=0.01,name=None):
        self.connection = serial.Serial(port,baudrate=115200,timeout=timeout)
        self.chtoport = {}
        self.chtoatten = {}
        self.chtopower = {}
        if not name:
            Nistica.count += 1
            self.name = str('Nistica Switch %s' % Nistica.count)

    def __repr__(self):
        return self.name

    def cal_checksum(self,msg):
        checksum = 0
        for i in range(2,len(msg)):
            if msg[i] == 4 and msg[i-1] == 221:               
                continue
            else:
                checksum ^= msg[i]
        return checksum

    def chan_port_switching(self,channel=1,port=1,table=0,MID=1):
        """


        CMD = 21 (0x01 or 0x20)
        objid = aa
        
        dd 01 01 08 21 aa table channel 01 00 port checksum dd 02
        
        """
        if MID == 221:
            msg = bytearray([221,1,MID,4,8,33,170,table,channel,1,0,port])
        else:
            msg = bytearray([221,1,MID,8,33,170,table,channel,1,0,port])
        checksum = self.cal_checksum(msg)
        if checksum == 221:
            msg.extend([checksum,4,221,2])
        else:
            msg.extend([checksum,221,2])
        self.msg = msg
        self.connection.write(msg)
        time.sleep(0.01)
        self.reply = self.connection.read(1000)

    def chan_port_attenuation(self,channel=1,port=1,attenuation=0,table=0,MID=2): #Per channel attenuation must be enabled
        """


        CMD = 61
        objid = ab

        dd 01 02 09 61 ab table port channel 01 00 value checksum dd 02
        """
        value = int(round(attenuation,1)*10)
        if MID == 221:
            msg = bytearray([221,1,MID,4,9,97,171,table,port,channel,1,0,value])
        else:
            msg = bytearray([221,1,MID,9,97,171,table,port,channel,1,0,value])
        if value == 221:
            msg.extend([4])
        checksum = self.cal_checksum(msg)
        if checksum == 221:
            msg.extend([checksum,4,221,2])
        else:
            msg.extend([checksum,221,2])
        self.msg = msg
        self.connection.write(msg)
        time.sleep(0.01)
        self.reply = self.connection.read(1000)

    def check_chan_port_switching(self,channel=1,table=0,MID=3,sleep=0.02):
        """

        MID = 03
        CMD = 22
        objid = aa

        dd 01 03 06 21 aa table channel 00 checksum dd 02
        """
        if MID==221:
            msg = bytearray([221,1,MID,4,6,34,170,table,channel,0])
        else:
            msg = bytearray([221,1,MID,6,34,170,table,channel,0])
        checksum = self.cal_checksum(msg)
        if checksum == 221:
            msg.extend([checksum,4,221,2])
        else:
            msg.extend([checksum,221,2])
        self.connection.write(msg)
        time.sleep(0.01)
        reply = self.connection.read(100)
        self.reply = reply
        if reply[2] == chr(MID) and reply[4] == '\x00': #Same MID and no error
            self.chtoport[channel] = ord(reply[6])

    def check_chan_port_attenuation(self,channel=1,port=1,table=0,MID=4,sleep=0.1):
        """

        MID = 04
        CMD = 62
        objid = ab
        
        """
        if MID==221:
           msg = bytearray([221,1,MID,4,7,98,171,table,port,channel,0])
        else:
            msg = bytearray([221,1,MID,7,98,171,table,port,channel,0])
        checksum = self.cal_checksum(msg)
        if checksum == 221:
            msg.extend([checksum,4,221,2])
        else:
            msg.extend([checksum,221,2])
        self.connection.write(msg)
        time.sleep(0.02)
        reply = self.connection.read(100)
        self.reply = reply
        if len(self.reply)<=5:
            return None
        if reply[2] == chr(MID) and reply[4] == '\x00': #Same MID and no error
            self.chtoatten[channel] = ord(reply[6])/10.0
        return self.chtoatten[channel]

    def per_channel_monitor(self,channel=1,table=0,MID=5,sleep=0.1):
        """

        MID = 05
        CMD = 22
        objid = c1

        """
##        print MID
        if MID==221:
            msg = bytearray([221,1,MID,4,6,34,193,table,channel,0])
        else:
            msg = bytearray([221,1,MID,6,34,193,table,channel,0])
        checksum = self.cal_checksum(msg)
        if checksum == 221:
       #     print('Really?')
            msg.extend([checksum,4,221,2])
        else:
            msg.extend([checksum,221,2])
        self.connection.write(msg)
        time.sleep(0.02)
        reply = self.connection.read(1000)
        self.reply = reply
        if len(self.reply)<=5:
            return None
        if reply[2] == chr(MID) and reply[4] == '\x00': #Same MID and no error
            if reply[5] == '\xff':
                self.chtopower[channel] = (ord(reply[6])-256)/10.0
            else:
                if reply[5] == '\xdd':
                    self.chtopower[channel] = (256*ord(reply[5])+ord(reply[7]) - 65536)/10.0
                else:
                    self.chtopower[channel] = (256*ord(reply[5])+ord(reply[6]) - 65536)/10.0
            return self.chtopower[channel]

    #Following defines the array commands for fast processing,most useful for data acquisition
    #Array Message:MID,LENGTH,CMD,OBJID,INSTANCE1,PARAMETER,INSTANCEN,DATA,CHECKSUM           
    def group_channel_power_monitor(self,channelstart,channelend,table=0,MID=6):

        """

        CMD = 31
        OBJID = c1
        """

        time1 = time.time()
        if MID == 221:
           msg = bytearray([221,1,MID,4,7,49,193,table,channelstart,0,channelend])
        else:
            msg = bytearray([221,1,MID,7,49,193,table,channelstart,0,channelend])
        checksum = self.cal_checksum(msg)
        if checksum == 221:
            msg.extend([checksum,4,221,2])
        else:
            msg.extend([checksum,221,2])
        self.connection.write(msg)
        chnum = channelend-channelstart+1
        time.sleep(0.01)
        self.reply = self.connection.read(1000)
        pos1 = 6 #Datavalue 1 position
        pos2 = 7 #DataValue 2 position
        if self.reply[2] == chr(MID) and self.reply[4] == '\x00': #Same MID and no error
            for ch in range(channelstart,channelend+1):
                if self.reply[pos1] == '\xdd':
                    pos2 += 1
                    self.chtopower[ch] = (256*ord(self.reply[pos1])+ord(self.reply[pos2]) - 65536)/10.0
                    pos1 += 1
                else:
                    self.chtopower[ch] = (256*ord(self.reply[pos1])+ord(self.reply[pos2]) - 65536)/10.0
                if self.reply[pos2] == '\xdd':
                    pos1 += 3
                else:
                    pos1 += 2
                pos2 = pos1 + 1
        time2 = time.time()
      #  print 'Using array to monitor 75 channels take %.2f second' % (time2-time1)                
            
    def group_switching_monitor(self,channelstart,channelend,table=0,MID=7):
        """
        MID = 07
        CMD = 31
        OBJID = aa
        """
        if MID == 221:
            msg = bytearray([221,1,MID,4,7,49,170,table,channelstart,0,channelend])
        else:
            msg = bytearray([221,1,MID,7,49,170,table,channelstart,0,channelend])
        checksum = self.cal_checksum(msg)
        if checksum == 221:
            msg.extend([checksum,4,221,2])
        else:
            msg.extend([checksum,221,2])
        self.connection.write(msg)
        chnum = channelend-channelstart+1
        time.sleep(0.01)
        self.reply = self.connection.read(1000)
        pos = 7 
        if self.reply[2] == chr(MID) and self.reply[4] == '\x00': #Same MID and no error
            for ch in range(channelstart,channelend+1):
                if self.reply[pos] == '\xdd':
                    self.chtoport[ch] = ord(self.reply[pos])
                    pos += 3
                else:
                    self.chtoport[ch] = ord(self.reply[pos])
                    pos += 2

    #Array Writing, handy!
                
    def group_per_port_attenuation_monitor(self,channelstart,channelend,port=1,table=0,MID=8):
        """
        CMD = 71
        OBJID = ab
        """
        if MID == 221:
            msg = bytearray([221,1,MID,4,8,113,171,table,port,channelstart,0,channelend])
        else:
            msg = bytearray([221,1,MID,8,113,171,table,port,channelstart,0,channelend])
        checksum = self.cal_checksum(msg)
        if checksum == 221:
            msg.extend([checksum,4,221,2])
        else:
            msg.extend([checksum,221,2])
        self.connection.write(msg)
        chnum = channelend-channelstart+1
        time.sleep(0.01)
        self.reply = self.connection.read(1000)
        pos = 7
        if self.reply[2] == chr(MID) and self.reply[4] == '\x00': #Same MID and no error
            for ch in range(channelstart,channelend+1):
                if self.reply[pos] == '\xdd':
                    self.chtoatten[ch] = ord(self.reply[pos])/10.0
                    pos += 3
                else:
                    self.chtoatten[ch] = ord(self.reply[pos])/10.0
                    pos += 2

    def group_switching(self,channelstart,channelend,values,table=0,MID=9):
        """
        CMD = 30
        OBJID = aa
        """
        
        if len(values) != (channelend-channelstart+1):
            print 'Not enough values,value nums provided must be equal to channel nums!'
            sys.exit()
        else:
            time1 = time.time()
            if MID == 221:
                msg = bytearray([221,1,MID,4,0,48,170,table,channelstart,1,channelend])
            else:
                msg = bytearray([221,1,MID,0,48,170,table,channelstart,1,channelend])
            count = 7
            for val in values:
                msg.extend([0,val])
                count += 2
            if MID == 221:
                msg[4] = count
            else:
                msg[3] = count
            checksum = self.cal_checksum(msg)
            if checksum == 221:
                msg.extend([checksum,4,221,2])
            else:
                msg.extend([checksum,221,2])
            self.connection.write(msg)
            time.sleep(0.01)
            self.reply = self.connection.read(1000)
            

    def group_attenuation(self,channelstart,channelend,values,port=1,table=0,MID=10):
        """
        CMD = 70
        OBJID = ab
        """
        if len(values) != (channelend-channelstart+1):
            print 'Not enough values,value nums provided must be equal to channel nums!'
            sys.exit()
        else:
            time1 = time.time()
            if MID == 221:
                msg = bytearray([221,1,MID,4,0,112,171,table,port,channelstart,1,channelend])
            else:
                msg = bytearray([221,1,MID,0,112,171,table,port,channelstart,1,channelend])
            count = 8
            for val in values:
                val = round(val,1)
                if val == 221:
                    msg.extend([0,int(round(val,1)*10),4])
                    count += 2
                else:
                    msg.extend([0,int(round(val,1)*10)])
                    count += 2
            if MID == 221:
                msg[4] = count
            else:
                msg[3] = count
            checksum = self.cal_checksum(msg)
            if checksum == 221:
                msg.extend([checksum,4,221,2])
            else:
                msg.extend([checksum,221,2])
            self.connection.write(msg)
            time.sleep(0.01)
            self.reply = self.connection.read(1000)

    #Configuration and Status
    def module_status(self,MID=11):
        """
        CMD = 2
        OBJID = 04
        """
        msg = bytearray([221,1,MID,5,2,4,1,0])
        checksum = self.cal_checksum(msg)
        if checksum == 221:
            msg.extend([checksum,4,221,2])
        else:
            msg.extend([checksum,221,2])
        self.connection.write(msg)
        time.sleep(0.01)
        self.reply = self.connection.read(1000)
        if self.reply[4] =='\x00' and self.reply[6] == '\x01':
            self.status = 'Operational'
            print 'Switch is operational'
        elif self.reply[4] =='\x00' and self.reply[6] == '\x00':
            self.status = 'Initializing'
            print 'Switch is initializing'

    def close(self):
        self.connection.close()

    def hardware_test(self,MID=12):
        """
        CMD = 2
        OBJID = 3
        """
        msg = bytearray([221,1,MID,5,2,3,1,0])
        checksum = self.cal_checksum(msg)
        if checksum == 221:
            msg.extend([checksum,4,221,2])
        else:
            msg.extend([checksum,221,2])
        self.connection.write(msg)
        time.sleep(0.01)
        self.reply = self.connection.read(1000)
        if self.reply[4] =='\x00' and self.reply[6] == '\x00':
            self.test = 'OK'
            print 'Test passed'
        elif self.reply[4] =='\x00' and self.reply[6] == '\x01':
            self.test = 'SDRAM failed'
            print 'SDRAN test failed'
        elif self.reply[4] =='\x00' and self.reply[6] == '\x02':
            self.test = 'Flash image verifiction failed'
            print 'Flash image verifiction failed'
        elif self.reply[4] =='\x00' and self.reply[6] == '\x04':
            self.test = 'Calibration data verification failed'
            print 'Calibration data verification failed'
        elif self.reply[4] =='\x00' and self.reply[6] == '\x08':
            self.test = 'Switch hardware failed'
            print 'Switch hardware failed'
