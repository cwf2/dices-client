'''shared fixtures for dicesapi tests

These build small, self-contained JSON-like dicts shaped like the records
returned by the DICES API (see dices/speechdb/serializers.py), so that the
client-side classes can be tested without a network connection.
'''

import pytest

from dicesapi import DicesAPI


@pytest.fixture
def api():
    '''A DicesAPI instance that makes no network calls on its own'''

    return DicesAPI(
        dices_api='http://testserver/api/',
        cts_api='http://testserver/cts/',
    )


@pytest.fixture
def author_data():
    return {
        'id': 1,
        'name': 'Homer',
        'wd': 'Q6691',
        'urn': 'urn:cts:greekLit:tlg0012',
    }


@pytest.fixture
def work_data(author_data):
    return {
        'id': 1,
        'title': 'Iliad',
        'wd': 'Q47542',
        'urn': 'urn:cts:greekLit:tlg0012.tlg001.perseus-grc2',
        'lang': 'greek',
        'author': dict(author_data),
    }


@pytest.fixture
def character_data():
    return [
        {
            'id': 1,
            'name': 'Achilles',
            'being': 'mortal',
            'number': 'individual',
            'gender': 'male',
            'wd': 'Q41746',
            'manto': 'MANTO_ACHILLES',
            'tt': 'TT_ACHILLES',
        },
        {
            'id': 2,
            'name': 'Agamemnon',
            'being': 'mortal',
            'number': 'individual',
            'gender': 'male',
            'wd': 'Q165518',
            'manto': 'MANTO_AGAMEMNON',
            'tt': 'TT_AGAMEMNON',
        },
    ]


@pytest.fixture
def character_instance_data(character_data):
    achilles, agamemnon = character_data
    return [
        {
            'id': 1,
            'name': 'Achilles',
            'context': 'speaking in anger',
            'char': dict(achilles),
            'being': 'mortal',
            'number': 'individual',
            'gender': 'male',
            'anon': False,
        },
        {
            'id': 2,
            'name': 'Agamemnon',
            'context': 'addressed by Achilles',
            'char': dict(agamemnon),
            'being': 'mortal',
            'number': 'individual',
            'gender': 'male',
            'anon': False,
        },
    ]


@pytest.fixture
def speech_data(work_data, character_instance_data):
    spkr, addr = character_instance_data
    return {
        'id': 1,
        'cluster': {'id': 1, 'type': 'D'},
        'work': dict(work_data),
        'seq': 1,
        'l_fi': '1.1',
        'l_la': '1.7',
        'spkr': [dict(spkr)],
        'addr': [dict(addr)],
        'part': 1,
        'level': 0,
        'type': 'M',
    }
