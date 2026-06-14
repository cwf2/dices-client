'''tests for dicesapi.text: Passage line handling and CtsAPI

dicesapi.text has no NLP dependencies (see test_module_split.py), so these
tests only cover CTS retrieval and line/text bookkeeping.
'''

from unittest.mock import Mock

from lxml import etree

from dicesapi.text import Passage, CtsAPI, squashWhiteSpace


TEI_PASSAGE = '''
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text><body><div>
    <l n="1">Some  words <note>an editorial note</note> on this line</l>
    <l n="2">and a second line of text</l>
  </div></body></text>
</TEI>
'''


def _fake_cts():
    cts = Mock()
    cts.xml = etree.fromstring(TEI_PASSAGE)
    return cts


def test_squash_white_space():
    assert squashWhiteSpace('  a   b\nc  ') == 'a b c'


def test_build_line_array_strips_notes_and_joins_text():
    passage = Passage()
    passage.cts = _fake_cts()
    passage.buildLineArray()

    assert passage.line_array == [
        {'n': '1', 'text': 'Some words on this line'},
        {'n': '2', 'text': 'and a second line of text'},
    ]
    assert passage.text == 'Some words on this line and a second line of text'


def test_build_line_array_noop_without_cts():
    passage = Passage()
    passage.buildLineArray()

    assert passage.line_array is None
    assert passage.text is None


def test_get_line_for_text_position():
    passage = Passage()
    passage.cts = _fake_cts()
    passage.buildLineArray()

    # fake a trivial 1-to-1 token index: token i sits at character i
    passage.nlp = list(passage.text)
    passage._token_index = list(range(len(passage.text)))

    # a character position in the second line ('and a second...')
    second_line_start = len(passage.line_array[0]['text']) + 1
    line = passage.getLine(second_line_start)

    assert line == passage.line_array[1]


def test_cts_api_get_cts_caches_result(api, speech_data):
    speech = api.indexedSpeech(speech_data)

    cts_api = CtsAPI(dices_api=api)
    fake_cts = _fake_cts()
    cts_api._resolvers[None] = Mock(getTextualNode=Mock(return_value=fake_cts))

    first = cts_api.getCTS(speech)
    second = cts_api.getCTS(speech)

    assert first is fake_cts
    assert second is fake_cts
    cts_api._resolvers[None].getTextualNode.assert_called_once()


def test_cts_api_get_cts_returns_none_without_urn(api, speech_data):
    speech_data['work']['urn'] = ''
    speech = api.indexedSpeech(speech_data)

    cts_api = CtsAPI(dices_api=api)

    assert cts_api.getCTS(speech) is None


def test_cts_api_get_passage_builds_line_array(api, speech_data):
    speech = api.indexedSpeech(speech_data)

    cts_api = CtsAPI(dices_api=api)
    cts_api._resolvers[None] = Mock(getTextualNode=Mock(return_value=_fake_cts()))

    passage = cts_api.getPassage(speech)

    assert isinstance(passage, Passage)
    assert passage.line_array is not None
    assert passage.text.startswith('Some words on this line')


def test_get_passage_with_cltk_true_without_nlp_cltk_raises(api, speech_data):
    '''Requesting the CLTK pipeline without importing dicesapi.nlp_cltk
    should fail with a clear, actionable error rather than AttributeError.
    '''

    speech = api.indexedSpeech(speech_data)

    cts_api = CtsAPI(dices_api=api)
    cts_api._resolvers[None] = Mock(getTextualNode=Mock(return_value=_fake_cts()))

    try:
        cts_api.getPassage(speech, cltk=True)
        assert False, 'expected ImportError'
    except ImportError as e:
        assert 'nlp_cltk' in str(e)
