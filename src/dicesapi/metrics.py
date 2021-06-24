import dicesapi


class Metrics(object):

    ERROR_VALUE = "CoolrooWasHere"

    def __init__(self, api):
        if api is None or not isinstance(api, dicesapi.DicesAPI):
            raise ValueError
        else:
            api.logThis("Metrics object created", dicesapi.DicesAPI.LOG_LOWDETAIL)

    #Cluster Functions

    #Int values
    def countInterruptions(self, cluster):
        self.api.logThis("Counting Interruptions from a cluster", dicesapi.DicesAPI.LOG_MEDDETAIL)
        if not isinstance(cluster, dicesapi.SpeechCluster):
            self.api.logCritical("Could not count interruptions as a SpeechCluster was not provided", dicesapi.DicesAPI.LOG_LOWDETAIL)
            return self.ERROR_VALUE
        speeches = self.api.getSpeeches(cluster_id=cluster.id)
        interruptions = 0
        prevAddr = []
        for speech in speeches:
            if not any(responder in speech.spkr for responder in prevAddr):
                interruptions += 1
            prevAddr = speech.addr
        return interruptions

    def countReplies(self, cluster):
        self.api.logThis("Counting Replies from a cluster", dicesapi.DicesAPI.LOG_MEDDETAIL)
        if not isinstance(cluster, dicesapi.SpeechCluster):
            self.api.logCritical("Could not count replies as a SpeechCluster was not provided", dicesapi.DicesAPI.LOG_LOWDETAIL)
            return self.ERROR_VALUE
        speeches = self.api.getSpeeches(cluster_id=cluster.id)
        interruptions = 0
        prevAddr = []
        for speech in speeches:
            if not any(responder in speech.spkr for responder in prevAddr):
                interruptions += 1
            prevAddr = speech.addr
        return interruptions

    def countSpeakers(self, cluster):
        self.api.logThis("Counting speakers in a cluster", dicesapi.DicesAPI.LOG_MEDDETAIL)
        if not isinstance(cluster, dicesapi.SpeechCluster):
            self.api.logCritical("Could not count speakers as a SpeechCluster was not provided", dicesapi.DicesAPI.LOG_LOWDETAIL)
            return self.ERROR_VALUE
        speeches = self.api.getSpeeches(cluster_id=cluster.id)
        speakers = 0
        for speech in speeches:
            speakers += len(speech.spkr)
        return speakers
    
    def countAddresees(self, cluster):
        self.api.logThis("Counting speakers in a cluster", dicesapi.DicesAPI.LOG_MEDDETAIL)
        if not isinstance(cluster, dicesapi.SpeechCluster):
            self.api.logCritical("Could not count replies as a SpeechCluster was not provided", dicesapi.DicesAPI.LOG_LOWDETAIL)
            return self.ERROR_VALUE
        speeches = self.api.getSpeeches(cluster_id=cluster.id)
        addressees = 0
        for speech in speeches:
            addressees += len(speech.addr)
        return addressees

    #Boolean Returns

    def isOneSided(self, cluster):
        self.api.logThis("Determining whether conversation is one sided", dicesapi.DicesAPI.LOG_MEDDETAIL)
        if not isinstance(cluster, dicesapi.SpeechCluster):
            self.api.logCritical("Could not determine one sidedness as a SpeechCluster was not provided", dicesapi.DicesAPI.LOG_LOWDETAIL)
            return self.ERROR_VALUE
        addressees = []
        speeches = self.api.getSpeeches(cluster_id=cluster.id)
        for speech in speeches:
            if any(speaker in speech.spkr for speaker in addressees):
                return False
            addressees.extend(speech.addr)
            addressees = list(set(addressees))
        return True

    def isMonologue(self, cluster):
        self.api.logThis("Determining whether conversation is a monologue", dicesapi.DicesAPI.LOG_MEDDETAIL)
        if not isinstance(cluster, dicesapi.SpeechCluster):
            self.api.logCritical("Could not determine if cluster is a monologue as a SpeechCluster was not provided", dicesapi.DicesAPI.LOG_LOWDETAIL)
            return self.ERROR_VALUE
        speeches = self.api.getSpeeches(cluster_id=cluster.id)
        if(len(speeches) == 0):
            self.api.logWarning("Cluster did not contain any speeches", dicesapi.DicesAPI.LOG_LOWDETAIL)
            return False
        if(len(speeches[0].spkr) != 1):
            return False
        speaker = speeches[0].spkr[0]
        for speech in speeches:
            if len(speech.spkr) != 1 or speech.spkr[0] is not speaker:
                return False
        return True


    #Float Values

    def speakerPriority(self, cluster, speaker):
        self.api.logThis("Checking speaker priority", dicesapi.DicesAPI.LOG_MEDDETAIL)
        if not isinstance(cluster, dicesapi.SpeechCluster):
            self.api.logCritical("Could not get speaker priority as a SpeechCluster was not provided", dicesapi.DicesAPI.LOG_LOWDETAIL)
            return self.ERROR_VALUE
        if not isinstance(speaker, dicesapi.CharacterInstance):
            self.api.logCritical("Could not get speaker priority as a Character Instance was not provided", dicesapi.DicesAPI.LOG_LOWDETAIL)
            return self.ERROR_VALUE
        speeches = self.api.getSpeeches(cluster_id=cluster.id)
        speaking = 0
        for speech in speeches:
            speaking += 1 if speaker in speech.spkr else 0
        return speaking/len(speeches)


    #Speech Functions
    
    def speechBalance(self, speech):
        self.api.logThis("Determining speech balance", dicesapi.DicesAPI.LOG_MEDDETAIL)
        if not isinstance(speech, dicesapi.Speech):
            self.api.logCritical("Could not get speech balance as a Speech was not provided", dicesapi.DicesAPI.LOG_LOWDETAIL)
            return self.ERROR_VALUE
        return len(speech.spkr)/len(speech.addr)