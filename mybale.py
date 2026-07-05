import asyncio
import ast
from aiobale import Client, Dispatcher
from aiobale.enums import ChatType


async def sender(a, text, chat_type=ChatType.PRIVATE):
    await client.send_message(chat_id=a, text=text, chat_type=ChatType(chat_type))


def _looks_like_payload_artifact(text):
    text = text.strip()
    if not (text.startswith("{") and text.endswith("}")):
        return False
    try:
        return isinstance(ast.literal_eval(text), dict)
    except (SyntaxError, ValueError):
        return False


def is_displayable_message_text(text):
    return bool(text and not _looks_like_payload_artifact(text))


async def loader(a, chat_type=ChatType.PRIVATE):
    try:
        history = await client.load_history(
            chat_id=a,
            chat_type=ChatType(chat_type),
            limit=20,
        )
    except Exception as ex:
        import traceback
        traceback.print_exc()
        return f"failed to load history: {ex}"

    lines = []
    for msg in history:
        if is_displayable_message_text(msg.text):
            lines.append(msg.text)
    if not lines:
        return "no messages"
    return "\n".join(lines)


async def nameGetter():
    dialogs = await client.load_dialogs(limit=20)
    list1 = list()
    groups = list()
    Dict1 = {}
    o = ""

    for i in dialogs:
        if (i.peer.type == ChatType.PRIVATE):
            list1.append(i.peer)
        elif i.peer.type in (ChatType.GROUP, ChatType.SUPER_GROUP):
            groups.append(i.peer)

    index = 0
    if len(list1) > 0:
        a = await client.load_users(list1)
        for i in a:
            Dict1[index] = {"name": i.name, "id": i.id, "type": int(ChatType.PRIVATE)}
            index += 1
    for g in groups:
        try:
            name = (await client.get_full_group(g.id)).title
        except Exception as ex:
            print(ex)
            name = f"group {g.id}"
        Dict1[index] = {"name": "👥 " + name, "id": g.id, "type": int(g.type)}
        index += 1

    for indexing, information in Dict1.items():
        o += f"{indexing, information['name']}\n"
    return Dict1, o


import pydantic
from aiobale.client.session.base import BaseSession

_orig_decode = BaseSession.decode_result


def _walk(data, loc):
    obj = data
    for key in loc[:-1]:
        obj = obj[key]
    return obj, loc[-1]


def _patched_decode(self, result, method):
    for _ in range(10):
        try:
            return _orig_decode(self, result, method)
        except pydantic.ValidationError as e:
            fixed = False
            for err in e.errors():
                try:
                    loc = tuple(k for k in err["loc"] if not (isinstance(k, str) and "[" in k))
                    parent, key = _walk(result, loc)
                    if not isinstance(parent, dict):
                        continue
                    if err["type"] == "string_type":
                        parent[key] = str(parent[key])
                    else:
                        parent.pop(key, None)
                    fixed = True
                except (KeyError, IndexError, TypeError, AttributeError):
                    pass
            if not fixed:
                raise
    return _orig_decode(self, result, method)


import logging
from aiobale.types import Response

logging.basicConfig(level=logging.ERROR)

_orig_validate = Response.model_validate.__func__


@classmethod
def _patched_validate(cls, obj, *args, **kwargs):
    for _ in range(10):
        try:
            return _orig_validate(cls, obj, *args, **kwargs)
        except pydantic.ValidationError as e:
            fixed = False
            for err in e.errors():
                try:
                    loc = tuple(k for k in err["loc"] if not (isinstance(k, str) and "[" in k))
                    parent, key = _walk(obj, loc)
                    if not isinstance(parent, dict):
                        continue
                    if err["type"] == "string_type":
                        parent[key] = str(parent[key])
                    else:
                        parent.pop(key, None)
                    fixed = True
                except (KeyError, IndexError, TypeError, AttributeError):
                    pass
            if not fixed:
                raise
    return _orig_validate(cls, obj, *args, **kwargs)


Response.model_validate = _patched_validate
BaseSession.decode_result = _patched_decode

dp = Dispatcher()
client = Client(dp, show_update_errors=True)
