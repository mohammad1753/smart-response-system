
import asyncio
import logging
from pathlib import Path

from app.channels.rubika import RubikaConnector


async def main():
    logging.basicConfig(level=logging.INFO)

    session_path = (
        Path.home()
        / ".smart_response_system"
        / "sessions"
        / "rubika_primary"
    )

    connector = RubikaConnector(
        session_path=session_path,
    )

    try:
        print("Connecting to Rubika...")

        await asyncio.wait_for(
            connector.connect(),
            timeout=45,
        )

        status = await connector.get_status()

        print("Connector status:", status)

        if status != "connected":
            raise RuntimeError(
                f"Unexpected connector status: {status}"
            )

        print("Rubika WebSocket connected successfully.")

    finally:
        print("Disconnecting...")

        await connector.disconnect()

        print(
            "Status after disconnect:",
            await connector.get_status(),
        )


if __name__ == "__main__":
    asyncio.run(main())




# python -c "import runpy; runpy.run_path('test/rubika_connection_smoke.py', run_name='__main__')"