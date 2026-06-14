'''tests for DicesAPI's HTTP/pagination layer, with requests mocked out'''

from unittest.mock import patch, Mock

from dicesapi import DicesAPI, AuthorGroup


def _paged_response(results, next_url=None, count=None):
    '''build a fake `requests.get` response mimicking DRF pagination'''

    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = {
        'count': count if count is not None else len(results),
        'next': next_url,
        'results': results,
    }
    return resp


def test_get_paged_json_single_page(api):
    page = _paged_response([{'id': 1, 'name': 'Homer'}])

    with patch('dicesapi.requests.get', return_value=page) as mock_get:
        results = api.getPagedJSON('authors')

    assert results == [{'id': 1, 'name': 'Homer'}]
    mock_get.assert_called_once_with('http://testserver/api/authors', None)


def test_get_paged_json_follows_next_link(api):
    page1 = _paged_response(
        [{'id': 1, 'name': 'Homer'}],
        next_url='http://testserver/api/authors?page=2',
        count=2,
    )
    page2 = _paged_response([{'id': 2, 'name': 'Vergil'}], count=2)

    with patch('dicesapi.requests.get', side_effect=[page1, page2]) as mock_get:
        results = api.getPagedJSON('authors')

    assert results == [
        {'id': 1, 'name': 'Homer'},
        {'id': 2, 'name': 'Vergil'},
    ]
    assert mock_get.call_count == 2
    mock_get.assert_any_call('http://testserver/api/authors?page=2')


def test_get_paged_json_raises_for_bad_status(api):
    resp = Mock()
    resp.status_code = 404
    resp.raise_for_status.side_effect = Exception('not found')

    with patch('dicesapi.requests.get', return_value=resp):
        try:
            api.getPagedJSON('authors')
            assert False, 'expected an exception'
        except Exception as e:
            assert 'not found' in str(e)


def test_get_authors_wraps_results_in_authorgroup(api):
    page = _paged_response([{'id': 1, 'name': 'Homer'}, {'id': 2, 'name': 'Vergil'}])

    with patch('dicesapi.requests.get', return_value=page):
        authors = api.getAuthors()

    assert isinstance(authors, AuthorGroup)
    assert authors.getNames() == ['Homer', 'Vergil']


def test_get_speeches_passes_filter_params(api):
    page = _paged_response([])

    with patch('dicesapi.requests.get', return_value=page) as mock_get:
        api.getSpeeches(work_id=1)

    args, _ = mock_get.call_args
    assert args[0] == 'http://testserver/api/speeches'
    assert args[1] == {'work_id': 1}
