Python client library for working with the DICES database of Greek and Latin epic speeches.

DICES (Digital Initiative for Classics: Epic Speeches) records who says what to whom in Greek and Latin epic poetry. The database is at [db.dices.mta.ca](https://db.dices.mta.ca); this package talks to its API (`https://db.dices.mta.ca/api/`) and returns speeches, characters, works and authors as Python objects.

## Installation

The base package gives you the API client and tools for retrieving the text of 
speeches via CTS.

If you also want to run NLP pipelines (tokenization, POS tagging, etc.) on
speech texts, install the SpaCy extras.

```sh
pip install git+https://github.com/cwf2/dices-client # base
pip install "dices-client[spacy]@git+https://github.com/cwf2/dices-client" # SpaCy NLP
```

## Quick start

```python
from dicesapi import DicesAPI

api = DicesAPI()

# every speech by Achilles in the Iliad
speeches = api.getSpeeches(work_title="Iliad", spkr_name="Achilles")
print(len(speeches))

for speech in speeches.list[:3]:
    print(speech, [str(a) for a in speech.addr])
```

`getSpeeches()` accepts any search field the API supports as a keyword argument. To see them all:

```python
api.printSearchFields("speeches")
```

The same pattern works for `getWorks()`, `getAuthors()`, `getCharacters()`, `getInstances()` and `getClusters()`. Downloading the whole database takes about a minute; for repeated use, filter on the server where you can.

## Related resources

- Database and project: [dices.mta.ca](https://dices.mta.ca), [db.dices.mta.ca](https://db.dices.mta.ca)
- Server code: [github.com/cwf2/dices](https://github.com/cwf2/dices)
- Archived releases of the database: [doi:10.5683/SP3/N8LS2Y](https://doi.org/10.5683/SP3/N8LS2Y)
- Parsed, speech-annotated token tables for the same texts (CSV): [doi:10.5281/zenodo.24230236](https://doi.org/10.5281/zenodo.24230236)

## License

Released under the [MIT License](LICENSE).
