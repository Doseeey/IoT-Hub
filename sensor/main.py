import asyncio
import os

from dotenv import load_dotenv
from Sensor import Sensor


async def main():
    load_dotenv()

    HostName = os.getenv("HostName")
    DeviceId = os.getenv("DeviceId")
    SharedAccessKey = os.getenv("SharedAccessKey")

    sensor = Sensor(HostName, DeviceId, SharedAccessKey)
    await sensor.connect()

    try:
        await sensor.gather()
    finally:
        await sensor.disconnect()
        

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Device stopped.")
