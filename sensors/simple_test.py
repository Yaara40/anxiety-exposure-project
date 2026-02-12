import time
import smbus

bus = smbus.SMBus(1)
address = 0x57
		
#read part id
part_id = bus.read_byte_data(address, 0xFF)
print(f"part ID: {part_id}")
#reset
bus.write_byte_data(address, 0x09, 0x40)
time.sleep(0.1)
#sp02 mode
bus.write_byte_data(address, 0x09, 0x03)
#reset
bus.write_byte_data(address, 0x0C, 0xFF)
bus.write_byte_data(address, 0x0D, 0xFF)

time. sleep(1)
print("\nPut your finger on the sensor")
time.sleep(3)
for i in range(20):
	data = bus.read_i2c_block_data(address, 0x07, 6)
	red = (data[0] << 16) | (data[1] << 8) | data[2]
	ir = (data[3] << 16) | (data[4] << 8) | data[5]
	print(f"{i+1}: RED={red:7d} | IR={ir:7d}")
	time.sleep(0.5)
		
print("\nTest completed!")
		
