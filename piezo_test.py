from ctypes import cdll, create_string_buffer, POINTER, byref
from ctypes import c_uint, c_int, c_char, c_char_p, c_void_p, c_ushort, c_short, c_int, c_long, \
    c_ulong, c_bool, c_double, c_uint64, \
            c_uint32, c_wchar, c_wchar_p, Array, CFUNCTYPE, WINFUNCTYPE
import os, time
import threading

def _buildFunction(call, args, result):
    call.argtypes = args
    call.restype = result
    return call

def c_str_array(strings):
    arr = (c_char_p * len(strings))()
    arr[:] = strings
    return arr

LOGGERFUNC = WINFUNCTYPE(None, c_void_p)
TIMEOUT = 10

class TLKinesisPiezoMotorController():

    def _initialize_library(self):

        libname = os.path.dirname(__file__)
        libname = os.path.join(libname, "dlls\Thorlabs.MotionControl.KCube.InertialMotor.dll")
        _library = cdll.LoadLibrary(libname)

        self.__BuildDeviceList = _buildFunction(_library.TLI_BuildDeviceList, None, c_short)
        self.__GetDeviceListSize = _buildFunction(_library.TLI_GetDeviceListSize, None, c_short)
        self.__CheckConnection = _buildFunction(_library.KIM_CheckConnection, [c_char_p], c_bool)
        self.__Open = _buildFunction(_library.KIM_Open, [c_char_p], c_short)
        self.__Enable = _buildFunction(_library.KIM_Enable, [c_char_p], c_short)
        self.__EnableChannel = _buildFunction(_library.KIM_EnableChannel, [c_char_p, c_ushort], c_short)
        self.__MoveAbsolute = _buildFunction(_library.KIM_MoveAbsolute, [c_char_p, c_ushort, c_uint], c_short)
        self.__MoveRelative = _buildFunction(_library.KIM_MoveRelative, [c_char_p, c_ushort, c_uint], c_short)
        self.__RequestStatusBits = _buildFunction(_library.KIM_RequestStatusBits, [c_char_p], c_short)
        self.__GetStatusBits = _buildFunction(_library.KIM_GetStatusBits, [c_char_p, c_ushort], c_ulong)
        self.__RequestCurrentPosition = _buildFunction(_library.KIM_RequestCurrentPosition, [c_char_p, c_ushort],
                                                       c_short)
        self.__GetCurrentPosition = _buildFunction(_library.KIM_GetCurrentPosition, [c_char_p, c_ushort], c_int)
        self.__MessageQueueSize = _buildFunction(_library.KIM_MessageQueueSize, [c_char_p], c_int)
        self.__GetFirmwareVersion = _buildFunction(_library.KIM_GetFirmwareVersion, [c_char_p], c_ulong)
        self.__PollingDuration = _buildFunction(_library.KIM_PollingDuration, [c_char_p], c_long)
        self.__StartPolling = _buildFunction(_library.KIM_StartPolling, [c_char_p, c_int], c_bool)
        self.__RegisterMessageCallback = _buildFunction(_library.KIM_RegisterMessageCallback, [c_char_p, LOGGERFUNC], c_void_p)
        self.__GetNextMessage = _buildFunction(_library.KIM_GetNextMessage, [c_char_p, POINTER(c_ulong), POINTER(c_ulong),
                                                                             POINTER(c_ulong)], c_bool)

    def __init__(self, serialno, pollingTime = 100):
        self._initialize_library()
        self.__serial = serialno.encode()
        self.__fn = LOGGERFUNC(self._callback)
        self.__eventHandler = threading.Event()
        self.BuildDeviceList()
        self.OpenConnection()
        self.StartPolling(pollingTime)
        time.sleep(0.5)
        self.__pos = self.GetCurrentPositionAll()
        self.RegisterMessageCallback()
        print(f'Initial position is {self.__pos}.')

    def _callback(self, p):
        res = self.GetNextMessage()
        if self.__pos == self.GetCurrentPositionAll():
            print(f'Message is {res}. Hardware position is {self.GetCurrentPositionAll()}. '
                  f'Soft. position is {self.__pos}')
            self.__eventHandler.set()

    def updatePosition(self):
        self.__pos = self.GetCurrentPositionAll()

    def BuildDeviceList(self):
        return self.__BuildDeviceList()

    def GetDeviceListSize(self):
        return self.__GetDeviceListSize()

    def CheckConnection(self):
        return self.__CheckConnection(self.__serial)

    def OpenConnection(self):
        return self.__Open(self.__serial)

    def MoveRelative(self, channel: int, step: int):
        if self.__pos[channel - 1] != self.__pos[channel - 1] + step:
            self.__eventHandler.clear()
            self.__pos[channel - 1] += step
            self.__MoveRelative(self.__serial, channel, step)
            self.__eventHandler.wait(TIMEOUT)
            return True
        return False

    def MoveAbsolute(self, channel: int, value: int):
        if self.__pos[channel - 1] != value:
            self.__eventHandler.clear()
            self.__pos[channel - 1] = value
            self.__MoveAbsolute(self.__serial, channel, value)
            self.__eventHandler.wait(TIMEOUT)
            return True
        return False

    def RequestStatusBits(self):
        return self.__RequestStatusBits(self.__serial)

    def GetStatusBits(self, channel: int):
        return self.__GetStatusBits(self.__serial, channel)

    def RequestCurrentPosition(self, channel: int):
        return self.__RequestCurrentPosition(self.__serial, channel)

    def GetCurrentPosition(self, channel: int):
        return self.__GetCurrentPosition(self.__serial, channel)

    def GetCurrentPositionAll(self):
        return [self.__GetCurrentPosition(self.__serial, x+1) for x in range(4)]

    def MessageQueueSize(self):
        return self.__MessageQueueSize(self.__serial)

    def GetFirmwareVersion(self):
        return self.__GetFirmwareVersion(self.__serial)

    def PollingDuration(self):
        return self.__PollingDuration(self.__serial)

    def StartPolling(self, time: int):
        return self.__StartPolling(self.__serial, time)

    def RegisterMessageCallback(self):
        self.__RegisterMessageCallback(self.__serial, self.__fn)

    def GetNextMessage(self):
        msg_type = c_ulong(0x00)
        msg_id = c_ulong(0x00)
        msg_data = c_ulong(0x00)
        res = self.__GetNextMessage(self.__serial, msg_type, msg_id, msg_data)
        return (msg_type.value, msg_id.value, msg_data.value, res)

my_piezo = TLKinesisPiezoMotorController('97101311')

val = 150
my_piezo.MoveRelative(1, val)
my_piezo.MoveRelative(2, val)
my_piezo.MoveRelative(3, val)
my_piezo.MoveRelative(4, val)


