
import asyncio
import logging
from pathlib import Path

from app.channels.rubika import RubikaConnector
from app.channels.schemas import OutgoingMessage


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
        print("Waiting for a test message from another account...")

        incoming = await asyncio.wait_for(
            receive_one_message(connector),
            timeout=120,
        )

        print("Incoming message received.")
        print("Preparing a test reply...")

        outgoing = OutgoingMessage(
            platform="rubika",
            external_chat_id=incoming.external_chat_id,
            text="سلام! این پیام برای تست Rubika Connector ارسال شده است.",
            message_type="text",
            reply_to_message_id=incoming.external_message_id,
        )

        result = await connector.send(outgoing)

        print("\nSend operation completed.")
        print("Send status:", result.status.value)
        print("Message ID received:", bool(result.external_message_id))

        if result.error_code:
            print("Error code:", result.error_code)
            print("Error message:", result.error_message)

    finally:
        print("\nDisconnecting...")
        await connector.disconnect()
        print("Final status:", await connector.get_status())


if __name__ == "__main__":
    asyncio.run(main())






# python -c "import runpy; runpy.run_path('test/rubika_send_smoke.py', run_name='__main__')"