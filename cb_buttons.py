import pyrogram
from plugins.zee5_dl import zee5_execute


@pyrogram.Client.on_callback_query()
async def formatbuttons(client, query):
    if query.data and "|" in query.data:
        await zee5_execute(client, query)
    elif query.data == "closeformat":
        await query.message.delete()
