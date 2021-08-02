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

LOGGERFUNC = WINFUNCTYPE(None, c_void_p)

class TLKinesisPiezoMotorController():

    def _error_check(self, val):
        if val != 0: print(f'Error {FTDI_COM_ERROR(val)}')
        return val

    def _initialize_library(self):

        libname = os.path.dirname(__file__)
        libname = os.path.join(libname, "../dlls/Thorlabs.MotionControl.KCube.InertialMotor.dll")
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
        self.__GetHardwareInfoBlock = _buildFunction(_library.KIM_GetHardwareInfoBlock, [c_char_p,
                                                                                        POINTER(TLI_HardwareInformation)], c_short)
        self.__GetDriveOPParameters = _buildFunction(_library.KIM_GetDriveOPParameters,
                                                     [c_char_p, c_ushort, POINTER(c_short), POINTER(c_int), POINTER(c_int)], c_short)
        self.__SetDriveOPParameters = _buildFunction(_library.KIM_SetDriveOPParameters,
                                                     [c_char_p, c_ushort, c_short, c_int, c_int], c_short)

    def __init__(self, serialno, pollingTime = 100, TIMEOUT = 5):
        self._initialize_library()
        self.__serial = serialno.encode()
        self.__fn = LOGGERFUNC(self._callback)
        self.__eventHandler = threading.Event()
        self.__timeout = TIMEOUT
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
            self.__eventHandler.set()

    def updatePosition(self):
        self.__pos = self.GetCurrentPositionAll()

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
        return self._error_check(self.__CheckConnection(self.__serial))

    def OpenConnection(self):
        """

        :return:
        Error Code
        """
        return self._error_check(self.__Open(self.__serial))

    def UpdatePosition(self):
        """

        :return: None
        """
        self.__pos = self.GetCurrentPositionAll()
        return

    def MoveRelative(self, channel: int, step: int):
        """

        :param channel: [1 - 4] for KIM101
        :param step: int
        :return: Error Code
        """
        if self.__pos[channel - 1] != self.__pos[channel - 1] + step:
            self.__eventHandler.clear()
            self.__pos[channel - 1] += step
            self._error_check(self.__MoveRelative(self.__serial, channel, step))
            if not self.__eventHandler.wait(self.__timeout):
                print('Timeout achieved. Updating position to the current position.')
                self.updatePosition()
            return True
        return False

    def MoveAbsolute(self, channel: int, value: int):
        """

        :param channel: [1 - 4] for KIM101
        :param value: int
        :return: Error Check
        """
        if self.__pos[channel - 1] != value:
            self.__eventHandler.clear()
            self.__pos[channel - 1] = value
            self._error_check(self.__MoveAbsolute(self.__serial, channel, value))
            if not self.__eventHandler.wait(self.__timeout):
                print('Timeout achieved. Updating position to the current position.')
                self.updatePosition()
            return True
        return False

    def RequestStatusBits(self):
        """

        :return: Error Code
        """
        return self._error_check(self.__RequestStatusBits(self.__serial))

    def GetStatusBits(self, channel: int):
        """

        :param channel: [1 - 4] for KIM101
        :return: DWORD (c_ulong)
        """
        return self.__GetStatusBits(self.__serial, channel)

    def RequestCurrentPosition(self, channel: int):
        """

        :param channel: [1 - 4] for KIM101
        :return: Error Code
        """
        return self._error_check(self.__RequestCurrentPosition(self.__serial, channel))

    def GetCurrentPosition(self, channel: int):
        """

        :param channel: [1 - 4] for KIM101
        :return: int32
        """
        return self.__GetCurrentPosition(self.__serial, channel)

    def GetCurrentPositionAll(self):
        return [self.__GetCurrentPosition(self.__serial, x+1) for x in range(4)]

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
        msg_type = c_ulong(0x00)
        msg_id = c_ulong(0x00)
        msg_data = c_ulong(0x00)
        res = self.__GetNextMessage(self.__serial, msg_type, msg_id, msg_data)
        return (msg_type.value, msg_id.value, msg_data.value, res)

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

    def GetDriveOPParameters(self, channel: int):
        """

        :param channel: int
        :return: Dict
        """
        voltage = c_short(0x00)
        sr = c_int(0x00)
        sa = c_int(0x00)
        self._error_check(self.__GetDriveOPParameters(self.__serial, channel, voltage, sr, sa))
        dict = {
            "Voltage": voltage.value,
            "Step Rate": sr.value,
            "Step Acceleration": sa.value
        }
        return dict

    def SetDriveOPParameters(self, channel: int, voltage: int, step_rate: int, step_acc: int):
        """

        :param channel: int
        :param voltage: int
        :param step_rate: int
        :param step_acc: int
        :return: None
        """
        self._error_check(self.__SetDriveOPParameters(self.__serial, channel, voltage, step_rate, step_acc))
        return