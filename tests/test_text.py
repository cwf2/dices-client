'''tests for dicesapi.text: Passage line handling and module-level retrieval functions

dicesapi.text has no NLP dependencies (see test_module_split.py), so these
tests only cover CTS retrieval and line/text bookkeeping.
'''

from unittest.mock import patch

from lxml import etree

from dicesapi.text import Passage, getXML, getPassage, squashWhiteSpace, DEFAULT_CTS_PATTERN


TEI_PASSAGE = '''
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text><body><div>
    <l n="1">Some  words <note>an editorial note</note> on this line</l>
    <l n="2">and a second line of text</l>
  </div></body></text>
</TEI>
'''

TEI_BYTES = TEI_PASSAGE.strip().encode()


def _fake_xml():
    return etree.fromstring(TEI_BYTES)


def _fake_response(ok=True):
    from unittest.mock import Mock
    res = Mock()
    res.ok = ok
    res.content = TEI_BYTES
    res.status_code = 200 if ok else 404
    res.reason = 'OK' if ok else 'Not Found'
    return res


def _initialized_api(api):
    '''Return an api instance with CTS initialized'''
    api.initializeCts()
    return api


def test_squash_white_space():
    assert squashWhiteSpace('  a   b\nc  ') == 'a b c'


def test_build_line_array_strips_notes_and_joins_text():
    passage = Passage()
    passage.xml = _fake_xml()
    passage._buildLineArray()

    assert passage.line_array == [
        {'n': '1', 'seq': 0, 'text': 'Some words on this line'},
        {'n': '2', 'seq': 1, 'text': 'and a second line of text'},
    ]
    assert passage.text == 'Some words on this line and a second line of text'


def test_build_line_array_noop_without_xml():
    passage = Passage()
    passage._buildLineArray()

    assert passage.line_array is None
    assert passage.text is None


def test_get_line_for_text_position():
    passage = Passage()
    passage.xml = _fake_xml()
    passage._buildLineArray()
    passage._buildLineIndex()

    # fake a trivial 1-to-1 token index: token i sits at character i
    passage.nlp = list(passage.text)
    passage._token_index = list(range(len(passage.text)))

    # a character position in the second line ('and a second...')
    second_line_start = len(passage.line_array[0]['text']) + 1
    line = passage.getLine(second_line_start)

    assert line == passage.line_array[1]


def test_initialize_cts_sets_config(api):
    api.initializeCts()
    assert 'cts_pattern' in api.config
    assert 'cts_cache' in api.config
    assert api.config['cts_pattern'] == DEFAULT_CTS_PATTERN


def test_initialize_cts_custom_pattern(api):
    api.initializeCts(cts_pattern='https://example.org/{cts_urn}/xml/')
    assert api.config['cts_pattern'] == 'https://example.org/{cts_urn}/xml/'


def test_initialize_cts_does_not_overwrite(api):
    api.initializeCts(cts_pattern='https://first.example.org/{cts_urn}/xml/')
    api.initializeCts(cts_pattern='https://second.example.org/{cts_urn}/xml/')
    assert api.config['cts_pattern'] == 'https://first.example.org/{cts_urn}/xml/'


def test_get_xml_caches_result(api, speech_data):
    _initialized_api(api)
    speech = api.indexedSpeech(speech_data)

    with patch('dicesapi.text.requests.get', return_value=_fake_response()) as mock_get:
        first = getXML(speech)
        second = getXML(speech)

    assert first is not None
    assert first is second
    mock_get.assert_called_once()


def test_get_xml_returns_none_without_urn(api, speech_data):
    _initialized_api(api)
    speech_data['work']['urn'] = ''
    speech = api.indexedSpeech(speech_data)

    assert getXML(speech) is None


def test_get_passage_builds_line_array(api, speech_data):
    _initialized_api(api)
    speech = api.indexedSpeech(speech_data)

    with patch('dicesapi.text.requests.get', return_value=_fake_response()):
        passage = getPassage(speech)

    assert isinstance(passage, Passage)
    assert passage.line_array is not None
    assert passage.text.startswith('Some words on this line')


def test_fetch_passage_populates_speech(api, speech_data):
    _initialized_api(api)
    speech = api.indexedSpeech(speech_data)

    with patch('dicesapi.text.requests.get', return_value=_fake_response()):
        result = speech.fetchPassage()

    assert isinstance(result, Passage)
    assert speech.passage is result


def test_fetch_passage_raises_without_init(api, speech_data):
    speech = api.indexedSpeech(speech_data)

    try:
        speech.fetchPassage()
        assert False, 'expected RuntimeError'
    except RuntimeError as e:
        assert 'initializeCts' in str(e)
