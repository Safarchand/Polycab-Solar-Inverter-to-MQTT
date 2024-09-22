import json
import asyncio
import datetime
import paho.mqtt.client as paho
from astral import LocationInfo
from astral.sun import sun
from bleak import BleakClient, BleakScanner, BleakError


# Characteristic
WRITE_CHARACTERISTIC_UUID = "0000ff11-0000-1000-8000-00805f9b34fb"
NOTIFY_CHARACTERISTIC_UUID = "0000ff12-0000-1000-8000-00805f9b34fb"


REQ_SI = bytearray.fromhex("0103100100201112") # Solar Input, Inverter Power etc command
REQ_ETODAY = bytearray.fromhex("01031021001DD109")# E-Today, E-Total, Peak Power etc command

# Passed through as globals
address = ''
Notifications = {0: '', 1: ''}
Notification_no = 0


client = paho.Client(paho.CallbackAPIVersion.VERSION2)
client.username_pw_set(username="USERNAME_PLACEHOLDER", password="PASSWORD_PLACEHOLDER") # Change this

client.connect("SERVER_ADDRESS_PLACEHOLDER", 1883, keepalive = 180) # Change this

def get_forcast(city: str, country: str, timezone: str, latitude: float, longitude: float, delta: int = 1) -> tuple:
    """
    Fetches the local time, sunset and sunrise info for the city
    """
    city_info = LocationInfo(city, country, timezone, latitude, longitude)
    local_time = datetime.datetime.now(city_info.tzinfo)
    s = sun(city_info.observer, datetime.date.today() + datetime.timedelta(days=delta), tzinfo=city_info.tzinfo)
    s1 = sun(city_info.observer, datetime.date.today(), tzinfo=city_info.tzinfo)
    todays_sunset = s1["sunset"]

    return local_time, todays_sunset, s["sunrise"]

async def handle_error(local_time: datetime, todays_sunset: datetime, sunrise: datetime) -> float:
    sleep_time = (sunrise - local_time).total_seconds()
    if local_time > todays_sunset:
        print(f"Its dark -_- sleeping for {sleep_time / 3600} hours before trying again zzZ")
        await asyncio.sleep(sleep_time)


def notification_handler(sender: str, data: bytearray) -> None:
    global Notifications, Notification_no
    print(f"[NOTIFY] Notification from {sender}: {data.hex()}")
    Notifications[Notification_no] += data.hex()


# Convert Hex to Int, Division factor defaults to 1 if not explicitely provided
def hex_to_int(data: str, position1: int, position2: int, division: int = 1) -> int:
    return int(data[position1:position2], 16) / division

# Calculate values and 
def calculate_values(data: dict) -> dict:
    try:
        # Initialize the variables
        E_Today, E_Total, Peak_Power, Active_Power, Solar_Input, Inverter_Power, L1V, L1C, Temperature = (None,) * 9
        for d in data: # Loop through all the dicts
            # Caculate E-Today and E-Total if the notification is resulted by 01031021001DD109 command
            if data[d].startswith("01033"):
                E_Today = hex_to_int(data[d], 34, 38, 1000)
                E_Total = hex_to_int(data[d], 10, 14, 1000)
                Peak_Power = hex_to_int(data[d], 114, 118, 10000)
                Active_Power = hex_to_int(data[d], 98, 102, 10)
            else:
                Solar_Input = hex_to_int(data[d], 78, 82, 10)
                Inverter_Power = hex_to_int(data[d], 18, 22, 10000)
                L1V = hex_to_int(data[d], 6, 10, 10)
                L1C = hex_to_int(data[d], 10, 14, 100)
                Temperature = hex_to_int(data[d], 116, 118)
    except:
        print("Error calculating values")
        
    data = {
        'Solar_Input' : Solar_Input,
            'Inverter_Power' : Inverter_Power,
            'Peak_Power' : Peak_Power,
            'Active_Power' : Active_Power,
            'L1_Voltage' : L1V,
            'L1_Current' : L1C,
            'Temperature': Temperature,
            'E_Today' : E_Today,
            'E_Total' : E_Total
    }
    return data

async def subscribe_notification(client: BleakClient, Characteristic_UUID: str, notification_handler: callable) -> None:
    try:
        await client.start_notify(Characteristic_UUID, notification_handler)
        print(f"[SUBSCRIBE] Subscribed to notifications on {NOTIFY_CHARACTERISTIC_UUID}")
    except Exception as e:
        print(f"[SUBSCRIBE] Failed to subscribe to notifications on {NOTIFY_CHARACTERISTIC_UUID}")

async def send_data(client: BleakClient, Characteristic_UUID: str, Command: bytes, Delay: float = 0.5) -> None:
    global Notification_no
    try:
        await client.write_gatt_char(Characteristic_UUID, Command)
        print(f"Requested {Command.hex()} to {Characteristic_UUID}")
    except Exception as e:
        print(f"Error writing to {Characteristic_UUID}: {e}")

    await asyncio.sleep(Delay) # Delay to wait for notification

    # Toggle the value between 0 and 1
    Notification_no = (Notification_no + 1) % 2

# Resolve device name to address
async def find_device(Name: str) -> str:
    try:
        devices = await BleakScanner.discover()
        for device in devices:
            if device.name == Name:
                return device.address
        print(f"Cant find the device: {Name}")
        return None
    except:
        print(f"Error: finding address")
        return None
    

async def main(Name: str) -> tuple:
    global Notifications, address
    if not address:
        print(f"Trying to find address for device: {Name}")
        address = await find_device(Name)
    local_time, todays_sunset, sunrise = get_forcast("CITY_PLACEHOLDER", "COUNTRY_PLACEHOLDER", "TIMEZONE_PLACEHOLDER", LATITUTE_PLACEHOLDER, LONGITUDE_PLACEHOLDER) # Change this
    if address:
        while True:
            try: 
                async with BleakClient(address) as client:
                    print(f"Connected: {client.is_connected}")

                    # Subscribe to Notifications
                    try:
                        await subscribe_notification(client, NOTIFY_CHARACTERISTIC_UUID, notification_handler)
                        await send_data(client, WRITE_CHARACTERISTIC_UUID, REQ_ETODAY)
                        await send_data(client, WRITE_CHARACTERISTIC_UUID, REQ_SI)
                    except Exception as e:
                        print(f"Error: {e}")
                        continue

                    # Stop Notifications
                    try:
                        print(f"[UNSUBSCRIBE] unsubscribing from notifications on {NOTIFY_CHARACTERISTIC_UUID}")
                        await client.stop_notify(NOTIFY_CHARACTERISTIC_UUID)
                    except:
                        print(f"[UNSUBSCRIBE] Failed to unsubscribe from notifications on {NOTIFY_CHARACTERISTIC_UUID}")
                        continue
                values = calculate_values(Notifications)
                Notifications = {0: '', 1: ''}
                return values
            except BleakError as e:
                print(f"BleakError: {e}")
                await handle_error(local_time, todays_sunset, sunrise)
                continue
            except Exception as e:
                print(f"Exception: {e}")
                await handle_error(local_time, todays_sunset, sunrise)
                continue
    else:
        await handle_error(local_time, todays_sunset, sunrise)

async def send_mqtt(Name: str, Delay: float) -> None:
    while True:
        data = await main(Name)
        client.publish('solar-data', json.dumps(data), 0)
        if data:
            print(data)
        else:
            print("No data to print")
        await asyncio.sleep(Delay)

if __name__ == "__main__":
    Name = "BLE1295" # Solar Inverter, Change this
    Delay = 5.0
    try:
        asyncio.run(send_mqtt(Name, Delay))
    except KeyboardInterrupt:
        print("User interrupted the script :'(")
