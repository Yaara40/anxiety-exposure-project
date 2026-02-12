import time
import smbus

class PulseSensor:
	try:
		self.bus = smbus.SMBus(1)
		self.address = 0x57
		
		#test conncetion
		self.bus.read_byte_data(self.address, 0x00)
		print("MAX30102 connected successfuly!")
		
		self.setup_sensor()
	except Exception as e:
		print(f"Error connecting: {e}")
		self.bus = None
	
	#configure the sensor	
	def setup_sensor(self):
		if self.bus is None:
			return
		try:
			#reset
			self.bus.write_byte_data(self.address, 0x09, 0x03) #SP02 mode
			self.bus.write_byte_data(self.address, 0x0A, 0x27) #SP02 config
			self.bus.write_byte_data(self.address, 0x0C, 0x24) #LED current
			print("Sensor configured!")
		except Exception as e:
			print(f"Setup error: {e}")
	
	#read data from FIFO		
	def read_fifo(self):
		if self.bus is None:
			return 0, 0
		try:
			#read RED and IR values
			data = self.bus.read_i2c_block_data(self.address, 0x07, 6)
			red = (data[0] << 16) | (data[1] << 8) | data[2]
			ir = (data[3] << 16) | (data[4] << 8) | data[5]
			return red, ir
		except:
			return 0, 0
			
	def read_all(self):
		#read all the data
		red, ir = self.read_fifo()
		return
		{
			'red': red,
			'ir': ir,
			'timestamp': time.time()
		}
			
#test
if __name__ == "__main__":
	print("testing pulse sensor...")
	sensor = PulseSensor()
	print("\nPut your finger on the sensor")
	time.sleep(3)
	
	for i in range(20):
		data = sensor.read_all()
		print(f"Measurement {i+1}: RED={data['red']:6d} | IR={data['ir']:6d}")
		time.sleep(0.5)
		
	print("\nTest completed!")
		
