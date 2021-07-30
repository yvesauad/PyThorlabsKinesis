from ctypes import cdll, create_string_buffer, POINTER, byref
from ctypes import c_uint, c_int, c_char, c_char_p, c_void_p, c_ushort, c_short, c_int, c_long, c_bool, c_double, c_uint64, \
            c_uint32, c_wchar, c_wchar_p, Array, CFUNCTYPE, WINFUNCTYPE
import os

def _buildFunction(call, args, result):
    call.argtypes = args
    call.restype = result
    return call


serial = b'97101311'

def c_str_array(strings):
    arr = (c_char_p * len(strings))()
    arr[:] = strings
    return arr



libname = os.path.dirname(__file__)
libname = os.path.join(libname, "Thorlabs.MotionControl.KCube.InertialMotor.dll")

_library = cdll.LoadLibrary(libname)

_BuildDeviceList = _buildFunction(_library.TLI_BuildDeviceList, None, c_short)
_GetDeviceListSize = _buildFunction(_library.TLI_GetDeviceListSize, None, c_short)
_CheckConnection = _buildFunction(_library.KIM_CheckConnection, [c_char_p], c_bool)
_Open = _buildFunction(_library.KIM_Open, [c_char_p], c_short)
_Enable = _buildFunction(_library.KIM_Enable, [c_char_p], c_short)
_EnableChannel = _buildFunction(_library.KIM_EnableChannel, [c_char_p, c_ushort], c_short)
_MoveAbsolute = _buildFunction(_library.KIM_MoveAbsolute, [c_char_p, c_ushort, c_uint], c_short)

a = _BuildDeviceList()
b = _GetDeviceListSize()
c = _CheckConnection(serial)
d = _Open(serial)
e = _CheckConnection(serial)
f = _Enable(serial)
#g = _EnableChannel(serial, 1)
h = _MoveAbsolute(serial, 1, 1)


print(a, b, c, d, e, f, h)
