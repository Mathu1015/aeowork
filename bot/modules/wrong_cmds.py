from bot.core.config_manager import Config
from bot.helper.telegram_helper.message_utils import (
    auto_delete_message,
    send_message,
)


async def handle_qb_commands(_, message):
    """Handle deprecated commands and show warning messages.

    Currently handles:
    - /qbleech and variants: Suggests using /leech instead
    - /qbmirror and variants: Suggests using /mirror instead

    Args:
        _: The client instance (unused)
        message: The message object containing the command
    """
    # Check if command warnings are enabled
    if not Config.WRONG_CMD_WARNINGS_ENABLED:
        return

    command = message.text.split()[0].lower()

    if "qbleech" in command:
        warning_msg = "⚠️ <b>Warning:</b> /qbleech command is deprecated. Please use /leech command instead."
    else:  # qbmirror
        warning_msg = "⚠️ <b>Warning:</b> /qbmirror command is deprecated. Please use /mirror command instead."

    # Send warning message
    reply = await send_message(message, warning_msg)

    # Schedule both messages for auto-deletion after 5 minutes (300 seconds)
    await auto_delete_message(reply, message, time=300)


async def handle_no_suffix_commands(client, message):
    """Handle commands without suffix and show warning messages.

    When CMD_SUFFIX is set:
    - No warning for standard commands with CMD_SUFFIX (like "/leech{CMD_SUFFIX}")
    - Warning for standard commands without CMD_SUFFIX (like "/leech")

    When CMD_SUFFIX is not set:
    - Warning for commands with non-standard suffix (like "/leech3")
    - No warning for standard commands (like "/leech")

    Args:
        client: The client instance
        message: The message object containing the command
    """
    # Check if command warnings are enabled
    if not Config.WRONG_CMD_WARNINGS_ENABLED:
        return
    # Get the full command text (including any suffix)
    full_command = message.text.split()[0].lower()
    # Extract the base command without the leading slash
    base_command = full_command.lstrip("/")
    # Get the command suffix from config
    cmd_suffix = Config.CMD_SUFFIX

    # Define standard commands (excluding those handled by direct handlers)
    standard_commands = [
        "mirror",
        "m",
        "leech",
        "l",
        "jdmirror",
        "jm",
        "jdleech",
        "jl",
        "nzbmirror",
        "nm",
        "nzbleech",
        "nl",
        "ytdl",
        "y",
        "ytdlleech",
        "yl",
        "clone",
        "count",
        "del",
        "cancelall",
        "forcestart",
        "fs",
        "list",
        "search",
        "nzbsearch",
        "status",
        "s",
        "statusall",
        "sall",
        "users",
        "auth",
        "unauth",
        "addsudo",
        "rmsudo",
        "ping",
        "restart",
        "restartall",
        "stats",
        "help",
        "log",
        "shell",
        "aexec",
        "exec",
        "clearlocals",
        "botsettings",
        "speedtest",
        "broadcast",
        "broadcastall",
        "sel",
        "rss",
        "check_deletions",
        "cd",
        "imdb",
        "login",
        "mediasearch",
        "mds",
        "truecaller",
        "ask",
        "mediainfo",
        "mi",
        "spectrum",
        "sox",
        "paste",
        "streamripmirror",
        "srmirror",
        "streamripleech",
        "srleech",
        "zotifymirror",
        "zmirror",
        "zotifyleech",
        "zleech",
        "zotifysearch",
        "zsearch",
        "streamripsearch",
        "srsearch",
        "virustotal",
    ]

    # Check if this is a standard command with a non-standard suffix
    found_standard_cmd = None
    for std_cmd in standard_commands:
        if base_command.startswith(std_cmd) and base_command != std_cmd:
            found_standard_cmd = std_cmd
            break

    # CASE: When CMD_SUFFIX is not set
    if not cmd_suffix:
        # Only show warning if command has a non-standard suffix (like /leech3)
        if found_standard_cmd:
            warning_msg = f"⚠️ <b>Warning:</b> Please use /{found_standard_cmd} command instead of /{base_command}."
            reply = await send_message(message, warning_msg)
            await auto_delete_message(reply, message, time=300)
        return

    # CASE: When CMD_SUFFIX is set
    # Check if the command already has the correct suffix
    if base_command.endswith(cmd_suffix):
        # Command already has the correct suffix, no warning needed
        return

    # Get the list of correct command suffixes (if any)
    correct_cmd_suffixes = []
    if Config.CORRECT_CMD_SUFFIX:
        correct_cmd_suffixes = [
            suffix.strip() for suffix in Config.CORRECT_CMD_SUFFIX.split(",")
        ]

    # Check if the command has a suffix that's in the list of correct suffixes
    for suffix in correct_cmd_suffixes:
        if suffix and base_command.endswith(suffix):
            # This is an allowed suffix, no warning needed
            return

    # Command with non-standard suffix (like /leech3 or /mirrorz)
    if found_standard_cmd:
        warning_msg = f"⚠️ <b>Warning:</b> For Bot <b>{cmd_suffix}</b> use /{found_standard_cmd}{cmd_suffix} instead of /{base_command}. Thank you."
        reply = await send_message(message, warning_msg)
        await auto_delete_message(reply, message, time=300)
    # Standard command without the required suffix
    elif base_command in standard_commands:
        warning_msg = f"⚠️ <b>Warning:</b> For Bot <b>{cmd_suffix}</b> use /{base_command}{cmd_suffix}. Thank you."
        reply = await send_message(message, warning_msg)
        await auto_delete_message(reply, message, time=300)
