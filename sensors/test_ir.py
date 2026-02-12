import smbus
import time

bus = smbus.SMBus(1)
addr = 0x57

bus.write_byte_data(addr, 0x09, 0x40)
time.sleep(0.2)
bus.write_byte_data(addr, 0x09, 0x03)
bus.write_byte_data(addr, 0x0D, 0xFF)
time.sleep(1)

print("NO FINGER - 3 seconds...")
time.sleep(3)

for i in range(5):
    d = bus.read_i2c_block_data(addr, 0x07, 6)
    ir = (d[3]<<16)|(d[4]<<8)|d[5]
    print(f"NO FINGER: IR={ir}")
    time.sleep(0.3)

print("\nPUT FINGER NOW! - 3 seconds...")
time.sleep(3)

for i in range(5):
    d = bus.read_i2c_block_data(addr, 0x07, 6)
    ir = (d[3]<<16)|(d[4]<<8)|d[5]
    print(f"WITH FINGER: IR={ir}")
    time.sleep(0.3)
