''' wd - tools for working with WikiData
'''

from qwikidata.linked_data_interface import get_entity_dict_from_api
from qwikidata.entity import WikidataItem, WikidataProperty

__wd_cache__ = {}


MOTHER_OF = 'P25'

def getWD(wd, cache=__wd_cache__):
    '''Return WikiData entity for a given ID'''

    if wd is not None and wd != '':
        if cache is None:
            return WikidataItem(get_entity_dict_from_api(wd))
        else:
            if wd not in cache:
                cache[wd] = WikidataItem(get_entity_dict_from_api(wd))
            return cache[wd]


def checkWDRelation(wd1, wd2, relation, cache=__wd_cache__):
    key = (wd1, wd2, relation)
    if cache is not None and key in cache:
        return cache[key]

    res = False

    wd_ent = getWD(wd1, cache=cache)

    claim_group = wd_ent.get_truthy_claim_group(relation)

    for claim in claim_group:
        if claim.mainsnak.datavalue is not None:
            if claim.mainsnak.datavalue.value['id'] == wd2:
                res = True
    
    if cache is not None:
        cache[key] = res
    return res

def instCheckWDRelation(inst1, inst2, relation, cache=__wd_cache__):
    if inst1.wd is not None and inst2.wd is not None:
        return checkWDRelation(inst1.wd, inst2.wd, relation, cache=cache)
    