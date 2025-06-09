#!/usr/bin/env python3
"""
Truecaller Lookup Module
------------------------
This module provides functionality to lookup phone numbers using the Truecaller API.
"""

from logging import getLogger
from urllib.parse import quote_plus

from httpx import AsyncClient, RequestError, TimeoutException

from bot.core.config_manager import Config
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.telegram_helper.message_utils import (
    auto_delete_message,
    delete_message,
    edit_message,
    send_message,
)

LOGGER = getLogger(__name__)

# No default Truecaller API URL - must be configured by the user


@new_task
async def truecaller_lookup(_, message):
    """
    Command handler for /truecaller
    Performs a phone number lookup using the Truecaller API
    """
    # Delete the command message instantly
    await delete_message(message)

    # Check if Extra Modules are enabled
    if not Config.ENABLE_EXTRA_MODULES:
        error_msg = await send_message(
            message,
            "❌ <b>Truecaller module is currently disabled.</b>\n\nPlease contact the bot owner to enable it.",
        )
        # Auto-delete error message after 5 minutes
        await auto_delete_message(error_msg, time=300)
        return

    # If this is a reply to another message, delete that too
    if message.reply_to_message:
        await delete_message(message.reply_to_message)

    # Check if the command is a reply to another message
    phone = None
    if message.reply_to_message and message.reply_to_message.text:
        # Try to extract a phone number from the replied message
        import re

        # Look for phone number patterns in the replied message
        phone_match = re.search(
            r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4,}",
            message.reply_to_message.text,
        )
        if phone_match:
            phone = phone_match.group(0)

    # If no phone found in reply, check the command itself
    if not phone:
        cmd_parts = message.text.split(maxsplit=1)
        if len(cmd_parts) >= 2:
            phone = cmd_parts[1].strip()

    # Check if a phone number was provided
    if not phone:
        error_msg = await send_message(
            message,
            "Please provide a phone number to lookup or reply to a message containing a phone number.\n\n"
            "Usage: `/truecaller +1234567890` or reply to a message containing a phone number with `/truecaller`",
        )
        # Auto-delete error message after 5 minutes
        await auto_delete_message(error_msg, time=300)
        return

    # Get the API URL from config
    api_url = Config.TRUECALLER_API_URL

    # Check if API URL is configured
    if not api_url:
        error_msg = await send_message(
            message,
            "❌ <b>Truecaller API URL is not configured.</b>\n\nPlease contact the bot owner to set up the Truecaller API URL.",
        )
        # Auto-delete error message after 5 minutes
        await auto_delete_message(error_msg, time=300)
        return

    # Send initial status message
    status_msg = await send_message(
        message,
        f"🔍 Looking up phone number: `{phone}`...",
    )

    try:
        # Make the API request
        async with AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{api_url}?q={quote_plus(phone)}",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "application/json",
                },
            )

            # Check if the request was successful
            if response.status_code != 200:
                await delete_message(status_msg)
                error_msg = await send_message(
                    message,
                    f"❌ Error: API returned status code {response.status_code}",
                )
                # Auto-delete error message after 5 minutes
                await auto_delete_message(error_msg, time=300)
                return

            # Parse the JSON response
            try:
                data = response.json()

                # Format the response with beautiful styling
                truecaller_name = data.get("Truecaller", "Unknown")

                # Create a decorative header
                msg = "┌─────────────────────────┐\n"
                msg += "│   🔍 TRUECALLER LOOKUP   │\n"
                msg += "└─────────────────────────┘\n\n"

                # Add the name with special formatting if available
                if truecaller_name not in {"Unknown", "N/A"}:
                    msg += f"✨ **{truecaller_name}** ✨\n\n"

                # Create a styled info box without fixed borders
                msg += "┌─────── 📋 DETAILS ───────┐\n"
                msg += (
                    f"│ 📱 **Number:** `{data.get('international_format', 'N/A')}`\n"
                )
                msg += f"│ 🔄 **Carrier:** `{data.get('carrier', 'N/A')}`\n"
                msg += f"│ 🌍 **Country:** `{data.get('country', 'N/A')}`\n"
                msg += f"│ 📍 **Location:** `{data.get('location', 'N/A')}`\n"
                msg += f"│ ⏰ **Timezone:** `{data.get('timezones', 'N/A')}`\n"

                # Add other info if available
                if data.get("Unknown") and data.get("Unknown") != "N/A":
                    msg += f"│ ℹ️ **Other:** `{data.get('Unknown', 'N/A')}`\n"

                msg += "└────────────────────────┘\n\n"

                # Add a footer
                msg += "ℹ️ _This message will be deleted in 5 minutes_"

                # Update the status message with the result
                await edit_message(status_msg, msg)

                # Auto-delete successful result message after 5 minutes
                await auto_delete_message(status_msg, time=300)

            except ValueError as e:
                LOGGER.error(f"Error parsing API response: {e}")
                await delete_message(status_msg)
                error_msg = await send_message(
                    message,
                    "❌ Error: Could not parse the API response.",
                )
                # Auto-delete error message after 5 minutes
                await auto_delete_message(error_msg, time=300)

    except (RequestError, TimeoutException) as e:
        LOGGER.error(f"Error making API request: {e}")
        await delete_message(status_msg)
        error_msg = await send_message(
            message,
            f"❌ Error: Could not connect to the Truecaller API. {e!s}",
        )
        # Auto-delete error message after 5 minutes
        await auto_delete_message(error_msg, time=300)
    except Exception as e:
        LOGGER.error(f"Unexpected error in truecaller lookup: {e}")
        await delete_message(status_msg)
        error_msg = await send_message(
            message,
            f"❌ An unexpected error occurred: {e!s}",
        )
        # Auto-delete error message after 5 minutes
        await auto_delete_message(error_msg, time=300)
