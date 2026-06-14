'''nlp_cltk - CLTK-based NLP for DICES passages

Importing this module adds CLTK-based parsing methods to
`dicesapi.text.Passage`. It requires the `cltk` package, which is not
installed by default because it pulls in a large dependency tree (including
its own spaCy-based Greek pipeline):

    pip install dices-client[cltk]

Usage:

    import dicesapi.nlp_cltk   # adds Passage.runCltkPipeline, etc.

    passage = cts_api.getPassage(speech)
    passage.runCltkPipeline()
    for word in passage.cltk_doc:
        print(word.string, word.pos)
'''

import re
import cltk

from .text import Passage, PUNCT

cltk_nlp = None


def cltk_load():
    '''Load the CLTK Greek and Latin pipelines

    Called automatically the first time `runCltkPipeline` is used.
    '''

    global cltk_nlp
    cltk_nlp = dict(
        latin = cltk.NLP('lat', suppress_banner=True),
        greek = cltk.NLP('grc', suppress_banner=True),
    )

    # trim to the first two processes (tokenization, POS tagging)
    cltk_nlp['latin'].pipeline.processes = cltk_nlp['latin'].pipeline.processes[:2]
    cltk_nlp['greek'].pipeline.processes = cltk_nlp['greek'].pipeline.processes[:2]


def runCltkPipeline(self, index=True, remove=PUNCT):
    '''Parse text with the CLTK pipeline, populating self.cltk_doc'''

    text = self.text

    if text is None:
        return
    if remove is not None:
        text = re.sub(remove, ' ', self.text).strip()

    if cltk_nlp is None:
        cltk_load()

    self.cltk_doc = cltk_nlp[self.speech.lang](text)
    self.nlp = self.cltk_doc

    if index:
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


def getCltkWordIndex(self, word):
    '''Return the word's position in the list of words'''
    if self.cltk_doc is None:
        return

    return list(self.cltk_doc).index(word)


def buildTokenIndex(self):
    '''Alias for backward compatibility'''
    self.buildCltkTokenIndex()


@property
def cltk_alias(self):
    '''alias for backward compatibility'''
    return self.cltk_doc


# attach methods to Passage

Passage.runCltkPipeline = runCltkPipeline
Passage.buildCltkTokenIndex = buildCltkTokenIndex
Passage.getCltkWordIndex = getCltkWordIndex
Passage.buildTokenIndex = buildTokenIndex
Passage.cltk = cltk_alias
