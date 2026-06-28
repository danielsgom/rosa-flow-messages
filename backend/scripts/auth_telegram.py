#!/usr/bin/env python
"""
Script to authenticate Telegram session interactively.
Run this ONCE to create the session file, then you can run the main app normally.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.modules.telegram.client import TelegramClientWrapper


async def main():
    settings = get_settings()
    print("🔐 Rosa Flow Telegram Authentication")
    print(f"Session: {settings.telegram_session_name}")
    print(f"Phone: {settings.telegram_phone}")
    print()

    wrapper = TelegramClientWrapper(
        api_id=settings.telegram_api_id,
        api_hash=settings.telegram_api_hash,
        session_name=settings.telegram_session_name,
    )

    client = wrapper.get_client() if wrapper.client else None
    if not client:
        await wrapper.connect()

    if await wrapper.client.is_user_authorized():
        me = await wrapper.client.get_me()
        print(f"✅ Already authorized as {me.first_name}")
    else:
        print("📱 You will receive a code via Telegram. Enter it below.")
        await wrapper.authorize(phone=settings.telegram_phone)
        print("✅ Authentication successful!")

    await wrapper.disconnect()
    print(f"\nSession saved to: sessions/{settings.telegram_session_name}.session")
    print("You can now run: ./start.sh")


if __name__ == "__main__":
    asyncio.run(main())
