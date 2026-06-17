'''nlp_spacy - spaCy-based NLP for DICES passages

Importing this module adds spaCy-based parsing methods to
`dicesapi.text.Passage`. It requires the `spacy` package, plus the Greek and
Latin models named below, to be installed separately:

    pip install dices-client[spacy]

Usage:

    import dicesapi.nlp_spacy   # adds Passage.runSpacyPipeline, etc.

    speech.fetchPassage()
    speech.passage.runSpacyPipeline()
    for tok in speech.passage.spacy_doc:
        print(tok.text, tok.pos_)
'''

import spacy

from .text import Passage

SPACY_MODEL_GREEK = 'grc_odycy_joint_trf'
SPACY_MODEL_LATIN = 'la_core_web_md'

SPACY_MODEL_URLS = {
    'grc_odycy_joint_sm':  'https://huggingface.co/chcaa/grc_odycy_joint_sm/resolve/main/grc_odycy_joint_sm-any-py3-none-any.whl',
    'grc_odycy_joint_trf': 'https://huggingface.co/chcaa/grc_odycy_joint_trf/resolve/main/grc_odycy_joint_trf-0.7.0-py3-none-any.whl',
    'la_core_web_md':      'https://huggingface.co/latincy/la_core_web_md/resolve/main/la_core_web_md-3.9.3-py3-none-any.whl',
}


def _load_model(name):
    '''Load a single spaCy model by name, with a helpful error if not installed.'''
    try:
        return spacy.load(name)
    except OSError:
        url = SPACY_MODEL_URLS.get(name)
        if url:
            raise OSError(
                f"spaCy model '{name}' is not installed. Install it with:\n\n"
                f"    pip install {url}\n\n"
                f"Then restart your kernel and try again.\n"
            ) from None
        raise
    except ValueError as e:
        if '[E002]' in str(e):
            raise RuntimeError(
                f"spaCy model '{name}' failed to load — a pipeline component "
                f"was not registered. This usually means the model was installed "
                f"after the kernel started. Restart your kernel and try again.\n"
            ) from None
        raise


def spacy_load(latin_model=SPACY_MODEL_LATIN, greek_model=SPACY_MODEL_GREEK):
    '''Load spaCy models and return them as a dict keyed by language.

    Called by DicesAPI.initializeNlp(); not normally called directly.
    '''
    try:
        import latincy_preprocess  # registers LatinCy pipeline components
    except ImportError:
        pass
    try:
        import spacy_transformers  # registers transformer factory for OdyCy trf
    except ImportError:
        pass
    return dict(
        latin = _load_model(latin_model),
        greek = _load_model(greek_model),
    )


def runSpacyPipeline(self, index=True):
    '''Parse text with spaCy, populating self.spacy_doc'''

    if 'nlp' not in self.speech.api.config:
        raise RuntimeError(
            "NLP is not initialized. Call api.initializeNlp() first."
        )

    text = self.text

    if text is None:
        return

    nlp = self.speech.api.config['nlp']
    self.spacy_doc = nlp[self.speech.lang](text)
    self.nlp = self.spacy_doc

    if index:
        self.buildSpacyTokenIndex()


def buildSpacyTokenIndex(self):
    '''Create an index mapping each spacy_doc token to its char offset in self.text'''

    if self.spacy_doc is None:
        return

    self._token_index = [tok.idx for tok in self.spacy_doc]


def getSpacyWordIndex(self, word):
    '''Return the word's position in the list of words'''
    if self.spacy_doc is None:
        return

    return list(self.spacy_doc).index(word)


# attach methods to Passage

Passage.runSpacyPipeline = runSpacyPipeline
Passage.buildSpacyTokenIndex = buildSpacyTokenIndex
Passage.getSpacyWordIndex = getSpacyWordIndex
