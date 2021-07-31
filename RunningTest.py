from Modules import Kinesis_PMC

my_piezo = Kinesis_PMC.TLKinesisPiezoMotorController('97101311')

val = 150
[my_piezo.MoveRelative(x+1, val) for x in range(4)]