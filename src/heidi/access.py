from __future__ import annotations

from heidi.util import *

STASH_URL = f'{ACCESS}/contact/stash'


async def stash_contact(email: str, provider: str, value: str) -> str:
    payload = {
        'email': email,
        'provider': provider,
        'value': value
    }

    return await fetch(PUT, STASH_URL, json=payload)


COMMIT_URL = f'{ACCESS}/contact/commit'


async def commit_contact(code: str):
    await fetch(GET, COMMIT_URL, params={'code': code})
