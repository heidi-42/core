import json

from aiohttp import request, ClientConnectionError
from aiohttp import web
from aioredis import RedisError
from aioredis import create_redis_pool
from gino import GinoException
from jsonschema import ValidationError

from .data import db, JSONEncoder as HeidiJSONEncoder
from .ex import ServerError, ConnectionError, HeidiError
from .etext.general import JSON_NOT_DECODED, VALIDATION_ERROR
from .hosts import *

PUT = 'PUT'
GET = 'GET'
POST = 'POST'
DELETE = 'DELETE'


def filter_not_none(d):
    return {k: v for k, v in d.items() if v is not None}


async def fetch(method, url, return_status=False, **kwargs):
    try:
        async with request(method, url, **kwargs) as response:
            status = response.status
            if status >= 500:
                raise ServerError

            response = await response.json()
            if 'heidi_error' in response:
                raise HeidiError(response['heidi_error'])

            if return_status:
                return response, status
            return response

    # aiohttp will not raise any exceptions for >= 400 status codes
    # since `raise_for_status` in `request` is false by default.
    except ClientConnectionError:
        raise ConnectionError


async def init_data_layer(app):
    """Extend your aiohttp.web.Application.on_startup with it"""
    app['gino'] = await db.set_bind(f'{POSTGRES}/heidi')
    await db.gino.create_all()


async def init_redis(app):
    """Extend your aiohttp.web.Application.on_startup with it"""
    app['redis'] = await create_redis_pool(f'{REDIS}/', encoding='utf-8')


@web.middleware
async def fearward(request, handler):
    try:
        return await handler(request)
        # You SHOULD handle `HeidiError`s earlier
    except (ServerError, HeidiError, GinoException, RedisError):
        raise web.HTTPInternalServerError
    except json.JSONDecodeError:
        raise web.HTTPBadRequest(reason=JSON_NOT_DECODED)
    except ValidationError:
        raise web.HTTPBadRequest(reason=VALIDATION_ERROR)


def dumps(o):
    return json.dumps(o, cls=HeidiJSONEncoder)


@web.middleware
async def jsonify_response(request, handler):
    try:
        response = await handler(request)
        if response is None:
            return web.json_response({'status': 'OK'})

        if isinstance(response, web.Response):
            return response
        return web.json_response(response, dumps=dumps)
    except web.HTTPException as ex:
        ex.headers.update({'Content-Type': 'application/json'})
        return web.Response(
            body=dumps({'heidi_error': ex.reason}),
            status=ex.status_code,
            headers=ex.headers,
        )


def hmset_serialize(dictionary, encoder=HeidiJSONEncoder):
    for key, value in dictionary.items():
        yield key
        if type(value) in (dict, list):
            yield json.dumps(value, ensure_ascii=False, cls=encoder)
        else:
            yield value
