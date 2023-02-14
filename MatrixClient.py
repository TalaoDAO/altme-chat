	
import asyncio

from nio import AsyncClient, MatrixRoom, RoomMessageText


async def message_callback(room: MatrixRoom, event: RoomMessageText) -> None:
    print(
        f"Message received in room {room.display_name}\n"
        f"{room.user_name(event.sender)} | {event.body}"
    )


async def main() -> None:
    #client = AsyncClient("https://matrix.talao.co")
    #print(await client.register("did78787877878954545567777788","altme"))
    client = AsyncClient("https://matrix.talao.co","@Taleb:matrix.talao.co")

    print(await client.login("altme2023"))
    #await client.sync_forever(timeout=30000)  # milliseconds
    await client.sync()
    # "Logged in as @alice:example.org device id: RANDOMDID"
    #room=await client.room_create(alias="did787878778789545455677777",invite=["@altme:altme"])
    #room=str(room)
    #roomID=room[len(room)-27:len(room)-2]
    #print(roomID)
    # If you made a new room and haven't joined as that user, you can use
    #await client.join("#")
    #client.add_event_callback(message_callback, RoomMessageText)
    """while True:
        chat=input("> ")
        await client.room_send(
            # Watch out! If you join an old room you'll see lots of old messages
            room_id=roomID,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": chat},
        )
        await client.sync()"""


asyncio.get_event_loop().run_until_complete(main())
