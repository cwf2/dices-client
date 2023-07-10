''' wd - tools for working with WikiData
'''

from dicesapi import Character, CharacterInstance
from qwikidata.linked_data_interface import get_entity_dict_from_api
from qwikidata.entity import WikidataItem, WikidataProperty

__wd_cache__ = dict()
__settings__ = dict(
    DEBUG = False,
)

HAS_PARENT = 'P8810'
HAS_MOTHER = 'P25'
HAS_FATHER = 'P22'
HAS_SPOUSE = 'P26'
HAS_CHILD = 'P40'

def settings(**kwargs):
    for k, v in kwargs.items():
        __settings__[k] = v

def getWDfromID(wd_id, cache=__wd_cache__):
    '''Return WikiData entity for a given WikiData ID'''

    if wd_id is not None and wd_id != '':
        if cache is None:
            return WikidataItem(get_entity_dict_from_api(wd_id))
        else:
            if wd_id not in cache:
                cache[wd_id] = WikidataItem(get_entity_dict_from_api(wd_id))
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


def checkWDRelation(wd1, wd2, relation, cache=__wd_cache__):
    '''Return True if relation holds between two WikiData entities'''
    
    if not isinstance(wd1, WikidataItem):
        wd1 = getWD(wd1, cache=cache)
        if wd1 is None:
            return
    if not isinstance(wd2, WikidataItem):
        wd2 = getWD(wd2, cache=cache)
        if wd2 is None:
            return
    
    if cache is None:
        cache = {}
        
    key = (wd1, wd2, relation)
    
    if key not in cache:
        result = False

        claim_group = wd1.get_truthy_claim_group(relation)

        for claim in claim_group:
            if claim.mainsnak.datavalue is not None:
                if claim.mainsnak.datavalue.value['id'] == wd2.entity_id:
                    result = True
        cache[key] = result

    return cache[key]