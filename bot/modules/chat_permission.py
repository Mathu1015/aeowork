from bot import user_data
from bot.helper.ext_utils.bot_utils import new_task, update_user_ldata
from bot.helper.ext_utils.db_handler import database
from bot.helper.telegram_helper.message_utils import send_message


@new_task
async def authorize(_, message):
    msg = message.text.split()
    thread_id = None

    # Handle special case for "all" - authorize all chats in sudo_users config
    if len(msg) > 1 and msg[1].strip().lower() == "all":
        from bot import sudo_users
        from bot.core.config_manager import Config

        # Authorize all sudo users
        authorized_count = 0

        # First authorize all sudo users from config
        if Config.SUDO_USERS:
            for user_id in sudo_users:
                if user_id not in user_data or not user_data[user_id].get("AUTH"):
                    update_user_ldata(user_id, "AUTH", True)
                    await database.update_user_data(user_id)
                    authorized_count += 1

        # Also authorize all users with SUDO flag in user_data
        for user_id in list(user_data.keys()):
            if user_data[user_id].get("SUDO") and not user_data[user_id].get("AUTH"):
                update_user_ldata(user_id, "AUTH", True)
                await database.update_user_data(user_id)
                authorized_count += 1

        if authorized_count > 0:
            msg = f"Successfully authorized {authorized_count} chat(s)"
        else:
            msg = "No new chats to authorize"
        await send_message(message, msg)
        return

    # Regular case for specific chat ID
    if len(msg) > 1:
        try:
            if "|" in msg[1]:
                chat_id, thread_id = list(map(int, msg[1].split("|")))
            else:
                chat_id = int(msg[1].strip())
        except ValueError:
            await send_message(
                message,
                "Invalid chat ID format. Please provide a valid numeric ID or use 'all'.",
            )
            return
    elif reply_to := message.reply_to_message:
        chat_id = (
            reply_to.from_user.id if reply_to.from_user else reply_to.sender_chat.id
        )
    else:
        if message.is_topic_message:
            thread_id = message.message_thread_id
        chat_id = message.chat.id

    # Initialize user data if not exists
    if chat_id not in user_data:
        user_data[chat_id] = {}

    if user_data[chat_id].get("AUTH"):
        if (
            thread_id is not None
            and thread_id in user_data[chat_id].get("thread_ids", [])
        ) or thread_id is None:
            msg = "Already Authorized!"
        else:
            if "thread_ids" in user_data[chat_id]:
                user_data[chat_id]["thread_ids"].append(thread_id)
            else:
                user_data[chat_id]["thread_ids"] = [thread_id]
            msg = "Authorized"
    else:
        update_user_ldata(chat_id, "AUTH", True)
        if thread_id is not None:
            update_user_ldata(chat_id, "thread_ids", [thread_id])
        await database.update_user_data(chat_id)
        msg = "Authorized"
    await send_message(message, msg)


@new_task
async def unauthorize(_, message):
    msg = message.text.split()
    thread_id = None

    # Handle special case for "all"
    if len(msg) > 1 and msg[1].strip().lower() == "all":
        # Unauthorize all authorized chats
        unauthorized_count = 0
        for chat_id in list(user_data.keys()):
            if user_data[chat_id].get("AUTH"):
                update_user_ldata(chat_id, "AUTH", False)
                await database.update_user_data(chat_id)
                unauthorized_count += 1

        if unauthorized_count > 0:
            msg = f"Successfully unauthorized {unauthorized_count} chat(s)"
        else:
            msg = "No authorized chats found to unauthorize"
        await send_message(message, msg)
        return

    # Regular case for specific chat ID
    if len(msg) > 1:
        try:
            if "|" in msg[1]:
                chat_id, thread_id = list(map(int, msg[1].split("|")))
            else:
                chat_id = int(msg[1].strip())
        except ValueError:
            await send_message(
                message,
                "Invalid chat ID format. Please provide a valid numeric ID or use 'all'.",
            )
            return
    elif reply_to := message.reply_to_message:
        chat_id = (
            reply_to.from_user.id if reply_to.from_user else reply_to.sender_chat.id
        )
    else:
        if message.is_topic_message:
            thread_id = message.message_thread_id
        chat_id = message.chat.id

    if chat_id not in user_data:
        await send_message(message, "Chat not found in database")
        return

    if user_data[chat_id].get("AUTH"):
        if thread_id is not None and thread_id in user_data[chat_id].get(
            "thread_ids",
            [],
        ):
            user_data[chat_id]["thread_ids"].remove(thread_id)
            msg = f"Thread {thread_id} unauthorized in chat {chat_id}"
        else:
            update_user_ldata(chat_id, "AUTH", False)
            msg = "Unauthorized"
        await database.update_user_data(chat_id)
    else:
        msg = "Already Unauthorized!"
    await send_message(message, msg)


@new_task
async def add_sudo(_, message):
    id_ = ""
    msg = message.text.split()
    if len(msg) > 1:
        try:
            id_ = int(msg[1].strip())
        except ValueError:
            await send_message(
                message, "Invalid user ID format. Please provide a valid numeric ID."
            )
            return
    elif reply_to := message.reply_to_message:
        id_ = (
            reply_to.from_user.id if reply_to.from_user else reply_to.sender_chat.id
        )

    if not id_:
        await send_message(
            message, "Give ID or Reply To message of whom you want to Promote."
        )
        return

    # Initialize user data if not exists
    if id_ not in user_data:
        user_data[id_] = {}

    if user_data[id_].get("SUDO"):
        msg = "Already Sudo!"
    else:
        update_user_ldata(id_, "SUDO", True)
        await database.update_user_data(id_)
        msg = "Promoted as Sudo"
    await send_message(message, msg)


@new_task
async def remove_sudo(_, message):
    id_ = ""
    msg = message.text.split()

    # Handle special case for "all"
    if len(msg) > 1 and msg[1].strip().lower() == "all":
        from bot.core.config_manager import Config

        # Remove all sudo users except the first owner
        removed_count = 0
        for user_id in list(user_data.keys()):
            # Skip the owner
            if user_id == Config.OWNER_ID:
                continue

            # Remove sudo status for all other users
            if user_data[user_id].get("SUDO"):
                update_user_ldata(user_id, "SUDO", False)
                await database.update_user_data(user_id)
                removed_count += 1

        if removed_count > 0:
            msg = f"Successfully removed {removed_count} user(s) from sudo"
        else:
            msg = "No sudo users found to remove"
        await send_message(message, msg)
        return

    # Regular case for specific user ID
    if len(msg) > 1:
        try:
            id_ = int(msg[1].strip())
        except ValueError:
            await send_message(
                message,
                "Invalid user ID format. Please provide a valid numeric ID or use 'all'.",
            )
            return
    elif reply_to := message.reply_to_message:
        id_ = (
            reply_to.from_user.id if reply_to.from_user else reply_to.sender_chat.id
        )

    if not id_:
        await send_message(
            message,
            "Give ID or Reply To message of whom you want to remove from Sudo",
        )
        return

    if id_ not in user_data:
        await send_message(message, "User not found in database")
        return

    if user_data[id_].get("SUDO"):
        update_user_ldata(id_, "SUDO", False)
        await database.update_user_data(id_)
        msg = "Demoted"
    else:
        msg = "This user is not a sudo user"
    await send_message(message, msg)
