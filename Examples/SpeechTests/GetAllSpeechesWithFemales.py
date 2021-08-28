from dicesapi import DicesAPI, _DataGroup, FilterParams

def filterFunc(thing):
    return any(char.gender == FilterParams.CHARACTER_GENDER_FEMALE for char in thing.spkr) or any(char == FilterParams.CHARACTER_GENDER_FEMALE for char in thing.addr)


api = DicesAPI()


speeches = api.getSpeeches()

#femaleChars = _DataGroup.unionize(speeches.getSpkrs().filterGenders(FilterParams.CHARACTER_GENDER_FEMALE), speeches.getAddrs().filterGenders(FilterParams.CHARACTER_GENDER_FEMALE), api, False)
femaleSpeeches = speeches.advancedFilter(lambda thing : any(char.gender == FilterParams.CHARACTER_GENDER_FEMALE for char in thing.spkr) or any(char == FilterParams.CHARACTER_GENDER_FEMALE for char in thing.addr))

print("Number of Speeches that contain a female is " + str(len(femaleSpeeches)))

