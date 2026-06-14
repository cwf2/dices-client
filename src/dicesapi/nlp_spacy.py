'''nlp_spacy - spaCy-based NLP for DICES passages

Importing this module adds spaCy-based parsing methods to
`dicesapi.text.Passage`. It requires the `spacy` package, plus the Greek and
Latin models named below, to be installed separately:

    pip install dices-client[spacy]

Usage:

    import dicesapi.nlp_spacy   # adds Passage.runSpacyPipeline, etc.

    passage = cts_api.getPassage(speech)
    passage.runSpacyPipeline()
    for tok in passage.spacy_doc:
        print(tok.text, tok.pos_)
'''

import re
import spacy

from .text import Passage, PUNCT

SPACY_MODEL_GREEK = 'grc_odycy_joint_sm'
SPACY_MODEL_LATIN = 'la_core_web_md'

spacy_nlp = None


def spacy_load(latin_model=SPACY_MODEL_LATIN, greek_model=SPACY_MODEL_GREEK):
    '''Load the spaCy Greek and Latin models

    Called automatically the first time `runSpacyPipeline` is used, but can
    also be called explicitly to load different models.
    '''

    global spacy_nlp
    spacy_nlp = dict(
        latin = spacy.load(latin_model),
        greek = spacy.load(greek_model),
    )


def runSpacyPipeline(self, index=True, remove=PUNCT):
    '''Parse text with spaCy, populating self.spacy_doc'''

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
            self._spacy_token_index.append(None)
            continue

        # otherwise, record position,
        # "cross off" matching string

        self._spacy_token_index.append(char_pos)
        length = len(w.text)
        text = text[:char_pos] + '🧀'*length + text[char_pos+length:]

    self._token_index = self._spacy_token_index


def getSpacyWordIndex(self, word):
    '''Return the word's position in the list of words'''
    if self.spacy_doc is None:
        return

    return list(self.spacy_doc).index(word)


# attach methods to Passage

Passage.runSpacyPipeline = runSpacyPipeline
Passage.buildSpacyTokenIndex = buildSpacyTokenIndex
Passage.getSpacyWordIndex = getSpacyWordIndex
