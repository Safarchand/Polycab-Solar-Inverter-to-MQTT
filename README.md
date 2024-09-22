# Polycab Solar Inverter to MQTT

This script communicates with the Polycab PSIS-3K-SM1 inverter over Bluetooth, sending key inverter data like solar generation to an MQTT broker. The values were reverse-engineered from the Android app used for local monitoring.

## Inverter Model:
**PSIS-3K-SM1**

## Key Features:
- **Auto Sleep:** Automatically enters sleep mode after sunset and wakes up at sunrise
- **Error Handling:** Automatically retries the connection if an error occurs

## Mapped Variables:
- **Solar Input:** Current power generated from solar input
- **Inverter Power:** Power being used by the inverter
- **Peak Power:** Maximum power achieved during the day
- **Active Power:** Real-time power consumption
- **L1 Voltage:** Voltage on Line 1
- **L1 Current:** Current on Line 1
- **Temperature:** Inverter temperature
- **E Today:** Total energy generated today (which was imp for me)
- **E Total:** Lifetime energy generation (also imp for me)
