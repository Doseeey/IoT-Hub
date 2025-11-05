import asyncio
import json
import thingspeak
import datetime
import random

from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message

class Sensor:
    def __init__(self, hostname, deviceId, sharedAccessKey):
        self.hostname = hostname
        self.deviceId = deviceId
        self.sharedAccessKey = sharedAccessKey

    def _get_data_from_thingspeak(self, n):
        #Main channel 2938875
        #Backup channel 819972
        ch = thingspeak.Channel(id=819972)
        data = json.loads(ch.get({'results': n}))

        messages = []

        for i in range(n):
            feed = data["feeds"][i]

            #can be used when will work
            #time = datetime.datetime.fromisoformat(feed["created_at"].replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S.%f")

            # Added fake noise
            temperature = float(feed["field1"]) + random.uniform(-0.01, 0.01)
            humidity = float(feed["field2"]) + random.uniform(-0.01, 0.01)

            # temperature = float(feed["field1"])
            # humidity = float(feed["field2"])

            message = Message(f'{{"time": "{datetime.datetime.now()-datetime.timedelta(seconds=6*i)}", "temperature": "{round(temperature, 2)}", "humidity": "{round(humidity, 2)}"}}')
            messages.append(message)

        return messages

    async def connect(self):
        """Connect to IoT Hub"""
        CONNECTION_STRING = f"HostName={self.hostname};DeviceId={self.deviceId};SharedAccessKey={self.sharedAccessKey}"
        self.client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
        await self.client.connect()

    async def _send_sensor_data_to_iot_hub(self):
        """Send telemetry to IoT Hub"""
        while True:
            messages = self._get_data_from_thingspeak(1)
            message = messages[0]
            await self.client.send_message(message)

            print(f"Sent message: {message}")
            await asyncio.sleep(5)

    async def _listen_for_c2d(self):
        """Listen for C2D messages"""
        print("Listening for cloud-to-device messages...")
        while True:
            message = await self.client.receive_message()  # blocking call
            print("Received command:", message.data.decode())

            try:
                cmd = json.loads(message.data.decode())
                if cmd.get("command") == "get_history":
                    # Send the last N readings
                    n = cmd.get("count", 5)
                    messages = self._get_data_from_thingspeak(n)
                    for message in messages:
                        await self.client.send_message(message)
                        print(f"Sent message from C2D: {message}")

                    print(f"Sent historical readings back to IoT Hub.")
            except Exception as e:
                print("Error handling command:", e)

    async def gather(self):
        """Gather sending telemetry and listening for c2d"""
        await asyncio.gather(
            self._send_sensor_data_to_iot_hub(),
            self._listen_for_c2d()
        )

    async def disconnect(self):
        """Disconnect from IoT Hub"""
        await self.client.disconnect()