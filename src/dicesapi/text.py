'''text - tools for working with CTS passages and NLP
'''

from MyCapytain.resolvers.cts.api import HttpCtsResolver
from MyCapytain.retrievers.cts5 import HttpCtsRetriever
import cltk
import spacy
import requests
from copy import deepcopy
import re

DEFAULT_SERVERS = {None: 'https://scaife-cts.perseus.org/api/cts'}
PUNCT = r'[ ,·.;\n—‘’“”]+'
SPACY_MODEL_GREEK = 'grc_proiel_sm'
SPACY_MODEL_LATIN = 'la_core_web_sm'

#
# setup default NLP pipelines
#

cltk_nlp = dict(
    latin = cltk.NLP('lat', suppress_banner=True),
    greek = cltk.NLP('grc', suppress_banner=True),
)

cltk_nlp['latin'].pipeline.processes = cltk_nlp['latin'].pipeline.processes[:2]
cltk_nlp['greek'].pipeline.processes = cltk_nlp['greek'].pipeline.processes[:2]


#
# spacy setup
#

spacy_nlp = None

def spacy_load(latin_model=SPACY_MODEL_LATIN, greek_model=SPACY_MODEL_GREEK):
    global spacy_nlp
    spacy_nlp = dict(
        latin = spacy.load(latin_model),
        greek = spacy.load(greek_model),
    )

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
        self.nlp = None
        self.cltk_doc = None
        self.spacy_doc = None
        self._line_index = None
        self._token_index = None
        self._cltk_token_index = None
        self._spacy_token_index = None
        self.text = None

    @property
    def cltk(self):
        '''alias for backward compatibility'''
        return self.cltk_doc
        
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
    
            
    def runSpacyPipeline(self, index=True, remove=PUNCT):
        '''Parse text with SpaCy create nlp doc'''

        text = self.text

        if text is None:
            return
        if remove is not None:
            text = re.sub(remove, ' ', self.text).strip()
        
        if spacy_nlp is None:
            spacy_load()
        
        self.spacy_doc = spacy_nlp[self.speech.lang](text)
        self.nlp = self.spacy_doc
        
        if index:
            self.buildSpacyTokenIndex()

    def runCltkPipeline(self, index=True, remove=PUNCT):
        '''Parse text with CLTK pipeline to populate cltk_doc'''

        text = self.text

        if text is None:
            return
        if remove is not None:
            text = re.sub(remove, ' ', self.text).strip()

        self.cltk_doc = cltk_nlp[self.speech.lang](text)
        self.nlp = self.cltk_doc
        
        if index:
            self.buildCltkTokenIndex()


    def buildTokenIndex(self):
        '''Alias for backward compatibility'''
        self.buildCltkTokenIndex()
        
    
    def buildCltkTokenIndex(self):
        '''Create an index linking cltk_doc to line_index'''
        
        if self.cltk_doc is None:
            return
        
        self._cltk_token_index = []
        
        text = self.text
        
        for w in self.cltk_doc:
            char_pos = text.find(w.string)
            
            # if string not found
            if char_pos == -1:
                self._cltk_token_index.append(None)
                continue
            
            self._cltk_token_index.append(char_pos)
            length = len(w.string)
            text = text[:char_pos] + '🧀'*length + text[char_pos+length:]
        
        self._token_index = self._cltk_token_index


    def buildSpacyTokenIndex(self):
        '''Create an index linking spacy_doc to line_index'''
        
        if self.spacy_doc is None:
            return
        
        self._spacy_token_index = []
        
        text = self.text
        
        for w in self.spacy_doc:
            char_pos = text.find(w.text)
            
            # bail if string not found
            if char_pos == -1:
                self._cltk_token_index.append(None)
                continue
        
            # otherwise, record position,
            # "cross off" matching string
            
            self._spacy_token_index.append(char_pos)
            length = len(w.text)
            text = text[:char_pos] + '🧀'*length + text[char_pos+length:]
        
        self._token_index = self._spacy_token_index
    

    def getWordIndex(self, word):
        '''Return the word's position in the list of words'''
        if self.nlp is None:
            return
            
        return list(self.nlp).index(word)
        
    
    def getCltkWordIndex(self, word):
        '''Return the word's position in the list of words'''
        if self.cltk_doc is None:
            return
            
        return list(self.cltk_doc).index(word)


    def getSpacyWordIndex(self, word):
        '''Return the word's position in the list of words'''
        if self.spacy_doc is None:
            return
            
        return list(self.spacy_doc).index(word)


    def getTextPos(self, word):
        '''Return a word's character position within the string passed to NLP'''

        if self.nlp is None:
            return        
        if self._token_index is None:
            return
        
        # if passed a Word, determine its index
        if isinstance(word, cltk.core.data_types.Word):
            word = self.getCltkWordIndex(word)
            token_index = self._cltk_token_index
        elif isinstance(word, spacy.tokens.token.Token):
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
        