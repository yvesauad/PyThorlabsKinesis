from Modules import Kinesis_PiezoDriver

my_piezo = Kinesis_PiezoDriver.TLKinesisPiezoDriver('29000001', pollingTime=100, TIMEOUT=5.0, SIMULATION = True)
print(my_piezo.CheckConnection())