from __future__ import annotations

from .data import User, Contact, Group, Ownership, Allegiance, SuperGroup


async def find_user(contact_value: str, provider: str) -> User:
    return await User.query.where((Contact.value == contact_value) & (
        Contact.provider == provider)).gino.one_or_none()


async def unlink(uid: int, contact_value: str, provider: str):
    return await Contact.delete.where(
        (Contact.user == uid) & (Contact.value == contact_value)
        & (Contact.provider == provider)).gino.status()


async def find_groups(owner: User) -> [Group]:
    return await Group.query.where((Ownership.user == owner.id)
                                   & (Ownership.group == Group.id)).gino.all()


async def find_supergroups(owner: User, groups: [Group]) \
    -> {SuperGroup: [Group]}:
    match = await SuperGroup.query.where((Ownership.user == owner.id) & (
        Ownership.supergroup == SuperGroup.id)).gino.all()

    result = {}
    for supergroup in match:
        result[supergroup] = []
        for group in groups:
            # If a user has an ownership over some supergroup, he MUST also
            # own every group it contains.
            if group.id in supergroup.contents:
                result[supergroup].append(group)
    return result


async def find_subscribers(groups: [Group]) -> {Group: [User]}:
    result = {}
    for group in groups:
        # TODO: Better query
        match = await User.query.where(
            # If the user has at least one contact linked...
            (Contact.user == User.id) & (Allegiance.group == group.id)
            & (Allegiance.user == User.id)).gino.all()

        if match:
            # Getting rid of duplicates
            result[group] = set(match)
    return result
