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

SPACY_MODEL_URLS = {
    'grc_odycy_joint_sm':  'https://huggingface.co/chcaa/grc_odycy_joint_sm/resolve/main/grc_odycy_joint_sm-any-py3-none-any.whl',
    'grc_odycy_joint_trf': 'https://huggingface.co/chcaa/grc_odycy_joint_trf/resolve/main/grc_odycy_joint_trf-0.7.0-py3-none-any.whl',
    'la_core_web_md':      'https://huggingface.co/latincy/la_core_web_md/resolve/main/la_core_web_md-3.9.3-py3-none-any.whl',
    'la_core_web_trf':     'https://huggingface.co/latincy/la_core_web_trf/resolve/main/la_core_web_trf-3.9.3-py3-none-any.whl',
}


def _load_model(name):
    '''Load a single spaCy model by name, returning (model, error_message) tuple.'''
    try:
        return spacy.load(name), None
    except OSError:
        url = SPACY_MODEL_URLS.get(name)
        if url:
            return None, f"    pip install {url}"
        return None, f"    # no install URL known for '{name}'"
    except ValueError as e:
        if '[E002]' in str(e):
            return None, (
                f"    # '{name}' was installed after the kernel started —\n"
                f"    # restart your kernel and try again"
            )
        raise


def spacy_load(latin_model=None, greek_model=None):
    '''Load spaCy models and return them as a dict keyed by language.

    Called by DicesAPI.initializeNlp(); not normally called directly.
    Pass None for a language to skip loading a model for it.
    Raises RuntimeError listing any missing models and their install commands.
    '''
    if latin_model is None and greek_model is None:
        raise RuntimeError(
            "No models specified. Pass at least one of latin_model= or "
            "greek_model= to api.initializeNlp()."
        )

    try:
        import latincy_preprocess  # registers LatinCy pipeline components
    except ImportError:
        pass
    try:
        import spacy_transformers  # registers transformer factory for trf models
    except ImportError:
        pass

    result = {}
    errors = {}

    if latin_model is not None:
        result['latin'], errors['latin'] = _load_model(latin_model)
    if greek_model is not None:
        result['greek'], errors['greek'] = _load_model(greek_model)

    missing = {lang: msg for lang, msg in errors.items() if msg is not None}

    if missing:
        lines = ["One or more spaCy models could not be loaded.\n"]
        lines.append("Run the following in a new cell, then restart your kernel:\n")
        for msg in missing.values():
            lines.append(msg)
        raise RuntimeError("\n".join(lines))

    return result


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
    lang = self.speech.lang
    if lang not in nlp:
        raise RuntimeError(
            f"No NLP model loaded for {lang}. "
            f"Pass {lang}_model=... to api.initializeNlp()."
        )
    self.spacy_doc = nlp[lang](text)
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
