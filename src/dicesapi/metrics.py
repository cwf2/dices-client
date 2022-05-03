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
        """
        The countInterruptions function counts the number of interruptions in a cluster.
        
        :param self: Used to store the API object.
        :param cluster: Used to get the speeches from a cluster.
        :return: the number of interruptions in the cluster.
        :doc-author: Trelent
        """
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
        """
        The countReplies function counts the number of replies in a cluster.
        
        :param self: Used to access the API object.
        :param cluster: Used to get the speeches from a cluster.
        :return: the number of replies in a cluster.
        :doc-author: Trelent
        """
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
        """
        The countSpeakers function counts the number of speakers in a cluster.
        
        :param self: Used to access the API object.
        :param cluster: Used to get the speeches from a cluster.
        :return: the number of speakers in a cluster.
        :doc-author: Trelent
        """
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
        """
        The countAddresees function counts the number of speeches in a cluster that are replies to other speeches.
        
        :param self: Used to access the API object.
        :param cluster: Used to get the speeches in that cluster.
        :return: a number that is the count of speeches in a cluster.
        :doc-author: Trelent
        """
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
        """
        The isOneSided function is used to determine whether a conversation is one sided.
        
        :param self: Used to access the DicesAPI class.
        :param cluster: Used to get the speeches from a given cluster.
        :return: a boolean value.
        :doc-author: Trelent
        """
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
        """
        The isMonologue function is used to determine whether a conversation is a monologue.
        
        :param self: Used to refer to the object instance itself.
        :param cluster: Used to pass a SpeechCluster object to the function.
        :return: True if the conversation is a monologue.
        :doc-author: Trelent
        """
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

    def doesInterruption(self, cluster, character):
        """
        The doesInterruption function specifically checks if the speaker is interrupting another speaker.
        
        :param self: Used to access the API class.
        :param cluster: Used to get the speeches from a cluster.
        :param character: Used to check if the speaker is interrupting.
        :return: True if the character object is a speaker and the cluster has an interruption, False otherwise.
        :doc-author: Trelent
        """
        self.api.logThis("Checking if speaker interrupts")
        if not isinstance(cluster, dicesapi.SpeechCluster):
            self.api.logCritical("Could not check if speaker interrupts as a SpeechCluster was not provided", dicesapi.DicesAPI.LOG_LOWDETAIL)
            return self.ERROR_VALUE
        if not isinstance(character, dicesapi.CharacterInstance):
            self.api.logCritical("Could not check if speaker interrupts as a Character Instance was not provided", dicesapi.DicesAPI.LOG_LOWDETAIL)
            return self.ERROR_VALUE
        speeches = self.api.getSpeeches(cluster_id=cluster.id)
        for speech in speeches:
            if character in speech.spkr and speech.isInterruption():
                return True
        return False

        

    #Float Values

    def speakerPriority(self, cluster, speaker):
        """
        The speakerPriority function is used to determine the priority of a speaker in a speech cluster.
        
        :param self: Used to access the API.
        :param cluster: Used to get the speeches from that cluster.
        :param speaker: Used to check whether the speaker of a given speech is the same as the one provided.
        :return: the number of times the speaker has spoken in the cluster.
        :doc-author: Trelent
        """
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
        """
        The speechBalance function is used to determine the number of speakers compared to the number of addressees.
        
        :param self: Used to access the API object.
        :param speech: Used to get the speech balance.
        :return: the balance of the speech, or -1 if there was an error.
        :doc-author: Trelent
        """
        self.api.logThis("Determining speech balance", dicesapi.DicesAPI.LOG_MEDDETAIL)
        if not isinstance(speech, dicesapi.Speech):
            self.api.logCritical("Could not get speech balance as a Speech was not provided", dicesapi.DicesAPI.LOG_LOWDETAIL)
            return self.ERROR_VALUE
        return len(speech.spkr)/len(speech.addr)