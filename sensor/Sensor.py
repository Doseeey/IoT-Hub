import asyncio
import json
import thingspeak
import datetime

from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message

class Sensor:
    def __init__(self, hostname, deviceId, sharedAccessKey):
        self.hostname = hostname
        self.deviceId = deviceId
        self.sharedAccessKey = sharedAccessKey

        self.history = [1, 2, 3, 4, 5] #to do for c2d

        
    async def connect(self):
        """Connect to IoT Hub"""
        CONNECTION_STRING = f"HostName={self.hostname};DeviceId={self.deviceId};SharedAccessKey={self.sharedAccessKey}"
        self.client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
        await self.client.connect()

    async def _send_sensor_data_to_iot_hub(self):
        """Send telemetry to IoT Hub"""
        while True:
            ch = thingspeak.Channel(id=2938875)
            data = json.loads(ch.get({'results': 1}))
            feed = data["feeds"][0]

            temperature = feed["field1"]
            humidity = feed["field2"]

            message = Message(f'{{"time": "{datetime.datetime.now()}", "temperature": "{temperature}", "humidity": "{humidity}"}}')
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
                    subset = self.history[-n:]
                    reply = Message(json.dumps({"history": subset}))
                    await self.client.send_message(reply)
                    print(f"Sent {len(subset)} historical readings back to IoT Hub.")
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