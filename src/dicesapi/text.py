'''text - tools for working with CTS passages

This module covers retrieval and line/text handling for the Greek and Latin
passages corresponding to speeches. It has no NLP dependencies.

For part-of-speech tagging, lemmatization, etc., see the optional
`dicesapi.nlp_spacy` and `dicesapi.nlp_cltk` modules, which add methods to
the `Passage` class when imported.
'''

from MyCapytain.resolvers.cts.api import HttpCtsResolver
from MyCapytain.retrievers.cts5 import HttpCtsRetriever
import requests
from copy import deepcopy
import re

DEFAULT_SERVERS = {None: 'https://scaife-cts.perseus.org/api/cts'}
PUNCT = r'[ ,·.;\n—‘’“”]+'


def squashWhiteSpace(text):
    '''strip, reduce all contiguous whitespace to single space'''

    text = re.sub(r'\s+', ' ', text).strip()
    return text


class Passage(object):
    '''interface offering line-based or token-based access to passage'''

    def __init__(self, speech=None):
        self.speech = speech
        self.line_array = None
        self.cts = None
        self.nlp = None
        self.cltk_doc = None
        self.spacy_doc = None
        self._line_index = None
        self._token_index = None
        self._cltk_token_index = None
        self._spacy_token_index = None
        self.text = None

    def buildLineArray(self):
        '''Parse CTS passage into lines'''

        if self.cts is None:
            return

        # build line array

        xml = deepcopy(self.cts.xml)

        for note in xml.findall('.//l//note', namespaces=xml.nsmap):
            note.clear(keep_tail=True)

        lines = xml.findall('.//l', namespaces=xml.nsmap)

        self.line_array = [dict(
            n = l.get('n'),
            text = squashWhiteSpace(''.join(l.itertext())),
        ) for l in lines]

        # build line index

        self._line_index = []
        cumsum = 0

        for i in range(len(self.line_array)):
            self._line_index.append(cumsum)
            cumsum += len(self.line_array[i]['text']) + 1

        self.text = ' '.join(l['text'] for l in self.line_array)


    def getWordIndex(self, word):
        '''Return the word's position in the list of words'''
        if self.nlp is None:
            return

        return list(self.nlp).index(word)


    def getTextPos(self, word):
        '''Return a word's character position within the string passed to NLP'''

        if self.nlp is None:
            return
        if self._token_index is None:
            return

        # if passed a token from an NLP library, determine its index
        # via the appropriate (optional) extension module; otherwise
        # treat `word` as an index into self._token_index directly
        if hasattr(word, 'string'):
            # duck-types as a cltk Word; requires dicesapi.nlp_cltk
            word = self.getCltkWordIndex(word)
            token_index = self._cltk_token_index
        elif hasattr(word, 'text') and hasattr(word, 'i'):
            # duck-types as a spacy Token; requires dicesapi.nlp_spacy
            word = self.getSpacyWordIndex(word)
            token_index = self._spacy_token_index
        else:
            token_index = self._token_index

        try:
            idx = token_index[word]
        except IndexError:
            idx = None

        return idx


    def getLineIndex(self, word):
        if self.nlp is None:
            return
        if self._token_index is None:
            return
        if self._line_index is None:
            return

        char_pos = self.getTextPos(word)

        if char_pos is None:
            return

        for i, length in enumerate(self._line_index):
            if length > char_pos:
                i -= 1
                break

        return i


    def getLinePos(self, word):
        '''Return a word's character position within its verse line'''

        char_pos = self.getTextPos(word)
        i = self.getLineIndex(word)

        return char_pos - self._line_index[i]


    def getLine(self, word):
        '''Return a word's containing line from line_array'''

        idx = self.getLineIndex(word)
        return self.line_array[idx]


    def toHTML(self):
        '''Create a simple html table for passage display'''

        if self.line_array is not None:
            html = ''

            s = self.speech
            spkr_names = ', '.join([inst.name for inst in s.spkr])
            addr_names = ', '.join([inst.name for inst in s.addr])

            html += '<div>'
            html += f'<h4>{s.author.name} {s.work.title} {s.l_range}</h4>'
            html += f'<h5>{spkr_names} to {addr_names}</h4>'
            html += '<table><tbody>'

            for row in s.passage.line_array:
                html += f'<tr><td class="n">{row["n"]}</td><td>{row["text"]}</td></tr>'

            html += '</tbody></table>'
            html += '</div>'

            return html


class CtsAPI(object):
    '''interace to digital texts via CTS
    '''

    def __init__(self, servers=DEFAULT_SERVERS, dices_api=None):
        self.dices_api = dices_api
        self._servers = servers
        self._resolvers = self._buildResolvers()
        self.__cts_cache__ = {}

    def _buildResolvers(self):
        '''create a set of urn-specific resolvers'''

        resolvers = dict()
        for urn, server in self._servers.items():
            resolvers[urn] = HttpCtsResolver(HttpCtsRetriever(server))
        return resolvers

    def getResolver(self, urn):
        '''return a resolved for the given text'''

        return self._resolvers.get(urn, self._resolvers[None])


    def getCTS(self, speech, force_download=False, cache=True):
        '''Fetch the CTS passage corresponding to the speech'''

        if cache:
            # return cached version if exists
            cache_key = f'{speech.work.urn}:{speech.l_range}'
            if cache_key in self.__cts_cache__:
                if not force_download:
                    return self.__cts_cache__[cache_key]

        # bail out if work has no urn
        if (speech.work.urn == '') or (speech.work.urn is None):
            return None

        # check for urn-specific resolver, otherwise, use default
        resolver = self.getResolver(speech.work.urn)

        # retrieve the passage
        try:
            cts_passage = resolver.getTextualNode(speech.work.urn, speech.l_range)

        except requests.exceptions.HTTPError as e:
            speech.api.logWarning(f'Failed to download {speech.urn}: ' + str(e), speech.api.LOG_LOWDETAIL)
            return None

        # cache
        if cache:
            self.__cts_cache__[cache_key] = cts_passage

        return cts_passage


    def getPassage(self, speech, force_download=False, cache=True, cltk=False):
        '''Return a parsed Passage object for the speech

        Args:
            cltk (bool): If True, also run the CLTK NLP pipeline on the
                passage. Requires `dicesapi.nlp_cltk` to have been imported.
        '''

        cts = self.getCTS(speech, force_download=force_download, cache=cache)

        if cts is None:
            return

        p = Passage(speech)
        p.cts = cts
        p.buildLineArray()

        if cltk:
            if not hasattr(p, 'runCltkPipeline'):
                raise ImportError(
                    'getPassage() was called with cltk=True, but the CLTK '
                    'pipeline is not available. Run `import dicesapi.nlp_cltk` '
                    'first to enable it.'
                )
            p.runCltkPipeline()

        return p
