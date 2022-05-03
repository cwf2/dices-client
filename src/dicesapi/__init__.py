import requests
import sys
from MyCapytain.resolvers.cts.api import HttpCtsResolver
from MyCapytain.retrievers.cts5 import HttpCtsRetriever
import logging

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

    def __init__(self, things=None, api=None):
        """
        The __init__ function is called when a new object is created from the class.
        The init function can take arguments, but self is always the first one. 
        Self is a reference to the instance of the class. It binds the attributes with 
        the given arguments.
        
        :param self: Refer to the object itself
        :param things=None: Create a datagroup object without any things
        :param api=None: Pass the api object to the class
        :return: A datagroup object
        :doc-author: Trelent
        """
        self._things=things
        if api is None:
            print("Could not create a datagroup with no API, exiting")
            quit()
        self.api=api
    

    def __iter__(self):
        """
        The __iter__ function is called when an iterator is required for a container. 
        This method should return a new iterator object that can iterate over all the objects in the container, 
        such as lists and tuples.
        
        :param self: Refer to the instance of the object
        :return: An iterator object
        :doc-author: Trelent
        """
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
        """
        The extend function combines two data groups of the same type.
        
        :param self: Used to refer to the object itself.
        :param datagroup: Used to pass in another instance of the same class.
        :param duplicates=False: Used to determine whether or not to remove duplicate entries.
        :return: None.
        :doc-author: Trelent
        """

        self.api.logThis("Attempting to extend a " + self.__class__.__name__[1:], self.api.LOG_MEDDETAIL)  
        if(isinstance(datagroup, self.__class__)):
            self._things.extend(datagroup._things)
            if(not duplicates):
                self._things = list(set(self._things))
        else:
            self.api.logWarning("Could not extend the given datagroup because of conflicting classes, skipping", self.api.LOG_LOWDETAIL)


    def unionize(datagroup1, datagroup2, api, duplicates=True):
        """
        The unionize function takes two data groups and returns a new data group that is the union of the two.
        
        :param datagroup1: Used to specify the first dataframe that is being unionized.
        :param datagroup2: Used to specify the second dataframe to be unioned with the first one.
        :param api: Used to pass in the API key.
        :param duplicates=True: Used to determine whether or not to include duplicate values in the union.
        :return: a pandas dataframe.
        :doc-author: Trelent
        """
        if(datagroup1.__class__ == datagroup2.__class__):
            return type(datagroup1)(datagroup1.list, api).extend(datagroup2, duplicates)


    def intersect(self, datagroup, newDataGroup=False):
        """
        The intersect function is used to find the intersection of two DataGroups.
        
        :param self: Used to refer to the object itself.
        :param datagroup: Used to specify the data group to intersect with.
        :param newDataGroup=False: Used to create a new DataGroup object.
        :return: a new DataGroup that contains elements from the original DataGroup and otherDataGroup.
        :doc-author: Trelent
        """
        self.api.logThis("Attempting to intersect a " + self.__class__.__name__[1:], self.api.LOG_MEDDETAIL)
        if(isinstance(datagroup, self.__class__)):
            return type(self)([thing for thing in self._things if thing in datagroup], self.api)
        else:
            self.api.logWarning("Could not intersect the given datagroup because of conflicting classes, skipping", self.api.LOG_LOWDETAIL)
            return type(self)([], self.api)


    def filterAttribute(self, attribute, value):
        """
        The filterAttribute function specifically filters the objects in a DataGroup for a specific attribute and value.
        
        :param self: Used to access the class attributes.
        :param attribute: Used to specify the attribute that will be used for filtering.
        :param value: Used to specify the value to filter for.
        :return: a new DataGroup object.
        :doc-author: Trelent
        """
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
        """
        The filterList function specifically filters the list of objects in this DataGroup for members that have a specific attribute and value.
        
        :param self: Used to access the class instance.
        :param attribute: Used to specify the attribute that is used for filtering.
        :param filterList: Used to filter the DataGroup for objects that have a specific attribute value.
        :return: a list of things that meet the criteria.
        :doc-author: Trelent
        """
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
        """
        The advancedFilter function is used to filter the list of things in a class using a user defined function.
        
        :param self: Used to access the API object that is created when we call the method.
        :param filterFunc: Used to filter the list of things.
        :param **kwargs: Used to pass a variable-length list of keyword arguments to a function.
        :return: a list of things that match the given filterFunc and kwargs.
        :doc-author: Trelent
        """
        self.api.logThis("Advanced filtering " + self.__class__.__name__[1:], self.api.LOG_MEDDETAIL)
        newlist = []
        for thing in self._things:
            if filterFunc(thing, **kwargs):
                newlist.append(thing)
        if len(newlist) == 0:
            self.api.logWarning("Advanced filtering yielded no results", self.api.LOG_LOWDETAIL)
        return type(self)(newlist, self.api)


class _AuthorGroup(_DataGroup):
    '''Datagroup used to hold a list of Authors'''

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
        """
        The filterNames function is used to filter an Authorgroup based on if the author's name is in the names list.
        
        :param self: Used to reference the object itself.
        :param names: Used to filter the list of names.
        :param incl_none=False: Used to include None values in the list of names.
        :return: a list of things that are in the names parameter.
        :doc-author: Trelent
        """
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
        """
        The filterIDs function specifically filters the list of things that are in the 
        list of IDs.
        
        :param self: Used to access the class attributes.
        :param ids: Used to filter the list of authors by their ID.
        :param incl_none=False: Used to include None values in the list of IDs.
        :return: a list of all the things that have an id in the ids list.
        :doc-author: Trelent
        """
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
        """
        The filterWDs function specifically filters the list of things along the WD's.
        
        :param self: Used to reference the object itself.
        :param wds: Used to filter the list of things by their Wikidata ID.
        :param incl_none=False: Used to include None values in the list.
        :return: a list of things.
        :doc-author: Trelent
        """
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
        """
        The filterUrns function specifically filters the list of things along the urns.
        
        :param self: Used to access the class attributes.
        :param urns: Used to filter the list of things by their urn.
        :param incl_none=False: Used to include None values in the list.
        :return: a list of things that match the urns in the list passed to it.
        :doc-author: Trelent
        """
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
        """
        The filterIDs function specifically filters the list of things along the ID's provided.
        
        :param self: Used to refer to the object itself.
        :param ids: Used to filter the list of works by their ID's.
        :param incl_none=False: Used to include None values in the list.
        :return: a list of things that have ids in the list passed to it.
        :doc-author: Trelent
        """
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
        """
        The filterTitles function filters the list of things along the titles that are passed in.
        
        :param self: Used to reference the class instance.
        :param titles: Used to filter the results along the titles.
        :param incl_none=False: Used to include None values in the list.
        :return: a new list of things that match the titles we passed in.
        :doc-author: Trelent
        """
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
        """
        The filterWDs function specifically filters the list of things along the WD's.
        
        :param self: Used to access the class attributes.
        :param wds: Used to filter the list of works.
        :param incl_none=False: Used to include None values in the list of things.
        :return: a new list of things that match the WD's passed in as an argument.
        :doc-author: Trelent
        """
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
        """
        The filterUrns function is used to filter the list of things along the URN's.
        
        :param self: Used to refer to the object itself.
        :param urns: Used to filter the list of works by their URN.
        :param incl_none=False: Used to include None values in the list of works.
        :return: a list of things.
        :doc-author: Trelent
        """
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
        """
        The filterAuthors function specifically filters the list of works by author.
        
        :param self: Used to refer to the object itself, which is useful for accessing its attributes.
        :param authors: Used to filter the list of works by author.
        :param incl_none=False: Used to include None values in the list.
        :return: a list of things that have an Author in the authors parameter.
        :doc-author: Trelent
        """
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
        """
        The filterLangs function is used to filter the list of works by language.
        
        :param self: Used to refer to the object itself.
        :param langs: Used to filter the list of works by language.
        :param incl_none=False: Used to include None values in the list.
        :return: a new list of things, filtered by the provided langs.
        :doc-author: Trelent
        """
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
        """
        The filterIDs function is used to filter the list of characters by ID.
        
        :param self: Used to access the class attributes.
        :param ids: Used to filter the list of things, and it is a list of integers.
        :param incl_none=False: Used to include None values in the list.
        :return: a list of characters that have the ID's specified in the ids parameter.
        :doc-author: Trelent
        """
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
        """
        The filterNames function specifically accomplishes two things:
        1.
        
        :param self: Used to access the class attributes and methods.
        :param names: Used to filter the list of names.
        :param incl_none=False: Used to include None values in the list.
        :return: a list of things that have a name attribute.
        :doc-author: Trelent
        """
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
        """
        The filterBeings function specifically accomplishes the following:
            1.
        
        :param self: Used to access the class instance.
        :param beings: Used to filter the list of beings that are returned.
        :param incl_none=False: Used to include None values in the list.
        :return: a list of things.
        :doc-author: Trelent
        """
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
        """
        The filterNumbers function specifically filters the list of things by a list of numbers.
        
        :param self: Used to access the class variables.
        :param numbers: Used to filter the list of things.
        :param incl_none=False: Used to include None values in the list.
        :return: a list of things that have a number in the numbers list.
        :doc-author: Trelent
        """
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
        """
        The filterWDs function is used to filter the list of things that are being returned by the API.
        
        :param self: Used to access the class attributes, and is used to access the API.
        :param wds: Used to filter the WD's that are used to create the list of characters.
        :param incl_none=False: Used to include None values in the list.
        :return: a list of Thing objects that have a wd attribute that is also present in the passed list of WD identifiers.
        :doc-author: Trelent
        """
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
        """
        The filterMantos function specifically filters the list of things by a list of mantos.
        
        :param self: Used to access the class attributes.
        :param mantos: Used to filter the list of things by their manto.
        :param incl_none=False: Used to include None values in the list.
        :return: a list of things that have a manto in the provided list.
        :doc-author: Trelent
        """
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
        """
        The filterGenders function is used to filter the list of characters by gender.
        
        :param self: Used to access the class' instance variables.
        :param genders: Used to specify the genders to include in the filtered list.
        :param incl_none=False: Used to include None values in the list.
        :return: the list of characters that have a gender in the genders list.
        :doc-author: Trelent
        """
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
        """
        The filterIDs function is used to filter the character instances by ID.
        
        :param self: Used to access the class attributes.
        :param ids: Used to filter the character instances by their ID.
        :param incl_none=False: Used to include None values in the list.
        :return: a list of all the things that are in the ids list.
        :doc-author: Trelent
        """
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
        """
        The filterContexts function is used to filter the list of things that are being returned by the getThings function.
        
        :param self: Used to access the class instance within the same class.
        :param contexts: Used to filter the character instances that are returned.
        :param incl_none=False: Used to include None values in the list.
        :return: a list of the things that are in the context, or None if you want to include all things with a None context.
        :doc-author: Trelent
        """
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
        """
        The filterChars function is used to filter the list of things that are contained in a ThingList.
        
        :param self: Used to refer to the object instance.
        :param chars: Used to filter on the character instance's character.
        :param incl_none=False: Used to include None values in the list.
        :return: a list of Thing's that have a character instance in the chars list.
        :doc-author: Trelent
        """
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
        """
        The filterDisgs function specifically filters the character instances in a list of characters based on whether or not they have a disguise.
        
        :param self: Used to refer to the object instance.
        :param disgs: Used to filter the character instances that are returned.
        :param incl_none=False: Used to include None values in the list.
        :return: a list of things that have a particular instance of Disguise in their list of Disguises.
        :doc-author: Trelent
        """
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
        """
        The filterNames function is used to filter the list of characters by their names.
        
        :param self: Used to access the class instance within a method.
        :param names: Used to filter the list of characters by name.
        :param incl_none=False: Used to include None values in the list.
        :return: a list of the things that are in names.
        :doc-author: Trelent
        """
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
        """
        The filterBeings function is used to filter the list of things that are being filtered by the filter function.
        
        :param self: Used to refer to the object instance.
        :param beings: Used to filter the list of things that are being.
        :param incl_none=False: Used to include None values in the list.
        :return: a list of things that have a being property and are in the beings list.
        :doc-author: Trelent
        """
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
        """
        The filterNumbers function is used to filter the list of characters by their number.
        
        :param self: Used to access the class instance.
        :param numbers: Used to filter the list of things by their number.
        :param incl_none=False: Used to include None values in the list.
        :return: a list of things that have a number attribute in the numbers parameter.
        :doc-author: Trelent
        """
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
        """
        The filterGenders function is used to filter the list of characters by gender.
        
        :param self: Used to store the class instance.
        :param genders: Used to specify the list of genders to filter on.
        :param incl_none=False: Used to include None values in the list.
        :return: a list of things that have the same gender as specified in the genders argument.
        :doc-author: Trelent
        """
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
        """
        The filterIDs function is used to filter the list of things in a class by their ID's.
        
        :param self: Used to access the class attributes.
        :param ids: Used to pass a list of ID's that you want to filter on.
        :param incl_none=False: Used to determine whether or not to include None values in the filtered list.
        :return: a list of things that have the ID in the ids variable.
        :doc-author: Trelent
        """
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
        """
        The getFirst function is a method of the Cluster class.
        
        :param self: Used to refer to the object itself.
        :return: an object of type speech.
        :doc-author: Trelent
        """
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
        """
        The countReplies function counts the number of replies in a cluster.
        
        :param self: Used to access the class attributes.
        :return: the number of replies in the cluster.
        :doc-author: Trelent
        """
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
        """
        The countInterruptions function counts the number of interruptions in a cluster.
        
        :param self: Used to access the class attributes.
        :return: an integer, the number of interruptions in a cluster.
        :doc-author: Trelent
        """
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
        """
        The isCluster function is used to check if a cluster exists in the clusters list.
        
        :param self: Used to refer to the object itself.
        :param clusterID: Used to check if the cluster with that ID exists in the list of clusters.
        :return: a boolean value that states whether or not the clusterID is in the clusters list.
        :doc-author: Trelent
        """
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
        """
        The filterIDs function is used to filter the list of things that are currently in the Speech class.
        
        :param self: Used to access the class attributes and methods.
        :param ids: Used to filter the list of speeches by their ID.
        :param incl_none=False: Used to include or exclude objects with None as their ID.
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
        return _SpeechGroup(newlist, self.api)


    def filterClusters(self, clusters, incl_none=False):
        """
        The filterClusters function specifically filters the list of things along the clusters that are passed in.
        
        :param self: Used to reference the class instance.
        :param clusters: Used to filter the list of things.
        :param incl_none=False: Used to include None's in the list.
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
        return _SpeechGroup(newlist, self.api)


    def filterSeqs(self, seqs, incl_none=False):
        """
        The filterSeqs function is used to filter the list of things that are being processed by the
        Speech API.
        
        :param self: Used to reference the object itself.
        :param seqs: Used to filter the list of things.
        :param incl_none=False: Used to include None values in the list of things.
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
        return _SpeechGroup(newlist, self.api)


    def filterL_FIs(self, l_fis, incl_none=False):
        """
        The filterL_FIs function specifically filters the list of things along the L_FI's.
        
        :param self: Used to access the class attributes and methods.
        :param l_fis: Used to filter the list of things along the L_FI's.
        :param incl_none=False: Used to include None values in the list.
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
        return _SpeechGroup(newlist, self.api)


    def filterL_LAs(self, l_las, incl_none=False):
        """
        The filterL_LAs function specifically filters the list of things along the L_LA's.
        
        :param self: Used to access the API.
        :param l_las: Used to filter the list of things by their L_LA.
        :param incl_none=False: Used to include None values in the list of L_LAs.
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
        return _SpeechGroup(newlist, self.api)


    def filterSpkrInstances(self, spkrs, incl_none=False):
        """
        The filterSpkrInstances function specifically filters the list of things in the class by speaker instances.
        
        :param self: Used to access the API class.
        :param spkrs: Used to specify the speakers to include in the filtered list.
        :param incl_none=False: Used to include None values in the list.
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
        return _SpeechGroup(newlist ,self.api)


    def filterSpkrs(self, spkrs, incl_none=False):
        """
        The filterSpkrs function specifically filters the list of things in the class by speaker.
        
        :param self: Used to access the class attributes.
        :param spkrs: Used to filter the list of things along the speakers.
        :param incl_none=False: Used to include None objects in the list of returned objects.
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
        return _SpeechGroup(newlist, self.api)


    def filterAddrInstances(self, addrs, incl_none=False):
        """
        The filterAddrInstances function specifically filters the list of things in the current instance
        of a class by whether or not they have an address character that is contained within a given list.
        
        :param self: Used to access the class's attributes and methods.
        :param addrs: Used to filter the list of instances by the addressee instance.
        :param incl_none=False: Used to include None values in the list.
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
        return _SpeechGroup(newlist, self.api)


    def filterAddrs(self, addrs, incl_none=False):
        """
        The filterAddrs function is used to filter the list of things that are being processed by the Speech Character's.
        
        :param self: Used to access the class attributes and methods.
        :param addrs: Used to filter the list of things.
        :param incl_none=False: Used to include None values in the list of things.
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
        return _SpeechGroup(newlist, self.api )


    def filterParts(self, parts, incl_none=False):
        """
        The filterParts function is used to filter the list of things along the part's.
        
        :param self: Used to access the class instance in which it is called.
        :param parts: Used to filter the list of things along the parts.
        :param incl_none=False: Used to include None values in the list.
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
        return _SpeechGroup(newlist, self.api)


    def filterTypes(self, types, incl_none=False):
        """
        The filterTypes function specifically filters the list of things by type.
        
        :param self: Used to access the class attributes.
        :param types: Used to filter the list of things along the types.
        :param incl_none=False: Used to include None's in the list.
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
        return _SpeechGroup(newlist, self.api)


    def filterWorks(self, works, incl_none=False):
        """
        The filterWorks function specifically filters the list of things along the works.
        
        :param self: Used to access the class attributes.
        :param works: Used to filter the list of things.
        :param incl_none=False: Used to include None values in the list.
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
        """
        The _from_data function populates attributes from a dict. 
        It is called by the __init__ function of the Speech class, and should not be called directly.
        
        
        :param self: Access the attributes of the class
        :param data: Populate the attributes of the instance
        :return: A dictionary of the attributes
        :doc-author: Trelent
        """
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
        """
        The __repr__ function is what is called when you try to &quot;print&quot; an object. It returns a string representation of the object, which is how the object appears when output in the console.
        
        
        :param self: Refer to the object itself
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
        
        
        :param self: Access the attributes and methods of the class in python
        :return: The author of the book
        :doc-author: Trelent
        """
        '''shortcut to author (via work)'''
        return self.work.author


    @property
    def lang(self):
        """
        The lang function returns the language code of the current locale setting.
        
        
        :param self: Reference the instance of the class
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
        
        :param self: Access variables that belongs to the class
        :return: The first and last line numbers of the file
        :doc-author: Trelent
        """
        '''line range in format <first>-<last>'''
        return f'{self.l_fi}-{self.l_la}'
    

    @property
    def urn(self):
        """
        The urn function returns the CTS URN for the passage.
        
        
        
        :param self: Access variables that belongs to the class
        :return: A list of the tokens in a passage
        :doc-author: Trelent
        """
        '''cts urn for the passage'''
        return f'{self.work.urn}:{self.l_range}'
    
    
    def getCTS(self):
        """
        The getCTS function returns the CTS URN corresponding to the speech.
           The function takes as input a URN for a work and an integer indicating 
           which speech in that work we want to get. It returns a string containing 
           the CTS URN of that speech.
        
        :param self: Refer to the object itself
        :return: The cts passage corresponding to the speech
        :doc-author: Trelent
        """
        '''Get the CTS passage corresponding to the speech'''
                
        resolver = self.api.resolver
        cts = resolver.getTextualNode(self.work.urn, self.l_range)

        return cts


    def isRepliedTo(self):
        """
        The isRepliedTo function is used to determine whether or not a speech has been responded to.
        
        :param self: Used to access the attributes of the class.
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
        
        :param self: Used to access the class attributes.
        :return: False when there are no interruptions in the cluster.
        :doc-author: Trelent
        """
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
        """
        The __init__ function is called when a class is instantiated. 
        It initializes the attributes of the class, and it can take arguments that get passed to it by its parent class. 
        In this case, we are using the __init__ function to initialize some attributes in our Dices object.
        
        :param self: Refer to the object instance (e
        :param dices_api=DEFAULT_API: Set the default value of the dices api
        :param cts_api=DEFAULT_CTS: Set the default cts api to use
        :param logfile=None: Specify a logfile
        :param logdetail=LOG_MEDDETAIL: Set the detail level of the log
        :param progress_class=None: Pass a custom progress class to the dices object
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
        self.logThis("Database Initialized", self.LOG_NODETAIL)


    def getPagedJSON(self, endpoint, params=None, progress=False):
        """
        The getPagedJSON function retrieves data from the API and returns a list of JSON objects.
        
        
        
        :param self: Access variables that belong to the class
        :param endpoint: Specify the api endpoint
        :param params=None: Pass in a dictionary of parameters to be passed into the api call
        :param progress=False: Turn off the progress bar
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
        
        :param self: Used to access the attributes and methods of the class in python.
        :param logfile: Used to specify the name of the log file.
        :param clearLog=False: Used to clear the log file.
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
        
        :param self: Access the attributes and methods of the class in python
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
        
        :param self: Used to refer to the object itself.
        :return: a None object.
        :doc-author: Trelent
        """
        if self.log:
            self.logWarning("Clearing log *LOG MAY END HERE*", self.LOG_NODETAIL)
            self.log = None


    def logThis(self, message, priority):
        """
        The logThis function is used to log the messages in a file or print it on console.
        
        :param self: Used to access the class attributes.
        :param message: Used to pass the message that needs to be logged.
        :param priority: Used to determine if a message should be logged.
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
        
        :param self: Used to access the class attributes.
        :param message: Used to pass the message that needs to be logged.
        :param priority: Used to determine if a message should be logged or not.
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
        
        :param self: Used to access the class variables.
        :param message: Used to store the error message.
        :param priority: Used to determine which messages are logged and which aren't.
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
        
        :param self: Used to access the class attributes.
        :param message: Used to pass the message that needs to be logged.
        :param priority: Used to determine the level of detail in the log.
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
        
        :param self: Used to refer to the object instance.
        :param progress=False: Used to turn off the progress bar.
        :param **kwargs: Used to pass a variable number of keyword arguments to a function.
        :return: a list of speeches.
        :doc-author: Trelent
        """
        '''Retrieve speeches from API'''
        
        self.logThis("Attempting to fetch a SpeechGroup", self.LOG_MEDDETAIL)
        # get the results from the speeches endpoint
        results = self.getPagedJSON('speeches', dict(**kwargs), progress=progress)
        
        # convert to Speech objects
        speeches = _SpeechGroup([self.indexedSpeech(s) for s in results], api=self)

        self.logThis("Successfully retrieved a list of speeches", self.LOG_MEDDETAIL)
        
        return speeches


    def getClusters(self, progress=False, **kwargs):
        """
        The getClusters function retrieves the clusters from the API and returns them as a list of Cluster objects.
        
        :param self: Used to access the API object's properties.
        :param progress=False: Used to turn off the progress bar.
        :param **kwargs: Used to pass a variable number of keyword arguments to a function.
        :return: a list of clusters.
        :doc-author: Trelent
        """
        '''Retrieve speech clusters from API'''
        self.logThis("Attempting to fetch a ClusterGroup", self.LOG_MEDDETAIL)
                
        # get the results from the clusters endpoint
        results = self.getPagedJSON('clusters', dict(**kwargs), progress=progress)
        
        # convert to Clusters objects
        clusters = _SpeechClusterGroup([self.indexedSpeechCluster(s) for s in results], api=self)
        self.logThis("Successfully retrieved a list of clusters", self.LOG_MEDDETAIL)
        
        return clusters

    
    def getCharacters(self, progress=False, **kwargs):
        """
        The getCharacters function retrieves a list of characters from the Marvel API.
        
        :param self: Used to refer to the object instance itself.
        :param progress=False: Used to tell the function to not display a progress bar.
        :param **kwargs: Used to pass a variable number of arguments to a function.
        :return: a list of _Character objects.
        :doc-author: Trelent
        """
        '''Retrieve characters from API'''
        self.logThis("Attempting to fetch a CharactersGroup", self.LOG_MEDDETAIL)
        
        # get the results from the characters endpoint
        results = self.getPagedJSON('characters', dict(**kwargs), progress=progress)
        
        # convert to Character objects
        characters = _CharacterGroup([self.indexedCharacter(c) for c in results], api=self)
        self.logThis("Successfully retrieved a list of characters", self.LOG_MEDDETAIL)
        
        return characters


    def getWorks(self, progress=False, **kwargs):
        """
        The getWorks function is used to fetch works from the API.
        
        :param self: Used to refer to the object itself.
        :param progress=False: Used to tell the function whether or not to print out a progress bar.
        :param **kwargs: Used to pass a dictionary of key-value pairs to the API.
        :return: a WorkGroup object.
        :doc-author: Trelent
        """
        '''Fetch works from the API'''
        self.logThis("Attempting to fetch a WorksGroup", self.LOG_MEDDETAIL)
        
        results = self.getPagedJSON('works', dict(**kwargs), progress=progress)

        works = _WorkGroup([self.indexedWork(w) for w in results], api=self)
        self.logThis("Successfully retrieved a list of works", self.LOG_MEDDETAIL)
        return works


    def getAuthors(self, progress=False, **kwargs):
        """
        The getAuthors function is used to retrieve a list of authors from the API.
        
        :param self: Used to access the API object's properties.
        :param progress=False: Used to tell the function not to display a progress bar.
        :param **kwargs: Used to pass keyworded variable length of arguments to a function.
        :return: a _AuthorGroup object.
        :doc-author: Trelent
        """
        '''Fetch authors from the API'''
        self.logThis("Attempting to fetch a AuthorGroup", self.LOG_MEDDETAIL)

        results = self.getPagedJSON('authors', dict(**kwargs), progress=progress)

        authors = _AuthorGroup([self.indexedAuthor(a) for a in results], api=self)
        self.logThis("Successfully retrieved a list of authors", self.LOG_MEDDETAIL)
        return authors


    def getInstances(self, progress=False, **kwargs):
        """
        The getInstances function specifically accomplishes the following:
            1.
        
        :param self: Used to access the class variables.
        :param progress=False: Used to specify if the function should display a progress bar.
        :param **kwargs: Used to pass a variable number of keyword arguments to the function.
        :return: a list of dictionaries.
        :doc-author: Trelent
        """
        '''Fetch character instances from the API'''  
        self.logThis("Attempting to fetch a CharacterInstanceGroup", self.LOG_MEDDETAIL)  
        results = self.getPagedJSON('instances', dict(**kwargs), progress=progress)

        instances = _CharacterInstanceGroup([self.indexedCharacterInstance(i) for i in results], api=self)
        self.logThis("Successfully retrieved a list of character instances", self.LOG_MEDDETAIL)
        return instances
        
    
    def indexedAuthor(self, data):
        """
        The indexedAuthor function creates an author object from the data that is passed to it.
        
        :param self: Used to access the class variables.
        :param data: Used to pass the data from the API to this function.
        :return: a new author object if the id doesn't exist in the index, and an existing object if it does.
        :doc-author: Trelent
        """
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
        """
        The indexedWork function creates a new work object and adds it to the index.
        
        :param self: Used to access the class attributes.
        :param data: Used to pass the work data to the Work class.
        :return: the work if it is already in the index.
        :doc-author: Trelent
        """
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
        """
        The indexedSpeech function creates a speech object from the data that is passed to it.
        
        :param self: Used to reference the class instance.
        :param data: Used to pass the speech data to the Speech class.
        :return: the speech object that is created.
        :doc-author: Trelent
        """
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
        """
        The indexedSpeechCluster function is used to create a speech cluster in the index. 
        If the ID of the speech cluster is already present in the index, it will fetch that object from cache. 
        Otherwise, it will create a new SpeechCluster object and add it to both memory and disk cache.
        
        :param self: Reference the class instance
        :param data: Pass the data from the api call
        :return: A speechcluster object
        :doc-author: Trelent
        """
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
        """
        The indexedCharacter function is used to create a character in the index. If the character already exists, it is recycled and returned.
        Otherwise, a new Character object is created with the data passed in as an argument.
        
        :param self: Reference the class instance
        :param data: Pass in the json data for the character
        :return: A character object
        :doc-author: Trelent
        """
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
        """
        The indexedCharacterInstance function is used to create a character instance in the index. If the character instance already exists, it is fetched from the index.
        
        
        :param self: Access the api object's properties
        :param data: Pass the data from the api to characterinstance
        :return: A characterinstance object
        :doc-author: Trelent
        """
        '''Create a character instance in the index'''
        
        if data['id'] in self._characterinstance_index:
            c = self._characterinstance_index[data['id']]
            self.logThis("Fetching character instance with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        else:
            c = CharacterInstance(data, api=self, index=True)
            self._characterinstance_index[data['id']] = c
            self.logThis("Creating new character instance with ID " + str(data['id']), self.LOG_HIGHDETAIL)
        
        return c