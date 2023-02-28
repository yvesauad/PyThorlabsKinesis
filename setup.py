from setuptools import setup

setup(
    name="Thorlabs_Kinesis",
    version="1.4",
    author="Yves Auad",
    description="ThorLabs Piezo Motor Controller",
    url="https://github.com/yvesauad/ThorlabsKinesis-KCubePiezo",
    packages=['Modules'],
    data_files=[('dlls', [
        'dlls/Thorlabs.MotionControl.DeviceManager.dll',
        'dlls/Thorlabs.MotionControl.KCube.InertialMotor.dll'])],
    python_requires='>=3.8.5',
)