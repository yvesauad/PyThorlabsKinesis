from Modules import Kinesis_InertialMotor, Kinesis_StrainGauge

"""
Instantiate my piezo controller and prints if the connection is successful. 
First string is the serial number
Polling time is the feedback message period. 
Timeout is the maximum time delay.
"""
my_piezo = Kinesis_InertialMotor.TLKinesisInertialMotor('97101311', pollingTime=100, TIMEOUT=1.5)
print(my_piezo.CheckConnection())

"""
Getting a few information from the piezo. 
"""
hardwareInfo = my_piezo.GetHardwareInfoBlock()
piezoInfo = my_piezo.GetDriveOPParameters(1)
print(hardwareInfo)
print(piezoInfo)

"""
Setting the piezo moving conditions. Max voltage is 112 moving at 250 steps/s and 1000 steps/s^2 acceleration.
Move all four channels a value of 100 relative to the initial value.
Move all four channels to the origin of the system.
Update the python position array with the hardware value. This is important to keep track between software and hardware
and to being as responsive as possible i.e. if (soft position == hardware position) => thread is set.
"""
val = 150
my_piezo.SetDriveOPParameters(1, 112, 500, 1000)
[my_piezo.MoveRelative(x+1, val) for x in range(4)]
[my_piezo.MoveAbsolute(x+1, 0) for x in range(4)]
my_piezo.UpdatePosition()

