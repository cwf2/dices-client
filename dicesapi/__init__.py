import requests
from MyCapytain.resolvers.cts.api import HttpCtsResolver
from MyCapytain.retrievers.cts5 import HttpCtsRetriever

class Author(object):
    '''An ancient author'''

    def __init__(self, data=None, api=None, index=False):
        self.api = api
        self.index = (api is not None and index is not None)
        self.id = None
        self.name = None
        self.wd = None
        self.urn = None
        
        if data:
            self._from_data(data)


    def _from_data(self, data):
        '''populate attributes from data dict'''
        
        if 'id' in data:
            self.id = data['id']
        if 'name' in data:
            self.name = data['name']
        if 'wd' in data:
            self.wd = data['wd']
        if 'urn' in data:
            self.urn = data['urn']
        

class Work(object):
    '''An epic poem'''
    
    def __init__(self, data=None, api=None, index=False):
        self.api = api
        self.index = (api is not None and index is not None)
        self.id = None
        self.title = None
        self.wd = None
        self.urn = None
        self.author = None

        if data:
            self._from_data(data)
    
    
    def _from_data(self, data):
        '''populate attributes from data dict'''
        
        if 'id' in data:
            self.id = data['id']
        if 'title' in data:
            self.title = data['title']
        if 'wd' in data:
            self.wd = data['wd']
        if 'urn' in data:
            self.urn = data['urn']
        if 'author' in data:
            if self.index:
                self.author = self.api.indexedAuthor(data['author'])
            else:
                self.author = Author(data['author'], api=self.api)


class Character(object):
    '''The base identity of an epic character''' 
    
    def __init__(self, data=None, api=None, index=False):
        self.api = api
        self.index = (api is not None and index is not None)        
        self.id = None
        self.name = None
        self.being = None
        self.type = None
        self.wd = None
        self.manto = None
        
        if data:
            self._from_data(data)

    
    def _from_data(self, data):
        '''populate attributes from data'''
        
        if 'id' in data:
            self.id = data['id']
        if 'name' in data:
            self.name = data['name']
        if 'being' in data:
            self.being = data['being']
        if 'type' in data:
            self.type = data['type']
        if 'wd' in data:
            self.wd = data['wd']
        if 'manto' in data:
            self.manto = data['manto']


class CharacterInstance(object):
    '''An instance of a character in context'''
    
    def __init__(self, data=None, api=None, index=False):
        self.api = api
        self.index = (api is not None and index is not None)        
        self.id = None
        self.context = None
        self.char = None
        self.disg = None
        self._name = None
    
        if data:
            self._from_data(data)
        
    
    def _from_data(self, data):
        '''populate attributes from data'''
        
        if 'id' in data:
            self.id = data['id']
        if 'context' in data:
            self.context = data['context']
        if 'char' in data:
            if self.index:
                self.char = self.api.indexedCharacter(data['char'])
            else:
                self.char = Character(data['char'], api=self.api)
        if 'disg' in data:
            # FIXME
            self.disg = data['disg']

    
    def getName(self):
        '''Return a name for the character instance
        
           - Defaults to name of underlying character
        '''
        
        if self._name is not None:
            name = self._name
        elif self.disg is not None:
            name = self.char.disg.name
        else:
            name = self.char.name
        
        return name


class SpeechCluster(object):
    '''A speech cluster'''
    
    def __init__(self, data=None, api=None, index=False):
        self.api = api
        self.index = (api is not None and index is not None)        
        self.id = None
        self.type = None
        self.work = None
        
        if data:
            self._from_data(data)


    def _from_data(self, data):
        '''populate attributes from data'''
        
        if 'id' in data:
            self.id = data['id']
        if 'type' in data:
            self.type = data['type']
        if 'work' in data:
            if self.index:
                self.work = self.api.indexedWork(data['work'])
            else:
                self.work = Work(data['work'], api=self.api)
            

class Speech(object):
    '''A single speech'''

    def __init__(self, data=None, api=None, index=False):
        self.api = api
        self.index = (api is not None and index is not None)        
        self.data = data
        self.id = None
        self.cluster = None
        self.seq = None
        self.l_fi = None
        self.l_la = None
        self.spkr = None
        self.addr = None
        self.part = None
        
        if data:
            self._from_data(data)

        
    def _from_data(self, data):
        '''populate attributes from dict'''    
        
        if 'id' in data:
            self.id = data['id']
        if 'cluster' in data:
            if self.index:
                self.cluster = self.api.indexedSpeechCluster(data['cluster'])
            else:
                self.cluster = SpeechCluster(data['cluster'], api=self.api)
        if 'seq' in data:
            self.seq = data['seq']
        if 'l_fi' in data:
            self.l_fi = data['l_fi']
        if 'l_la' in data:
            self.l_la = data['l_la']
        if 'spkr' in data:
            if self.index:
                self.spkr = [self.api.indexedCharacterInstance(c)
                                    for c in data['spkr']]
            else:
                self.spkr = [CharacterInstance(c, api=self.api) 
                                    for c in data['spkr']]
        if 'addr' in data:
            if self.index:
                self.addr = [self.api.indexedCharacterInstance(c)
                                    for c in data['addr']]
            else:
                self.addr = [CharacterInstance(c, api=self.api) 
                                    for c in data['addr']]
        if 'part' in data:
            self.part = data['part']

    
    def __repr__(self):
        auth = self.cluster.work.author.name
        work = self.cluster.work.title
        l_fi = self.l_fi
        l_la = self.l_la
        return f'<Speech: {auth} {work} {l_fi}-{l_la}>'
    
    
    @property
    def work(self):
        '''shortcut to work (via cluster)'''
        return self.cluster.work
    
    
    @property
    def author(self):
        '''shortcut to work (via cluster)'''
        return self.work.author
    
    
    @property
    def l_range(self):
        '''line range in format <first>-<last>'''

        return f'{self.l_fi}-{self.l_la}'
    

    @property
    def urn(self):
        '''cts urn for the passage'''
    
        return f'{self.work.urn}:{self.l_range}'
    
    
    def getCTS(self):
        '''Get the CTS passage corresponding to the speech'''
                
        resolver = self.api.resolver
        cts = resolver.getTextualNode(self.work.urn, self.l_range)

        return cts

    
    def getLang(self):
        '''return language for the speech'''
        #FIXME
        
        if self.author.name in ['Homer', 'Apollonius']:
            lang = 'greek'
        elif self.author.name in ['Vergil']:
            lang = 'latin'
        else:
            lang = None
            
        return lang


class DicesAPI(object):
    '''a connection to the DICES API'''
    
    def __init__(self, dices_api=None, cts_api=None):
        self.API = dices_api
        self.CTS_API = cts_api
        self.resolver = HttpCtsResolver(HttpCtsRetriever(self.CTS_API))
        self._ProgressClass = None
        self._work_index = {}
        self._author_index = {}
        self._character_index = {}
        self._characterinstance_index = {}
        self._speech_index = {}
        self._speechcluster_index = {}
    

    def getPagedJSON(self, endpoint, params=None, progress=False):
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
        pbar = None
        if progress:
            if self._ProgressClass is not None:
                pbar = self._ProgressClass(max=count)
        
        # check for more pages
        while data['next']:
            res = requests.get(data['next'])
            if res.status_code == requests.codes.ok:
                data = res.json()
            else:
                res.raise_for_status()
            results.extend(data['results'])
            if pbar is not None:
                pbar.update(len(results))

        # check that we got everything
        if len(results) != count:
            print(f'Expected {count} results, got {len(results)}!')

        return results
        
        
    def getSpeeches(self, progress=False, **kwargs):
        '''Retrieve speeches from API'''
                
        # get the results from the speeches endpoint
        results = self.getPagedJSON('speeches', dict(**kwargs), progress=progress)
        
        # convert to Speech objects
        speeches = [self.indexedSpeech(s) for s in results]
        
        return speeches


    def getClusters(self, progress=False, **kwargs):
        '''Retrieve speech clusters from API'''
                
        # get the results from the speeches endpoint
        results = self.getPagedJSON('clusters', dict(**kwargs), progress=progress)
        
        # convert to Speech objects
        clusters = [self.indexedSpeechCluster(s) for s in results]
        
        return clusters

    
    def getCharacters(self, progress=False, **kwargs):
        '''Retrieve speeches from API'''
        
        # get the results from the speeches endpoint
        results = self.getPagedJSON('characters', dict(**kwargs), progress=progress)
        
        # convert to Character objects
        characters = [Character(c) for c in results]
        
        return characters
    

    def indexedAuthor(self, data):
        '''Create an author in the index'''
        
        if data['id'] in self._author_index:
            a = self._author_index[data['id']]
        else:
            a = Author(data, api=self, index=True)
            self._author_index[data['id']] = a
 
        return a


    def indexedWork(self, data):
        '''Create a work in the index'''
        
        if data['id'] in self._work_index:
            w = self._work_index[data['id']]
        else:
            w = Work(data, api=self, index=True)
            self._work_index[data['id']] = w
 
        return w

    
    def indexedSpeech(self, data):
        '''Create a speech in the index'''
        
        if data['id'] in self._speech_index:
            s = self._speech_index[data['id']]
        else:
            s = Speech(data, api=self, index=True)
            self._speech_index[data['id']] = s
        
        return s

        
    def indexedSpeechCluster(self, data):
        '''Create a speech cluster in the index'''
        
        if data['id'] in self._speechcluster_index:
            s = self._speechcluster_index[data['id']]
        else:
            s = SpeechCluster(data, api=self, index=True)
            self._speechcluster_index[data['id']] = s
        
        return s


    def indexedCharacter(self, data):
        '''Create a character in the index'''
        
        if data['id'] in self._character_index:
            c = self._character_index[data['id']]
        else:
            c = Character(data, api=self, index=True)
            self._character_index[data['id']] = c
        
        return c


    def indexedCharacterInstance(self, data):
        '''Create a character instance in the index'''
        
        if data['id'] in self._characterinstance_index:
            c = self._characterinstance_index[data['id']]
        else:
            c = CharacterInstance(data, api=self, index=True)
            self._characterinstance_index[data['id']] = c
        
        return c