import requests
import ipywidgets as widgets
from IPython.display import display

class Author(object):
    '''An ancient author'''

    def __init__(self, data=None):
        if data:
            self.data = data
        else:
            data = {}


class Work(object):
    '''An epic poem'''
    
    def __init__(self, data=None):
        if data:
            self.data = data
        else:
            data = {}


class Character(object):
    '''The base identity of an epic character''' 
    
    def __init__(self, data=None):
        if data:
            self.data = data
        else:
            data = {}


class Speech(object):
    '''A single speech'''

    def __init__(self, data=None):
        if data:
            self.data = data
        else:
            data = {}
    
    def getURN(self):
        '''generate urn for the passage'''
        
        try:
            work = self.data['cluster']['work']['urn']
            l_fi = self.data['l_fi']
            l_la = self.data['l_la']
        except KeyError:
            return None
        
        return f'{work}:{l_fi}-{l_la}'
    
    def getSpeakers(self):
        '''Return the list of speakers'''
        try:
            spkr = self.data['spkr']
        except KeyError:
            return None
            
        return [Character(inst['char']) for inst in spkr]


    def getAddressees(self):
        '''Return the list of addressees'''
        try:
            addr = self.data['addr']
        except KeyError:
            return None
            
        return [Character(inst['char']) for inst in addr]
        
        
    def getCTS(self, resolver):
        '''Get the CTS passage corresponding to the speech'''
        
        try:
            work = self.data['cluster']['work']['urn']
            l_fi = self.data['l_fi']
            l_la = self.data['l_la']
        except KeyError:
            return None
        
        cts = resolver.getTextualNode(work, f'{l_fi}-{l_la}')

        return cts

class SpeechCluster(object):
    '''A group of related speeches (conversation)'''

    def __init__(self, data=None):
        if data:
            self.data = data
        else:
            data = {}


class DicesAPI(object):
    '''a connection to the DICES API'''
    
    def __init__(self, api=None):
        self.API = api

    def getPagedJSON(self, endpoint, params=None, output=None):
        '''Collect paged results from the API'''
        
        # tidy slashes
        api = self.API.rstrip('/')
        endpoint = endpoint.lstrip('/')
        
        # make the request, retrieve json
        res = requests.get(f'{api}/{endpoint}', params)
        
        if res.status_code == requests.codes.ok:
            data = res.json()
        else:
            res.raise_for_status()
        
        # how many results in total?
        count = data['count']
        
        # collect results
        results = data['results']
        
        # create a progress bar
        pbar = widgets.IntProgress(
            value = len(results),
            min = 0,
            max = count,
            bar_style='info',
            orientation='horizontal'
        )
        pbar_label = widgets.Label(value = f'{len(results)}/{count}')
        
        if output is not None:
            output.children = [pbar, pbar_label]
        
        # check for more pages
        while data['next']:
            res = requests.get(data['next'])
            if res.status_code == requests.codes.ok:
                data = res.json()
            else:
                res.raise_for_status()
            results.extend(data['results'])
            pbar.value = len(results)
            pbar_label.value = f'{len(results)}/{count}'

        # check that we got everything
        if len(results) != count:
            print(f'Expected {count} results, got {len(results)}!')

        return results
        
        
    def getSpeeches(self, **kwargs):
        '''Retrieve speeches from API'''
        
        # output
        output = widgets.HBox()
        display(output)
        
        # get the results from the speeches endpoint
        results = self.getPagedJSON('speeches', dict(**kwargs), output)
        
        # convert to Speech objects
        speeches = [Speech(s) for s in results]
        
        return speeches
        
    
    def getCharacters(self, **kwargs):
        '''Retrieve speeches from API'''
        
        # output
        output = widgets.HBox()
        display(output)
        
        # get the results from the speeches endpoint
        results = self.getPagedJSON('characters', dict(**kwargs), output)
        
        # convert to Character objects
        characters = [Character(c) for c in results]
        
        return characters