Python client library for working with the DICES database of Greek and Roman epic speeches.

## Installation

The base package gives you the API client and tools for retrieving the text of 
speeches via CTS.

If you also want to run NLP pipelines (tokenization, POS tagging, etc.) on
speech texts, install the SpaCy extras.

```sh
pip install git+https://github.com/cwf2/dices-client # base
pip install "dices-client[spacy]@git+https://github.com/cwf2/dices-client" # SpaCy NLP
```
