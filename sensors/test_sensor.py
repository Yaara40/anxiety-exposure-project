import time
import smbus

print("checking i2c connection")
try:
	bus = smbus.SMBus(1)

	SENSOR_ADDRESS = 0x57

	data = bus.read_byte_data(SENSOR_ADDRESS, 0x00)
	print("the sensor is responding!")
	print(f"Initial data: {data}")
	
	print("\nPut your finger on the sensor")
	time.sleep(3)
	
	print("\nReading 10 measurements...")
	
	for i in range(10):
		try:
			#Basic data reading
			data = bus.read_byte_data(SENSOR_ADDRESS, 0x00)
			print(f"Measurement {i+1}: {data}")
			time.sleep(1)
		except:
			print(f"Measurement {i+1}: Read ERROOR")
		print("\nTest compleated!")
		
except Exception as e:
	print(f"Error: {e}")
	print("\nCheck:")
	print("1. Sensor is stable")
	print("2. sudo i2cdetect -y 1 shows 57")
	
	
