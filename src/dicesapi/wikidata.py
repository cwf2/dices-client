''' wikidata - tools for working with WikiData

Uses the `wikidata` PyPI package for read access to Wikidata's API. This
replaces an earlier implementation based on `qwikidata`, which no longer
respects Wikidata's bot policy and is unusable as of mid-2026.

    pip install dices-client[wikidata]
'''

from dicesapi import Character, CharacterInstance
from wikidata.client import Client
from wikidata.entity import Entity

__wd_cache__ = dict()
__settings__ = dict(
    DEBUG = False,
)

_client = None

HAS_PARENT = 'P8810'
HAS_MOTHER = 'P25'
HAS_FATHER = 'P22'
HAS_SPOUSE = 'P26'
HAS_CHILD = 'P40'


def settings(**kwargs):
    for k, v in kwargs.items():
        __settings__[k] = v


def getClient():
    '''Return the module's shared wikidata.client.Client, creating it if needed'''

    global _client
    if _client is None:
        _client = Client()
    return _client


def getWDfromID(wd_id, cache=__wd_cache__):
    '''Return WikiData entity for a given WikiData ID'''

    if wd_id is not None and wd_id != '':
        if cache is None:
            return getClient().get(wd_id, load=True)
        else:
            if wd_id not in cache:
                cache[wd_id] = getClient().get(wd_id, load=True)
            return cache[wd_id]


def getWDfromChar(char, cache=__wd_cache__):
    '''Return WikiData entity for a DICES Character'''

    return getWDfromID(char.wd, cache=cache)


def getWDfromInst(inst, cache=__wd_cache__):
    '''Return WikiData entity for a DICES CharacterInstance'''

    if inst.char is not None:
        return getWDfromChar(inst.char, cache=cache)


def getWD(obj, cache=__wd_cache__):
    '''Return WikiData entity for an ID, Character or CharacterInstance'''

    result = None

    if isinstance(obj, str):
        result = getWDfromID(obj, cache=cache)

    elif isinstance(obj, Character):
        result = getWDfromChar(obj, cache=cache)

    elif isinstance(obj, CharacterInstance):
        result = getWDfromInst(obj, cache=cache)

    if result is None:
        if __settings__['DEBUG']:
            print(f"Can't resolve {obj} to a WikiData entity!")

    return result


def getLabel(entity, lang='en'):
    '''Return an entity's label in the given language, or None if absent'''

    if entity is None:
        return None

    labels = entity.attributes.get('labels', {})
    label = labels.get(lang)

    if label is not None:
        return label.get('value')


def checkWDRelation(wd1, wd2, relation, cache=__wd_cache__):
    '''Return True if relation holds between two WikiData entities'''

    if not isinstance(wd1, Entity):
        wd1 = getWD(wd1, cache=cache)
        if wd1 is None:
            return
    if not isinstance(wd2, Entity):
        wd2 = getWD(wd2, cache=cache)
        if wd2 is None:
            return

    if cache is None:
        cache = {}

    # cache by entity id strings, not Entity objects
    key = (wd1.id, wd2.id, relation)

    if key not in cache:
        relation_entity = getClient().get(relation, load=True)
        related = wd1.getlist(relation_entity)
        cache[key] = wd2 in related

    return cache[key]
