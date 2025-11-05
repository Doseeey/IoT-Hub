import asyncio
import aiohttp
import json
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QTimer
from azure.eventhub.aio import EventHubConsumerClient
from azure.iot.hub import IoTHubRegistryManager
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime, timedelta


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, hostname: str, deviceId: str, sharedAccessKey: str, sharedAccessKeyName: str, eventHubHostName: str, eventHubEntityPath: str):
        super().__init__()

        uic.loadUi("iotgui.ui", self)

        self.CONSUMER_GROUP = "$Default"
        self.DEVICE_ID = deviceId
        self.EVENTHUB_CONNECTION_STR = f"Endpoint={eventHubHostName};SharedAccessKeyName={sharedAccessKeyName};SharedAccessKey={sharedAccessKey};EntityPath={eventHubEntityPath}"
        self.SERVICE_CONNECTION_STR = f"HostName={hostname};SharedAccessKeyName={sharedAccessKeyName};SharedAccessKey={sharedAccessKey}"

        self.timeData = []
        self.temperatureData = []
        self.humidityData = []

        self.temp_fig = Figure(figsize=(4,3), facecolor='#F0F0F0')
        self.temp_canvas = FigureCanvas(self.temp_fig)
        self.temp_plot_layout = QtWidgets.QVBoxLayout(self.temp_plot)
        self.temp_plot_layout.addWidget(self.temp_canvas)

        self.hum_fig = Figure(figsize=(4,3), facecolor='#F0F0F0')
        self.hum_canvas = FigureCanvas(self.hum_fig)
        self.hum_plot_layout = QtWidgets.QVBoxLayout(self.hum_plot)
        self.hum_plot_layout.addWidget(self.hum_canvas)


        self.plot_timer = QTimer(self)
        self.plot_timer.timeout.connect(self.update_interface)
        self.plot_timer.start(1000)

        # # QTimer to trigger periodic updates
        # self.timer = QTimer(self)
        # # self.timer.timeout.connect(self.update_data)
        # self.timer.singleShot(1000, self.update_data)  # 5 seconds

        # Buttons
        self.startButton.clicked.connect(self.update_data)

    async def on_event(self, partition_context, event):
        print(f"[Telemetry] {event.body_as_str()}")
        telemetry = json.loads(event.body_as_str())
        self.timeData.append(datetime.fromisoformat(telemetry["time"]))
        self.temperatureData.append(telemetry["temperature"])
        self.humidityData.append(telemetry["humidity"])

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

    def update_interface(self):
        self.update_plot()
        if len(self.temperatureData): 
            latest_temp = self.temperatureData[-1]
            self.temperature_label.setText(f"{latest_temp} °C")
        if len(self.humidityData): 
            latest_humidity = self.humidityData[-1]
            self.humidity_label.setText(f"{latest_humidity} %")
        
    def update_plot(self):
        if not self.timeData:
            return

        # Temperature plot
        self.temp_fig.clear()
        ax1 = self.temp_fig.add_subplot(111)
        ax1.plot(self.timeData, self.temperatureData)
        ax1.set_xlim(self.timeData[-20], self.timeData[-1])
        ax1.set_title("Temperature")
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Temperature [°C]")
        ax1.set_facecolor("#F0F0F0")
        ax1.grid(True, linestyle='-', linewidth=0.5)
        self.temp_canvas.draw()

        # Humidity plot
        self.hum_fig.clear()
        ax2 = self.hum_fig.add_subplot(111)
        ax2.plot(self.timeData, self.humidityData)
        ax2.set_xlim(self.timeData[-20], self.timeData[-1])
        ax2.set_title("Humidity")
        ax2.set_xlabel("Time")
        ax2.set_ylabel("Humidity [%]")
        ax2.set_facecolor("#F0F0F0")
        ax2.grid(True, linestyle='-', linewidth=0.5)
        self.hum_canvas.draw()

