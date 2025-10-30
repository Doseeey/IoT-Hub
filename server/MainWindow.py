import asyncio
import aiohttp
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QTimer
from azure.eventhub.aio import EventHubConsumerClient
from azure.iot.hub import IoTHubRegistryManager


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, hostname: str, deviceId: str, sharedAccessKey: str, sharedAccessKeyName: str, eventHubHostName: str, eventHubEntityPath: str):
        super().__init__()

        uic.loadUi("iotgui.ui", self)

        self.CONSUMER_GROUP = "$Default"
        self.DEVICE_ID = deviceId
        self.EVENTHUB_CONNECTION_STR = f"Endpoint={eventHubHostName};SharedAccessKeyName={sharedAccessKeyName};SharedAccessKey={sharedAccessKey};EntityPath={eventHubEntityPath}"
        self.SERVICE_CONNECTION_STR = f"HostName={hostname};SharedAccessKeyName={sharedAccessKeyName};SharedAccessKey={sharedAccessKey}"

        #self.label_status.setText("Waiting for data...")
        print("Waiting for data...")

        # QTimer to trigger periodic updates
        self.timer = QTimer(self)
        # self.timer.timeout.connect(self.update_data)
        self.timer.singleShot(1000, self.update_data)  # 5 seconds

    async def on_event(self, partition_context, event):
        print(f"[Telemetry] {event.body_as_str()}")

    async def receive_telemetry(self):
        client = EventHubConsumerClient.from_connection_string(
            conn_str=self.EVENTHUB_CONNECTION_STR,
            consumer_group=self.CONSUMER_GROUP
            )
        async with client:
            print(" Listening for telemetry from IoT Hub...")
            await client.receive(
                on_event=self.on_event,
                starting_position="-1", # from beginning
                )
    
    def update_data(self):
        # Schedule async task without blocking GUI
        asyncio.create_task(self.receive_telemetry())

