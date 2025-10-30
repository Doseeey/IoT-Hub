import asyncio
import sys
import os
import qasync

from PyQt5 import QtWidgets
from dotenv import load_dotenv

from MainWindow import MainWindow
# --------------------------------------------------
# COMMAND SENDER (sync inside async loop)
# --------------------------------------------------
# async def send_command_loop():
#     manager = IoTHubRegistryManager(SERVICE_CONNECTION_STR)
#     print(" Command interface ready. Type 'get_history <n>' or 'exit'.\n")  
#     while True:
#         cmd = input("Command> ").strip()
#         if cmd.lower() in ["exit", "quit"]:
#             print("Exiting command loop...")
#             break
#         elif cmd.startswith("get_history"):
#             parts = cmd.split()
#             n = int(parts[1]) if len(parts) > 1 else 5
#             payload = json.dumps({"command": "get_history", "count": n})
#             manager.send_c2d_message(DEVICE_ID, payload)
#             print(f" Sent command to device: {payload}")
#         else:
#             print("Unknown command. Try: get_history <n> or exit")

async def main():
    load_dotenv()

    app = QtWidgets.QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    HostName = os.getenv("HostName")
    DeviceId = os.getenv("DeviceId")
    SharedAccessKey = os.getenv("SharedAccessKey")
    SharedAccessKeyName = os.getenv("SharedAccessKeyName")
    EventHubHostname = os.getenv("EventHubHostname")
    EventHubEntityPath = os.getenv("EventHubEntityPath")

    window = MainWindow(HostName, DeviceId, SharedAccessKey, SharedAccessKeyName, EventHubHostname, EventHubEntityPath)
    window.show()

    with loop:
        await loop.run_forever()


if __name__ == "__main__":
    asyncio.run(main())