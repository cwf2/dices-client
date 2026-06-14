'''tests for the cltk/spacy dependency split

`dicesapi` and `dicesapi.text` must be importable, and must not pull in
`cltk` or `spacy`, without the optional `nlp` extras installed. The
`nlp_spacy`/`nlp_cltk` modules are only exercised if those extras are
available (e.g. when running in a venv with `pip install dices-client[nlp]`).
'''

import subprocess
import sys

import pytest


def test_core_import_does_not_require_cltk_or_spacy():
    '''A fresh interpreter can import dicesapi and dicesapi.text even if
    cltk/spacy are not importable.'''

    code = (
        "import sys\n"
        "import dicesapi\n"
        "from dicesapi import text\n"
        "assert 'cltk' not in sys.modules\n"
        "assert 'spacy' not in sys.modules\n"
        "print('ok')\n"
    )
    result = subprocess.run(
        [sys.executable, '-c', code],
        capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'ok'


def test_passage_has_no_nlp_methods_by_default():
    from dicesapi.text import Passage

    p = Passage()
    assert not hasattr(p, 'runCltkPipeline')
    assert not hasattr(p, 'runSpacyPipeline')


def test_nlp_spacy_attaches_methods_to_passage():
    spacy = pytest.importorskip('spacy')

    import dicesapi.nlp_spacy  # noqa: F401
    from dicesapi.text import Passage

    p = Passage()
    assert hasattr(p, 'runSpacyPipeline')
    assert hasattr(p, 'buildSpacyTokenIndex')
    assert hasattr(p, 'getSpacyWordIndex')


def test_nlp_cltk_attaches_methods_to_passage():
    cltk = pytest.importorskip('cltk')

    import dicesapi.nlp_cltk  # noqa: F401
    from dicesapi.text import Passage

    p = Passage()
    assert hasattr(p, 'runCltkPipeline')
    assert hasattr(p, 'buildCltkTokenIndex')
    assert hasattr(p, 'getCltkWordIndex')
    assert p.cltk is None
