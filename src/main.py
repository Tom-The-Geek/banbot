import asyncio
import os
import re

from dotenv import load_dotenv
from nio import AsyncClient, AsyncClientConfig
from nio.events.invite_events import InviteMemberEvent
from nio.events.room_events import RoomMemberEvent, RoomMessageText
from nio.responses import JoinError, RoomResolveAliasError
from nio.rooms import MatrixRoom
from nio.store import SqliteStore

from store import Store

load_dotenv()

bot_owner = os.getenv('BOT_OWNER')

LINK_COMMAND_REGEX = re.compile("!ban-sync link #(.*):(.*)")


async def send_message_to_room(room: MatrixRoom, content: str):
    await client.room_send(
        room_id=room.room_id,
        message_type="m.room.message",
        content={
            "msgtype": "m.text",
            "body": content
        }
    )


async def message_cb(room: MatrixRoom, event: RoomMessageText):
    if event.sender != bot_owner:
        return

    content = event.body.strip()
    if content.startswith('!ban-sync link '):
        matches = re.match(LINK_COMMAND_REGEX, content)
        if not matches:
            return
        room_name, room_server = matches.groups()
        result = (await client.room_resolve_alias(f"#{room_name}:{room_server}"))
        if type(result) is RoomResolveAliasError:
            print(f"[ERROR] Failed to resolve room alias: #{room_name}:{room_server} -> {result}")
            return
        room_id = result.room_id
        if room.room_id == room_id:
            await send_message_to_room(room=room, content="You cannot link a room to itself!")
            return
        store.link_channels(room.room_id, room_id)
        await send_message_to_room(room=room, content=f"Linked this room to #{room_name}:{room_server}")
    elif content.startswith('!ban-sync unlink'):
        unlinked = store.unlink_channels(room.room_id)
        if unlinked:
            message = "Unlinked this channel!"
        else:
            message = "This channel is not linked anywhere!"
        await send_message_to_room(room=room, content=message)


async def member_event_callback(room: MatrixRoom, event: RoomMemberEvent):
    if event.sender == client.user_id:
        return

    linked_channels = store.get_linked_channels(room.room_id)
    if len(linked_channels) == 0:
        return

    if event.membership == 'ban':
        # print(
        #     f"User {member} was banned from {room.display_name} for {event.content.get('reason')}")
        for channel in linked_channels:
            await client.room_ban(room_id=channel, user_id=event.state_key, reason=event.content.get('reason'))

    # unbans are 'leave' because matrix /shrug
    elif (event.membership == 'leave' or event.membership is None) and event.prev_membership == 'ban':
        # print(f"User {member} was unbanned from {room.display_name}")
        for channel in linked_channels:
            await client.room_unban(room_id=channel, user_id=event.state_key)


# based on https://github.com/anoadragon453/nio-template/blob/master/my_project_name/callbacks.py#L80-L105
async def auto_join_room(room: MatrixRoom, event: InviteMemberEvent):
    if event.sender != bot_owner:
        return

    print(f"Got invite to room {room.display_name}, joining...")
    for attempt in range(3):
        result = await client.join(room.room_id)
        if type(result) == JoinError:
            print(
                f"[ERROR] Error joining room {room.room_id} (attempt {attempt}): {result.message}")
        else:
            print(f"Joined room: {room.display_name}!")
            break
    else:
        print(f"[ERROR] Unable to join room: {room.display_name}")


async def main() -> None:
    global client
    user = os.getenv('BOT_USER')
    client = AsyncClient(os.getenv('HOMESERVER'), user, store_path="store",
                         device_id="banbot",
                         config=AsyncClientConfig(
                             max_limit_exceeded=0,
                             max_timeouts=0,
                             store_sync_tokens=True,
                             store=SqliteStore,
                         ))

    # noinspection PyTypeChecker
    client.add_event_callback(message_cb, RoomMessageText)
    # noinspection PyTypeChecker
    client.add_event_callback(member_event_callback, RoomMemberEvent)
    # noinspection PyTypeChecker
    client.add_event_callback(auto_join_room, InviteMemberEvent)

    print(f"Login as {user} on {os.getenv('HOMESERVER')}")
    await client.login(password=os.getenv("BOT_PASSWORD"), device_name="banbot")
    await client.sync_forever(timeout=30000, full_state=True)


store = Store("store.json")
store.load()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
