import asyncio
import json
import math
import matplotlib

import matplotlib.pyplot as plt
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QTimer
from azure.eventhub.aio import EventHubConsumerClient
from azure.iot.hub import IoTHubRegistryManager
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime, timedelta

matplotlib.use("Qt5Agg")

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, hostname: str, deviceId: str, sharedAccessKey: str, sharedAccessKeyName: str, eventHubHostName: str, eventHubEntityPath: str):
        super().__init__()

        uic.loadUi("iotgui.ui", self)

        # IoT Hub Data
        self.CONSUMER_GROUP = "testgroup"
        self.DEVICE_ID = deviceId
        self.EVENTHUB_CONNECTION_STR = f"Endpoint={eventHubHostName};SharedAccessKeyName={sharedAccessKeyName};SharedAccessKey={sharedAccessKey};EntityPath={eventHubEntityPath}"
        self.SERVICE_CONNECTION_STR = f"HostName={hostname};SharedAccessKeyName={sharedAccessKeyName};SharedAccessKey={sharedAccessKey}"

        # Data arrays
        self.timeData = []
        self.temperatureData = []
        self.humidityData = []

        # Alerts
        self.dew_alert = True
        self.temp_alert = True
        self.humidity_alert = True

        # Plots
        self.temp_fig = Figure(figsize=(4,3), facecolor='#F0F0F0')
        self.temp_canvas = FigureCanvas(self.temp_fig)
        self.temp_plot_layout = QtWidgets.QVBoxLayout(self.temp_plot)
        self.temp_plot_layout.addWidget(self.temp_canvas)

        self.hum_fig = Figure(figsize=(4,3), facecolor='#F0F0F0')
        self.hum_canvas = FigureCanvas(self.hum_fig)
        self.hum_plot_layout = QtWidgets.QVBoxLayout(self.hum_plot)
        self.hum_plot_layout.addWidget(self.hum_canvas)

        # Timers
        self.plot_timer = QTimer(self)
        self.plot_timer.timeout.connect(self.update_interface)
        self.plot_timer.start(1000)

        # Buttons
        self.startButton.clicked.connect(self.update_data)
        self.fetch_history_button.clicked.connect(self.get_history)

    def logAction(self, action):
        text: str = self.log_window.toPlainText()
        newText: str = text + f"[{datetime.now().strftime('%H:%M:%S')}] {action}\n"
        text: str = self.log_window.setPlainText(newText)
        self.log_window.verticalScrollBar().setValue(self.log_window.verticalScrollBar().maximum())

    async def on_event(self, partition_context, event):
        print(f"[Telemetry] {event.body_as_str()}")
        telemetry = json.loads(event.body_as_str())

        if len(self.timeData) < 2:
            self.timeData.append(datetime.fromisoformat(telemetry["time"]))
            self.temperatureData.append(float(telemetry["temperature"]))
            self.humidityData.append(float(telemetry["humidity"]))
        elif (datetime.fromisoformat(telemetry["time"]) < self.timeData[0] or datetime.fromisoformat(telemetry["time"]) > self.timeData[-1]):
            self.timeData.append(datetime.fromisoformat(telemetry["time"]))
            self.temperatureData.append(float(telemetry["temperature"]))
            self.humidityData.append(float(telemetry["humidity"]))

        #Sort to assert assert proper times
        combined = list(zip(self.timeData, self.temperatureData, self.humidityData))
        combined.sort(key=lambda x: x[0])
        self.timeData, self.temperatureData, self.humidityData = map(list, zip(*combined))

    async def receive_telemetry(self):
        client = EventHubConsumerClient.from_connection_string(
            conn_str=self.EVENTHUB_CONNECTION_STR,
            consumer_group=self.CONSUMER_GROUP
            )
        async with client:
            self.logAction("Connected to IoT Hub")
            self.logAction("Listening for telemetry from IoT Hub...")
            await client.receive(
                on_event=self.on_event,
                starting_position="@latest",
                )
    
    def update_data(self):
        asyncio.create_task(self.receive_telemetry())

    def get_history(self):
        elems = self.historyNumber.text()

        if not elems.isdigit():
            self.logAction("Invalid number entered for history. Must be an integer.")
            return
        
        self.logAction(f"Request {elems} history data elements from Sensor")

        manager = IoTHubRegistryManager(self.SERVICE_CONNECTION_STR)
        payload = json.dumps({"command": "get_history", "count": int(elems)})
        manager.send_c2d_message(self.DEVICE_ID, payload)

    def calculate_dew_point(self):
        if len(self.temperatureData) and len(self.humidityData):
            a = 17.27
            b = 237.7
            temp = float(self.temperatureData[-1])
            hum = float(self.humidityData[-1])
            alpha = ((a * temp) / (b + temp)) + math.log(float(hum) / 100.0)
            return (b * alpha) / (a - alpha)
        return 0 
    
    def update_dew_point(self):
        dew_point = self.calculate_dew_point()
        self.dew_label.setText(f"{dew_point:.2f} °C")

        if dew_point >= 15 and dew_point <= 18:
            self.dew_label.setStyleSheet("color: #fcba03")
            if self.dew_alert:
                self.logAction("Triggered minor alert for Dew Point")
                self.dew_alert = False
        elif dew_point > 18:
            self.dew_label.setStyleSheet("color: red")
            if self.dew_alert:
                self.logAction("Triggered major alert for Dew Point")
                self.dew_alert = False
        else:
            self.dew_label.setStyleSheet("color: green")
            self.dew_alert = True

    def update_temperature(self):
        if len(self.temperatureData): 
            latest_temp = float(self.temperatureData[-1])
            self.temperature_label.setText(f"{latest_temp:.2f} °C")

            if latest_temp >= 25 and latest_temp <= 27:
                self.temperature_label.setStyleSheet("color: #fcba03")
                if self.temp_alert:
                    self.logAction("Triggered minor alert for Temperature")
                    self.temp_alert = False
            elif latest_temp > 27:
                self.temperature_label.setStyleSheet("color: red")
                if self.temp_alert:
                    self.logAction("Triggered major alert for Temperature")
                    self.temp_alert = False
            else:
                self.temperature_label.setStyleSheet("color: green")
                self.temp_alert = True

    def update_humidity(self):
        if len(self.humidityData): 
            latest_humidity = float(self.humidityData[-1])
            self.humidity_label.setText(f"{latest_humidity:.2f} %")

            if latest_humidity >= 60 and latest_humidity <= 70:
                self.humidity_label.setStyleSheet("color: #fcba03")
                if self.humidity_alert:
                    self.logAction("Triggered minor alert for Humidity")
                    self.humidity_alert = False
            elif latest_humidity > 70:
                self.humidity_label.setStyleSheet("color: red")
                if self.humidity_alert:
                    self.logAction("Triggered major alert for Humidity")
                    self.humidity_alert = False
            else:
                self.humidity_label.setStyleSheet("color: green")
                self.humidity_alert = True
    
    def update_plot(self):
        if not self.timeData:
            return

        # Temperature plot
        self.temp_fig.clear()
        ax1 = self.temp_fig.add_subplot(111)
        ax1.plot(self.timeData, self.temperatureData)
        ax1.set_xlim(datetime.now()-timedelta(minutes=5), datetime.now())
        ax1.set_title("Temperature")
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Temperature [°C]")
        ax1.set_facecolor("#F0F0F0")
        ax1.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))
        ax1.grid(True, linestyle='-', linewidth=0.5)
        self.temp_canvas.draw()

        # Humidity plot
        self.hum_fig.clear()
        ax2 = self.hum_fig.add_subplot(111)
        ax2.plot(self.timeData, self.humidityData)
        ax2.set_xlim(datetime.now()-timedelta(minutes=5), datetime.now())
        ax2.set_title("Humidity")
        ax2.set_xlabel("Time")
        ax2.set_ylabel("Humidity [%]")
        ax2.set_facecolor("#F0F0F0")
        ax2.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))
        ax2.grid(True, linestyle='-', linewidth=0.5)
        self.hum_canvas.draw()

    def update_interface(self):
        self.update_plot()
        self.update_temperature()
        self.update_humidity()
        self.update_dew_point()