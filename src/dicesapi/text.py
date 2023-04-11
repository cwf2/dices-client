'''text - tools for working with CTS passages and CLTK
'''

from MyCapytain.resolvers.cts.api import HttpCtsResolver
from MyCapytain.retrievers.cts5 import HttpCtsRetriever
import cltk
import requests
from copy import deepcopy
import re

DEFAULT_SERVERS = {None: 'https://scaife-cts.perseus.org/api/cts'}
PUNCT = re.compile(r'[ ,·.;\n—]+')


#
# setup default NLP pipelines
#

cltk_nlp = dict(
    latin = cltk.NLP('lat', suppress_banner=True),
    greek = cltk.NLP('grc', suppress_banner=True),
)

cltk_nlp['latin'].pipeline.processes = cltk_nlp['latin'].pipeline.processes[:2]
cltk_nlp['greek'].pipeline.processes = cltk_nlp['greek'].pipeline.processes[:2]

# trigger installation of stanza data
cltk_nlp['greek']('χαίρε, ὦ κόσμος')
cltk_nlp['latin']('salve, mundus')

#
# definitions
#

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
        self.cltk = None
        self._line_index = None
        self._token_index = None
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
    
            
    def runCltkPipeline(self, index=True, remove_punct=False):
        '''Parse text with CLTK pipeline to populate cltk_doc'''

        text = self.text

        if text is None:
            return
        if remove_punct:
            text = PUNCT.sub(' ', self.text).strip()

        self.cltk = cltk_nlp[self.speech.lang](text)
        
        if index:
            self.buildCltkTokenIndex()
        
    
    def buildCltkTokenIndex(self):
        '''Create an index linking cltk_doc to line_index'''
        
        if self.cltk is None:
            return
        
        self._token_index = []
        
        text = self.text
        
        for w in self.cltk:
            char_pos = text.find(w.string)
            
            # bail if string not found
            if char_pos == -1:
                return
        
            # otherwise, record position,
            # "cross off" matching string
            
            self._token_index.append(char_pos)
            length = len(w.string)
            text = text[:char_pos] + '🧀'*length + text[char_pos+length:]
    
    
    def getWordIndex(self, word):
        '''Return the word's position in the list of words'''
        if self.cltk is None:
            return
            
        return list(self.cltk).index(word)


    def getTextPos(self, word):
        '''Return a word's character position within the string passed to CLTK'''

        if self.cltk is None:
            return        
        if self._token_index is None:
            return
        
        # if passed a Word, determine its index
        if isinstance(word, cltk.core.data_types.Word):
            word = self.getWordIndex(word)
        
        return self._token_index[word]


    def getLineIndex(self, word):
        if self.cltk is None:
            return
        if self._token_index is None:
            return
        if self._line_index is None:
            return
        
        char_pos = self.getTextPos(word)
        
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
        '''Return a parsed Passage object for the speech'''
        
        cts = self.getCTS(speech, force_download=force_download, cache=cache)
        
        if cts is None:
            return
        
        p = Passage(speech)
        p.cts = cts
        p.buildLineArray()

        if cltk:    
            p.runCltkPipeline()
        
        return p
        