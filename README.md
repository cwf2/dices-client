Python client library for working with the DICES database of Greek and Roman epic speeches.

⚠️ Work in progress: caveat qui utitur.

## Installation

The base package (`pip install dices-client`) gives you the API client
(`dicesapi`) and tools for retrieving the text of speeches via CTS
(`dicesapi.text`). It has no NLP dependencies.

If you also want to run NLP pipelines (tokenization, POS tagging, etc.) on
speech texts, install the relevant extra(s):

```sh
pip install dices-client[spacy]   # spaCy-based pipelines
pip install dices-client[cltk]    # CLTK-based pipelines
pip install dices-client[nlp]     # both
```

Each extra adds methods to `dicesapi.text.Passage` as a side effect of
importing the corresponding module:

```python
from dicesapi import DicesAPI
from dicesapi.text import CtsAPI

api = DicesAPI()
cts = CtsAPI(dices_api=api)
passage = cts.getPassage(some_speech)

# spaCy
import dicesapi.nlp_spacy
passage.runSpacyPipeline()

# CLTK
import dicesapi.nlp_cltk
passage.runCltkPipeline()
```

Previously, `dicesapi.text` imported both `spacy` and `cltk` unconditionally
and built CLTK pipelines for Greek and Latin at import time, even for users
who never used either. This made the package slow to import and prone to
dependency conflicts (e.g. clashing `numpy`/`spacy` versions) in fresh
environments such as Google Colab. NLP support is now opt-in as shown above;
existing code that calls `passage.runCltkPipeline()` or
`passage.runSpacyPipeline()` will keep working as long as the corresponding
`dicesapi.nlp_cltk` / `dicesapi.nlp_spacy` module has been imported first.
