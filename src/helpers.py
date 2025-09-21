import os
from livekit import api
import uuid
from livekit.api import LiveKitAPI, ListRoomsRequest
from utils.constant import LIVEKIT_API_KEY, LIVEKIT_API_SECRET





async def generate_room_name():
    name = "room-" + str(uuid.uuid4())[:8]
    rooms = await get_rooms()
    while name in rooms:
        name = "room-" + str(uuid.uuid4())[:8]
    return name

async def get_rooms():
    api = LiveKitAPI()
    rooms = await api.room.list_rooms(ListRoomsRequest())
    await api.aclose()
    return [room.name for room in rooms.rooms]


async def getToken(room_name: str, user_name: str):
    room = room_name
    if not room:
        room = await generate_room_name()
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
        .with_identity(user_name) \
        .with_name(user_name) \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room,
        ))
    return token.to_jwt()