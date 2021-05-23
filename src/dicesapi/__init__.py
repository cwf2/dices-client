import requests
from MyCapytain.resolvers.cts.api import HttpCtsResolver
from MyCapytain.retrievers.cts5 import HttpCtsRetriever

class _DataGroup(object):
    '''Parent class for all DataGroups used to hold objects from the API'''
    def __init__(self, things=None):
        self._things=things
    
    def __iter__(self):
        for x in self._things:
            yield x
    
    def __getitem__(self, key):
        return self._things[key]
    
    def __len__(self):
        return len(self._things)

    def extend(self, datagroup):
        '''Combines two data groups of the same type'''
        if(isinstance(datagroup, self.__class__)):
            self._things.extend(datagroup._things)
            self._things = list(set(self._things))

    def filterAttribute(self, attribute, value):
        '''Filters all objects in this DataGroup using the specified attribute for a given value'''
        newlist = []
        for thing in self._things:
            if thing._attributes[attribute] == value:
                newlist.append(thing)
        #return self.__init__(newlist)
        return type(self)(newlist)
    
    def filterList(self, attribute, filterList):
        '''Filters all objects in this DataGroup using the specified attribute and checks if the value exists in the given list'''
        newlist = []
        for thing in self._things:
            if(thing._attributes[attribute] in filterList and thing._attributes[attribute] is not None):
                newlist.append(thing)
        return type(self)(newlist)
    
    def deepFilterAttributes(self, attributes, value):
        '''Filters all objects in this DataGroup by filtering the attributes given from a list of attributes (If given ["cluster", "work"] it will check if object->attributes->cluster->work equals the given value)'''
        print("Deep filtering")
        newlist = []
        for thing in self._things:
            filterList = thing._attributes
            success = True
            for attr in attributes:
                if(attr not in filterList):
                    success = False
                    print("Failed")
                    break
                filterList=filterList[attr]
            if(success and filterList == value):
                newlist.append(thing)
        return type(self)(newlist)
            
    @property
    def list(self):
        return [x for x in self._things]

class _AuthorGroup(_DataGroup):
    '''Datagroup used to hold a list of Authors'''
    def __init__(self, things=None):
        self._things = things
    
    def getIDs(self):
        '''Returns a list of author ID's'''
        return [x.id for x in self._things]
    
    def getNames(self):
        '''Return a list of the authors names'''
        return [x.name for x in self._things]

    def getWDs(self):
        '''Returns a list of the author WD's'''
        return [x.wd for x in self._things]
    
    def getUrns(self):
        '''Returns a list of author Urn's'''
        return [x.urn for x in self._things]

    def filterNames(self, names, incl_none=False):
        '''Filter on the author names'''
        newlist = []
        for thing in self._things:
            if((thing is not None or (thing is None and incl_none)) and thing.name in names):
                newlist.append(thing)
        return _AuthorGroup(newlist)
    
    def filterIDs(self, ids, incl_none=False):
        '''Filter on the author ID's'''
        newlist = []
        for thing in self._things:
            if((thing is not None or (thing is None and incl_none)) and thing.id in ids):
                newlist.append(thing)
        return _AuthorGroup(newlist)

    def filterWDs(self, wds, incl_none=False):
        '''Filter on the author WD's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.wd in wds ):
                newlist.append(thing)
        return _AuthorGroup(newlist)

    def filterUrns(self, urns, incl_none=False):
        '''Filter on the author Urns'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.urn in urns ):
                newlist.append(thing)
        return _AuthorGroup(newlist)

class Author(object):
    '''An ancient author'''

    def __init__(self, data=None, api=None, index=True):
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
    '''Datagroup used to hold a list of works'''
    def __init__(self, things=None):
        self._things = things   

    def getIDs(self):
        '''Returns a list of work ID's'''
        return [x.id for x in self._things]
    
    def getTitles(self):
        '''Returns a list of work Title's'''
        return [x.title for x in self._things]
    
    def getWDs(self):
        '''Returns a list of work WD's'''
        return [x.wd for x in self._things]

    def getURNs(self):
        '''Returns a list of work Urn's'''
        return [x.urn for x in self._things]
    
    def getAuthors(self):
        '''Returns a list of work Author's'''
        return _AuthorGroup([x.author for x in self._things])

    def filterIDs(self, ids, incl_none=False):
        '''Filter on the works ID's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.id in ids ):
                newlist.append(thing)
        return _WorkGroup(newlist)

    def filterTitles(self, titles, incl_none=False):
        '''Filter on the works Title's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.title in titles ):
                newlist.append(thing)
        return _WorkGroup(newlist)

    def filterWDs(self, wds, incl_none=False):
        '''Filter on the works WD's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.wd in wds ):
                newlist.append(thing)
        return _WorkGroup(newlist)

    def filterUrns(self, urns, incl_none=False):
        '''Filter on the works Urn's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.urn in urns ):
                newlist.append(thing)
        return _WorkGroup(newlist)

    def filterAuthors(self, authors, incl_none=False):
        '''Filter on the works Author's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.author in authors ):
                newlist.append(thing)
        return _WorkGroup(newlist)

class Work(object):
    '''An epic poem'''
    
    def __init__(self, data=None, api=None, index=True):
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
            #data['author'] = self.author

class _CharacterGroup(_DataGroup):
    '''Datagroup used to hold a list of Characters'''
    def __init__(self, things=None):
        self._things = things
    
    def getIDs(self):
        '''Returns a list of character ID's'''
        return [x.id for x in self._things]
    
    def getNames(self):
        '''Returns a list of character Name's'''
        return [x.name for x in self._things]
    
    def getBeings(self):
        '''Returns a list of character Being's'''
        return [x.being for x in self._things]
    
    def getTypes(self):
        '''Returns a list of character Type's'''
        return [x.type for x in self._things]
    
    def getWDs(self):
        '''Returns a list of character WD's'''
        return [x.wd for x in self._things]

    def getMantos(self):
        '''Returns a list of character Manto's'''
        return [x.manto for x in self._things]
    
    def getGenders(self):
        '''Returns a list of character Gender's'''
        return [x.gender for x in self._things]

    def filterIDs(self, ids, incl_none=False):
        '''Filter on the characters ID's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.id in ids ):
                newlist.append(thing)
        return _CharacterGroup(newlist)

    def filterNames(self, names, incl_none=False):
        '''Filter on the characters Name's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.name in names ):
                newlist.append(thing)
        return _CharacterGroup(newlist)

    def filterBeings(self, beings, incl_none=False):
        '''Filter on the characters Being's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.being in beings ):
                newlist.append(thing)
        return _CharacterGroup(newlist)

    def filterTypes(self, types, incl_none=False):
        '''Filter on the characters Type's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.type in types ):
                newlist.append(thing)
        return _CharacterGroup(newlist)

    def filterWDs(self, wds, incl_none=False):
        '''Filter on the characters WD's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.wd in wds ):
                newlist.append(thing)
        return _CharacterGroup(newlist)

    def filterMantos(self, mantos, incl_none=False):
        '''Filter on the characters Manto's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.manto in mantos ):
                newlist.append(thing)
        return _CharacterGroup(newlist)

    def filterGenders(self, genders, incl_none=False):
        '''Filter on the characters Gender's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.gender in genders ):
                newlist.append(thing)
        return _CharacterGroup(newlist)

class Character(object):
    '''The base identity of an epic character''' 
    
    def __init__(self, data=None, api=None, index=True):
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
    '''Datagroup used to hold a list of Character Instances'''
    def __init__(self, things=None):
        self._things = things
    
    def getIDs(self):
        '''Returns a list of character instance ID's'''
        return [x.id for x in self._things]
    
    def getContexts(self):
        '''Returns a list of character instance context's'''
        return [x.context for x in self._things]
    
    def getChars(self):
        '''Returns a list of character instance Character's'''
        return _CharacterGroup([x.char for x in self._things])
    
    def getDisgs(self):
        '''Returns a list of character instance Disg's'''
        return [x.disg for x in self._things]
    
    def getNames(self):
        '''Returns a list of character instance Name's'''
        return [x._name for x in self._things]
    
    def getGenders(self):
        '''Returns a list of character instance Gender's'''
        return [x._gender for x in self._things]
    
    def filterIDs(self, ids, incl_none=False):
        '''Filter on the character instances ID's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.id in ids ):
                newlist.append(thing)
        return _CharacterInstanceGroup(newlist)
    
    def filterContexts(self, contexts, incl_none=False):
        '''Filter on the character instances context's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.context in contexts ):
                newlist.append(thing)
        return _CharacterInstanceGroup(newlist)

    def filterChars(self, chars, incl_none=False):
        '''Filter on the character instances character's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.char in chars ):
                newlist.append(thing)
        return _CharacterInstanceGroup(newlist)

    def filterDisgs(self, disgs, incl_none=False):
        '''Filter on the character instances Disguise's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.disg in disgs ):
                newlist.append(thing)
        return _CharacterInstanceGroup(newlist)

    def filterNames(self, names, incl_none=False):
        '''Filter on the character instances Name's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing._names in names ):
                newlist.append(thing)
        return _CharacterInstanceGroup(newlist)

    def filterGenders(self, genders, incl_none=False):
        '''Filter on the character instances Gender's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing._gender in genders ):
                newlist.append(thing)
        return _CharacterInstanceGroup(newlist)

class CharacterInstance(object):
    '''An instance of a character in context'''
    
    def __init__(self, data=None, api=None, index=True):
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
            #data['char'] = self.char
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
    '''Datagroup used to hold a list of Speech Cluster's'''
    def __init__(self, speeches=None):
        self._things = speeches
    
    def getIDs(self):
        '''Returns a list of Speech Cluster ID's'''
        return [x.id for x in self._things]
    
    def getTypes(self):
        '''Returns a list of Speech CLuster type's'''
        return [x.type for x in self._things]
    
    def getWorks(self):
        '''Returns a list of Speech CLuster work's'''
        return _WorkGroup([x.work for x in self._things])

    def filterIDs(self, ids, incl_none=False):
        '''Filter on the Speech Cluster ID's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.id in ids ):
                newlist.append(thing)
        return _SpeechClusterGroup(newlist)

    def filterTypes(self, types, incl_none=False):
        '''Filter on the Speech Cluster Type's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.type in types ):
                newlist.append(thing)
        return _SpeechClusterGroup(newlist)

    def filterWorks(self, works, incl_none=False):
        '''Filter on the Speech Cluster Work's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.work in works ):
                newlist.append(thing)
        return _SpeechClusterGroup(newlist)

class SpeechCluster(object):
    '''A speech cluster'''
    
    def __init__(self, data=None, api=None, index=True):
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
            #data['work'] = self.work
            

class _SpeechGroup(_DataGroup):
    '''Datagroup used to hold a list of Speech's'''
    def __init__(self, speeches=None):
        self._things = speeches
    
    def getIDs(self):
        '''Returns a list of Speech ID's'''
        return [x.id for x in self._things]
    
    def getClusters(self):
        '''Returns a list of Speech Cluster's'''
        return _SpeechClusterGroup([x.cluster for x in self._things])
    
    def getSeqs(self):
        '''Returns a list of Speech Seq's'''
        return [x.seq for x in self._things]
    
    def get_L_FIs(self):
        '''Returns a list of Speech First Line's'''
        return [x.l_fi for x in self._things]
    
    def get_L_LAs(self):
        '''Returns a list of Speech Last Line's'''
        return [x.l_la for x in self._things]
    
    def getSpkrs(self, flatten=True):
        '''Returns a list of Speech Speaker's'''
        print("Here")
        if flatten:
            newlist = []
            for elem in [x.spkr for x in self._things]:
                newlist.append(elem)
            return _CharacterInstanceGroup(newlist)
        else:
            return _CharacterInstanceGroup([x.spkr for x in self._things])
    
    def getAddrs(self, flatten=True):
        '''Returns a list of Speech Addressee's'''
        if flatten:
            newlist = []
            for elem in [x.addr for x in self._things]:
                newlist.append(elem)
            return _CharacterInstanceGroup(newlist)
        else:
            return _CharacterInstanceGroup([x.addr for x in self._things])
    
    def getParts(self):
        '''Returns a list of Speech Part's'''
        return [x.part for x in self._things]

    def filterIDs(self, ids, incl_none=False):
        '''Filter on the Speech ID's'''
        newlist = []
        for thing in self._things:
            if(thing.id in ids ):
                newlist.append(thing)
        return _SpeechGroup(newlist)

    def filterClusters(self, clusters, incl_none=False):
        '''Filter on the Speech Cluster's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.cluster in clusters ):
                newlist.append(thing)
        return _SpeechGroup(newlist)

    def filterSeqs(self, seqs, incl_none=False):
        '''Filter on the Speech Seq's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.seq in seqs ):
                newlist.append(thing)
        return _SpeechGroup(newlist)

    def filterL_FIs(self, l_fis, incl_none=False):
        '''Filter on the Speech First Line's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.l_fi in l_fis ):
                newlist.append(thing)
        return _SpeechGroup(newlist)

    def filterL_LAs(self, l_las, incl_none=False):
        '''Filter on the Speech Last Line's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.l_la in l_las ):
                newlist.append(thing)
        return _SpeechGroup(newlist)

    def filterSpkrInstances(self, spkrs, incl_none=False):
        '''Filter on the Speech Character Instance's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and any(c in spkrs for c in thing.spkr) ):
                newlist.append(thing)
        return _SpeechGroup(newlist)

    def filterSpkrs(self, spkrs, incl_none=False):
        '''Filter on the Speech Character's'''
        newlist = []
        for thing in self._things:
            #print(*(c.id for c in thing.spkr))
            if( (thing is not None or (thing is None and incl_none)) and any(c.char in spkrs for c in thing.spkr) ):
                newlist.append(thing)
        return _SpeechGroup(newlist)

    def filterAddrInstances(self, addrs, incl_none=False):
        '''Filter on the Speech Character Instances's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and any(c in addrs for c in thing.addr) ):
                newlist.append(thing)
        return _SpeechGroup(newlist)

    def filterAddrs(self, addrs, incl_none=False):
        '''Filter on the Speech Character's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and any(c.char in addrs for c in thing.addr) ):
                newlist.append(thing)
        return _SpeechGroup(newlist)

    def filterParts(self, parts, incl_none=False):
        '''Filter on the Speech Part's'''
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.part in parts ):
                newlist.append(thing)
        return _SpeechGroup(newlist)

class Speech(object):
    '''A single speech'''

    def __init__(self, data=None, api=None, index=True):
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
            #data['cluster'] = self.cluster
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
            #data['spkr'] = self.spkr
        if 'addr' in data:
            if self.index:
                self.addr = [self.api.indexedCharacterInstance(c)
                                    for c in data['addr']]
            else:
                self.addr = [CharacterInstance(c, api=self.api) 
                                    for c in data['addr']]
            #data['addr'] = self.addr
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
        characters = _CharacterGroup([self.indexedCharacter(c) for c in results])
        
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
            #print("Recycling character with ID " + str(data['id']))
            c = self._character_index[data['id']]
        else:
            #print("Adding character with ID " + str(data['id']))
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