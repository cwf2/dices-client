import requests
from MyCapytain.resolvers.cts.api import HttpCtsResolver
from MyCapytain.retrievers.cts5 import HttpCtsRetriever
import logging
import csv
import re

class FilterParams(object):

    CHARACTER_GENDER_FEMALE="female"
    CHARACTER_GENDER_MALE="male"
    CHARACTER_GENDER_NON_BINARY="non-binary"

    CHARACTER_NUMBER_INDIVIDUAL='individual'
    CHARACTER_NUMBER_COLLECTIVE='collective'
    CHARACTER_NUMBER_OTHER='other'

    CHARACTER_BEING_MORTAL='mortal'
    CHARACTER_BEING_DIVINE='divine'
    CHARACTER_BEING_CREATURE='creature'
    CHARACTER_BEING_OTHER='other'

    SPEECH_TYPE_SOLILOQUY='S'
    SPEECH_TYPE_MONOLOGUE='M'
    SPEECH_TYPE_DIALOGUE='D'
    SPEECH_TYPE_GENERAL='G'


class _DataGroup(object):
    '''Parent class for all DataGroups used to hold objects from the API'''

    PREDEF_HEADERS = []
    def __init__(self, things=None, api=None):
        self._things=things
        if api is None:
            print("Could not create a datagroup with no API, exiting")
            quit()
        self.api=api
    

    def __iter__(self):
        for x in self._things:
            yield x
    

    def __getitem__(self, key):
        return self._things[key]
    

    def __len__(self):
        return len(self._things)


    def __iadd__(self, other):
        if(isinstance(other, self.__class__)):
            self.extend(other, False)
        else:
            self.api.logWarning("Cannot add two datagroups of different classes", self.api.LOG_LOWDETAIL)
    

    def __add__(self, other):
        if(isinstance(other, self.__class__)):
            thing = type(self)([x for x in self._things], self.api)
            thing.extend(other)
            return thing
        else:
            self.api.logWarning("Cannot add two datagroups of different classes", self.api.LOG_LOWDETAIL)
    

    def __isub__(self, other):
        if(isinstance(other, self.__class__)):
            self._things = [thing for thing in self._things if thing not in other._things] 
        else:
            self.api.logWarning("Cannot subtract two datagroups of different classes", self.api.LOG_LOWDETAIL)
    

    def __sub__(self, other):
        if(isinstance(other, self.__class__)):
            return type(self)([thing for thing in self._things if thing not in other._things], self.api)
        else:
            self.api.logWarning("Cannot subtract two datagroups of different classes", self.api.LOG_LOWDETAIL)
    
    
    def sorted(self, reverse=False, key=None):
        '''Return a copy with items in increasing order'''
        return type(self)(sorted(self._things, reverse=reverse, key=key), self.api)
        
    
    def sort(self, reverse=False, key=None):
        '''Rearrange items in increasing order'''
        self._things.sort(reverse=reverse, key=key)
    
    
    @property
    def list(self):
        return [x for x in self._things]


    def extend(self, datagroup, duplicates=False):
        '''Combines two data groups of the same type'''

        self.api.logThis("Attempting to extend a " + self.__class__.__name__[1:], self.api.LOG_MEDDETAIL)  
        if(isinstance(datagroup, self.__class__)):
            self._things.extend(datagroup._things)
            if(not duplicates):
                self._things = list(set(self._things))
        else:
            self.api.logWarning("Could not extend the given datagroup because of conflicting classes, skipping", self.api.LOG_LOWDETAIL)


    def unionize(datagroup1, datagroup2, api, duplicates=True):
        if(datagroup1.__class__ == datagroup2.__class__):
            return type(datagroup1)(datagroup1.list, api).extend(datagroup2, duplicates)


    def intersect(self, datagroup, newDataGroup=False):
        self.api.logThis("Attempting to intersect a " + self.__class__.__name__[1:], self.api.LOG_MEDDETAIL)
        if(isinstance(datagroup, self.__class__)):
            return type(self)([thing for thing in self._things if thing in datagroup], self.api)
        else:
            self.api.logWarning("Could not intersect the given datagroup because of conflicting classes, skipping", self.api.LOG_LOWDETAIL)
            return type(self)([], self.api)


    def filterAttribute(self, attribute, value):
        '''Filters all objects in this DataGroup using the specified attribute for a given value'''

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " for attributes", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if attribute in thing._attributes and thing._attributes[attribute] == value:
                newlist.append(thing)
        #return self.__init__(newlist)
        if len(newlist) == 0:
            self.api.logWarning("Filtering on attribute [" + str(attribute) + "] searching for the value [" + str(value) + "] yielded no results", self.api.LOG_LOWDETAIL)
        return type(self)(newlist, self.api)
    

    def filterList(self, attribute, filterList):
        '''Filters all objects in this DataGroup using the specified attribute and checks if the value exists in the given list'''

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " for members of a list", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if(attribute in thing._attributes and thing._attributes[attribute] in filterList and thing._attributes[attribute] is not None):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering on attribute [" + str(attribute) + "] yielded no results", self.api.LOG_LOWDETAIL)
        return type(self)(newlist, self.api)
    
    """
    def deepFilterAttributes(self, attributes, value):
        '''Filters all objects in this DataGroup by filtering the attributes given from a list of attributes (If given ["cluster", "work"] it will check if object->attributes->cluster->work equals the given value)'''

        self.api.logThis("Deep filtering " + self.__class__.__name__[1:], self.api.LOG_MEDDETAIL)
        #print("Deep filtering")
        newlist = []
        for thing in self._things:
            filterList = thing._attributes
            success = True
            for attr in attributes:
                if(attr not in filterList):
                    self.api.logWarning("the attribute [" + str(attr) + "] could not be found, skipping this element of the list", self.api.LOG_HIGHDETAIL)
                    success = False
                    #print("Failed")    
                    break
                filterList=filterList[attr]
            if(success and filterList == value):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Deep filtering for the value [" + str(value) + "] yielded no results", self.api.LOG_LOWDETAIL)
        return type(self)(newlist, self.api)"""
    
    
    def advancedFilter(self, filterFunc, **kwargs):

        self.api.logThis("Advanced filtering " + self.__class__.__name__[1:], self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if filterFunc(thing, **kwargs):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Advanced filtering yielded no results", self.api.LOG_LOWDETAIL)
        return type(self)(newlist, self.api)
    
    @property
    def __headers__(self):
        h = self.PREDEF_HEADERS
        for thing in self:
            for val in thing._attributes.keys():
                if val not in h:
                    h.append(val)
        h.append("API Hash")
        return h

    def __serialize__(self, headers):
        rows = []
        self.api.logThis("Serializing a " + self.__class__.__name__[1:] + " with " + str(len(headers)) + " headers", self.api.LOG_MEDDETAIL)
        for i, thing in enumerate(self):
            rows.append([])
            for key in headers:
                if key == "API Hash":
                    continue
                if key in thing._attributes and (thing._attributes[key] is None or not str(thing._attributes[key]).isspace()):
                    rows[i].append(thing._attributes[key])
                else:
                    rows[i].append("N/A")
            rows[i].append(self.api.version)
        return rows

    def ExportToCSV(self, filePath):
        with open(filePath, 'w', newline='') as f:
            writer = csv.writer(f)
            headers = self.__headers__
            writer.writerow(headers)
            writer.writerows(self.__serialize__(headers))
            self.api.logThis("A " + self.__class__.__name__[1:] + " has been exported to a CSV file at the path " + filePath, self.api.LOG_LOWDETAIL)
        


class _AuthorGroup(_DataGroup):
    '''Datagroup used to hold a list of Authors'''
    PREDEF_HEADERS = ["name"]

    def __init__(self, things=None, api=None):
        self._things = things
        if api is None:
            print("Could not create a datagroup with no API, exiting")
            quit()
        self.api = api
    

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

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along names", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if((thing is not None or (thing is None and incl_none)) and thing.name in names):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " names returned no entries", self.api.LOG_LOWDETAIL)
        return _AuthorGroup(newlist, api=self.api)
    

    def filterIDs(self, ids, incl_none=False):
        '''Filter on the author ID's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along ID's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if((thing is not None or (thing is None and incl_none)) and thing.id in ids):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " ID's returned no entries", self.api.LOG_LOWDETAIL)
        return _AuthorGroup(newlist, self.api)


    def filterWDs(self, wds, incl_none=False):
        '''Filter on the author WD's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along WD's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.wd in wds ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " WD's returned no entries", self.api.LOG_LOWDETAIL)
        return _AuthorGroup(newlist, self.api)


    def filterUrns(self, urns, incl_none=False):
        '''Filter on the author Urns'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Urn's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.urn in urns ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Urn's returned no entries", self.api.LOG_LOWDETAIL)
        return _AuthorGroup(newlist, self.api)


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

    def __repr__(self):
        return f'<Author {self.id}: {self.name}>'

    
    def __lt__(self, other):
        '''True if author names in alpha order'''
        
        if(isinstance(other, self.__class__)):
            return self.name < other.name
        else:
            self.api.logWarning("Cannot compare objects of different classes", 
                                    self.api.LOG_LOWDETAIL)
            raise TypeError


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

    def __init__(self, things=None, api=None):
        self._things = things 
        if api is None:
            print("Could not create a datagroup with no API, exiting")
            quit()
        self.api=api  


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
    

    def getLangs(self):
        '''Returns a list of work Lang's'''
        return [x.lang for x in self._things]


    def getAuthors(self):
        '''Returns a list of work Author's'''
        return _AuthorGroup([x.author for x in self._things])


    def filterIDs(self, ids, incl_none=False):
        '''Filter on the works ID's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along ID's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.id in ids ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " ID's returned no entries", self.api.LOG_LOWDETAIL)
        return _WorkGroup(newlist, self.api)


    def filterTitles(self, titles, incl_none=False):
        '''Filter on the works Title's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Title's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.title in titles ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Title's returned no entries", self.api.LOG_LOWDETAIL)
        return _WorkGroup(newlist, self.api)


    def filterWDs(self, wds, incl_none=False):
        '''Filter on the works WD's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along WD's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.wd in wds ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " WD's returned no entries", self.api.LOG_LOWDETAIL)
        return _WorkGroup(newlist, self.api)


    def filterUrns(self, urns, incl_none=False):
        '''Filter on the works Urn's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Urn's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.urn in urns ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Urn's returned no entries", self.api.LOG_LOWDETAIL)
        return _WorkGroup(newlist, self.api)


    def filterAuthors(self, authors, incl_none=False):
        '''Filter on the works Author's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Author's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.author in authors ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Author's returned no entries", self.api.LOG_LOWDETAIL)
        return _WorkGroup(newlist, self.api)
        
        
    def filterLangs(self, langs, incl_none=False):
        '''Filter on the works Lang's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Lang's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.lang in langs ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Lang's returned no entries", self.api.LOG_LOWDETAIL)
        return _WorkGroup(newlist, self.api)

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
        self.lang = None
        self._attributes = data

        if data:
            self._from_data(data)
    
    def __repr__(self):
        return f'<Work {self.id}: {self.title}>'
    

    def __lt__(self, other):
        '''True if author, title in alpha order'''
        
        if(isinstance(other, self.__class__)):
            return (self.author < other.author) or (
                    (self.author == other.author) and 
                    (self.title < other.title))
        else:
            self.api.logWarning("Cannot compare objects of different classes", 
                                    self.api.LOG_LOWDETAIL)
            raise TypeError


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
        if 'lang' in data:
            self.lang = data['lang']
        if 'author' in data:
            if self.index:
                self.author = self.api.indexedAuthor(data['author'])
            else:
                self.author = Author(data['author'], api=self.api)
            data['author'] = self.author


class _CharacterGroup(_DataGroup):
    '''Datagroup used to hold a list of Characters'''
    
    PREDEF_HEADERS = ["name"]
    def __init__(self, things=None, api=None):
        self._things = things
        if api is None:
            print("Could not create a datagroup with no API, exiting")
            quit()
        self.api=api
    

    def getIDs(self):
        '''Returns a list of character ID's'''
        return [x.id for x in self._things]
    

    def getNames(self):
        '''Returns a list of character Name's'''
        return [x.name for x in self._things]
    

    def getBeings(self):
        '''Returns a list of character Being's'''
        return [x.being for x in self._things]
    

    def getNumbers(self):
        '''Returns a list of character Number's'''
        return [x.number for x in self._things]
    

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
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along ID's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.id is not None and thing.id in ids ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " ID's returned no entries", self.api.LOG_LOWDETAIL)
        return _CharacterGroup(newlist, self.api)


    def filterNames(self, names, incl_none=False):
        '''Filter on the characters Name's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Name's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.name is not None and thing.name in names ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Name's returned no entries", self.api.LOG_LOWDETAIL)
        return _CharacterGroup(newlist, self.api)


    def filterBeings(self, beings, incl_none=False):
        '''Filter on the characters Being's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Being's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.being is not None and thing.being in beings ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Being's returned no entries", self.api.LOG_LOWDETAIL)
        return _CharacterGroup(newlist, self.api)


    def filterNumbers(self, numbers, incl_none=False):
        '''Filter on the characters Number's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Number's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.number is not None and thing.number in numbers ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Number's returned no entries", self.api.LOG_LOWDETAIL)
        return _CharacterGroup(newlist, self.api)


    def filterWDs(self, wds, incl_none=False):
        '''Filter on the characters WD's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along WD's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.wd is not None and thing.wd in wds ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " WD's returned no entries", self.api.LOG_LOWDETAIL)
        return _CharacterGroup(newlist, self.api)


    def filterMantos(self, mantos, incl_none=False):
        '''Filter on the characters Manto's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Manto's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.manto is not None and thing.manto in mantos ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Manto's returned no entries", self.api.LOG_LOWDETAIL)
        return _CharacterGroup(newlist, self.api)


    def filterGenders(self, genders, incl_none=False):
        '''Filter on the characters Gender's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Gender's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.gender is not None and thing.gender in genders ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Gender's returned no entries", self.api.LOG_LOWDETAIL)
        return _CharacterGroup(newlist, self.api)


class Character(object):
    '''The base identity of an epic character''' 
    
    def __init__(self, data=None, api=None, index=True):
        self.api = api
        self.index = (api is not None and index is not None)        
        self.id = None
        self.name = None
        self.being = None
        self.number = None
        self.gender = None
        self.wd = None
        self.manto = None
        self._attributes = data
        
        if data:
            self._from_data(data)


    def __repr__(self):
        return f'<Character {self.id}: {self.name}>'

    
    def __lt__(self, other):
        '''True if names in alpha order'''
        
        if(isinstance(other, self.__class__)):
            return (self.name < other.name)
        else:
            self.api.logWarning("Cannot compare objects of different classes", 
                                    self.api.LOG_LOWDETAIL)
            raise TypeError
    

    def _from_data(self, data):
        '''populate attributes from data'''
        
        if 'id' in data:
            self.id = data['id']
        if 'name' in data:
            self.name = data['name']
        if 'being' in data:
            self.being = data['being']
        if 'number' in data:
            self.number = data['number']
        if 'gender' in data:
            self.gender = data['gender']
        if 'wd' in data:
            self.wd = data['wd']
        if 'manto' in data:
            self.manto = data['manto']


class _CharacterInstanceGroup(_DataGroup):
    '''Datagroup used to hold a list of Character Instances'''

    PREDEF_HEADERS = ["name"]
    def __init__(self, things=None, api=None):
        self._things = things
        if api is None:
            print("Could not create a datagroup with no API, exiting")
            quit()
        self.api=api
    

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
        

    def getAnons(self):
        '''Returns a list of character instance Anon's'''
        return [x.anon for x in self._things]
    

    def getNames(self):
        '''Returns a list of character instance Name's'''
        return [x.name for x in self._things]


    def getBeings(self):
        '''Returns a list of character instance Being's'''
        return [x.being for x in self._things]


    def getNumbers(self):
        '''Returns a list of character instance Name's'''
        return [x.number for x in self._things]
    

    def getGenders(self):
        '''Returns a list of character instance Gender's'''
        return [x.gender for x in self._things]
    

    def filterIDs(self, ids, incl_none=False):
        '''Filter on the character instances ID's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along ID's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.id is not None and thing.id in ids ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " ID's returned no entries", self.api.LOG_LOWDETAIL)
        return _CharacterInstanceGroup(newlist, self.api)
    

    def filterContexts(self, contexts, incl_none=False):
        '''Filter on the character instances context's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Context's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.context is not None and thing.context in contexts ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Context's returned no entries", self.api.LOG_LOWDETAIL)
        return _CharacterInstanceGroup(newlist ,self.api)


    def filterChars(self, chars, incl_none=False):
        '''Filter on the character instances character's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Char's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.char is not None and thing.char in chars ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Char's returned no entries", self.api.LOG_LOWDETAIL)
        return _CharacterInstanceGroup(newlist, self.api)


    def filterDisgs(self, disgs, incl_none=False):
        '''Filter on the character instances Disguise's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Disg's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.disg is not None and thing.disg in disgs ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Disg's returned no entries", self.api.LOG_LOWDETAIL)
        return _CharacterInstanceGroup(newlist, self.api)


    def filterNames(self, names, incl_none=False):
        '''Filter on the character instances Name's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Name's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.name is not None and thing.name in names ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Name's returned no entries", self.api.LOG_LOWDETAIL)
        return _CharacterInstanceGroup(newlist, self.api)


    def filterBeings(self, beings, incl_none=False):
        '''Filter on the character instances Being's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Being's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.being is not None and thing.being in beings ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Being's returned no entries", self.api.LOG_LOWDETAIL)
        return _CharacterInstanceGroup(newlist, self.api)


    def filterNumbers(self, numbers, incl_none=False):
        '''Filter on the character instances Number's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Number's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.number is not None and thing.number in numbers):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Number's returned no entries", self.api.LOG_LOWDETAIL)
        return _CharacterInstanceGroup(newlist, self.api)


    def filterGenders(self, genders, incl_none=False):
        '''Filter on the character instances Gender's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Gender's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.gender is not None and thing.gender in genders ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Gender's returned no entries", self.api.LOG_LOWDETAIL)
        return _CharacterInstanceGroup(newlist, self.api)


class CharacterInstance(object):
    '''An instance of a character in context'''

    def __init__(self, data=None, api=None, index=True):
        self.api = api
        self.index = (api is not None and index is not None)        
        self.id = None
        self.context = None
        self.char = None
        self.disg = None
        self.number = None
        self.being = None
        self.anon = None
        self._name = None
        self._being = None
        self._number = None
        self._gender = None
        self._attributes = data

        if data:
            self._from_data(data)


    def __lt__(self, other):
        '''True if names, char names in alpha order'''
        
        if(isinstance(other, self.__class__)):
            return (self.name < other.name) or (
                self.name == other.name and (self.char < other.char))
        else:
            self.api.logWarning("Cannot compare objects of different classes", 
                                    self.api.LOG_LOWDETAIL)
            raise TypeError

    def __repr__(self):
        name = self.name
        if self.char is not None and self.char.name != self.char.name:
            name = f'{self.name}/{self.char.name}'
        return f'<CharacterInstance {self.id}: {name}>'


    def _from_data(self, data):
        '''populate attributes from data'''
        
        if 'id' in data:
            self.id = data['id']
        if 'context' in data:
            self.context = data['context']
        if 'char' in data and data['char'] is not None:
            if self.index:
                self.char = self.api.indexedCharacter(data['char'])
            else:
                self.char = Character(data['char'], api=self.api)
            data['char'] = self.char
        if 'disg' in data:
            # FIXME
            self.disg = data['disg']
        if 'anon' in data:
            self.anon = data['anon']
        if 'name' in data and data['name'] is not None:
            self.name = data['name']
        if 'being' in data and data['being'] is not None:
            self.being = data['being']
        if 'number' in data and data['number'] is not None:
            self.number = data['number']
        if 'gender' in data and data['gender'] is not None:
            self.gender = data['gender']


class _SpeechClusterGroup(_DataGroup):
    '''Datagroup used to hold a list of Speech Cluster's'''

    def __init__(self, things=None, api=None):
        self._things = things
        if api is None:
            print("Could not create a datagroup with no API, exiting")
            quit()
        self.api=api

    
    def getIDs(self):
        '''Returns a list of Speech Cluster ID's'''
        return [x.id for x in self._things]

    
    def filterIDs(self, ids, incl_none=False):
        '''Filter on the Speech Cluster ID's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along ID's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.id in ids ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " ID's returned no entries", self.api.LOG_LOWDETAIL)
        return _SpeechClusterGroup(newlist, self.api)


class SpeechCluster(object):
    '''A speech cluster'''
    
    def __init__(self, data=None, api=None, index=True):
        self.api = api
        self.index = (api is not None and index is not None)        
        self.id = None
        self._attributes = data
        self._first = None
        
        if data:
            self._from_data(data)


    def __lt__(self, other):
        '''True if initial speeches in seq order'''
        
        if(isinstance(other, self.__class__)):
            return self.getFirst().seq < other.getFirst().seq
        else:
            self.api.logWarning("Cannot compare objects of different classes", 
                                    self.api.LOG_LOWDETAIL)
            raise TypeError

    def __repr__(self):
        incipit = self.getFirst()
        loc = f'{incipit.work.title} {incipit.l_fi} ff.'
        return f'<SpeechCluster {self.id}: {loc}>'


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

    @property
    def speeches(self):
        return self.api.getSpeeches(cluster_id=self.id)
    
    def countSpeeches(self):
        return len(self.speeches)
    

    def getFirst(self):
        '''Return first speech of the cluster'''
        
        if self._first is None:
            sgroup = self.api.getSpeeches(cluster_id=self.id)
            if len(sgroup) < 1:
                self.api.logWarning(f'API returned no speeches for cluster '
                                    f'{self.id}',
                                     self.api.LOG_LOWDETAIL)
                raise Exception # FIXME
            else:
                self._first = sorted(sgroup._things, key=lambda s: s.part)[0]
                if self._first.part != 1:
                    self.api.logWarning(f'First speech in cluster {self.id} '
                                        f'has part {self._first.part}',
                                         self.api.LOG_LOWDETAIL)
        
        return self._first


    def countReplies(self):
        speeches = self.api.getSpeeches(cluster_id=self.id)
        replies = 0
        addresseeList = []
        for speech in speeches:
            if any(responder in speech.spkr for responder in addresseeList):
                replies += 1
            addresseeList.extend(speech.spkr)
            addresseeList = list(set(addresseeList))
        return replies
    

    def countInterruptions(self):
        speeches = self.api.getSpeeches(cluster_id=self.id)
        interruptions = 0
        prevAddr = []
        for speech in speeches:
            if not any(responder in speech.spkr for responder in prevAddr):
                interruptions += 1
            prevAddr = speech.addr
        return interruptions


class _SpeechGroup(_DataGroup):
    '''Datagroup used to hold a list of Speech's'''

    def __init__(self, things=None, api=None):
        self._things = things
        if api is None:
            print("Could not create a datagroup with no API, exiting")
            quit()
        self.api=api

    
    def getIDs(self):
        '''Returns a list of Speech ID's'''
        return [x.id for x in self._things]
    

    def getClusters(self):
        '''Returns a list of Speech Cluster's'''
        return _SpeechClusterGroup([x.cluster for x in self._things], api=self.api)
    

    def getSeqs(self):
        '''Returns a list of Speech Seq's'''
        return [x.seq for x in self._things]
    

    def get_L_FIs(self):
        '''Returns a list of Speech First Line's'''
        return [x.l_fi for x in self._things]
    

    def get_L_LAs(self):
        '''Returns a list of Speech Last Line's'''
        return [x.l_la for x in self._things]
    

    def isCluster(self, clusterID):
        clusters = self.getClusters()
        for thing in clusters:
            if(thing.id != clusterID):
                return False
        return True
    

    def getSpkrs(self, flatten=True):
        '''Returns a list of Speech Speaker's'''
        if flatten:
            newlist = []
            for x in self._things:
                for elem in x.spkr:
                    if elem not in newlist:
                        newlist.append(elem)
        else:
            newlist = [x.spkr for x in self._things]
        return _CharacterInstanceGroup(newlist, self.api)

    def getAddrs(self, flatten=True):
        '''Returns a list of Speech Addressee's'''
        if flatten:
            newlist = []
            for x in self._things:
                for elem in x.addr:
                    if elem not in newlist:
                        newlist.append(elem)
        else:
            newlist = [x.addr for x in self._things]
        return _CharacterInstanceGroup(newlist, self.api)

    def getParts(self):
        '''Returns a list of Speech Part's'''
        return [x.part for x in self._things]


    def getTypes(self):
        '''Returns a list of Speech Part's'''
        return [x.type for x in self._things]


    def getWorks(self):
        '''Returns a list of Speech Part's'''
        return [x.work for x in self._things]


    def filterIDs(self, ids, incl_none=False):
        '''Filter on the Speech ID's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along ID's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if(thing.id in ids ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " ID's returned no entries", self.api.LOG_LOWDETAIL)
        return _SpeechGroup(newlist, self.api)


    def filterClusters(self, clusters, incl_none=False):
        '''Filter on the Speech Cluster's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Cluster's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.cluster in clusters ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Cluster's returned no entries", self.api.LOG_LOWDETAIL)
        return _SpeechGroup(newlist, self.api)


    def filterSeqs(self, seqs, incl_none=False):
        '''Filter on the Speech Seq's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Seq's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.seq in seqs ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Seq's returned no entries", self.api.LOG_LOWDETAIL)
        return _SpeechGroup(newlist, self.api)


    def filterL_FIs(self, l_fis, incl_none=False):
        '''Filter on the Speech First Line's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along L_FI's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.l_fi in l_fis ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " L_FI's returned no entries", self.api.LOG_LOWDETAIL)
        return _SpeechGroup(newlist, self.api)


    def filterL_LAs(self, l_las, incl_none=False):
        '''Filter on the Speech Last Line's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along L_LA's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.l_la in l_las ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " L_LA's returned no entries", self.api.LOG_LOWDETAIL)
        return _SpeechGroup(newlist, self.api)


    def filterSpkrInstances(self, spkrs, incl_none=False):
        '''Filter on the Speech Character Instance's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Speaker Instance's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and any(c in spkrs for c in thing.spkr) ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Speaker Instance's returned no entries", self.api.LOG_LOWDETAIL)
        return _SpeechGroup(newlist ,self.api)


    def filterSpkrs(self, spkrs, incl_none=False):
        '''Filter on the Speech Character's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Speaker's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            #print(*(c.id for c in thing.spkr))
            if( (thing is not None or (thing is None and incl_none)) and any(c.char in spkrs for c in thing.spkr) ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Speaker's returned no entries", self.api.LOG_LOWDETAIL)
        return _SpeechGroup(newlist, self.api)


    def filterAddrInstances(self, addrs, incl_none=False):
        '''Filter on the Speech Character Instances's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Addressee Instance's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and any(c in addrs for c in thing.addr) ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Addressee Instance's returned no entries", self.api.LOG_LOWDETAIL)
        return _SpeechGroup(newlist, self.api)


    def filterAddrs(self, addrs, incl_none=False):
        '''Filter on the Speech Character's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Addressee's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and any(c.char in addrs for c in thing.addr) ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Addressee's returned no entries", self.api.LOG_LOWDETAIL)
        return _SpeechGroup(newlist, self.api )


    def filterParts(self, parts, incl_none=False):
        '''Filter on the Speech Part's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Part's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.part in parts ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Part's returned no entries", self.api.LOG_LOWDETAIL)
        return _SpeechGroup(newlist, self.api)


    def filterTypes(self, types, incl_none=False):
        '''Filter on the Speech Type's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Type's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.type in types ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Type's returned no entries", self.api.LOG_LOWDETAIL)
        return _SpeechGroup(newlist, self.api)


    def filterWorks(self, works, incl_none=False):
        '''Filter on the Speech Work's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Work's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.work in works ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Work's returned no entries", self.api.LOG_LOWDETAIL)
        return _SpeechGroup(newlist, self.api)


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
        self.type = None
        self.work = None
        self._attributes = data
        
        if data:
            self._from_data(data)

        
    def _from_data(self, data):
        '''populate attributes from dict'''    
        
        if 'id' in data:
            self.id = data['id']
        if 'cluster' in data:
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
        if 'type' in data:
            self.type = data['type']
        if 'work' in data:
            self.work = self.api.indexedWork(data['work'])


    def __repr__(self):
        return f'<Speech {self.id}: {self.work.title} {self.l_range}>'
       
        
    def __lt__(self, other):
        '''True if in seq order'''
        
        if(isinstance(other, self.__class__)):
            return (self.work < other.work) or (
                (self.work == other.work) and (self.seq < other.seq))
        else:
            self.api.logWarning("Cannot compare objects of different classes", 
                                    self.api.LOG_LOWDETAIL)
            raise TypeError
        
        
    @property
    def author(self):
        '''shortcut to author (via work)'''
        return self.work.author


    @property
    def lang(self):
        '''shortcut to language (via work)'''        
        return self.work.lang
    
    
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


    def isRepliedTo(self):
        SpeechesInCluster = self.api.getSpeeches(cluster_id=self.cluster.id)
        for thing in SpeechesInCluster:
            if(thing.seq > self.seq):
                if(any(responder in thing.spkr for responder in self.addr)):
                    return True
        return False

    
    def isInterrupted(self):
        speech = [speechs for speechs in self.api.getSpeeches(cluster_id=self.cluster.id) if speechs.seq == self.seq + 1]
        return len(speech) > 0 and any(responder in speech[0].spkr for responder in self.addr)
    
    def isInterruption(self):
        speech = [speechs for speechs in self.api.getSpeeches(cluster_id=self.cluster.id) if speechs.seq == self.seq - 1]
        return len(speech) > 0 and any(talker in speech[0].addr for talker in self.spkr)


class DicesAPI(object):
    '''a connection to the DICES API'''
    
    DEFAULT_API = 'https://fierce-ravine-99183.herokuapp.com/api'
    DEFAULT_CTS = 'https://scaife-cts.perseus.org/api/cts'

    LOG_HIGHDETAIL=3
    LOG_MEDDETAIL=2
    LOG_LOWDETAIL=1
    LOG_NODETAIL=0


    def __init__(self, dices_api=DEFAULT_API, cts_api=DEFAULT_CTS, logfile=None, 
                    logdetail=LOG_MEDDETAIL, progress_class=None):
        self.API = dices_api
        self.CTS_API = cts_api
        self.log = None
        self.logdetail=logdetail
        if(logfile is not None):
            self.createLog(logfile)
        self.resolver = HttpCtsResolver(HttpCtsRetriever(self.CTS_API))
        self._ProgressClass = progress_class
        self._work_index = {}
        self._author_index = {}
        self._character_index = {}
        self._characterinstance_index = {}
        self._speech_index = {}
        self._speechcluster_index = {}
        self.version = "DEBUG VERSION 1.0"
        self.logThis("Database Initialized", self.LOG_NODETAIL)


    def getPagedJSON(self, endpoint, params=None, progress=False):
        '''Collect paged results from the API'''
        self.logThis("Retrieving data from the database", self.LOG_LOWDETAIL)
        
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

        if pbar is not None:
            pbar.update(len(results))

        # check that we got everything
        if len(results) != count:
            self.logWarning(f'Expected {count} results, got {len(results)}!', self.LOG_MEDDETAIL)
        self.logThis("Successfully fetched data from the database", self.LOG_LOWDETAIL)
        return results


    def createLog(self, logfile, clearLog=False):
        if not self.log or clearLog:
            self.clearLog()
            self.log = logging.getLogger("dicesLog")
            self.log.setLevel(logging.DEBUG)
            formatter = logging.Formatter(fmt='%(asctime)s - [%(levelname)s] %(message)s')
            fh = logging.FileHandler(logfile)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            sh = logging.StreamHandler()
            sh.setLevel(logging.ERROR)
            sh.setFormatter(formatter)
            self.log.addHandler(fh)
            self.log.addHandler(sh)     
            self.logThis("New log created with " + self._detailtostring() + " Detail", self.LOG_NODETAIL)
        else:
            self.logWarning("A new log cannot be initialized when a log already exists", self.LOG_MEDDETAIL)
        
    
    def _detailtostring(self):
        if self.logdetail == self.LOG_NODETAIL:
            return "No"
        elif self.logdetail == self.LOG_LOWDETAIL:
            return "Low"
        elif self.logdetail == self.LOG_MEDDETAIL:
            return "Medium"
        else:
            return "High"

    
    def clearLog(self):
        if self.log:
            self.logWarning("Clearing log *LOG MAY END HERE*", self.LOG_NODETAIL)
            self.log = None


    def logThis(self, message, priority):
        if self.log and priority <= self.logdetail:
            self.log.debug(message)

        
    def logWarning(self, message, priority):
        if self.log and priority <= self.logdetail:
            self.log.warning(message)

    
    def logError(self, message, priority):
        if self.log and priority <= self.logdetail:
            self.log.error(message)

    
    def logCritical(self, message, priority):
        if self.log and priority <= self.logdetail:
            self.log.critical(message)

        
    def getSpeeches(self, progress=False, **kwargs):
        '''Retrieve speeches from API'''
        
        self.logThis("Attempting to fetch a SpeechGroup", self.LOG_MEDDETAIL)
        # get the results from the speeches endpoint
        results = self.getPagedJSON('speeches', dict(**kwargs), progress=progress)
        
        # convert to Speech objects
        speeches = _SpeechGroup([self.indexedSpeech(s) for s in results], api=self)

        self.logThis("Successfully retrieved a list of speeches", self.LOG_MEDDETAIL)
        
        return speeches


    def getClusters(self, progress=False, **kwargs):
        '''Retrieve speech clusters from API'''
        self.logThis("Attempting to fetch a ClusterGroup", self.LOG_MEDDETAIL)
                
        # get the results from the clusters endpoint
        results = self.getPagedJSON('clusters', dict(**kwargs), progress=progress)
        
        # convert to Clusters objects
        clusters = _SpeechClusterGroup([self.indexedSpeechCluster(s) for s in results], api=self)
        self.logThis("Successfully retrieved a list of clusters", self.LOG_MEDDETAIL)
        
        return clusters

    
    def getCharacters(self, progress=False, **kwargs):
        '''Retrieve characters from API'''
        self.logThis("Attempting to fetch a CharactersGroup", self.LOG_MEDDETAIL)
        
        # get the results from the characters endpoint
        results = self.getPagedJSON('characters', dict(**kwargs), progress=progress)
        
        # convert to Character objects
        characters = _CharacterGroup([self.indexedCharacter(c) for c in results], api=self)
        self.logThis("Successfully retrieved a list of characters", self.LOG_MEDDETAIL)
        
        return characters


    def getWorks(self, progress=False, **kwargs):
        '''Fetch works from the API'''
        self.logThis("Attempting to fetch a WorksGroup", self.LOG_MEDDETAIL)
        
        results = self.getPagedJSON('works', dict(**kwargs), progress=progress)

        works = _WorkGroup([self.indexedWork(w) for w in results], api=self)
        self.logThis("Successfully retrieved a list of works", self.LOG_MEDDETAIL)
        return works


    def getAuthors(self, progress=False, **kwargs):
        '''Fetch authors from the API'''
        self.logThis("Attempting to fetch a AuthorGroup", self.LOG_MEDDETAIL)

        results = self.getPagedJSON('authors', dict(**kwargs), progress=progress)

        authors = _AuthorGroup([self.indexedAuthor(a) for a in results], api=self)
        self.logThis("Successfully retrieved a list of authors", self.LOG_MEDDETAIL)
        return authors


    def getInstances(self, progress=False, **kwargs):
        '''Fetch character instances from the API'''  
        self.logThis("Attempting to fetch a CharacterInstanceGroup", self.LOG_MEDDETAIL)  
        results = self.getPagedJSON('instances', dict(**kwargs), progress=progress)

        instances = _CharacterInstanceGroup([self.indexedCharacterInstance(i) for i in results], api=self)
        self.logThis("Successfully retrieved a list of character instances", self.LOG_MEDDETAIL)
        return instances
        
    
    def indexedAuthor(self, data):
        '''Create an author in the index'''
        
        if data['id'] in self._author_index:
            a = self._author_index[data['id']]
            self.logThis("Fetching author with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        else:
            a = Author(data, api=self, index=True)
            self._author_index[data['id']] = a
            self.logThis("Creating new author with ID " + str(data['id']), self.LOG_HIGHDETAIL)
 
        return a


    def indexedWork(self, data):
        '''Create a work in the index'''
        
        if data['id'] in self._work_index:
            w = self._work_index[data['id']]
            self.logThis("Fetching work with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        else:
            w = Work(data, api=self, index=True)
            self._work_index[data['id']] = w
            self.logThis("Creating new work with ID " + str(data['id']), self.LOG_HIGHDETAIL)
 
        return w

    
    def indexedSpeech(self, data):
        '''Create a speech in the index'''
        
        if data['id'] in self._speech_index:
            s = self._speech_index[data['id']]
            self.logThis("Fetching speech with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        else:
            s = Speech(data, api=self, index=True)
            self._speech_index[data['id']] = s
            self.logThis("Creating new speech with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        return s

        
    def indexedSpeechCluster(self, data):
        '''Create a speech cluster in the index'''
        
        if data['id'] in self._speechcluster_index:
            s = self._speechcluster_index[data['id']]
            self.logThis("Fetching cluster with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        else:
            s = SpeechCluster(data, api=self, index=True)
            self._speechcluster_index[data['id']] = s
            self.logThis("Creating new cluster with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        
        return s


    def indexedCharacter(self, data):
        '''Create a character in the index'''
        
        if data['id'] in self._character_index:
            #print("Recycling character with ID " + str(data['id']))
            c = self._character_index[data['id']]
            self.logThis("Fetching character with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        else:
            #print("Adding character with ID " + str(data['id']))
            c = Character(data, api=self, index=True)
            self._character_index[data['id']] = c
            self.logThis("Creating new character with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        
        return c


    def indexedCharacterInstance(self, data):
        '''Create a character instance in the index'''
        
        if data['id'] in self._characterinstance_index:
            c = self._characterinstance_index[data['id']]
            self.logThis("Fetching character instance with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        else:
            c = CharacterInstance(data, api=self, index=True)
            self._characterinstance_index[data['id']] = c
            self.logThis("Creating new character instance with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        
        return c