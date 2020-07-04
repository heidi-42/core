from __future__ import annotations

from typing import Optional

from .util import *

TEMPLATE_EMAIL_URL = f'{EMAIL}/template_email'


async def template_email(recipients: [str], template: str,
                         data: {str: any}, sender: Optional[str] = None):
    payload = {
        'recipients': recipients,
        'template': template,
        'data': data,
    }

    if sender is not None:
        payload['sender'] = sender

    return await fetch(POST, TEMPLATE_EMAIL_URL, json=payload)
