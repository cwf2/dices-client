import requests
from MyCapytain.resolvers.cts.api import HttpCtsResolver
from MyCapytain.retrievers.cts5 import HttpCtsRetriever

class _DataGroup(object):
    def __init__(self, things=None):
        self._things=things

    def filter(self, attribute, value):
        newlist = []
        for thing in self._things:
            if thing._attributes[attribute] == value:
                newlist.append(thing)
        return self.__init__(newlist)
    
    def filterList(self, attribute, filterList):
        newlist = []
        for thing in self._things:
            if(thing._attributes[attribute] in filterList and thing._attributes[attribute] is not None):
                newlist.append(thing)
        return self.__init__(newlist)
    
    def deepFilter(self, attributes, value):
        newlist = []
        for thing in self._things:
            filterList = thing._attributes
            success = True
            for attr in attributes:
                if(attr not in filterList):
                    success = False
                    break
                filterList=filterList[attr]
            if(success and filterList == value):
                newlist.append(thing)
        return self.__init__(newlist)
            
    @property
    def list(self):
        return [x for x in self._things]

class _AuthorGroup(_DataGroup):
    def __init__(self, things=None):
        self._things = things
    
    def getIDs(self):
        return [x.id for x in self._things]
    
    def getNames(self):
        return [x.name for x in self._things]

    def getWDs(self):
        return [x.wd for x in self._things]
    
    def getUrns(self):
        return [x.urn for x in self._things]

    def filterNames(self, names, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.name in names and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _AuthorGroup(newlist)
    
    def filterIDs(self, ids, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.id in ids and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _AuthorGroup(newlist)

    def filterWDs(self, wds, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.wd in wds and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _AuthorGroup(newlist)

    def filterUrns(self, urns, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.urn in urns and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _AuthorGroup(newlist)

class Author(object):
    '''An ancient author'''

    def __init__(self, data=None, api=None, index=False):
        self.api = api
        self.index = (api is not None and index is not None)
        self.id = None
        self.name = None
        self.wd = None
        self.urn = None
        self._attributes = data
        
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

class _WorkGroup(_DataGroup):
    def __init__(self, things=None):
        self._things = things   

    def getIDs(self):
        return [x.id for x in self._things]
    
    def getTitles(self):
        return [x.title for x in self._things]
    
    def getWDs(self):
        return [x.wd for x in self._things]

    def getURNs(self):
        return [x.urn for x in self._things]
    
    def getAuthors(self):
        return [x.author for x in self._things]

    def filterIDs(self, ids, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.id in ids and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _WorkGroup(newlist)

    def filterTitles(self, titles, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.title in titles and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _WorkGroup(newlist)

    def filterWDs(self, wds, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.wd in wds and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _WorkGroup(newlist)

    def filterUrns(self, urns, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.urn in urns and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _WorkGroup(newlist)

    def filterAuthors(self, authors, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.author in authors and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _WorkGroup(newlist)

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
        self._attributes = data

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
            data['author'] = self.author

class _CharacterGroup(_DataGroup):
    def __init__(self, things=None):
        self._things = things
    
    def getIDs(self):
        return [x.id for x in self._things]
    
    def getNames(self):
        return [x.name for x in self._things]
    
    def getBeings(self):
        return [x.being for x in self._things]
    
    def getTypes(self):
        return [x.type for x in self._things]
    
    def getWDs(self):
        return [x.wd for x in self._things]

    def getMantos(self):
        return [x.manto for x in self._things]
    
    def getGenders(self):
        return [x.gender for x in self._things]

    def filterIDs(self, ids, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.id in ids and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _CharacterGroup(newlist)

    def filterNames(self, names, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.name in names and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _CharacterGroup(newlist)

    def filterBeings(self, beings, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.being in beings and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _CharacterGroup(newlist)

    def filterTypes(self, types, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.type in types and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _CharacterGroup(newlist)

    def filterWDs(self, wds, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.wd in wds and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _CharacterGroup(newlist)

    def filterMantos(self, mantos, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.manto in mantos and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _CharacterGroup(newlist)

    def filterGenders(self, genders, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.gender in genders and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _CharacterGroup(newlist)

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
        self.gender = None
        self._attributes = data
        
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
        if 'gender' in data:
            self.gender = data['gender']

class _CharacterInstanceGroup(_DataGroup):
    def __init__(self, things=None):
        self._things = things
    
    def getIDs(self):
        return [x.id for x in self._things]
    
    def getContexts(self):
        return [x.context for x in self._things]
    
    def getChars(self):
        return [x.char for x in self._things]
    
    def getDisgs(self):
        return [x.disg for x in self._things]
    
    def getNames(self):
        return [x._name for x in self._things]
    
    def getGenders(self):
        return [x._gender for x in self._things]
    
    def filterIDs(self, ids, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.id in ids and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _CharacterInstanceGroup(newlist)
    
    def filterContexts(self, contexts, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.context in contexts and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _CharacterInstanceGroup(newlist)

    def filterChars(self, chars, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.char in chars and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _CharacterInstanceGroup(newlist)

    def filterDisgs(self, disgs, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.disg in disgs and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _CharacterInstanceGroup(newlist)

    def filterNames(self, names, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing._names in names and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _CharacterInstanceGroup(newlist)

    def filterGenders(self, genders, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing._gender in genders and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _CharacterInstanceGroup(newlist)

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
        self._gender = None
        self._attributes = data

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
            data['char'] = self.char
        if 'disg' in data:
            # FIXME
            self.disg = data['disg'] 
        if 'gender' in data and data['gender'] is not None:
            self._gender = data['gender']
    
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

    @property
    def gender(self):
        return self._gender or self.char.gender
    
    '''@gender.setter
    def gender(self, new_gender):
        self._gender = new_gender'''

class _SpeechClusterGroup(_DataGroup):
    def __init__(self, speeches=None):
        self._things = speeches
    
    def getIDs(self):
        return [x.id for x in self._things]
    
    def getTypes(self):
        return [x.type for x in self._things]
    
    def getWorks(self):
        return [x.work for x in self._things]

    def filterIDs(self, ids, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.id in ids and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _SpeechClusterGroup(newlist)

    def filterTypes(self, types, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.type in types and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _SpeechClusterGroup(newlist)

    def filterWDs(self, works, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.work in works and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _SpeechClusterGroup(newlist)

class SpeechCluster(object):
    '''A speech cluster'''
    
    def __init__(self, data=None, api=None, index=False):
        self.api = api
        self.index = (api is not None and index is not None)        
        self.id = None
        self.type = None
        self.work = None
        self._attributes = data
        
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
            data['work'] = self.work
            

class _SpeechGroup(_DataGroup):
    def __init__(self, speeches=None):
        self._things = speeches
    
    def getIDs(self):
        return [x.id for x in self._things]
    
    def getClusters(self):
        return [x.cluster for x in self._things]
    
    def getSeqs(self):
        return [x.seq for x in self._things]
    
    def get_L_FIs(self):
        return [x.l_fi for x in self._things]
    
    def get_L_LAs(self):
        return [x.l_la for x in self._things]
    
    def getSpkrs(self):
        return [x.spkr for x in self._things]
    
    def getAddrs(self):
        return [x.addr for x in self._things]
    
    def getParts(self):
        return [x.part for x in self._things]

    def filterIDs(self, ids, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.id in ids and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _SpeechGroup(newlist)

    def filterClusters(self, clusters, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.cluster in clusters and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _SpeechGroup(newlist)

    def filterSeqs(self, seqs, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.seq in seqs and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _SpeechGroup(newlist)

    def filterL_FIs(self, l_fis, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.l_fi in l_fis and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _SpeechGroup(newlist)

    def filterL_LAs(self, l_las, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.l_la in l_las and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _SpeechGroup(newlist)

    def filterSpkrs(self, spkrs, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.spkr in spkrs and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _SpeechGroup(newlist)

    def filterAddrs(self, addrs, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.addr in addrs and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _SpeechGroup(newlist)

    def filterParts(self, parts, incl_none=False):
        newlist = []
        for thing in self._things:
            if(thing.part in parts and (thing is not None or (thing is None and incl_none))):
                newlist.append(thing)
        return _SpeechGroup(newlist)

class Speech(object):
    '''A single speech'''

    def __init__(self, data=None, api=None, index=False):
        self.api = api
        self.index = (api is not None and index is not None)        
        self.id = None
        self.cluster = None
        self.seq = None
        self.l_fi = None
        self.l_la = None
        self.spkr = None
        self.addr = None
        self.part = None
        self._attributes = data
        
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
            data['cluster'] = self.cluster
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
            data['spkr'] = self.spkr
        if 'addr' in data:
            if self.index:
                self.addr = [self.api.indexedCharacterInstance(c)
                                    for c in data['addr']]
            else:
                self.addr = [CharacterInstance(c, api=self.api) 
                                    for c in data['addr']]
            data['addr'] = self.addr
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
    DEFAULT_API = 'https://fierce-ravine-99183.herokuapp.com/api'
    DEFAULT_CTS = 'http://cts.perseids.org/api/cts/'
    
    def __init__(self, dices_api=DEFAULT_API, cts_api=DEFAULT_CTS):
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
        speeches = _SpeechGroup([self.indexedSpeech(s) for s in results])
        
        return speeches


    def getClusters(self, progress=False, **kwargs):
        '''Retrieve speech clusters from API'''
                
        # get the results from the clusters endpoint
        results = self.getPagedJSON('clusters', dict(**kwargs), progress=progress)
        
        # convert to Clusters objects
        clusters = _SpeechClusterGroup([self.indexedSpeechCluster(s) for s in results])
        
        return clusters

    
    def getCharacters(self, progress=False, **kwargs):
        '''Retrieve characters from API'''
        
        # get the results from the characters endpoint
        results = self.getPagedJSON('characters', dict(**kwargs), progress=progress)
        
        # convert to Character objects
        characters = _CharacterGroup([Character(c) for c in results])
        
        return characters

    def getWorks(self, progress=False, **kwargs):
        '''Fetch works from the API'''
        results = self.getPagedJSON('works', dict(**kwargs), progress=progress)

        works = _WorkGroup([self.indexedWork(w) for w in results])
        return works

    def getAuthors(self, progress=False, **kwargs):
        '''Fetch authors from the API'''
        results = self.getPagedJSON('authors', dict(**kwargs), progress=progress)

        authors = _AuthorGroup([self.indexedAuthor(a) for a in results])
        return authors

    def getInstances(self, progress=False, **kwargs):
        '''Fetch character instances from the API'''
        results = self.getPagedJSON('instances', dict(**kwargs), progress=progress)

        instances = _CharacterInstanceGroup([self.indexedCharacterInstance(i) for i in results])
        return instances
        
    

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