# Polycab Solar Inverter to MQTT

This script runs as a service on my raspberry pi zero 2 w and communicates with the Polycab PSIS-3K-SM1 inverter over Bluetooth. It feeds the key inverter data like solar generation, to the mosquitto MQTT broker on my Home assistant. The values were reverse-engineered from the [Android app](https://play.google.com/store/apps/details?id=com.polycab.e&hl=en_IN) used for local monitoring.

## Inverter Model:
**PSIS-3K-SM1**

## Key Features:
- **Auto Sleep:** Automatically enters sleep mode after sunset and wakes up at sunrise
- **Error Handling:** Automatically retries the connection if an error occurs

## Mapped Variables:
- **Solar Input:** Power coming from solar panels
- **Inverter Power:** The power going to the grid from the inverter
- **Peak Power:** Maximum power achieved during the day
- **Active Power:** Not exactly sure what this is (lmk if you know)
- **L1 Voltage:** Voltage on Line 1
- **L1 Current:** Current on Line 1
- **Temperature:** Inverter temperature
- **E Today:** Total energy generated today (which was imp for me)
- **E Total:** Lifetime energy generation (also imp for me)
