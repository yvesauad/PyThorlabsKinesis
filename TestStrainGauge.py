from Modules import Kinesis_StrainGauge

my_piezo = Kinesis_StrainGauge.TLKinesisStrainGauge('59000001', pollingTime=100, TIMEOUT=5.0, SIMULATION = True)
print(my_piezo.CheckConnection())

my_piezo.SetZero()
print(my_piezo.GetMaximumTravel() / 100) #In microns
print(my_piezo.GetForceCalib())

my_piezo.SetDisplayMode(0)
position = my_piezo.GetReadingExt(False)
print(position)

my_piezo.SetDisplayMode(1)
voltage = my_piezo.GetReadingExt(False)
print(voltage)

my_piezo.SetDisplayMode(2)
force = my_piezo.GetReadingExt(False)
print(force)
