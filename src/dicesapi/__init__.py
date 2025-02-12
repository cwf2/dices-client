import requests
import pandas as pd
import sys
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


class DataGroup(object):
    '''Parent class for all DataGroups used to hold objects from the API'''

    PREDEF_HEADERS = []
    def __init__(self, things=None, api=None):
        """Creates a new DataGroup
        
        Args:
            things (list): Things is a dictionary that is used to store info on the objects in the DataGroup
            api (DicesAPI): The api object attached to the class
        
        Returns:
            A datagroup object
        """
        
        self._things=things
        if api is None:
            print("Could not create a datagroup with no API, exiting")
            quit()
        self.api=api
    

    def __iter__(self):
        for x in self._things:
            yield x
    

    def __getitem__(self, key):
        if isinstance(key, slice):
            return type(self)(self._things[key], api=self.api)

        else:
            return self._things[key]
    

    def __len__(self):
        return len(self._things)


    def __iadd__(self, other):
        '''Add the contents of other to self
        
        Alias for self.extend(other)
        '''
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
        """Returns a copy of self with items in ascending order.

        Args:
            reverse (bool): If True, then items are arranged in decreasing order
            key (lambda): A function that takes one argument and returns a value to be used for sorting purposes
        Returns:
            A list of the items in a sequence, sorted
        """

        return type(self)(sorted(self._things, reverse=reverse, key=key), self.api)
        
    
    def sort(self, reverse=False, key=None):
        """Sorts contents in ascending order

        Args:
            reverse (bool): If True, then items are arranged in decreasing order
            key (lambda): A function that takes one argument and returns a value to be used for sorting purposes
        """
        
        self._things.sort(reverse=reverse, key=key)
    
    
    @property
    def list(self):
        """Returns the contents of the DataGroup as a list."""
        
        return [x for x in self._things]


    def extend(self, datagroup, duplicates=False):
        """Adds contents of another datagroup to the present one

        Args:
            datagroup: Another instance of the same class
            duplicates (bool): If true, remove duplicate entries after combining
        """

        self.api.logThis("Attempting to extend a " + self.__class__.__name__[1:], self.api.LOG_MEDDETAIL)  
        if(isinstance(datagroup, self.__class__)):
            self._things.extend(datagroup._things)
            if(not duplicates):
                self._things = list(set(self._things))
        else:
            self.api.logWarning("Could not extend the given datagroup because of conflicting classes, skipping", self.api.LOG_LOWDETAIL)


    def intersect(self, other):
        """Return a new DataGroup containing items common to self, other

        Args:
            other (DataGroup): The data group to intersect with
        
        Returns: 
            A new DataGroup.
        """
        
        self.api.logThis("Attempting to intersect a " + self.__class__.__name__[1:], self.api.LOG_MEDDETAIL)
        if(isinstance(other, self.__class__)):
            return type(self)([thing for thing in self if thing in other], self.api)
        else:
            self.api.logWarning("Could not intersect the given datagroup because of conflicting classes, skipping", self.api.LOG_LOWDETAIL)
            return type(self)([], self.api)


    def filterAttribute(self, attribute, value):
        """Returns a subset of the DataGroup based on an attribute

        Args:
            attribute (str): Used to specify the attribute that will be used for filtering.
            value: Used to specify the value to filter for.

        Returns:
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " for attributes", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if attribute in thing._attributes and thing._attributes[attribute] == value:
                newlist.append(thing)
        #return self.__init__(newlist)
        if len(newlist) == 0:
            self.api.logWarning("Filtering on attribute [" + str(attribute) + "] searching for the value [" + str(value) + "] yielded no results", self.api.LOG_LOWDETAIL)
        return type(self)(newlist, self.api)
    

    def filterList(self, attribute, values):
        """Returns objects in this DataGroup for which an attribute matches a list of possible values

        Args:
            attribute (str): The attribute that is used for filtering
            values (list): List of allowable values
        
        Returns:
            A new DataGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " for members of a list", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if(attribute in thing._attributes and thing._attributes[attribute] in filterList and thing._attributes[attribute] is not None):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering on attribute [" + str(attribute) + "] yielded no results", self.api.LOG_LOWDETAIL)
        return type(self)(newlist, self.api)
    

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
        return type(self)(newlist, self.api)
    
    
    def advancedFilter(self, filterFunc, **kwargs):
        """Returns objects in this DataGroup based on results of a user-defined function.
        
        Args:
            filterFunc (lambda): Function that takes elements of the DataGroup as its first argument
            **kwargs: Additional keyword arguments to filterFunc.
        
        Returns:
            A new DataGroup.
        """
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
        


class AuthorGroup(DataGroup):
    '''Datagroup used to hold a list of Authors'''
    PREDEF_HEADERS = ["name"]

    def __init__(self, things=None, api=None):
        self._things = things
        if api is None:
            print("Could not create a datagroup with no API, exiting")
            quit()
        self.api = api
    

    def getIDs(self):
        '''Returns a list of author IDs'''
        return [x.id for x in self._things]
    

    def getNames(self):
        '''Return a list of the authors names'''
        return [x.name for x in self._things]


    def getWDs(self):
        '''Returns a list of the author WDs'''
        return [x.wd for x in self._things]
    

    def getUrns(self):
        '''Returns a list of author URNs'''
        return [x.urn for x in self._things]
    

    def filterNames(self, names, incl_none=False):
        '''Filter the authors by name

        Args:
            names (list): List of names to match
            incl_none (bool): Include None values in the list of names
        
        Returns:
            A new AuthorGroup
        '''
        
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along names", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if((thing is not None or (thing is None and incl_none)) and thing.name in names):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " names returned no entries", self.api.LOG_LOWDETAIL)
        return AuthorGroup(newlist, api=self.api)
    

    def filterIDs(self, ids, incl_none=False):
        """Filter the authors by ID

        Args:
            ids (list): Author IDs to match
            incl_none (bool): Include None values in the list of IDs
        
        Returns:
            A new AuthorGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along IDs", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if((thing is not None or (thing is None and incl_none)) and thing.id in ids):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " IDs returned no entries", self.api.LOG_LOWDETAIL)
        return AuthorGroup(newlist, self.api)


    def filterWDs(self, wds, incl_none=False):
        """Filter the authors by WikiData ID
        
        Args:
            wds (list): List of Wikidata IDs to match
            incl_none (bool): Include None values in the list
        
        Returns:
            A new AuthorGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along WD's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.wd in wds ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " WD's returned no entries", self.api.LOG_LOWDETAIL)
        return AuthorGroup(newlist, self.api)


    def filterUrns(self, urns, incl_none=False):
        """Filter the authors by URN

        Args:
            urns (list): List URNs to match
            incl_none (bool): Include None values in the list
        
        Returns:
            A new AuthorGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Urn's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.urn in urns ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Urn's returned no entries", self.api.LOG_LOWDETAIL)
        return AuthorGroup(newlist, self.api)


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


class WorkGroup(DataGroup):
    '''Datagroup used to hold a list of works'''

    def __init__(self, things=None, api=None):
        self._things = things 
        if api is None:
            print("Could not create a datagroup with no API, exiting")
            quit()
        self.api=api  


    def getIDs(self):
        '''Returns a list of work IDs'''
        return [x.id for x in self._things]
    

    def getTitles(self):
        '''Returns a list of work titles'''
        return [x.title for x in self._things]
    

    def getWDs(self):
        '''Returns a list of work WDs'''
        return [x.wd for x in self._things]


    def getURNs(self):
        '''Returns a list of work URNs'''
        return [x.urn for x in self._things]
    

    def getLangs(self):
        '''Returns a list of work languages'''
        return [x.lang for x in self._things]


    def getAuthors(self, flatten=False):
        '''Returns a list of Authors'''
        auths = [x.author for x in self._things]
        if flatten:
            auths = AuthorGroup(list(set(auths)), api=self.api)
        return auths


    def filterIDs(self, ids, incl_none=False):
        """Filter the works by ID

        Args:
            ids (list): List of work IDs to match
            incl_none (bool): Include None values in the list
        
        Returns:
            A new WorkGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along ID's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.id in ids ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " ID's returned no entries", self.api.LOG_LOWDETAIL)
        return WorkGroup(newlist, self.api)


    def filterTitles(self, titles, incl_none=False):
        """Filter the works by title

        Args:
            titles (list): List of titles to match
            incl_none (bool): Include None values in the list.
        
        Returns:
            A new WorkGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Title's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.title in titles ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Title's returned no entries", self.api.LOG_LOWDETAIL)
        return WorkGroup(newlist, self.api)


    def filterWDs(self, wds, incl_none=False):
        """Filter the works by WikiData ID

        Args:
            wds (list): List of WikiData IDs to match
            incl_none (bool): Include None values in the list of things

        Returns:
            A new WorkGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along WD's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.wd in wds ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " WD's returned no entries", self.api.LOG_LOWDETAIL)
        return WorkGroup(newlist, self.api)


    def filterUrns(self, urns, incl_none=False):
        """Filter the works by URN

        Args:
            urns (list): List of URNs to match
            incl_none (bool): Include None values in the list of works.
        
        Returns:
            A new WorkGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Urn's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.urn in urns ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Urn's returned no entries", self.api.LOG_LOWDETAIL)
        return WorkGroup(newlist, self.api)


    def filterAuthors(self, authors, incl_none=False):
        """Filter the works by author
        
        Args:
            authors (list): List of Author objects to match
            incl_none (bool): Include None values in the list
        
        Returns:
            A new WorkGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Author's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.author in authors ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Author's returned no entries", self.api.LOG_LOWDETAIL)
        return WorkGroup(newlist, self.api)
        
        
    def filterLangs(self, langs, incl_none=False):
        """Filter the works by language

        Args:
            langs (list): List of languages to match
            incl_none (bool): Include None values in the list

        Returns:
            A new WorkGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Lang's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.lang in langs ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Lang's returned no entries", self.api.LOG_LOWDETAIL)
        return WorkGroup(newlist, self.api)


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


class CharacterGroup(DataGroup):
    '''Datagroup used to hold a list of Characters'''
    
    PREDEF_HEADERS = ["name"]
    def __init__(self, things=None, api=None):
        self._things = things
        if api is None:
            print("Could not create a datagroup with no API, exiting")
            quit()
        self.api=api
    

    def getIDs(self):
        '''Returns a list of character IDs'''
        return [x.id for x in self._things]
    

    def getNames(self):
        '''Returns a list of character names'''
        return [x.name for x in self._things]
    

    def getBeings(self):
        '''Returns a list of character beings'''
        return [x.being for x in self._things]
    

    def getNumbers(self):
        '''Returns a list of character numbers'''
        return [x.number for x in self._things]
    

    def getWDs(self):
        '''Returns a list of character WikiData IDs'''
        return [x.wd for x in self._things]


    def getMantos(self):
        '''Returns a list of character MANTO IDs'''
        return [x.manto for x in self._things]
    

    def getGenders(self):
        '''Returns a list of character genders'''
        return [x.gender for x in self._things]


    def filterIDs(self, ids, incl_none=False):
        """Filter characters by ID

        Args:
            ids (list): list of IDs to match
            incl_none (bool): Include None values in the list.
        
        Returns:
            A new CharacterGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along ID's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.id is not None and thing.id in ids ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " ID's returned no entries", self.api.LOG_LOWDETAIL)
        return CharacterGroup(newlist, self.api)


    def filterNames(self, names, incl_none=False):
        """Filter characters by name

        Args:
            names (list): List of names to match
            incl_none (bool): Include None values in the list.
        
        Returns:
            A new CharacterGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Name's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.name is not None and thing.name in names ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Name's returned no entries", self.api.LOG_LOWDETAIL)
        return CharacterGroup(newlist, self.api)


    def filterBeings(self, beings, incl_none=False):
        """Filter characters by `being` attribute
        
        Args:
            beings (list): list of allowed `being` values
            incl_none (bool): Include None values in the list
        
        Returns:
            A new CharacterGroup
        """
        
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Being's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.being is not None and thing.being in beings ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Being's returned no entries", self.api.LOG_LOWDETAIL)
        return CharacterGroup(newlist, self.api)


    def filterNumbers(self, numbers, incl_none=False):
        """Filter characters by `number` attribute
        
        Args:
            numbers (list): List of allowed `number` values
            incl_none (bool): Include None values in the list
        
        Returns:
            A new CharacterGroup
        """
        
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Number's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.number is not None and thing.number in numbers ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Number's returned no entries", self.api.LOG_LOWDETAIL)
        return CharacterGroup(newlist, self.api)


    def filterWDs(self, wds, incl_none=False):
        """Filter characters by `wd` attribute (WikiData ID)
        
        Args:
            wds (list): List of allowed WikiData IDs
            incl_none (bool): Include None values in the list
        
        Returns:
            A new CharacterGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along WD's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.wd is not None and thing.wd in wds ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " WD's returned no entries", self.api.LOG_LOWDETAIL)
        return CharacterGroup(newlist, self.api)


    def filterMantos(self, mantos, incl_none=False):
        """Filter characters by `manto` attribute (MANTO ID)
        
        Args:
            mantos (list): List of allowed MANTO IDs
            incl_none (bool): Include None values in the list
        
        Returns:
            A new CharacterGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Manto's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.manto is not None and thing.manto in mantos ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Manto's returned no entries", self.api.LOG_LOWDETAIL)
        return CharacterGroup(newlist, self.api)


    def filterGenders(self, genders, incl_none=False):
        """Filter characters by `gender` attribute
        
        Args:
            genders (list): List of allowed `gender` values
            incl_none (bool): Include None values in the list
        
        Returns:
            A new CharacterGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Gender's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.gender is not None and thing.gender in genders ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Gender's returned no entries", self.api.LOG_LOWDETAIL)
        return CharacterGroup(newlist, self.api)


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
        self.tt = None
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
        if 'tt' in data:
            self.tt = data['tt']


class CharacterInstanceGroup(DataGroup):
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
    

    def getChars(self, flatten=False):
        '''Returns a list of character instance Character's'''
        chars = [x.char for x in self._things]
        if flatten:
            chars = CharacterGroup(chars, api=self.api)
        return chars
    

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
        """Filter character instances by `id` attribute

        Args:
            ids (list): List of allowed `id` values
            incl_none (bool): Include None values in the results
        
        Returns:
            A new CharacterInstanceGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along ID's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.id is not None and thing.id in ids ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " ID's returned no entries", self.api.LOG_LOWDETAIL)
        return CharacterInstanceGroup(newlist, self.api)
    

    def filterContexts(self, contexts, incl_none=False):
        """Filter character instances by `context` attribute

        Args:
            contexts (list): List of allowed `context` values
            incl_none (bool): Include None values in the results
        
        Returns:
            A new CharacterInstanceGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Context's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.context is not None and thing.context in contexts ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Context's returned no entries", self.api.LOG_LOWDETAIL)
        return CharacterInstanceGroup(newlist ,self.api)


    def filterChars(self, chars, incl_none=False):
        """Filter character instances by underlying Character

        Args:
            chars (list): List of allowed Character objects
            incl_none (bool): Include None values in the results
        
        Returns:
            A new CharacterInstanceGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Char's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.char is not None and thing.char in chars ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Char's returned no entries", self.api.LOG_LOWDETAIL)
        return CharacterInstanceGroup(newlist, self.api)


    def filterNames(self, names, incl_none=False):
        """Filter character instances by `name` attribute

        Args:
            names (list): List of allowed `name` values
            incl_none (bool): Include None values in the results
        
        Returns:
            A new CharacterInstanceGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Name's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.name is not None and thing.name in names ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Name's returned no entries", self.api.LOG_LOWDETAIL)
        return CharacterInstanceGroup(newlist, self.api)


    def filterBeings(self, beings, incl_none=False):
        """Filter character instances by `being` attribute

        Args:
            beings (list): List of allowed `being` values
            incl_none (bool): Include None values in the results
        
        Returns:
            A new CharacterInstanceGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Being's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.being is not None and thing.being in beings ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Being's returned no entries", self.api.LOG_LOWDETAIL)
        return CharacterInstanceGroup(newlist, self.api)


    def filterNumbers(self, numbers, incl_none=False):
        """Filter character instances by `number` attribute

        Args:
            numbers (list): List of allowed `number` values
            incl_none (bool): Include None values in the results
        
        Returns:
            A new CharacterInstanceGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Number's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.number is not None and thing.number in numbers):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Number's returned no entries", self.api.LOG_LOWDETAIL)
        return CharacterInstanceGroup(newlist, self.api)


    def filterGenders(self, genders, incl_none=False):
        """Filter character instances by `gender` attribute

        Args:
            genders (list): List of allowed `gender` values
            incl_none (bool): Include None values in the results
        
        Returns:
            A new CharacterInstanceGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Gender's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.gender is not None and thing.gender in genders ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Gender's returned no entries", self.api.LOG_LOWDETAIL)
        return CharacterInstanceGroup(newlist, self.api)


class CharacterInstance(object):
    '''An instance of a character in context'''

    def __init__(self, data=None, api=None, index=True):
        self.api = api
        self.index = (api is not None and index is not None)        
        self.id = None
        self.name = None
        self.context = None
        self.char = None
        self.disg = None
        self.number = None
        self.being = None
        self.anon = None
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
        if 'disguise' in data:
            # FIXME
            self.disg = data['disguise']
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

    @property
    def wd(self):
        '''returns WikiData id of underlying Character'''
        if self.char is not None:
            return self.char.wd

    @property
    def manto(self):
        '''returns MANTO id of underlying Character'''
        if self.char is not None:
            return self.char.manto

    @property
    def tt(self):
        '''returns MANTO id of underlying Character'''
        if self.char is not None:
            return self.char.tt


class SpeechClusterGroup(DataGroup):
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
        """Filter speech clusters by ID

        Args:
            ids: List of allowed IDs
            incl_none (bool): Include None values in the results
        
        Returns:
            A new SpeechClusterGroup
        """

        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along ID's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.id in ids ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " ID's returned no entries", self.api.LOG_LOWDETAIL)
        return SpeechClusterGroup(newlist, self.api)


class SpeechCluster(object):
    '''A speech cluster'''
    
    def __init__(self, data=None, api=None, index=True):
        self.api = api
        self.index = (api is not None and index is not None)        
        self.id = None
        self.type = None
        self._attributes = data
        self._first = None
        
        if data:
            self._from_data(data)


    def __lt__(self, other):
        '''True if initial speeches in seq order'''
        
        if(isinstance(other, self.__class__)):
            return self.getFirstSpeech().seq < other.getFirstSpeech().seq
        else:
            self.api.logWarning("Cannot compare objects of different classes", 
                                    self.api.LOG_LOWDETAIL)
            raise TypeError

    def __repr__(self):
        incipit = self.getFirstSpeech()
        loc = f'{incipit.work.title} {incipit.l_fi} ff.'
        return f'<SpeechCluster {self.id}: {loc}>'


    def _from_data(self, data):
        '''populate attributes from data'''
        
        if 'id' in data:
            self.id = data['id']
        if 'type' in data:
            self.type = data['type']
        if 'speeches' in data:
            if isinstance(data['speeches'], list):
                if self.index:
                    self.speeches = []
                    for s in data['speeches']:
                        self.speeches.append(self.api.indexedSpeech(s))
        if 'work' in data:
            if self.index:
                self.work = self.api.indexedWork(data['work'])
            else:
                self.work = Work(data['work'], api=self.api)
            data['work'] = self.work


    def getSpeeches(self):
        return self.api.getSpeeches(cluster_id=self.id)
    
    
    def getFirstSpeech(self):
        """Return the first speech of a cluster"""
        
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
        """Returns the number of replies in a cluster"""

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
        """Returns the number of interruptions in a cluster"""

        speeches = self.api.getSpeeches(cluster_id=self.id)
        interruptions = 0
        prevAddr = []
        for speech in speeches:
            if not any(responder in speech.spkr for responder in prevAddr):
                interruptions += 1
            prevAddr = speech.addr
        return interruptions


class SpeechGroup(DataGroup):
    '''Datagroup used to hold a list of Speeches'''

    def __init__(self, things=None, api=None):
        self._things = things
        if api is None:
            print("Could not create a datagroup with no API, exiting")
            quit()
        self.api=api

    
    def getIDs(self):
        '''Returns a list of Speech IDs'''
        return [x.id for x in self._things]
    

    def getClusters(self, flatten=False):
        '''Returns a list of Speech Clusters'''
        clusters = [x.cluster for x in self._things]
        
        if flatten:
            clusters = SpeechClusterGroup(list(set(clusters)), api=self.api)
        return clusters
    

    def getSeqs(self):
        '''Returns a list of Speech Seqs'''
        return [x.seq for x in self._things]
    

    def getL_fis(self):
        '''Returns a list of Speech First Lines'''
        return [x.l_fi for x in self._things]
    

    def getL_las(self):
        '''Returns a list of Speech Last Lines'''
        return [x.l_la for x in self._things]
    

    def getSpkrs(self, flatten=False):
        '''Returns speakers of member speeches
        
        Args:
            flatten (bool): If False, result will have one list for each
                            member speech, representing the `spkr` attribute of
                            the respective speech. If True, all speakers of all
                            speeches are consolidated, duplicates removed, and
                            result is converted to a CharacterInstanceGroup.
        Returns:
            list or CharacterInstanceGroup
        '''

        spkrs = [x.spkr for x in self._things]
        
        if flatten:
            spkrs = set(inst for spkr_list in spkrs for inst in spkr_list)
            spkrs = CharacterInstanceGroup(list(spkrs), api=self.api)
        
        return spkrs


    def getAddrs(self, flatten=False):
        '''Returns speakers of member speeches
        
        Args:
            flatten (bool): If False, result will have one list for each
                            member speech, representing the `spkr` attribute of
                            the respective speech. If True, all speakers of all
                            speeches are consolidated, duplicates removed, and
                            result is converted to a CharacterInstanceGroup.
        Returns:
            list or CharacterInstanceGroup
        '''

        addrs = [x.addr for x in self._things]
        
        if flatten:
            addrs = set(inst for addr_list in addrs for inst in addr_list)
            addrs = CharacterInstanceGroup(list(addrs), api=self.api)
        
        return addrs


    def getParts(self):
        '''Returns the `part` attrs of member speeches as a list'''
        return [x.part for x in self._things]


    def getTypes(self):
        '''Returns the `type` attrs of member speeches as a list'''
        return [x.type for x in self._things]


    def getWorks(self, flatten=False):
        '''Returns the works of '''
        
        works = [x.work for x in self._things]
        if flatten:
            works = WorkGroup(list(set(works)), api=self.api)
        
        return works


    def filterIDs(self, ids, incl_none=False):
        """
        The filterIDs function is used to filter the list of things that are currently in the Speech class.
        
            self: Used to access the class attributes and methods.
            ids: Used to filter the list of speeches by their ID.
            incl_none=False: Used to include or exclude objects with None as their ID.
        :return: a list of the speeches that have an ID in the ids parameter.
        :doc-author: Trelent
        """
        '''Filter on the Speech ID's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along ID's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if(thing.id in ids ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " ID's returned no entries", self.api.LOG_LOWDETAIL)
        return SpeechGroup(newlist, self.api)


    def filterClusters(self, clusters, incl_none=False):
        """
        The filterClusters function specifically filters the list of things along the clusters that are passed in.
        
            self: Used to reference the class instance.
            clusters: Used to filter the list of things.
            incl_none=False: Used to include None's in the list.
        :return: a list of the things that are in any of the clusters listed as parameters.
        :doc-author: Trelent
        """
        '''Filter on the Speech Cluster's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Cluster's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.cluster in clusters ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Cluster's returned no entries", self.api.LOG_LOWDETAIL)
        return SpeechGroup(newlist, self.api)


    def filterSeqs(self, seqs, incl_none=False):
        """
        The filterSeqs function is used to filter the list of things that are being processed by the
        Speech API.
        
            self: Used to reference the object itself.
            seqs: Used to filter the list of things.
            incl_none=False: Used to include None values in the list of things.
        :return: a list of things that are in seqs.
        :doc-author: Trelent
        """
        '''Filter on the Speech Seq's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Seq's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.seq in seqs ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Seq's returned no entries", self.api.LOG_LOWDETAIL)
        return SpeechGroup(newlist, self.api)


    def filterL_fis(self, l_fis, incl_none=False):
        """
        The filterL_FIs function specifically filters the list of things along the L_FI's.
        
            self: Used to access the class attributes and methods.
            l_fis: Used to filter the list of things along the L_FI's.
            incl_none=False: Used to include None values in the list.
        :return: the filtered list of things that have a l_fi in the l_fis list.
        :doc-author: Trelent
        """
        '''Filter on the Speech First Line's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along L_FI's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.l_fi in l_fis ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " L_FI's returned no entries", self.api.LOG_LOWDETAIL)
        return SpeechGroup(newlist, self.api)


    def filterL_ls(self, l_las, incl_none=False):
        """
        The filterL_LAs function specifically filters the list of things along the L_LA's.
        
            self: Used to access the API.
            l_las: Used to filter the list of things by their L_LA.
            incl_none=False: Used to include None values in the list of L_LAs.
        :return: a list of the things that are included in l_las.
        :doc-author: Trelent
        """
        '''Filter on the Speech Last Line's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along L_LA's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.l_la in l_las ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " L_LA's returned no entries", self.api.LOG_LOWDETAIL)
        return SpeechGroup(newlist, self.api)


    def filterSpkrInstances(self, spkrs, incl_none=False):
        """
        The filterSpkrInstances function specifically filters the list of things in the class by speaker instances.
        
            self: Used to access the API class.
            spkrs: Used to specify the speakers to include in the filtered list.
            incl_none=False: Used to include None values in the list.
        :return: a new list of objects that contain the specified speaker instances.
        :doc-author: Trelent
        """
        '''Filter on the Speech Character Instance's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Speaker Instance's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and any(c in spkrs for c in thing.spkr) ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Speaker Instance's returned no entries", self.api.LOG_LOWDETAIL)
        return SpeechGroup(newlist ,self.api)


    def filterSpkrs(self, spkrs, incl_none=False):
        """
        The filterSpkrs function specifically filters the list of things in the class by speaker.
        
            self: Used to access the class attributes.
            spkrs: Used to filter the list of things along the speakers.
            incl_none=False: Used to include None objects in the list of returned objects.
        :return: a list of the things that have a speaker with a character in the spkrs list.
        :doc-author: Trelent
        """
        '''Filter on the Speech Character's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Speaker's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            #print(*(c.id for c in thing.spkr))
            if( (thing is not None or (thing is None and incl_none)) and any(c.char in spkrs for c in thing.spkr) ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Speaker's returned no entries", self.api.LOG_LOWDETAIL)
        return SpeechGroup(newlist, self.api)


    def filterAddrInstances(self, addrs, incl_none=False):
        """
        The filterAddrInstances function specifically filters the list of things in the current instance
        of a class by whether or not they have an address character that is contained within a given list.
        
            self: Used to access the class's attributes and methods.
            addrs: Used to filter the list of instances by the addressee instance.
            incl_none=False: Used to include None values in the list.
        :return: the list of things that are in addrs.
        :doc-author: Trelent
        """
        '''Filter on the Speech Character Instances's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Addressee Instance's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and any(c in addrs for c in thing.addr) ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Addressee Instance's returned no entries", self.api.LOG_LOWDETAIL)
        return SpeechGroup(newlist, self.api)


    def filterAddrs(self, addrs, incl_none=False):
        """
        The filterAddrs function is used to filter the list of things that are being processed by the Speech Character's.
        
            self: Used to access the class attributes and methods.
            addrs: Used to filter the list of things.
            incl_none=False: Used to include None values in the list of things.
        :return: a list of things that match the filter.
        :doc-author: Trelent
        """
        '''Filter on the Speech Character's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Addressee's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and any(c.char in addrs for c in thing.addr) ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Addressee's returned no entries", self.api.LOG_LOWDETAIL)
        return SpeechGroup(newlist, self.api )


    def filterParts(self, parts, incl_none=False):
        """
        The filterParts function is used to filter the list of things along the part's.
        
            self: Used to access the class instance in which it is called.
            parts: Used to filter the list of things along the parts.
            incl_none=False: Used to include None values in the list.
        :return: a list of things that meet the given parts.
        :doc-author: Trelent
        """
        '''Filter on the Speech Part's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Part's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.part in parts ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Part's returned no entries", self.api.LOG_LOWDETAIL)
        return SpeechGroup(newlist, self.api)


    def filterTypes(self, types, incl_none=False):
        """
        The filterTypes function specifically filters the list of things by type.
        
            self: Used to access the class attributes.
            types: Used to filter the list of things along the types.
            incl_none=False: Used to include None's in the list.
        :return: a list of things that are not None and have a type in the types argument.
        :doc-author: Trelent
        """
        '''Filter on the Speech Type's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Type's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.type in types ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Type's returned no entries", self.api.LOG_LOWDETAIL)
        return SpeechGroup(newlist, self.api)


    def filterWorks(self, works, incl_none=False):
        """
        The filterWorks function specifically filters the list of things along the works.
        
            self: Used to access the class attributes.
            works: Used to filter the list of things.
            incl_none=False: Used to include None values in the list.
        :return: a list of things that are in the works.
        :doc-author: Trelent
        """
        '''Filter on the Speech Work's'''
        self.api.logThis("Filtering " + self.__class__.__name__[1:] + " along Work's", self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if( (thing is not None or (thing is None and incl_none)) and thing.work in works ):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Filtering " + self.__class__.__name__[1:] + " Work's returned no entries", self.api.LOG_LOWDETAIL)
        return SpeechGroup(newlist, self.api)


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
        self.level = None
        self.type = None
        self.work = None
        self._attributes = data
        
        if data:
            self._from_data(data)

        
    def _from_data(self, data):
        """
        The _from_data function populates attributes from a dict. 
        It is called by the __init__ function of the Speech class, and should not be called directly.
        
        
            self: Access the attributes of the class
            data: Populate the attributes of the instance
        :return: A dictionary of the attributes
        :doc-author: Trelent
        """
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
        if 'level' in data:
            self.level = data['level']
        if 'type' in data:
            self.type = data['type']
        if 'work' in data:
            self.work = self.api.indexedWork(data['work'])


    def __repr__(self):
        """
        The __repr__ function is what is called when you try to &quot;print&quot; an object. It returns a string representation of the object, which is how the object appears when output in the console.
        
        
            self: Refer to the object itself
        :return: The string representation of the object
        :doc-author: Trelent
        """
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
        """
        The author function returns the name of the author of this book.
        
        
            self: Access the attributes and methods of the class in python
        :return: The author of the book
        :doc-author: Trelent
        """
        '''shortcut to author (via work)'''
        return self.work.author


    @property
    def lang(self):
        """
        The lang function returns the language code of the current locale setting.
        
        
            self: Reference the instance of the class
        :return: The language of the current document
        :doc-author: Trelent
        """
        '''shortcut to language (via work)'''        
        return self.work.lang
    
    
    @property
    def l_range(self):
        """
        The l_range function returns a list of line numbers from the first parameter to the second.
        The first parameter is inclusive, while the second is exclusive.
        
            self: Access variables that belongs to the class
        :return: The first and last line numbers of the file
        :doc-author: Trelent
        """
        '''line range in format <first>-<last>'''
        return f'{self.l_fi}-{self.l_la}'
    

    @property
    def urn(self):
        """
        The urn function returns the CTS URN for the passage.
        
        
        
            self: Access variables that belongs to the class
        :return: A list of the tokens in a passage
        :doc-author: Trelent
        """
        '''cts urn for the passage'''
        return f'{self.work.urn}:{self.l_range}'
    
    
    def getSpkrString(self, sep=', '):
        ''''Returns speaker names as a single string'''
        return sep.join(inst.name for inst in self.spkr)


    def getAddrString(self, sep=', '):
        ''''Returns speaker names as a single string'''
        return sep.join(inst.name for inst in self.addr)

    
    def getCTS(self):
        """
        The getCTS function returns the CTS URN corresponding to the speech.
           The function takes as input a URN for a work and an integer indicating 
           which speech in that work we want to get. It returns a string containing 
           the CTS URN of that speech.
        
            self: Refer to the object itself
        :return: The cts passage corresponding to the speech
        :doc-author: Trelent
        """
        '''Get the CTS passage corresponding to the speech'''
        
        # bail out if work has no urn
        if (self.work.urn == '') or (self.work.urn is None):
            return None
        
        # otherwise, try to download
        resolver = self.api.resolver

        try:
            cts = resolver.getTextualNode(self.work.urn, self.l_range)

        except requests.exceptions.HTTPError as e:
            self.api.logWarning("Failed to download self.urn: " + str(e), self.api.LOG_LOWDETAIL)
            cts = None

        return cts


    def isRepliedTo(self):
        """
        The isRepliedTo function is used to determine whether or not a speech has been responded to.
        
            self: Used to access the attributes of the class.
        :return: a boolean value of True if the speech is a reply to another speech in the cluster, and False otherwise.
        :doc-author: Trelent
        """
        SpeechesInCluster = self.api.getSpeeches(cluster_id=self.cluster.id)
        for thing in SpeechesInCluster:
            if(thing.seq > self.seq):
                if(any(responder in thing.spkr for responder in self.addr)):
                    return True
        return False

    
    def isInterrupted(self):
        """
        The isInterrupted function specifically accomplishes two things:
        1.
        
            self: Used to access the class attributes.
        :return: False when there are no interruptions in the cluster.
        :doc-author: Trelent
        """
        speech = [speechs for speechs in self.api.getSpeeches(cluster_id=self.cluster.id) if speechs.seq == self.seq + 1]
        return len(speech) > 0 and any(responder in speech[0].spkr for responder in self.addr)
    
    def isInterruption(self):
        speech = [speechs for speechs in self.api.getSpeeches(cluster_id=self.cluster.id) if speechs.seq == self.seq - 1]
        return len(speech) > 0 and any(talker in speech[0].addr for talker in self.spkr)


    def splitLocus(self, loc=None, sep=".", max_split=-1, alpha=True, keep="all", trailing=False):
        """
        Return components of the locus as a list of strings
        """
        
        if loc is None:
            loc = self.l_fi
        elif loc.strip().lower() == "first":
            loc = self.l_fi
        elif loc.strip().lower() == "last":
            loc = self.l_la
        
        if sep in loc:
            parts = loc.split(sep, max_split)
        else:
            parts = [loc]
        
        # remove extra whitespace
        parts = [part.strip() for part in parts]
        
        # get rid of non-numeric characters
        if not alpha:
            parts = [re.sub("[^0-9]", "", part) for part in parts]
                
        # option 1. keep prefix
        if keep.strip().lower().startswith("pref"):
            
            # if there is a prefix
            if len(parts) > 0:
                scalar = parts[0]
                
                # add back trailing sep
                if trailing:
                    scalar = scalar + sep
                    
            # if no prefix, return empty string
            else:
                scalar = ""
            
            return scalar
        
        # option 2. keep line number
        if keep.strip().lower().startswith("line"):
            scalar = parts[-1]
        
            return scalar
            
        # option 3. return list of parts
        return parts
        
    def getLineNo(self, loc=None, sep=".", alpha=True):
        return self.splitLocus(loc, sep=sep, keep="line", alpha=alpha)

    def getPrefix(self, loc=None, sep=".", trailing=False):
        return self.splitLocus(loc, sep=sep, keep="prefix", trailing=trailing)
        
    def isMultiPrefix(self, sep="."):
        return self.getPrefix("first") != self.getPrefix("last")
        

class Tag(object):
    '''A speech type tag'''
    
    def __init__(self, data=None, api=None, index=False):
        self.api = api
        self.index = (api is not None and index is not None)
        self.type = None
        self.doubt = None
        self.notes = None
        self._attributes = data

        if data:
            self._from_data(data)

        
    def _from_data(self, data):
        self.type = data.get('type')
        self.doubt = data.get('doubt')
        self.notes = data.get('notes')
    
    def __repr__(self):
        tag = self.type
        if self.doubt:
            tag = tag + '?'
        return f'<Tag: {tag}>'

             
class DicesAPI(object):
    '''a connection to the DICES API'''
    
    DEFAULT_API = 'http://dices.ub.uni-rostock.de/api/'
    DEFAULT_CTS = 'https://scaife-cts.perseus.org/api/cts'

    LOG_HIGHDETAIL=3
    LOG_MEDDETAIL=2
    LOG_LOWDETAIL=1
    LOG_NODETAIL=0


    def __init__(self, dices_api=DEFAULT_API, cts_api=DEFAULT_CTS, logfile=None, 
                    logdetail=LOG_MEDDETAIL, progress_class=None):
        """
        The __init__ function is called when a class is instantiated. 
        It initializes the attributes of the class, and it can take arguments that get passed to it by its parent class. 
        In this case, we are using the __init__ function to initialize some attributes in our Dices object.
        
            self: Refer to the object instance (e
            dices_api=DEFAULT_API: Set the default value of the dices api
            cts_api=DEFAULT_CTS: Set the default cts api to use
            logfile=None: Specify a logfile
            logdetail=LOG_MEDDETAIL: Set the detail level of the log
            progress_class=None: Pass a custom progress class to the dices object
        :return: Nothing
        :doc-author: Trelent
        """
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
        self._tag_index = {}
        self.version = "DEBUG VERSION 1.0"
        self.logThis("Database Initialized", self.LOG_NODETAIL)


    def getPagedJSON(self, endpoint, params=None, progress=False):
        """
        The getPagedJSON function retrieves data from the API and returns a list of JSON objects.
        
        
        
            self: Access variables that belong to the class
            endpoint: Specify the api endpoint
            params=None: Pass in a dictionary of parameters to be passed into the api call
            progress=False: Turn off the progress bar
        :return: A list of dictionaries
        :doc-author: Trelent
        """
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
        """
        The createLog function is used to create a new log file.
        
            self: Used to access the attributes and methods of the class in python.
            logfile: Used to specify the name of the log file.
            clearLog=False: Used to clear the log file.
        :return: None.
        :doc-author: Trelent
        """
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
        """
        The _detailtostring function is used to convert the logdetail attribute into a string.
        The logdetail attribute is an integer that represents the level of detail in the logs. 
        It can be set to one of four values: No, Low, Medium or High.  The _detailtostring function returns these values as strings instead of integers.
        
            self: Access the attributes and methods of the class in python
        :return: The log detail level as a string
        :doc-author: Trelent
        """
        if self.logdetail == self.LOG_NODETAIL:
            return "No"
        elif self.logdetail == self.LOG_LOWDETAIL:
            return "Low"
        elif self.logdetail == self.LOG_MEDDETAIL:
            return "Medium"
        else:
            return "High"

    
    def clearLog(self):
        """
        The clearLog function is used to clear the log file.
        
            self: Used to refer to the object itself.
        :return: a None object.
        :doc-author: Trelent
        """
        if self.log:
            self.logWarning("Clearing log *LOG MAY END HERE*", self.LOG_NODETAIL)
            self.log = None


    def logThis(self, message, priority):
        """
        The logThis function is used to log the messages in a file or print it on console.
        
            self: Used to access the class attributes.
            message: Used to pass the message that needs to be logged.
            priority: Used to determine if a message should be logged.
        :return: the message that was passed into it.
        :doc-author: Trelent
        """
        if priority <= self.logdetail:
            if self.log:
                self.log.debug(message)
            else:
                sys.stderr.write("[GENE]" + message)


        
    def logWarning(self, message, priority):
        """
        The logWarning function prints a warning message to the screen and also writes it to the log file if one is specified.
        
            self: Used to access the class attributes.
            message: Used to pass the message that needs to be logged.
            priority: Used to determine if a message should be logged or not.
        :return: None.
        :doc-author: Trelent
        """
        if priority <= self.logdetail:
            if self.log:
                self.log.warning(message)
            else:
                sys.stderr.write("[WARNING]" + message)

    
    def logError(self, message, priority):
        """
        The logError function is used to log errors in the event that a user does not have logging enabled.
        
            self: Used to access the class variables.
            message: Used to store the error message.
            priority: Used to determine which messages are logged and which aren't.
        :return: True.
        :doc-author: Trelent
        """
        if priority <= self.logdetail:
            if self.log:
                self.log.error(message)
            else:
                sys.stderr.write("[ERROR]" + message)

    
    def logCritical(self, message, priority):
        """
        The logCritical function prints the message to the console and also writes it to a log file if logging is enabled.
        
            self: Used to access the class attributes.
            message: Used to pass the message that needs to be logged.
            priority: Used to determine the level of detail in the log.
        :return: the log object.
        :doc-author: Trelent
        """
        if priority <= self.logdetail:
            if self.log:
                self.log.critical(message)
            else:
                sys.stderr.write("[CRITICAL]" + message)

        
    def getSpeeches(self, progress=False, **kwargs):
        """
        The getSpeeches function retrieves speeches from the API and returns them as a SpeechGroup object.
        
            self: Used to refer to the object instance.
            progress=False: Used to turn off the progress bar.
            **kwargs: Used to pass a variable number of keyword arguments to a function.
        :return: a list of speeches.
        :doc-author: Trelent
        """
        '''Retrieve speeches from API'''
        
        self.logThis("Attempting to fetch a SpeechGroup", self.LOG_MEDDETAIL)
        # get the results from the speeches endpoint
        results = self.getPagedJSON('speeches', dict(**kwargs), progress=progress)
        
        # convert to Speech objects
        speeches = SpeechGroup([self.indexedSpeech(s) for s in results], api=self)

        self.logThis("Successfully retrieved a list of speeches", self.LOG_MEDDETAIL)
        
        return speeches


    def getClusters(self, progress=False, **kwargs):
        """
        The getClusters function retrieves the clusters from the API and returns them as a list of Cluster objects.
        
            self: Used to access the API object's properties.
            progress=False: Used to turn off the progress bar.
            **kwargs: Used to pass a variable number of keyword arguments to a function.
        :return: a list of clusters.
        :doc-author: Trelent
        """
        '''Retrieve speech clusters from API'''
        self.logThis("Attempting to fetch a ClusterGroup", self.LOG_MEDDETAIL)
                
        # get the results from the clusters endpoint
        results = self.getPagedJSON('clusters', dict(**kwargs), progress=progress)
        
        # convert to Clusters objects
        clusters = SpeechClusterGroup([self.indexedSpeechCluster(s) for s in results], api=self)
        self.logThis("Successfully retrieved a list of clusters", self.LOG_MEDDETAIL)
        
        return clusters

    
    def getCharacters(self, progress=False, **kwargs):
        """
        The getCharacters function retrieves a list of characters from the Marvel API.
        
            self: Used to refer to the object instance itself.
            progress=False: Used to tell the function to not display a progress bar.
            **kwargs: Used to pass a variable number of arguments to a function.
        :return: a list of _Character objects.
        :doc-author: Trelent
        """
        '''Retrieve characters from API'''
        self.logThis("Attempting to fetch a CharactersGroup", self.LOG_MEDDETAIL)
        
        # get the results from the characters endpoint
        results = self.getPagedJSON('characters', dict(**kwargs), progress=progress)
        
        # convert to Character objects
        characters = CharacterGroup([self.indexedCharacter(c) for c in results], api=self)
        self.logThis("Successfully retrieved a list of characters", self.LOG_MEDDETAIL)
        
        return characters


    def getWorks(self, progress=False, **kwargs):
        """
        The getWorks function is used to fetch works from the API.
        
            self: Used to refer to the object itself.
            progress=False: Used to tell the function whether or not to print out a progress bar.
            **kwargs: Used to pass a dictionary of key-value pairs to the API.
        :return: a WorkGroup object.
        :doc-author: Trelent
        """
        '''Fetch works from the API'''
        self.logThis("Attempting to fetch a WorksGroup", self.LOG_MEDDETAIL)
        
        results = self.getPagedJSON('works', dict(**kwargs), progress=progress)

        works = WorkGroup([self.indexedWork(w) for w in results], api=self)
        self.logThis("Successfully retrieved a list of works", self.LOG_MEDDETAIL)
        return works


    def getAuthors(self, progress=False, **kwargs):
        """
        The getAuthors function is used to retrieve a list of authors from the API.
        
            self: Used to access the API object's properties.
            progress=False: Used to tell the function not to display a progress bar.
            **kwargs: Used to pass keyworded variable length of arguments to a function.
        :return: a AuthorGroup object.
        :doc-author: Trelent
        """

        self.logThis("Attempting to fetch a AuthorGroup", self.LOG_MEDDETAIL)

        results = self.getPagedJSON('authors', dict(**kwargs), progress=progress)

        authors = AuthorGroup([self.indexedAuthor(a) for a in results], api=self)
        self.logThis("Successfully retrieved a list of authors", self.LOG_MEDDETAIL)
        return authors


    def getInstances(self, progress=False, **kwargs):
        """
        The getInstances function specifically accomplishes the following:
            1.
        
            self: Used to access the class variables.
            progress=False: Used to specify if the function should display a progress bar.
            **kwargs: Used to pass a variable number of keyword arguments to the function.
        :return: a list of dictionaries.
        :doc-author: Trelent
        """
        '''Fetch character instances from the API'''  
        self.logThis("Attempting to fetch a CharacterInstanceGroup", self.LOG_MEDDETAIL)  
        results = self.getPagedJSON('instances', dict(**kwargs), progress=progress)

        instances = CharacterInstanceGroup([self.indexedCharacterInstance(i) for i in results], api=self)
        self.logThis("Successfully retrieved a list of character instances", self.LOG_MEDDETAIL)
        return instances
        
    
    def indexedAuthor(self, data):
        """
        The indexedAuthor function creates an author object from the data that is passed to it.
        
            self: Used to access the class variables.
            data: Used to pass the data from the API to this function.
        :return: a new author object if the id doesn't exist in the index, and an existing object if it does.
        :doc-author: Trelent
        """
        '''Create an author in the index'''
        
        # if someone has passed an existing author object
        if isinstance(data, Author):
            if data.id in self._author_index:
                if data is not self._author_index[data.id]:
                    self.logThis("Refused to add non-identical duplicate author ID {data.id} to index", self.LOG_LOWDETAIL)
                
            else:
                if data.api is not self:
                    self.logThis("Importing author ID {data.id} from other api {data.api}", self.LOG_HIGHDETAIL)
                    data.api = self
                else:
                    self.logThis("Adding a new author with ID {data.id}", self.LOG_HIGHDETAIL)
                data.index = True
                self._author_index[data.id] = data
                
            return self._author_index[data.id]
        
        # if someone has passed just an ID
        if isinstance(data, int):
            data = {"id": data}
        
        # otherwise, assume JSON data
        else:
            if data['id'] in self._author_index:
                self.logThis("Fetching author with ID " + str(data['id']), self.LOG_HIGHDETAIL)
            else:
                self.logThis("Creating new author with ID " + str(data['id']), self.LOG_HIGHDETAIL)
                self._author_index[data['id']] = Author(data, api=self, index=True)
 
        return self._author_index[data['id']]


    def indexedWork(self, data):
        """
        The indexedWork function creates a new work object and adds it to the index.
        
            self: Used to access the class attributes.
            data: Used to pass the work data to the Work class.
        :return: the work if it is already in the index.
        :doc-author: Trelent
        """
        '''Create a work in the index'''
        
        if isinstance(data, int):
            data = {"id": data}
        
        if data['id'] in self._work_index:
            w = self._work_index[data['id']]
            self.logThis("Fetching work with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        else:
            w = Work(data, api=self, index=True)
            self._work_index[data['id']] = w
            self.logThis("Creating new work with ID " + str(data['id']), self.LOG_HIGHDETAIL)
 
        return w

    
    def indexedSpeech(self, data):
        """
        The indexedSpeech function creates a speech object from the data that is passed to it.
        
            self: Used to reference the class instance.
            data: Used to pass the speech data to the Speech class.
        :return: the speech object that is created.
        :doc-author: Trelent
        """
        '''Create a speech in the index'''
        
        if isinstance(data, int):
            data = {"id": data}
        
        if data['id'] in self._speech_index:
            s = self._speech_index[data['id']]
            self.logThis("Fetching speech with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        else:
            s = Speech(data, api=self, index=True)
            self._speech_index[data['id']] = s
            self.logThis("Creating new speech with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        return s

        
    def indexedSpeechCluster(self, data):
        """
        The indexedSpeechCluster function is used to create a speech cluster in the index. 
        If the ID of the speech cluster is already present in the index, it will fetch that object from cache. 
        Otherwise, it will create a new SpeechCluster object and add it to both memory and disk cache.
        
            self: Reference the class instance
            data: Pass the data from the api call
        :return: A speechcluster object
        :doc-author: Trelent
        """
        '''Create a speech cluster in the index'''
        
        if isinstance(data, int):
            data = {"id": data}
                
        if data['id'] in self._speechcluster_index:
            s = self._speechcluster_index[data['id']]
            self.logThis("Fetching cluster with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        else:
            s = SpeechCluster(data, api=self, index=True)
            self._speechcluster_index[data['id']] = s
            self.logThis("Creating new cluster with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        
        return s


    def indexedCharacter(self, data):
        """
        The indexedCharacter function is used to create a character in the index. If the character already exists, it is recycled and returned.
        Otherwise, a new Character object is created with the data passed in as an argument.
        
            self: Reference the class instance
            data: Pass in the json data for the character
        :return: A character object
        :doc-author: Trelent
        """
        '''Create a character in the index'''
        
        if isinstance(data, int):
            data = {"id": data}
                
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
        """
        The indexedCharacterInstance function is used to create a character instance in the index. If the character instance already exists, it is fetched from the index.
        
        
            self: Access the api object's properties
            data: Pass the data from the api to characterinstance
        :return: A characterinstance object
        :doc-author: Trelent
        """
        '''Create a character instance in the index'''
        
        if isinstance(data, int):
            data = {"id": data}
                
        if data['id'] in self._characterinstance_index:
            c = self._characterinstance_index[data['id']]
            self.logThis("Fetching character instance with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        else:
            c = CharacterInstance(data, api=self, index=True)
            self._characterinstance_index[data['id']] = c
            self.logThis("Creating new character instance with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        
        return c
        
    # def indexedTag(self, data):
    #     '''Create a tag in the index'''
    #
    #     if isinstance(data, int):
    #         data = {"id": data}
    #
    #     if data['id'] in self._tag_index:
    #         tag = self._tag_index[data['id']]
    #         self.logThis("Fetching tag with ID " + str(data['id']), self.LOG_HIGHDETAIL)
    #     else:
    #         tag = Tag(data, api=self, index=True)
    #         self._tag_index[data['id']] = tag
    #         self.logThis("Creating new tag with ID " + str(data['id']), self.LOG_HIGHDETAIL)
    #
    #     return tag
    
    def cachedAuthors(self):
        return AuthorGroup([auth for auth in self._author_index.values()], api=self)
        
    def cachedWorks(self):
        return WorkGroup([work for work in self._work_index.values()], api=self)
        
    def cachedCharacters(self):
        return CharacterGroup([char for char in self._character_index.values()], api=self)
        
    def cachedCharacterInstances(self):
        return CharacterInstanceGroup([inst for inst in self._characterinstance_index.values()], api=self)

    def cachedSpeechClusters(self):
        return SpeechClusterGroup([cluster for cluster in self._speechcluster_index.values()], api=self)
        
    def cachedSpeeches(self):
        return SpeechGroup([s for s in self._speech_index.values()], api=self)
        
    
    @classmethod
    def fromGitDump(cls, commit, logdetail=LOG_NODETAIL):
        '''Create a self-contained dataset from a DB dump saved to GitHub
        
            Returns a fake DicesAPI with cached data downloaded from Github, specifically, from the file data/speechdb.json
        '''

        api = cls(dices_api="", logdetail=logdetail)
        url = "https://github.com/cwf2/dices/raw/{commit}/data/speechdb.json".format(commit=commit)

        # download json data
        print(f"Downloading from {url}")
        res = requests.get(url)
        if not res.ok:
            res.raise_for_status()
        db_dump = res.json()

        # build tables
        tables = dict(
            metadata = [],
            author = [],
            work = [],
            character = [],
            characterinstance = [],
            speech = [],
            speechcluster = [],
            speechtag = []
        )

        # populate tables
        for rec in db_dump:
            model = rec["model"].split(".")[-1]
            row = rec["fields"]
            row["id"] = rec["pk"]
            tables[model].append(row)

        # diagnostic info
        ts = None
        for row in tables["metadata"]:
            if row["name"] == "date":
                ts = row["value"]
        print(f"timestamp: {ts}")
    
        # add authors
        for auth in tables["author"]:
            api.indexedAuthor(auth)

        # add works
        for work in tables["work"]:
            api.indexedWork(work)

        # add characters
        for char in tables["character"]:
            api.indexedCharacter(char)

        # add character instances
        for inst in tables["characterinstance"]:
            api.indexedCharacterInstance(inst)

        # add speech clusters
        for clust in tables["speechcluster"]:
            api.indexedSpeechCluster(clust)

        # add speeches
        for s in tables["speech"]:
            api.indexedSpeech(s)

        api._raw_data = tables
        api._git_hash = commit
    
        # # add tags
        # for tag in tables["speechtag"]:
        #     api.indexedTag(s)
    
        return api