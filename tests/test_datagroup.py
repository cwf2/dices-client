'''tests for DataGroup and its subclasses (filtering, set operations, etc.)'''

import pytest

from dicesapi import AuthorGroup, CharacterGroup


@pytest.fixture
def authors(api):
    return AuthorGroup(
        [
            api.indexedAuthor({'id': 1, 'name': 'Homer'}),
            api.indexedAuthor({'id': 2, 'name': 'Vergil'}),
            api.indexedAuthor({'id': 3, 'name': 'Apollonius'}),
        ],
        api=api,
    )


@pytest.fixture
def characters(api, character_data):
    return CharacterGroup(
        [api.indexedCharacter(c) for c in character_data],
        api=api,
    )


def test_len_and_iteration(authors):
    assert len(authors) == 3
    assert [a.name for a in authors] == ['Homer', 'Vergil', 'Apollonius']


def test_getitem_slice_returns_same_type(authors):
    subset = authors[:2]

    assert isinstance(subset, AuthorGroup)
    assert [a.name for a in subset] == ['Homer', 'Vergil']


def test_sorted_does_not_mutate_original(authors):
    ordered = authors.sorted()

    assert [a.name for a in ordered] == ['Apollonius', 'Homer', 'Vergil']
    # original order is untouched
    assert [a.name for a in authors] == ['Homer', 'Vergil', 'Apollonius']


def test_sort_mutates_in_place(authors):
    authors.sort()

    assert [a.name for a in authors] == ['Apollonius', 'Homer', 'Vergil']


def test_filter_names(authors):
    homer_only = authors.filterNames(['Homer'])

    assert isinstance(homer_only, AuthorGroup)
    assert homer_only.getNames() == ['Homer']


def test_filter_names_no_match_returns_empty_group(authors):
    none_found = authors.filterNames(['Nobody'])

    assert len(none_found) == 0


def test_add_and_sub(authors):
    a = AuthorGroup(authors[:2].list, api=authors.api)
    b = AuthorGroup(authors[1:].list, api=authors.api)

    combined = a + b
    assert sorted(combined.getNames()) == sorted(authors.getNames())

    difference = a - b
    assert difference.getNames() == [authors[0].name]


def test_filter_genders(characters):
    males = characters.filterGenders(['male'])

    assert males.getNames() == ['Achilles', 'Agamemnon']

    females = characters.filterGenders(['female'])
    assert len(females) == 0
