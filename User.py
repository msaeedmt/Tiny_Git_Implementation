import os
import pickle
from Repository import Repository


class User:
    def __init__(self, location, username):
        self.username = username
        self.location = location
        self.repositories = {}

    def createRepo(self, repoName, isPrivate):
        print(self.repositories)
        if repoName in self.repositories:
            print("repository already exists!")
            return False

        self.repositories[repoName] = isPrivate
        userFilePath = os.path.join(self.location, self.username)
        userFile = open(userFilePath, 'wb')
        pickle.dump(self, userFile)
        userFile.close()

        path = os.path.join(self.location, repoName)
        os.makedirs(path, exist_ok=True)

        oRepo = Repository(path, repoName, isPrivate, self.username)
        repoFilePath = os.path.join(path, repoName)
        repoFile = open(repoFilePath, 'wb')
        pickle.dump(oRepo, repoFile)
        repoFile.close()

        return True

    def getRepoPath(self, repoName):
        if repoName not in self.repositories.keys():
            print("repository not exists!")
            return None

        path = os.path.join(self.location, repoName)
        return path

    def getRepo(self, repoName):
        repoFilePath = os.path.join(self.getRepoPath(repoName), repoName)

        repoFile = open(repoFilePath, 'rb')
        repo = pickle.load(repoFile)
        repoFile.close()

        return repo

    def addContributer(self, username, repoName):
        foundedRepo = self.getRepo(repoName)
        if foundedRepo == None:
            print("Repo not found")
            return
        foundedRepo.contributers.add(username)
