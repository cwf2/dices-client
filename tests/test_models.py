'''tests for the core data model: Author, Work, Character, CharacterInstance, Speech'''

from dicesapi import Author, Work, Character, CharacterInstance, Speech


def test_author_from_data(api, author_data):
    author = Author(author_data, api=api)

    assert author.id == 1
    assert author.name == 'Homer'
    assert author.wd == 'Q6691'
    assert repr(author) == '<Author 1: Homer>'


def test_work_from_data_indexes_author(api, work_data):
    work = api.indexedWork(work_data)

    assert work.title == 'Iliad'
    assert work.lang == 'greek'
    assert work.author.name == 'Homer'

    # the author should also be reachable via the api's author index
    assert api.indexedAuthor({'id': 1, 'name': 'Homer'}) is work.author


def test_character_from_data(api, character_data):
    achilles_data, _ = character_data
    achilles = Character(achilles_data, api=api)

    assert achilles.name == 'Achilles'
    assert achilles.being == 'mortal'
    assert achilles.gender == 'male'
    assert achilles.wd == 'Q41746'
    assert achilles.manto == 'MANTO_ACHILLES'


def test_character_instance_exposes_underlying_character_ids(api, character_instance_data):
    spkr_data, _ = character_instance_data
    inst = CharacterInstance(spkr_data, api=api)

    assert inst.name == 'Achilles'
    assert inst.char.name == 'Achilles'

    # wd/manto/tt are forwarded from the underlying Character
    assert inst.wd == 'Q41746'
    assert inst.manto == 'MANTO_ACHILLES'
    assert inst.tt == 'TT_ACHILLES'


def test_speech_from_data(api, speech_data):
    speech = api.indexedSpeech(speech_data)

    assert speech.id == 1
    assert speech.work.title == 'Iliad'
    assert speech.author.name == 'Homer'
    assert speech.lang == 'greek'
    assert speech.l_fi == '1.1'
    assert speech.l_la == '1.7'
    assert speech.l_range == '1.1-1.7'
    assert speech.urn == f'{speech.work.urn}:1.1-1.7'

    assert speech.getSpkrString() == 'Achilles'
    assert speech.getAddrString() == 'Agamemnon'

    assert repr(speech) == '<Speech 1: Iliad 1.1-1.7>'


def test_speech_indexing_recycles_objects(api, speech_data):
    '''Fetching the same speech twice should return the same object'''

    s1 = api.indexedSpeech(speech_data)
    s2 = api.indexedSpeech({'id': speech_data['id']})

    assert s1 is s2


def test_speech_split_locus():
    speech = Speech()
    speech.l_fi = '9.503'
    speech.l_la = '9.510'

    assert speech.getLineNo('first') == '503'
    assert speech.getLineNo('last') == '510'
    assert speech.getPrefix('first') == '9'
    assert speech.getPrefix('first', trailing=True) == '9.'
    assert speech.isMultiPrefix() is False


def test_speech_split_locus_multi_prefix():
    speech = Speech()
    speech.l_fi = '9.999'
    speech.l_la = '10.5'

    assert speech.isMultiPrefix() is True
    assert speech.getPrefix('first') == '9'
    assert speech.getPrefix('last') == '10'


def test_author_ordering():
    a = Author({'id': 1, 'name': 'Apollonius'}, api=None, index=False)
    b = Author({'id': 2, 'name': 'Homer'}, api=None, index=False)

    assert a < b
    assert sorted([b, a]) == [a, b]
