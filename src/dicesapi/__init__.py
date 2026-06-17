import requests
import pandas as pd
import logging
import csv
import re

# Module logger. Following standard library practice, this module does not
# configure any handlers of its own -- by default, messages simply go
# nowhere. Users who want to see DICES log messages should configure logging
# themselves, e.g.:
#
#     import logging
#     logging.basicConfig(level=logging.INFO)
#
logger = logging.getLogger('dicesapi')
logger.addHandler(logging.NullHandler())


def _assign_fields(obj, data, fields):
    '''Copy each field present in `data` onto the same-named attribute of `obj`

    Used by model classes' `_from_data` methods for simple scalar fields.
    Fields that need special handling (e.g. nested objects) should be
    excluded here and handled separately.
    '''

    for field in fields:
        if field in data:
            setattr(obj, field, data[field])


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
            raise ValueError("Could not create a datagroup with no API")
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
            logger.warning("Cannot add two datagroups of different classes")
    

    def __add__(self, other):
        if(isinstance(other, self.__class__)):
            thing = type(self)([x for x in self._things], self.api)
            thing.extend(other)
            return thing
        else:
            logger.warning("Cannot add two datagroups of different classes")
    

    def __isub__(self, other):
        if(isinstance(other, self.__class__)):
            self._things = [thing for thing in self._things if thing not in other._things] 
        else:
            logger.warning("Cannot subtract two datagroups of different classes")
    

    def __sub__(self, other):
        if(isinstance(other, self.__class__)):
            return type(self)([thing for thing in self._things if thing not in other._things], self.api)
        else:
            logger.warning("Cannot subtract two datagroups of different classes")
    
    
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

        logger.debug("Attempting to extend a " + self.__class__.__name__[1:])  
        if(isinstance(datagroup, self.__class__)):
            self._things.extend(datagroup._things)
            if(not duplicates):
                self._things = list(set(self._things))
        else:
            logger.warning("Could not extend the given datagroup because of conflicting classes, skipping")


    def intersect(self, other):
        """Return a new DataGroup containing items common to self, other

        Args:
            other (DataGroup): The data group to intersect with
        
        Returns: 
            A new DataGroup.
        """
        
        logger.debug("Attempting to intersect a " + self.__class__.__name__[1:])
        if(isinstance(other, self.__class__)):
            return type(self)([thing for thing in self if thing in other], self.api)
        else:
            logger.warning("Could not intersect the given datagroup because of conflicting classes, skipping")
            return type(self)([], self.api)


    def filterAttribute(self, attribute, value):
        """Returns a subset of the DataGroup based on an attribute

        Args:
            attribute (str): Used to specify the attribute that will be used for filtering.
            value: Used to specify the value to filter for.

        Returns:
        """

        logger.debug("Filtering " + self.__class__.__name__[1:] + " for attributes")
        newlist = []
        for thing in self._things:
            if attribute in thing._attributes and thing._attributes[attribute] == value:
                newlist.append(thing)
        #return self.__init__(newlist)
        if len(newlist) == 0:
            logger.warning("Filtering on attribute [" + str(attribute) + "] searching for the value [" + str(value) + "] yielded no results")
        return type(self)(newlist, self.api)
    

    def filterList(self, attribute, values):
        """Returns objects in this DataGroup for which an attribute matches a list of possible values

        Args:
            attribute (str): The attribute that is used for filtering
            values (list): List of allowable values
        
        Returns:
            A new DataGroup
        """

        logger.debug("Filtering " + self.__class__.__name__[1:] + " for members of a list")
        newlist = []
        for thing in self._things:
            if(attribute in thing._attributes and thing._attributes[attribute] in filterList and thing._attributes[attribute] is not None):
                newlist.append(thing)
        if len(newlist) == 0:
            logger.warning("Filtering on attribute [" + str(attribute) + "] yielded no results")
        return type(self)(newlist, self.api)
    

    def deepFilterAttributes(self, attributes, value):
        '''Filters all objects in this DataGroup by filtering the attributes given from a list of attributes (If given ["cluster", "work"] it will check if object->attributes->cluster->work equals the given value)'''

        logger.debug("Deep filtering " + self.__class__.__name__[1:])
        #print("Deep filtering")
        newlist = []
        for thing in self._things:
            filterList = thing._attributes
            success = True
            for attr in attributes:
                if(attr not in filterList):
                    logger.warning("the attribute [" + str(attr) + "] could not be found, skipping this element of the list")
                    success = False
                    #print("Failed")    
                    break
                filterList=filterList[attr]
            if(success and filterList == value):
                newlist.append(thing)
        if len(newlist) == 0:
            logger.warning("Deep filtering for the value [" + str(value) + "] yielded no results")
        return type(self)(newlist, self.api)
    
    
    def advancedFilter(self, filterFunc, **kwargs):
        """Returns objects in this DataGroup based on results of a user-defined function.
        
        Args:
            filterFunc (lambda): Function that takes elements of the DataGroup as its first argument
            **kwargs: Additional keyword arguments to filterFunc.
        
        Returns:
            A new DataGroup.
        """
        logger.debug("Advanced filtering " + self.__class__.__name__[1:])
        newlist = []
        for thing in self._things:
            if filterFunc(thing, **kwargs):
                newlist.append(thing)
        if len(newlist) == 0:
            logger.warning("Advanced filtering yielded no results")
        return type(self)(newlist, self.api)

    def filterBy(self, attr, values, incl_none=False):
        """Return a new group containing items whose `attr` is in `values`

        Args:
            attr (str): Name of the attribute to filter on
            values: Collection of allowed values for `attr`
            incl_none (bool): Include items whose `attr` is None

        Returns:
            A new group of the same type
        """

        label = self.__class__.__name__[1:]
        logger.debug(f"Filtering {label} along '{attr}'")
        newlist = []
        for thing in self._things:
            val = getattr(thing, attr)
            if (val is None and incl_none) or (val is not None and val in values):
                newlist.append(thing)
        if len(newlist) == 0:
            logger.warning(f"Filtering {label} along '{attr}' returned no entries")
        return type(self)(newlist, self.api)

    def pluck(self, attr):
        """Return a list of `attr` values, one for each item in the group"""

        return [getattr(thing, attr) for thing in self._things]

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
        logger.debug("Serializing a " + self.__class__.__name__[1:] + " with " + str(len(headers)) + " headers")
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
            logger.info("A " + self.__class__.__name__[1:] + " has been exported to a CSV file at the path " + filePath)
        


class AuthorGroup(DataGroup):
    '''Datagroup used to hold a list of Authors'''
    PREDEF_HEADERS = ["name"]

    def getIDs(self):
        '''Returns a list of author IDs'''
        return self.pluck('id')


    def getNames(self):
        '''Return a list of the authors names'''
        return self.pluck('name')


    def getWDs(self):
        '''Returns a list of the author WDs'''
        return self.pluck('wd')


    def getUrns(self):
        '''Returns a list of author URNs'''
        return self.pluck('urn')


    def filterNames(self, names, incl_none=False):
        '''Filter the authors by name

        Args:
            names (list): List of names to match
            incl_none (bool): Include None values in the list of names

        Returns:
            A new AuthorGroup
        '''

        return self.filterBy('name', names, incl_none)


    def filterIDs(self, ids, incl_none=False):
        """Filter the authors by ID

        Args:
            ids (list): Author IDs to match
            incl_none (bool): Include None values in the list of IDs

        Returns:
            A new AuthorGroup
        """

        return self.filterBy('id', ids, incl_none)


    def filterWDs(self, wds, incl_none=False):
        """Filter the authors by WikiData ID

        Args:
            wds (list): List of Wikidata IDs to match
            incl_none (bool): Include None values in the list

        Returns:
            A new AuthorGroup
        """

        return self.filterBy('wd', wds, incl_none)


    def filterUrns(self, urns, incl_none=False):
        """Filter the authors by URN

        Args:
            urns (list): List URNs to match
            incl_none (bool): Include None values in the list

        Returns:
            A new AuthorGroup
        """

        return self.filterBy('urn', urns, incl_none)


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
            logger.warning("Cannot compare objects of different classes")
            raise TypeError


    def _from_data(self, data):
        '''populate attributes from data dict'''

        _assign_fields(self, data, ['id', 'name', 'wd', 'urn'])


class WorkGroup(DataGroup):
    '''Datagroup used to hold a list of works'''

    def getIDs(self):
        '''Returns a list of work IDs'''
        return self.pluck('id')


    def getTitles(self):
        '''Returns a list of work titles'''
        return self.pluck('title')


    def getWDs(self):
        '''Returns a list of work WDs'''
        return self.pluck('wd')


    def getURNs(self):
        '''Returns a list of work URNs'''
        return self.pluck('urn')


    def getLangs(self):
        '''Returns a list of work languages'''
        return self.pluck('lang')


    def getAuthors(self, flatten=False):
        '''Returns a list of Authors'''
        auths = self.pluck('author')
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

        return self.filterBy('id', ids, incl_none)


    def filterTitles(self, titles, incl_none=False):
        """Filter the works by title

        Args:
            titles (list): List of titles to match
            incl_none (bool): Include None values in the list.

        Returns:
            A new WorkGroup
        """

        return self.filterBy('title', titles, incl_none)


    def filterWDs(self, wds, incl_none=False):
        """Filter the works by WikiData ID

        Args:
            wds (list): List of WikiData IDs to match
            incl_none (bool): Include None values in the list of things

        Returns:
            A new WorkGroup
        """

        return self.filterBy('wd', wds, incl_none)


    def filterUrns(self, urns, incl_none=False):
        """Filter the works by URN

        Args:
            urns (list): List of URNs to match
            incl_none (bool): Include None values in the list of works.

        Returns:
            A new WorkGroup
        """

        return self.filterBy('urn', urns, incl_none)


    def filterAuthors(self, authors, incl_none=False):
        """Filter the works by author

        Args:
            authors (list): List of Author objects to match
            incl_none (bool): Include None values in the list

        Returns:
            A new WorkGroup
        """

        return self.filterBy('author', authors, incl_none)


    def filterLangs(self, langs, incl_none=False):
        """Filter the works by language

        Args:
            langs (list): List of languages to match
            incl_none (bool): Include None values in the list

        Returns:
            A new WorkGroup
        """

        return self.filterBy('lang', langs, incl_none)


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
            logger.warning("Cannot compare objects of different classes")
            raise TypeError


    def _from_data(self, data):
        '''populate attributes from data dict'''

        _assign_fields(self, data, ['id', 'title', 'wd', 'urn', 'lang'])

        if 'author' in data:
            if self.index:
                self.author = self.api.indexedAuthor(data['author'])
            else:
                self.author = Author(data['author'], api=self.api)
            data['author'] = self.author


class CharacterGroup(DataGroup):
    '''Datagroup used to hold a list of Characters'''
    
    PREDEF_HEADERS = ["name"]

    def getIDs(self):
        '''Returns a list of character IDs'''
        return self.pluck('id')


    def getNames(self):
        '''Returns a list of character names'''
        return self.pluck('name')


    def getBeings(self):
        '''Returns a list of character beings'''
        return self.pluck('being')


    def getNumbers(self):
        '''Returns a list of character numbers'''
        return self.pluck('number')


    def getWDs(self):
        '''Returns a list of character WikiData IDs'''
        return self.pluck('wd')


    def getMantos(self):
        '''Returns a list of character MANTO IDs'''
        return self.pluck('manto')


    def getGenders(self):
        '''Returns a list of character genders'''
        return self.pluck('gender')


    def filterIDs(self, ids, incl_none=False):
        """Filter characters by ID

        Args:
            ids (list): list of IDs to match
            incl_none (bool): Include None values in the list.

        Returns:
            A new CharacterGroup
        """

        return self.filterBy('id', ids, incl_none)


    def filterNames(self, names, incl_none=False):
        """Filter characters by name

        Args:
            names (list): List of names to match
            incl_none (bool): Include None values in the list.

        Returns:
            A new CharacterGroup
        """

        return self.filterBy('name', names, incl_none)


    def filterBeings(self, beings, incl_none=False):
        """Filter characters by `being` attribute

        Args:
            beings (list): list of allowed `being` values
            incl_none (bool): Include None values in the list

        Returns:
            A new CharacterGroup
        """

        return self.filterBy('being', beings, incl_none)


    def filterNumbers(self, numbers, incl_none=False):
        """Filter characters by `number` attribute

        Args:
            numbers (list): List of allowed `number` values
            incl_none (bool): Include None values in the list

        Returns:
            A new CharacterGroup
        """

        return self.filterBy('number', numbers, incl_none)


    def filterWDs(self, wds, incl_none=False):
        """Filter characters by `wd` attribute (WikiData ID)

        Args:
            wds (list): List of allowed WikiData IDs
            incl_none (bool): Include None values in the list

        Returns:
            A new CharacterGroup
        """

        return self.filterBy('wd', wds, incl_none)


    def filterMantos(self, mantos, incl_none=False):
        """Filter characters by `manto` attribute (MANTO ID)

        Args:
            mantos (list): List of allowed MANTO IDs
            incl_none (bool): Include None values in the list

        Returns:
            A new CharacterGroup
        """

        return self.filterBy('manto', mantos, incl_none)


    def filterGenders(self, genders, incl_none=False):
        """Filter characters by `gender` attribute

        Args:
            genders (list): List of allowed `gender` values
            incl_none (bool): Include None values in the list

        Returns:
            A new CharacterGroup
        """

        return self.filterBy('gender', genders, incl_none)


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
            logger.warning("Cannot compare objects of different classes")
            raise TypeError
    

    def _from_data(self, data):
        '''populate attributes from data'''

        _assign_fields(self, data, ['id', 'name', 'being', 'number', 'gender', 'wd', 'manto', 'tt'])


class CharacterInstanceGroup(DataGroup):
    '''Datagroup used to hold a list of Character Instances'''

    PREDEF_HEADERS = ["name"]

    def getIDs(self):
        '''Returns a list of character instance ID's'''
        return self.pluck('id')


    def getContexts(self):
        '''Returns a list of character instance context's'''
        return self.pluck('context')


    def getChars(self, flatten=False):
        '''Returns a list of character instance Character's'''
        chars = self.pluck('char')
        if flatten:
            chars = CharacterGroup(list(set(chars)), api=self.api)
        return chars


    def getDisgs(self):
        '''Returns a list of character instance Disg's'''
        return self.pluck('disg')


    def getAnons(self):
        '''Returns a list of character instance Anon's'''
        return self.pluck('anon')


    def getNames(self):
        '''Returns a list of character instance Name's'''
        return self.pluck('name')


    def getBeings(self):
        '''Returns a list of character instance Being's'''
        return self.pluck('being')


    def getNumbers(self):
        '''Returns a list of character instance Name's'''
        return self.pluck('number')


    def getGenders(self):
        '''Returns a list of character instance Gender's'''
        return self.pluck('gender')


    def filterIDs(self, ids, incl_none=False):
        """Filter character instances by `id` attribute

        Args:
            ids (list): List of allowed `id` values
            incl_none (bool): Include None values in the results

        Returns:
            A new CharacterInstanceGroup
        """

        return self.filterBy('id', ids, incl_none)


    def filterContexts(self, contexts, incl_none=False):
        """Filter character instances by `context` attribute

        Args:
            contexts (list): List of allowed `context` values
            incl_none (bool): Include None values in the results

        Returns:
            A new CharacterInstanceGroup
        """

        return self.filterBy('context', contexts, incl_none)


    def filterChars(self, chars, incl_none=False):
        """Filter character instances by underlying Character

        Args:
            chars (list): List of allowed Character objects
            incl_none (bool): Include None values in the results

        Returns:
            A new CharacterInstanceGroup
        """

        return self.filterBy('char', chars, incl_none)


    def filterNames(self, names, incl_none=False):
        """Filter character instances by `name` attribute

        Args:
            names (list): List of allowed `name` values
            incl_none (bool): Include None values in the results

        Returns:
            A new CharacterInstanceGroup
        """

        return self.filterBy('name', names, incl_none)


    def filterBeings(self, beings, incl_none=False):
        """Filter character instances by `being` attribute

        Args:
            beings (list): List of allowed `being` values
            incl_none (bool): Include None values in the results

        Returns:
            A new CharacterInstanceGroup
        """

        return self.filterBy('being', beings, incl_none)


    def filterNumbers(self, numbers, incl_none=False):
        """Filter character instances by `number` attribute

        Args:
            numbers (list): List of allowed `number` values
            incl_none (bool): Include None values in the results

        Returns:
            A new CharacterInstanceGroup
        """

        return self.filterBy('number', numbers, incl_none)


    def filterGenders(self, genders, incl_none=False):
        """Filter character instances by `gender` attribute

        Args:
            genders (list): List of allowed `gender` values
            incl_none (bool): Include None values in the results

        Returns:
            A new CharacterInstanceGroup
        """

        return self.filterBy('gender', genders, incl_none)


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
        self.gender = None
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
            logger.warning("Cannot compare objects of different classes")
            raise TypeError


    def __repr__(self):
        name = self.name
        if self.char is not None and self.char.name != self.char.name:
            name = f'{self.name}/{self.char.name}'
        return f'<CharacterInstance {self.id}: {name}>'


    def _from_data(self, data):
        '''populate attributes from data'''

        _assign_fields(self, data, ['id', 'context', 'anon', 'name', 'being', 'number', 'gender'])

        if 'char' in data and data['char'] is not None:
            if self.index:
                self.char = self.api.indexedCharacter(data['char'])
            else:
                self.char = Character(data['char'], api=self.api)
            data['char'] = self.char
        if 'disguise' in data:
            # FIXME
            self.disg = data['disguise']

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

    def getIDs(self):
        '''Returns a list of Speech Cluster ID's'''
        return self.pluck('id')


    def filterIDs(self, ids, incl_none=False):
        """Filter speech clusters by ID

        Args:
            ids: List of allowed IDs
            incl_none (bool): Include None values in the results

        Returns:
            A new SpeechClusterGroup
        """

        return self.filterBy('id', ids, incl_none)


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
            logger.warning("Cannot compare objects of different classes")
            raise TypeError

    def __repr__(self):
        incipit = self.getFirstSpeech()
        loc = f'{incipit.work.title} {incipit.l_fi} ff.'
        return f'<SpeechCluster {self.id}: {loc}>'


    def _from_data(self, data):
        '''populate attributes from data'''

        _assign_fields(self, data, ['id', 'type'])

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
                logger.warning(f'API returned no speeches for cluster '
                                    f'{self.id}')
                raise Exception # FIXME
            else:
                self._first = sorted(sgroup._things, key=lambda s: s.part)[0]
                if self._first.part != 1:
                    logger.warning(f'First speech in cluster {self.id} '
                                        f'has part {self._first.part}')
        
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

    def getIDs(self):
        '''Returns a list of Speech IDs'''
        return self.pluck('id')


    def getClusters(self, flatten=False):
        '''Returns a list of Speech Clusters'''
        clusters = self.pluck('cluster')

        if flatten:
            clusters = SpeechClusterGroup(list(set(clusters)), api=self.api)
        return clusters


    def getSeqs(self):
        '''Returns a list of Speech Seqs'''
        return self.pluck('seq')


    def getL_fis(self):
        '''Returns a list of Speech First Lines'''
        return self.pluck('l_fi')


    def getL_las(self):
        '''Returns a list of Speech Last Lines'''
        return self.pluck('l_la')



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
        return self.pluck('part')


    def getTypes(self):
        '''Returns the `type` attrs of member speeches as a list'''
        return self.pluck('type')


    def getWorks(self, flatten=False):
        '''Returns the works of '''

        works = self.pluck('work')
        if flatten:
            works = WorkGroup(list(set(works)), api=self.api)

        return works


    def filterIDs(self, ids, incl_none=False):
        '''Filter on the Speech ID's'''

        return self.filterBy('id', ids, incl_none)


    def filterClusters(self, clusters, incl_none=False):
        '''Filter on the Speech Cluster's'''

        return self.filterBy('cluster', clusters, incl_none)


    def filterSeqs(self, seqs, incl_none=False):
        '''Filter on the Speech Seq's'''

        return self.filterBy('seq', seqs, incl_none)


    def filterL_fis(self, l_fis, incl_none=False):
        '''Filter on the Speech First Line's'''

        return self.filterBy('l_fi', l_fis, incl_none)


    def filterL_ls(self, l_las, incl_none=False):
        '''Filter on the Speech Last Line's'''

        return self.filterBy('l_la', l_las, incl_none)


    def filterSpkrInstances(self, spkrs, incl_none=False):
        '''Filter to speeches with one of `spkrs` among their speaker instances'''

        label = self.__class__.__name__[1:]
        logger.debug(f"Filtering {label} along Speaker Instance's")
        newlist = [thing for thing in self._things if any(c in spkrs for c in thing.spkr)]
        if len(newlist) == 0:
            logger.warning(f"Filtering {label} along Speaker Instance's returned no entries")
        return SpeechGroup(newlist, self.api)


    def filterSpkrs(self, spkrs, incl_none=False):
        '''Filter to speeches with one of `spkrs` among their speakers' underlying Characters'''

        label = self.__class__.__name__[1:]
        logger.debug(f"Filtering {label} along Speaker's")
        newlist = [thing for thing in self._things if any(c.char in spkrs for c in thing.spkr)]
        if len(newlist) == 0:
            logger.warning(f"Filtering {label} along Speaker's returned no entries")
        return SpeechGroup(newlist, self.api)


    def filterAddrInstances(self, addrs, incl_none=False):
        '''Filter to speeches with one of `addrs` among their addressee instances'''

        label = self.__class__.__name__[1:]
        logger.debug(f"Filtering {label} along Addressee Instance's")
        newlist = [thing for thing in self._things if any(c in addrs for c in thing.addr)]
        if len(newlist) == 0:
            logger.warning(f"Filtering {label} along Addressee Instance's returned no entries")
        return SpeechGroup(newlist, self.api)


    def filterAddrs(self, addrs, incl_none=False):
        '''Filter to speeches with one of `addrs` among their addressees' underlying Characters'''

        label = self.__class__.__name__[1:]
        logger.debug(f"Filtering {label} along Addressee's")
        newlist = [thing for thing in self._things if any(c.char in addrs for c in thing.addr)]
        if len(newlist) == 0:
            logger.warning(f"Filtering {label} along Addressee's returned no entries")
        return SpeechGroup(newlist, self.api)


    def filterParts(self, parts, incl_none=False):
        '''Filter on the Speech Part's'''

        return self.filterBy('part', parts, incl_none)


    def filterTypes(self, types, incl_none=False):
        '''Filter on the Speech Type's'''

        return self.filterBy('type', types, incl_none)


    def filterWorks(self, works, incl_none=False):
        '''Filter on the Speech Work's'''

        return self.filterBy('work', works, incl_none)


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
        self.passage = None
        self._attributes = data

        if data:
            self._from_data(data)

        
    def _from_data(self, data):
        '''populate attributes from dict'''

        _assign_fields(self, data, ['id', 'seq', 'l_fi', 'l_la', 'part', 'level', 'type'])

        if 'cluster' in data:
            if self.index:
                self.cluster = self.api.indexedSpeechCluster(data['cluster'])
            else:
                self.cluster = SpeechCluster(data['cluster'], api=self.api)
                data['cluster'] = self.cluster
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
            logger.warning("Cannot compare objects of different classes")
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
    
    
    def getSpkrString(self, sep=', '):
        ''''Returns speaker names as a single string'''
        return sep.join(inst.name for inst in self.spkr)


    def getAddrString(self, sep=', '):
        ''''Returns speaker names as a single string'''
        return sep.join(inst.name for inst in self.addr)

    
    def getCTS(self):
        '''Get the CTS passage corresponding to the speech'''

        # bail out if work has no urn
        if (self.work.urn == '') or (self.work.urn is None):
            return None
        
        # otherwise, try to download
        resolver = self.api.resolver

        try:
            cts = resolver.getTextualNode(self.work.urn, self.l_range)

        except requests.exceptions.HTTPError as e:
            logger.warning("Failed to download self.urn: " + str(e))
            cts = None

        return cts


    def isRepliedTo(self):
        '''True if a later speech in the cluster addresses one of this speech's speakers'''

        SpeechesInCluster = self.api.getSpeeches(cluster_id=self.cluster.id)
        for thing in SpeechesInCluster:
            if(thing.seq > self.seq):
                if(any(responder in thing.spkr for responder in self.addr)):
                    return True
        return False


    def isInterrupted(self):
        '''True if the following speech in the cluster interrupts this one'''

        speech = [speechs for speechs in self.api.getSpeeches(cluster_id=self.cluster.id) if speechs.seq == self.seq + 1]
        return len(speech) > 0 and any(responder in speech[0].spkr for responder in self.addr)

    def isInterruption(self):
        '''True if this speech interrupts the preceding speech in the cluster'''

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
            if len(parts) > 1:
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


    def fetchPassage(self, force=False):
        '''Download the text of this speech from Perseus and store it as self.passage.

        Requires api.initializeCts() to have been called first.
        Returns the Passage object, which is also stored as self.passage.
        '''
        if 'cts_cache' not in self.api.config:
            raise RuntimeError(
                "Text retrieval is not initialized. Call api.initializeCts() first."
            )
        from dicesapi import text
        self.passage = text.getPassage(self, force=force)
        return self.passage


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

    DEFAULT_API = 'http://db.dices.mta.ca/api/'

    # Deprecated `logdetail` levels, retained for backward compatibility with
    # code written against earlier versions of dicesapi. New code should
    # configure the `dicesapi` logger directly, e.g.:
    #
    #     import logging
    #     logging.getLogger('dicesapi').setLevel(logging.INFO)
    #
    LOG_NODETAIL = 0
    LOG_LOWDETAIL = 1
    LOG_MEDDETAIL = 2
    LOG_HIGHDETAIL = 3

    _LOGDETAIL_LEVELS = {
        LOG_NODETAIL: logging.WARNING,
        LOG_LOWDETAIL: logging.INFO,
        LOG_MEDDETAIL: logging.DEBUG,
        LOG_HIGHDETAIL: logging.DEBUG,
    }


    def __init__(self, dices_api=DEFAULT_API, logfile=None,
                    logdetail=None, progress_class=None):
        """Create a connection to the DICES API.

        Args:
            dices_api: Base URL of the DICES API.
            logfile (str): If given, also write log messages to this file.
            logdetail: Deprecated. If given, sets the verbosity of the
                shared `dicesapi` logger (one of the LOG_* constants).
                New code should call
                `logging.getLogger('dicesapi').setLevel(...)` instead.
            progress_class: Optional progress-bar class used by
                `getPagedJSON`.
        """
        self.API = dices_api
        self.config = {}
        if logdetail is not None:
            logger.setLevel(self._LOGDETAIL_LEVELS.get(logdetail, logging.DEBUG))
        if logfile is not None:
            self.createLog(logfile)
        self._ProgressClass = progress_class
        self._work_index = {}
        self._author_index = {}
        self._character_index = {}
        self._characterinstance_index = {}
        self._speech_index = {}
        self._speechcluster_index = {}
        self._tag_index = {}
        self.version = "DEBUG VERSION 1.0"
        logger.info("Database Initialized")


    def initializeCts(self, cts_pattern=None):
        '''Enable text retrieval via the dicesapi.text module.

        Call this before using Speech.fetchPassage(). Optionally pass a custom
        URL pattern with a {cts_urn} placeholder to override the default
        Perseus endpoint.
        '''
        from dicesapi import text
        from dicesapi.text import DEFAULT_CTS_PATTERN
        self.config.setdefault('cts_pattern', cts_pattern or DEFAULT_CTS_PATTERN)
        self.config.setdefault('cts_cache', {})
        logger.info("CTS text retrieval initialized")


    def initializeNlp(self, latin_model=None, greek_model=None):
        '''Enable NLP via the dicesapi.nlp_spacy module.

        Call this before using Passage.runSpacyPipeline(). Optionally pass
        model names to override the defaults (OdyCy for Greek, LatinCy for
        Latin).
        '''
        import dicesapi.nlp_spacy as nlp_spacy
        lat = latin_model or nlp_spacy.SPACY_MODEL_LATIN
        grk = greek_model or nlp_spacy.SPACY_MODEL_GREEK
        self.config.setdefault('nlp', nlp_spacy.spacy_load(lat, grk))
        logger.info("NLP initialized")


    def getPagedJSON(self, endpoint, params=None, progress=False):
        '''Collect paged results from the API'''

        logger.info("Retrieving data from the database")
        
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
            logger.warning(f'Expected {count} results, got {len(results)}!')
        logger.info("Successfully fetched data from the database")
        return results


    def createLog(self, logfile):
        """Add a file handler so log messages are also written to `logfile`.

        Args:
            logfile (str): Path to the log file.
        """
        formatter = logging.Formatter(fmt='%(asctime)s - [%(levelname)s] %(message)s')
        fh = logging.FileHandler(logfile)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.debug("New log created at " + logfile)


    def getSpeeches(self, progress=False, **kwargs):
        '''Retrieve speeches from API'''

        logger.debug("Attempting to fetch a SpeechGroup")
        # get the results from the speeches endpoint
        results = self.getPagedJSON('speeches', dict(**kwargs), progress=progress)
        
        # convert to Speech objects
        speeches = SpeechGroup([self.indexedSpeech(s) for s in results], api=self)

        logger.debug("Successfully retrieved a list of speeches")
        
        return speeches


    def getClusters(self, progress=False, **kwargs):
        '''Retrieve speech clusters from API'''

        logger.debug("Attempting to fetch a ClusterGroup")
                
        # get the results from the clusters endpoint
        results = self.getPagedJSON('clusters', dict(**kwargs), progress=progress)
        
        # convert to Clusters objects
        clusters = SpeechClusterGroup([self.indexedSpeechCluster(s) for s in results], api=self)
        logger.debug("Successfully retrieved a list of clusters")
        
        return clusters

    
    def getCharacters(self, progress=False, **kwargs):
        '''Retrieve characters from API'''

        logger.debug("Attempting to fetch a CharactersGroup")
        
        # get the results from the characters endpoint
        results = self.getPagedJSON('characters', dict(**kwargs), progress=progress)
        
        # convert to Character objects
        characters = CharacterGroup([self.indexedCharacter(c) for c in results], api=self)
        logger.debug("Successfully retrieved a list of characters")
        
        return characters


    def getWorks(self, progress=False, **kwargs):
        '''Fetch works from the API'''

        logger.debug("Attempting to fetch a WorksGroup")
        
        results = self.getPagedJSON('works', dict(**kwargs), progress=progress)

        works = WorkGroup([self.indexedWork(w) for w in results], api=self)
        logger.debug("Successfully retrieved a list of works")
        return works


    def getAuthors(self, progress=False, **kwargs):
        '''Fetch authors from the API'''

        logger.debug("Attempting to fetch a AuthorGroup")

        results = self.getPagedJSON('authors', dict(**kwargs), progress=progress)

        authors = AuthorGroup([self.indexedAuthor(a) for a in results], api=self)
        logger.debug("Successfully retrieved a list of authors")
        return authors


    def getInstances(self, progress=False, **kwargs):
        '''Fetch character instances from the API'''

        logger.debug("Attempting to fetch a CharacterInstanceGroup")
        results = self.getPagedJSON('instances', dict(**kwargs), progress=progress)

        instances = CharacterInstanceGroup([self.indexedCharacterInstance(i) for i in results], api=self)
        logger.debug("Successfully retrieved a list of character instances")
        return instances
        
    
    def indexedAuthor(self, data):
        '''Create an author in the index'''

        # if someone has passed an existing author object
        if isinstance(data, Author):
            if data.id in self._author_index:
                if data is not self._author_index[data.id]:
                    logger.info("Refused to add non-identical duplicate author ID {data.id} to index")
                
            else:
                if data.api is not self:
                    logger.debug("Importing author ID {data.id} from other api {data.api}")
                    data.api = self
                else:
                    logger.debug("Adding a new author with ID {data.id}")
                data.index = True
                self._author_index[data.id] = data
                
            return self._author_index[data.id]
        
        # if someone has passed just an ID
        if isinstance(data, int):
            data = {"id": data}
        
        # otherwise, assume JSON data
        else:
            if data['id'] in self._author_index:
                if len(data) > 1:
                    self._author_index[data['id']]._from_data(data)
                logger.debug("Fetching author with ID " + str(data['id']))
            else:
                logger.debug("Creating new author with ID " + str(data['id']))
                self._author_index[data['id']] = Author(data, api=self, index=True)
 
        return self._author_index[data['id']]


    def indexedWork(self, data):
        '''Create a work in the index'''

        if isinstance(data, int):
            data = {"id": data}
        
        if data['id'] in self._work_index:
            w = self._work_index[data['id']]
            if len(data) > 1:
                w._from_data(data)
            logger.debug("Fetching work with ID " + str(data['id']))
        else:
            w = Work(data, api=self, index=True)
            self._work_index[data['id']] = w
            logger.debug("Creating new work with ID " + str(data['id']))
 
        return w

    
    def indexedSpeech(self, data):
        '''Create a speech in the index'''

        if isinstance(data, int):
            data = {"id": data}
        
        if data['id'] in self._speech_index:
            s = self._speech_index[data['id']]
            if len(data) > 1:
                s._from_data(data)
            logger.debug("Fetching speech with ID " + str(data['id']))
        else:
            s = Speech(data, api=self, index=True)
            self._speech_index[data['id']] = s
            logger.debug("Creating new speech with ID " + str(data['id']))
        return s

        
    def indexedSpeechCluster(self, data):
        '''Create a speech cluster in the index'''

        if isinstance(data, int):
            data = {"id": data}
                
        if data['id'] in self._speechcluster_index:
            s = self._speechcluster_index[data['id']]
            if len(data) > 1:
                s._from_data(data)
            logger.debug("Fetching cluster with ID " + str(data['id']))
        else:
            s = SpeechCluster(data, api=self, index=True)
            self._speechcluster_index[data['id']] = s
            logger.debug("Creating new cluster with ID " + str(data['id']))
        
        return s


    def indexedCharacter(self, data):
        '''Create a character in the index'''

        if isinstance(data, int):
            data = {"id": data}
                
        if data['id'] in self._character_index:
            #print("Recycling character with ID " + str(data['id']))
            c = self._character_index[data['id']]
            if len(data) > 1:
                c._from_data(data)
            logger.debug("Fetching character with ID " + str(data['id']))
        else:
            #print("Adding character with ID " + str(data['id']))
            c = Character(data, api=self, index=True)
            self._character_index[data['id']] = c
            logger.debug("Creating new character with ID " + str(data['id']))
        
        return c


    def indexedCharacterInstance(self, data):
        '''Create a character instance in the index'''

        if isinstance(data, int):
            data = {"id": data}
                
        if data['id'] in self._characterinstance_index:
            c = self._characterinstance_index[data['id']]
            if len(data) > 1:
                c._from_data(data)
            logger.debug("Fetching character instance with ID " + str(data['id']))
        else:
            c = CharacterInstance(data, api=self, index=True)
            self._characterinstance_index[data['id']] = c
            logger.debug("Creating new character instance with ID " + str(data['id']))
        
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
    def fromGitDump(cls, commit):
        '''Create a self-contained dataset from a DB dump saved to GitHub

            Returns a fake DicesAPI with cached data downloaded from Github, specifically, from the file data/speechdb.json
        '''

        api = cls(dices_api="")
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