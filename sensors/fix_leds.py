import smbus
import time

bus = smbus.SMBus(1)
address = 0x57

print("Fixing LED configuration...\n")

# Reset
bus.write_byte_data(address, 0x09, 0x40)
time.sleep(0.2)

# SpO2 mode
bus.write_byte_data(address, 0x09, 0x03)

# SpO2 config
bus.write_byte_data(address, 0x0A, 0x27)

# Try different LED registers
print("Trying register 0x0C (LED1)...")
bus.write_byte_data(address, 0x0C, 0x1F)  # Start with lower value
time.sleep(0.1)

print("Trying register 0x0D (LED2)...")  
bus.write_byte_data(address, 0x0D, 0x1F)
time.sleep(0.1)

# Also try register 0x0E (pilot LED if exists)\
try:
    bus.write_byte_data(address, 0x0E, 0x1F)
    print("Set register 0x0E")
except:
    pass

time.sleep(0.5)

# Read back
led1 = bus.read_byte_data(address, 0x0C)
led2 = bus.read_byte_data(address, 0x0D)

print(f"\nLED1 (0x0C): 0x{led1:02X}")
print(f"LED2 (0x0D): 0x{led2:02X}")

print("\nNow testing data...\n")
time.sleep(2)

for i in range(10):
    data = bus.read_i2c_block_data(address, 0x07, 6)
    red = (data[0] << 16) | (data[1] << 8) | data[2]
    ir = (data[3] << 16) | (data[4] << 8) | data[5]
    print(f"{i+1}. RED={red:7d} | IR={ir:7d}")
    time.sleep(0.3)
