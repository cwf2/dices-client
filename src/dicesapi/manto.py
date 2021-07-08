'''manto - tools for interacting with the MANTO database
'''
import requests
import dicesapi


MANTO_API = 'https://resource.manto.unh.edu'
NGID = '6580' # nodegoat project number
DEBUG = True

__manto_index__ = {}


class Tie():
    '''Collection of values for MANTO ties'''
    SON = '31764'
    DAUGHTER = '31765'


class MantoEntity(object):
    '''Basic MANTO entity'''
    
    def __init__(self, id, data=None):
        self.id = id
        if data is None:
            data = {}
        self._populate_from_data(data)

    def __repr__(self):
        tag = f'{self.id}'
        if self.name is not None:
            tag += f': {self.name}'
        return f'<MANTO Entity {tag}>'
    
    def _populate_from_data(self, data):
        '''Set attributes from JSON data'''
        
        # throw away a couple outer layers, save everything else
        self.data = data.get('data', {}).get('objects', {}).get(self.id, {})

        # set name
        self.name = self.data.get('object', {}).get('object_name')
        if self.name is not None:
            self.name = self.name.strip()
        
    def force_download(self, api=MANTO_API, debug=DEBUG):
        '''Re-download data from MANTO and overwrite existing attributes'''
        data = dlMantoData(self.id, MANTO_API, debug)
        self._populate_from_data(data)
            
    def getAltNames(self):
        '''Return MANTO "Alternate Names" field'''
        def_vals = self.data.get('object_definitions', {}
                        ).get('object_definition_value', {})
        alt_names = def_vals.get('18817')
        return(alt_names)

    def getTies(self, ties):
        '''Retrieve a set of entities having a given tie to self'''        
        results = []
        
        if not isinstance(ties, list):
            ties = [ties]

        for tie in ties:
            objs = self.data.get('object_definitions', {}
                            ).get(tie, {}
                            ).get('object_definition_ref_object_id', {}
                            ).get(NGID, {})
            for ent_id in objs:
                results.append(getMantoID(ent_id))
        
        return results

    def getParents(self):
        return self.getTies([Tie.SON, Tie.DAUGHTER])

    def isChildOf(self, other):
        return other in self.getParents()
        
    def isParentOf(self, other):
        return self in other.getParents()


def dlMantoData(manto_id, api=MANTO_API, debug=DEBUG):
    '''Retrieve a character's record from MANTO'''

    # this is the trick to getting JSON data from MANTO's API
    headers = {'Accept': 'application/json'}

    # make request
    res = requests.get(f'{api}/{manto_id}', headers=headers)

    # check results
    if res.ok:
        data = res.json()
        if 'error' in data:
            error = data.get('error')
            descr = data.get('error_description')
            if debug:
                print(f'Failed to retrieve MANTO id {manto_id}: {error} / {descr}')
        return data
    else:
        if debug:
            print(f'Failed to retrieve MANTO id {manto_id}: HTTP status: {res.status}')


def getMantoID(manto_id, cache_empty=False):
    '''Retrieve MANTO entity by ID'''
    
    if manto_id in __manto_index__:
        manto_ent = __manto_index__[manto_id]
    else:
        data = dlMantoData(manto_id)
        manto_ent = MantoEntity(manto_id, data)
        if (manto_ent.data != {}) or cache_empty:
            __manto_index__[manto_id] = manto_ent 
    
    return manto_ent


def getMantoChar(char, debug=DEBUG, cache_empty=False):
    '''Retrieve MANTO entity from DICES Character or CharacterInstance'''

    # if passed CharacerInstance instead of Character,
    #     try to resolve to underlying character
    if isinstance(char, dicesapi.CharacterInstance):
        if char.char is None:
            if debug:
                print(f'Can\'t get MANTO data: {char} is an anonymous CharacterInstance')
            return None
        else:
            char = char.char
    
    # check that manto id is present
    if char.manto is None or len(char.manto) == 0:
        if debug:
            print(f'Can\'t get MANTO data: {char} has no MANTO id')
        return None
    
    manto_ent = getMantoID(char.manto, cache_empty=cache_empty)
    return manto_ent
        

def charIsMantoTie(char_a, char_b, ties, err_val=None, debug=DEBUG):
    '''Compare two DICES Character instances based on MANTO ties'''
    
    ent_a = getMantoChar(char_a, debug=debug)
    ent_b = getMantoChar(char_b, debug=debug)
    
    if ent_a and ent_b:
        valid = ent_a.getTies(ties)
        return ent_b in valid
    else:
        return err_val
    

def charIsChild(char_a, char_b, err_val=None, debug=DEBUG):
    '''True if char_b is one of char_a's parents'''
    return CharIsMantoTie(char_a, char_b, [Tie.SON, Tie.DAUGHTER], err_val, debug=debug)