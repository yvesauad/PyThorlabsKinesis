from ctypes import cdll, POINTER, c_uint, c_char, c_byte, c_char_p, c_void_p, c_ushort, c_short, c_int, c_long, \
    c_ulong, c_bool, WINFUNCTYPE, Structure

from Modules.ErrorEnum import FTDI_COM_ERROR

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

class TLI_HardwareInformation(Structure):
    _fields_ = [("serialNumber", c_ulong),
                ("modelNumber", (8 * c_char)),
                ("type", c_ushort),
                ("firmwareVersion", c_ulong),
                ("notes", (48 * c_char)),
                ("deviceDependantData", (12 * c_byte)),
                ("hardwareVersion", c_ushort),
                ("modificationState", c_ushort),
                ("numChannels", c_short)]



class MessageQueue():
    def __init__(self):
        self.msg_type = c_ulong(0)
        self.msg_id = c_ulong(0)
        self.msg_data = c_ulong(0)

    def get_status(self):
        return [self.msg_type.value, self.msg_id.value, self.msg_data.value]


LOGGERFUNC = WINFUNCTYPE(None, c_void_p)

class TLKinesisStrainGauge():

    def _error_check(self, val):
        if val != 0: print(f'Error {FTDI_COM_ERROR(val)}')
        return val

    def _initialize_library(self):

        libname = os.path.dirname(__file__)
        libname = os.path.join(libname, "../dlls/Thorlabs.MotionControl.KCube.StrainGauge.dll")
        _library = cdll.LoadLibrary(libname)

        self.__InitializeSimulations = _buildFunction(_library.TLI_InitializeSimulations, None, c_void_p)
        self.__BuildDeviceList = _buildFunction(_library.TLI_BuildDeviceList, None, c_short)
        self.__GetDeviceListSize = _buildFunction(_library.TLI_GetDeviceListSize, None, c_short)
        self.__CheckConnection = _buildFunction(_library.SG_CheckConnection, [c_char_p], c_bool)
        self.__Open = _buildFunction(_library.SG_Open, [c_char_p], c_short)
        self.__Close = _buildFunction(_library.SG_Close, [c_char_p], None)
        self.__Enable = _buildFunction(_library.SG_Enable, [c_char_p], c_short)
        self.__GetStatusBits = _buildFunction(_library.SG_GetStatusBits, [c_char_p, c_ushort], c_ulong)
        self.__MessageQueueSize = _buildFunction(_library.SG_MessageQueueSize, [c_char_p], c_int)
        self.__GetFirmwareVersion = _buildFunction(_library.SG_GetFirmwareVersion, [c_char_p], c_ulong)
        self.__PollingDuration = _buildFunction(_library.SG_PollingDuration, [c_char_p], c_long)
        self.__StartPolling = _buildFunction(_library.SG_StartPolling, [c_char_p, c_int], c_bool)
        self.__StopPolling = _buildFunction(_library.SG_StopPolling, [c_char_p], None)
        self.__RegisterMessageCallback = _buildFunction(_library.SG_RegisterMessageCallback, [c_char_p, LOGGERFUNC], None)
        self.__GetNextMessage = _buildFunction(_library.SG_GetNextMessage, [c_char_p, POINTER(c_ulong), POINTER(c_ulong),
                                                                             POINTER(c_ulong)], c_bool)
        self.__GetHardwareInfoBlock = _buildFunction(_library.SG_GetHardwareInfoBlock, [c_char_p,
                                                                                        POINTER(TLI_HardwareInformation)], c_short)

        self.__SetZero = _buildFunction(_library.SG_SetZero, [c_char_p], c_short)
        self.__SetDisplayMode = _buildFunction(_library.SG_SetDisplayMode, [c_char_p, c_int], c_short)
        self.__GetReadingExt = _buildFunction(_library.SG_GetReadingExt, [c_char_p, c_bool, POINTER(c_bool)], c_int)
        self.__GetMaximumTravel = _buildFunction(_library.SG_GetMaximumTravel, [c_char_p], c_ulong)
        self.__GetForceCalib = _buildFunction(_library.SG_GetForceCalib, [c_char_p], c_uint)
        self.__GetHubAnalogOutput = _buildFunction(_library.SG_GetHubAnalogOutput, [c_char_p], c_uint)
        self.__SetHubAnalogOutput = _buildFunction(_library.SG_SetHubAnalogOutput, [c_char_p, c_uint], c_short)


    def __init__(self, serialno, pollingTime = 150, TIMEOUT = 5.0, SIMULATION = False):
        self._initialize_library()
        self.__serial = serialno.encode()
        self.__fn = LOGGERFUNC(self._callback)
        self.__eventHandler = threading.Event()
        self.__timeout = TIMEOUT
        if SIMULATION: self.InitializeSimulations()
        self.BuildDeviceList()
        self.OpenConnection()
        self.StartPolling(pollingTime)
        time.sleep(0.5)
        self.__messageQueue = MessageQueue()
        self.RegisterMessageCallback()

    def _callback(self, p):
        res = self.GetNextMessage()
        #print(res, self.__messageQueue.get_status())
        if self.__messageQueue.get_status() == [0, 2, 0]: #Settings properly done
            print('OK')
            self.__eventHandler.set()

    def InitializeSimulations(self):
        """

        :return:
        """
        return self.__InitializeSimulations()

    def BuildDeviceList(self):
        """

        :return: Error Code
        """
        return self._error_check(self.__BuildDeviceList())

    def GetDeviceListSize(self):
        """

        :return: int16
        """
        return self.__GetDeviceListSize()

    def CheckConnection(self):
        """

        :return: Boolean
        """
        return self.__CheckConnection(self.__serial)

    def OpenConnection(self):
        """

        :return:
        Error Code
        """
        return self._error_check(self.__Open(self.__serial))

    def GetStatusBits(self, channel: int):
        """

        :param channel: [1 - 4] for KIM101
        :return: DWORD (c_ulong)
        """
        return self.__GetStatusBits(self.__serial, channel)

    def MessageQueueSize(self):
        """

        :return: int
        """
        return self.__MessageQueueSize(self.__serial)

    def GetFirmwareVersion(self):
        """

        :return: DWORD (c_ulong)
        """
        return self.__GetFirmwareVersion(self.__serial)

    def PollingDuration(self):
        """

        :return: int64 (in ms)
        """
        return self.__PollingDuration(self.__serial)

    def StartPolling(self, time: int):
        """

        :param time: int (in ms)
        :return: Boolean (True if successful)
        """
        return self.__StartPolling(self.__serial, time)

    def RegisterMessageCallback(self):
        self.__RegisterMessageCallback(self.__serial, self.__fn)

    def GetNextMessage(self):
        """

        :return: Boolean (True if successful)
        """
        res = self.__GetNextMessage(self.__serial, self.__messageQueue.msg_type, self.__messageQueue.msg_id,
                                    self.__messageQueue.msg_data)
        return res

    def GetHardwareInfoBlock(self):
        """

        :return: Dict
        """
        value = TLI_HardwareInformation()
        self._error_check(self.__GetHardwareInfoBlock(self.__serial, value))
        dict = {
            "Serial Number": value.serialNumber,
            "Model Number": value.modelNumber,
            "Type": value.type,
            "Firmware Version": value.firmwareVersion,
            "Notes": value.notes,
            "Device Data": value.deviceDependantData,
            "Hardware Version": value.hardwareVersion,
            "Modification State": value.modificationState,
            "Number of channels": value.numChannels
        }
        return dict

    def SetZero(self):
        return self._error_check(self.__SetZero(self.__serial))

    def SetDisplayMode(self, mode):
        self.__eventHandler.clear()
        assert (mode == 1 or mode == 2 or mode == 3)
        return self._error_check(self.__SetDisplayMode(self.__serial, mode))

    def GetReadingExt(self, clip):
        overrange = c_bool(1)
        if not self.__eventHandler.wait(self.__timeout): #Must wait until the settings is properly done
            print('Timeout achieved. Updating position to the current position.')
        response = self.__GetReadingExt(self.__serial, clip, overrange)
        return (response, overrange)

    def GetMaximumTravel(self):
        return self.__GetMaximumTravel(self.__serial)

    def GetForceCalib(self):
        return self.__GetForceCalib(self.__serial)

    def GetHubAnalogOutput(self):
        return self.__GetHubAnalogOutput(self.__serial)

    def SetHubAnalogOutput(self, mode):
        assert (mode == 1 or mode == 2)
        return self._error_check(self.__SetHubAnalogOutput(self.__serial, mode))