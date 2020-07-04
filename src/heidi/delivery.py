from __future__ import annotations

import json
from http import HTTPStatus

from typing import Optional
from datetime import datetime

from dotmap import DotMap

from . import redis_lua

from .data import Contact, User, Group, Allegiance
from .util import *

DELIVERY_QUEUE_URL = f'{DELIVERY}/queue'
DELIVERY_TRACK_URL = f'{DELIVERY}/track'
DELIVERY_HISTORY_KEY_URL = f'{DELIVERY}/history_key'
DELIVERY_QUEUE_LIMIT_URL = f'{DELIVERY}/queue/limit'


async def get_queue_limit(user: User):
    return DotMap(await fetch(GET,
                              DELIVERY_QUEUE_LIMIT_URL,
                              params={'uid': user.id}))


async def get_history_key(sender: User):
    return await fetch(GET,
                       DELIVERY_HISTORY_KEY_URL,
                       params={'sender_id': sender.id})


async def track(history_key: str, touch_count: int, timeout: int):
    payload = {
        'history_key': history_key,
        'touch_count': touch_count,
        'timeout': timeout,
    }

    response = await fetch(POST, DELIVERY_TRACK_URL, json=payload)
    return DotMap(response['history']), response['timeouted']


async def users(history_key: str,
                sender: User, recipients: [User],
                text: str, provider: str,
                deliver_at: Optional[datetime.isoformat] = None) \
            -> (datetime, bool):
    payload = {
        'history_key': history_key,
        # `fetch` does not support heidi JSON encoder
        'sender': sender.as_dict(),
        'recipients': list(map(lambda r: r.as_dict(), recipients)),
        'text': text,
        'provider': provider,
    }

    if deliver_at is not None:
        payload['deliver_at'] = deliver_at

    deliver_at, status = await fetch(PUT,
                                     DELIVERY_QUEUE_URL,
                                     json=payload,
                                     return_status=True)

    deliver_at = datetime.fromisoformat(deliver_at)
    return deliver_at, status == HTTPStatus.ACCEPTED.value


async def groups(
        history_key: str,
        sender: User,
        recipients: [Group],
        text: str,
        provider: str,
        deliver_at: Optional[datetime.isoformat] = None) -> (datetime, bool):
    users_ = set()
    for group in recipients:
        users_.update(
            await User.query.where((Allegiance.group == group.id)
                                   & (Allegiance.user == User.id)).gino.all())
    return await users(history_key, sender, users_, text, provider, deliver_at)


async def update_status(history_key: str, provider: str, recipients: [int],
                        redis):
    """Obtain the `history_key` from a `task_stream`"""
    recipients.sort()
    await redis_lua.update_delivery_status.eval(redis, [history_key],
                                                [provider, *recipients])


async def task_stream(provider: str, redis):
    pattern = '__keyspace@0__:delivery*'
    reader, = await redis.psubscribe(pattern)
    async for key, event in reader.iter(encoding='utf-8'):
        if event not in ('expired', 'del'):
            continue

        # @see delivery.handlers.queue.put for the format explanation
        history_key = 'history:' + (key.decode('utf-8'))[24:]

        history = DotMap(json.loads(await redis.get(history_key)))

        contacts = {}
        for user in history.recipients:
            values = [
                contact.value for contact in await Contact.query.where(
                    (Contact.user == user.id)
                    & (Contact.provider == provider)).gino.all()
            ]

            if values:
                contacts[user.id] = values

        yield history_key, history, contacts
