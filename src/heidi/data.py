import json

import gino

from . import hosts

db = gino.Gino()


class DictConvertible:

    def as_dict(self):
        return {c.name: getattr(self, c.name)
                for c in self.__table__.columns}


class JSONEncoder(json.JSONEncoder):

    def default(self, o):
        if issubclass(o.__class__, DictConvertible):
            return o.as_dict()
        return json.JSONEncoder.default(self, o)


async def init_data_layer(*args, **kwargs):
    """Use this as an aiohttp web application startup routine."""
    await db.set_bind(hosts.POSTGRES)
    await db.gino.create_all()


class Role(db.Model, DictConvertible):
    __tablename__ = 'role'

    value = db.Column(db.Unicode(), primary_key=True)

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return type(other) is Role and self.value == other.value


class User(db.Model, DictConvertible):
    __tablename__ = 'user'

    id = db.Column(db.BigInteger(),
                   autoincrement=True,
                   primary_key=True)

    name = db.Column(db.Unicode(), nullable=False)

    email = db.Column(db.Unicode(), unique=True, nullable=False)

    role = db.Column(db.Unicode(), db.ForeignKey('role.value'),
                     nullable=False)

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return type(other) is User and self.id == other.id


class Provider(db.Model, DictConvertible):
    __tablename__ = 'provider'

    value = db.Column(db.Unicode(), primary_key=True)

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return type(other) is Provider and self.value == other.value


class Contact(db.Model, DictConvertible):
    __tablename__ = 'contact'

    id = db.Column(db.BigInteger(),
                   autoincrement=True,
                   primary_key=True)

    user = db.Column(db.BigInteger(), db.ForeignKey('user.id'),
                     nullable=False)

    provider = db.Column(db.Unicode(), db.ForeignKey('provider.value'),
                         nullable=False)

    value = db.Column(db.Unicode(), nullable=False)

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return type(other) is Contact and self.id == other.id


class Group(db.Model, DictConvertible):
    __tablename__ = 'group'

    id = db.Column(db.BigInteger(),
                   autoincrement=True,
                   primary_key=True)

    alias = db.Column(db.Unicode(), nullable=False)

    is_virtual = db.Column(db.Boolean(), nullable=False)

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return type(other) is Group and self.id == other.id


class Ownership(db.Model, DictConvertible):
    __tablename__ = 'ownership'

    id = db.Column(db.BigInteger(),
                   autoincrement=True,
                   primary_key=True)

    user = db.Column(db.BigInteger(), db.ForeignKey('user.id'),
                     nullable=False)

    group = db.Column(db.BigInteger(), db.ForeignKey('group.id'),
                      nullable=True)

    supergroup = db.Column(db.BigInteger(),
                           db.ForeignKey('supergroup.id'), nullable=True)

    def __hash__(self):
        return self.id
    
    def __eq__(self, other):
        return type(other) is Ownership and self.id == other.id


class Allegiance(db.Model, DictConvertible):
    __tablename__ = 'allegiance'

    id = db.Column(db.BigInteger(),
                   autoincrement=True,
                   primary_key=True)

    group = db.Column(db.BigInteger(), db.ForeignKey('group.id'),
                      nullable=False)

    user = db.Column(db.BigInteger(), db.ForeignKey('user.id'),
                     nullable=False)

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return type(other) is Allegiance and self.id == other.id


class SuperGroup(db.Model, DictConvertible):
    __tablename__ = 'supergroup'

    id = db.Column(db.BigInteger(),
                   autoincrement=True,
                   primary_key=True)

    alias = db.Column(db.Unicode(), nullable=False)

    contents = db.Column(db.ARRAY(db.BigInteger()))

    is_virtual = db.Column(db.Boolean(), nullable=False)

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return type(other) is SuperGroup and self.id == other.id

