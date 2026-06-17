'''text - tools for working with CTS passages

This module covers retrieval and line/text handling for the Greek and Latin
passages corresponding to speeches. It has no NLP dependencies.

For part-of-speech tagging, lemmatization, etc., see the optional
`dicesapi.nlp_spacy` module, which adds methods to the `Passage` class when
imported.
'''

import requests
from copy import deepcopy
from lxml import etree
import bisect
import re

from . import logger

DEFAULT_CTS_PATTERN = "https://atlas.perseus.tufts.edu/library/passage/{cts_urn}/xml/"
PUNCT = r'[ ,·.;\n—‘’“”]+'

# XML namespaces used by Perseus TEI, needed for xpath
nsmap = {
    "cts": "http://chs.harvard.edu/xmlns/cts",
    "tei": "http://www.tei-c.org/ns/1.0",
    "py": "http://codespeak.net/lxml/objectify/pytype",
}


#-----------------------------------------------------------------------------------
# Cludge to fix bad Perseus URNs: FIXME!!
#
# A set of regexes to replace our loci with Perseus-specific loci
# These fall into two different categories:
#   - some specific loci are mismatched because editions differ
#   - Perseus adds an extra hierarchical level in several of Claudian's
#     poems to distinguish the preface from the body of individual books.

PERSEUS_ADJUSTMENTS = {
    # Changes due to weird numbering schemes
    # Claudian
    #  - In Rufinum - change 1., 2. to 1.1., 2.1.
    "urn:cts:latinLit:stoa0089.stoa009.perseus-lat2": [(r"(\d)\.", r"\1.1.")],
    #  - DRP - change 1., 2. to 1.1., 2.1., except 2.praef -> 2.pr
    "urn:cts:latinLit:stoa0089.stoa005.perseus-lat2": [(r"(\d)\.(\d)", r"\1.1.\2"),
                                                       (r"praef", r"pr")],
    #  - De Bello Gothico - add 1. to every locus
    "urn:cts:latinLit:stoa0089.stoa003.perseus-lat2": [(r"(.+)", r"1.\1")],
    #  - Epithalamium - add 1. to every locus
    "urn:cts:latinLit:stoa0089.stoa006.perseus-lat2": [(r"(.+)", r"1.\1")],
    #  - 3 Hon. - add 1. to every locus
    "urn:cts:latinLit:stoa0089.stoa010.perseus-lat2": [(r"(.+)", r"1.\1")],
    #  - 6 Hon. - add 1. to every locus
    "urn:cts:latinLit:stoa0089.stoa012.perseus-lat2": [(r"(.+)", r"1.\1")],
    #  - de cons. Manlii Theodori - add 1. to every locus
    "urn:cts:latinLit:stoa0089.stoa013.perseus-lat2": [(r"(.+)", r"1.\1")],

    # Prudentius Psychomachia - add 1. to every locus
    "urn:cts:latinLit:stoa0238.stoa002.perseus-lat2": [(r"(.+)", r"1.\1")],

    # Changes due to differences between editions
    # A.R. Argon. - line 3.739 doesn't exist
    "urn:cts:greekLit:tlg0001.tlg001.perseus-grc2": [(r"3\.739", r"3.738")],
    # Hom. Od. - line 10.456 doesn't exist
    "urn:cts:greekLit:tlg0012.tlg002.perseus-grc2": [(r"10\.456", r"10.457")],
    # Ov. Met - lines 1.546, 4.802–803, 14.385 don't exist
    "urn:cts:latinLit:phi0959.phi006.perseus-lat2": [(r"1\.546", r"1.547"),
                                                     (r"4\.803", r"4.801"),
                                                     (r"14\.385", r"14.384")],
    # Stat. Theb. - line numbers for this speech are very wrong -- FIXME
    "urn:cts:latinLit:phi1020.phi001.perseus-lat2": [(r"4\.832", r"4.825"),
                                                     (r"4\.850", r"4.842")],
}

def getAdjustedUrn(speech):
    '''Work-specific cludges
        - to accommodate peculiarities of the way Perseus translates loci into URNs
    '''

    l_fi, l_la = speech.l_fi, speech.l_la
    
    if speech.work.urn in PERSEUS_ADJUSTMENTS:
        for pat, repl in PERSEUS_ADJUSTMENTS[speech.work.urn]:
            l_fi = re.sub(pat, repl, l_fi)
            l_la = re.sub(pat, repl, l_la)
        urn = f"{speech.work.urn}:{l_fi}-{l_la}"
    
        return urn
    else:
        return speech.urn

#-----------------------------------------------------------------------------------

def squashWhiteSpace(text):
    '''strip, reduce all contiguous whitespace to single space'''

    text = re.sub(r'\s+', ' ', text).strip()
    return text


class Passage(object):
    '''interface offering line-based or token-based access to passage'''

    def __init__(self, speech=None):
        self.speech = speech
        self.line_array = None
        self.xml = None
        self.nlp = None
        self.spacy_doc = None
        self._line_offsets = None
        self._token_index = None


    def _buildLineArray(self):
        '''Turn XML passage into an array of verse lines'''

        # bail if no XML
        if self.xml is None:
            return None

        # initialize line array
        line_array = []

        # work from copy of xml
        xml = deepcopy(self.xml)

        # remove notes
        for note in xml.findall(".//tei:note", namespaces=nsmap):
            note.clear(keep_tail=True)

        # remove deleted lines
        for del_ in xml.findall(".//tei:del", namespaces=nsmap):
            del_.clear(keep_tail=True)

        # iterate over verse lines
        for l in xml.findall(".//tei:l", namespaces=nsmap):
            line_num = l.get("n")
            if line_num is None:
                continue

            line_text = squashWhiteSpace("".join(s for s in l.itertext()))
            line_array.append(dict(
                n = line_num,
                seq = len(line_array),
                text = line_text,
            ))

        self.line_array = line_array

    @property
    def text(self):
        '''Return text of passage as one long string'''
        
        # bail if no line_array
        if not self.line_array:
            return None
        
        # join all the lines together with single spaces
        text = " ".join(l["text"] for l in self.line_array)
        
        return text


    def _buildLineIndex(self):
        '''Build _line_offsets: cumulative character start positions for each line.

        Used to map a token's character position back to its verse line via bisect.
        '''

        # bail if no line_array
        if not self.line_array:
            return None

        # initialize offsets, cumulative sum
        line_offsets = []
        cumsum = 0

        # iterate over line array, add length (plus 1 for spaces between lines)
        for line in self.line_array:
            line_offsets.append(cumsum)
            cumsum += len(line["text"]) + 1

        # make sure the count works out
        if cumsum != len(self.text) + 1:
            logger.warning(f"_buildLineIndex: character count doesn't match: {self.speech}")
            return None

        self._line_offsets = line_offsets


    def getTextPos(self, word):
        '''Return a word's character position within the string passed to NLP'''

        if self.nlp is None:
            return
        if self._token_index is None:
            return

        # if passed a spaCy Token, get its integer index; otherwise
        # treat `word` as an index into self._token_index directly
        if hasattr(word, 'text') and hasattr(word, 'i'):
            word = self.getSpacyWordIndex(word)
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
        if self._line_offsets is None:
            return

        # get position within the long string of the first character of this word
        char_pos = self.getTextPos(word)

        if char_pos is None:
            return
            
        # find appropriate line for this character position
        i = bisect.bisect_right(self._line_offsets, char_pos) - 1

        return i


    def getLinePos(self, word):
        '''Return a word's character position within its verse line'''

        char_pos = self.getTextPos(word)
        i = self.getLineIndex(word)

        return char_pos - self._line_offsets[i]


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


def getXML(speech, force=False):
    '''Fetch the CTS passage for a speech, returning parsed XML.

    Reads cts_pattern and cts_cache from speech.api.config.
    Returns None if the work has no URN or the request fails.
    '''

    if not speech.work.urn:
        return None

    config = speech.api.config
    url = config['cts_pattern'].format(cts_urn=getAdjustedUrn(speech))
    cache = config['cts_cache']

    if not force and url in cache:
        return cache[url]

    res = requests.get(url)
    if not res.ok:
        logger.warning(f"failed to download {speech.urn}: {res.status_code}: {res.reason}")
        return None

    xml = etree.fromstring(res.content)
    cache[url] = xml
    return xml


def getPassage(speech, force=False):
    '''Download and parse the text for a speech. Returns a Passage object.

    Reads configuration from speech.api.config (set up by api.initializeCts()).
    '''

    xml = getXML(speech, force=force)
    if xml is None:
        return None

    p = Passage(speech)
    p.xml = xml
    p._buildLineArray()
    p._buildLineIndex()
    return p
