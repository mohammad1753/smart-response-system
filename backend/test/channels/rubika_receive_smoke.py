
import asyncio
import logging
from pathlib import Path

from app.channels.rubika import RubikaConnector


async def receive_one_message(connector):
    stream = connector.receive()

    try:
        return await anext(stream)
    finally:
        await stream.aclose()


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

        print("Connector status:", await connector.get_status())
        print("Waiting for a new incoming message...")

        print(
            "Send a private test message to this account "
            "from another Rubika account."
        )

        message = await asyncio.wait_for(
            receive_one_message(connector),
            timeout=120,
        )

        print("\nIncoming message received successfully.")
        print("Platform:", message.platform)
        print("Message type:", message.message_type)
        print("Has text:", message.text is not None)
        print("Has media:", message.media is not None)

    except asyncio.TimeoutError:
        print("No incoming message received within 120 seconds.")

    finally:
        print("\nDisconnecting...")
        await connector.disconnect()

        print(
            "Final connector status:",
            await connector.get_status(),
        )


if __name__ == "__main__":
    asyncio.run(main())



# python -c "import runpy; runpy.run_path('test/rubika_receive_smoke.py', run_name='__main__')"