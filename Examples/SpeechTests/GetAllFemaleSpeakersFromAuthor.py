from dicesapi import DicesAPI, FilterParams

api = DicesAPI(logfile="./src/GetAllFemaleSpeakersFromAuthor.log") #Create a link to the API

speeches = api.getSpeeches(author_name="Homer")

femaleSpeakers = speeches.getSpkrs().filterGenders(FilterParams.CHARACTER_GENDER_FEMALE)
#print(len(femaleSpeakers))

for x in femaleSpeakers:
    print(x.getName())
