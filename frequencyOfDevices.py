import asyncio
from bleak import BleakScanner
from collections import defaultdict
from datetime import datetime

# Configurable parameters
SCAN_DURATION = 10  # How long each individual scan lasts (seconds)
INTERVAL_BETWEEN_SCANS = 20  # Time to wait between scans (seconds)
NUMBER_OF_SCANS = 3

async def scan_devices():
    """
    Perform a single Bluetooth scan and return discovered devices.
    """
    try:
        devices = await BleakScanner.discover(timeout=SCAN_DURATION)
        return devices
    except Exception as e:
        print(f"Error during scan: {e}")
        return []

async def multiple_scans(num_scans=NUMBER_OF_SCANS, interval=INTERVAL_BETWEEN_SCANS):
    """
    Perform multiple Bluetooth scans with specified intervals.
    
    Args:
        num_scans (int): Number of scans to perform
        interval (int): Time to wait between scans in seconds
    """
    device_counts = defaultdict(int)
    device_rssi_history = defaultdict(list)
    
    print(f"Starting {num_scans} Bluetooth scans...")
    print(f"Scan duration: {SCAN_DURATION} seconds")
    print(f"Interval between scans: {interval} seconds")
    
    for scan_num in range(num_scans):
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"\nScan {scan_num + 1}/{num_scans} at {current_time}")
        
        devices = await scan_devices()
        print(f"Detected {len(devices)} devices in this scan")
        
        for device in devices:
            if device.rssi >= -80: #WE ARE IGNORING WEAK SIGNALS
                device_counts[device.address] += 1
                device_rssi_history[device.address].append(device.rssi)
                
                print(f"  Device: {device.name or 'Unknown'}")
                print(f"  UUID: {device.address}")
                print(f"  RSSI: {device.rssi} dBm")
                print("  ----------------------")
        
        if scan_num < num_scans - 1:  # Don't wait after the last scan
            print(f"\nWaiting {interval} seconds before next scan...")
            await asyncio.sleep(interval)
    
    # Print final summary with average RSSI values
    print("\nFinal Device Summary:")
    print("------------------------")
    for uuid, count in device_counts.items():
        avg_rssi = sum(device_rssi_history[uuid]) / len(device_rssi_history[uuid])
        print(f"UUID: {uuid}")
        print(f"  Appeared in {count}/{num_scans} scans")
        print(f"  Average RSSI: {avg_rssi:.1f} dBm")
        print(f"  RSSI variance: {max(device_rssi_history[uuid]) - min(device_rssi_history[uuid])} dBm")
        print("------------------------")

async def main():
    try:
        await multiple_scans()
    except KeyboardInterrupt:
        print("\nScanning stopped by user")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())