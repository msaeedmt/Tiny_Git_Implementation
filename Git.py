import pickle
import os
from User import User


class Git:
    def __init__(self, location):
        self.location = location
        self.users = {}
        self.repositories = {}
        print(self.location)

    def addUser(self, username, password):
        if username in self.users:
            print("username exists")
            return False

        self.users[username] = password

        path = os.path.join(self.location, username)
        os.makedirs(path, exist_ok=True)

        OUser = User(path, username)
        userFilePath = os.path.join(path, username)
        userFile = open(userFilePath, 'wb')
        pickle.dump(OUser, userFile)
        userFile.close()

        return True

    def login(self, username, password):
        if username not in self.users.keys():
            return False
        if self.users[username] == password:
            return True

        return False

    def getRepoPath(self, repoName):
        if repoName not in self.repositories.keys():
            print('repoitory not exists!')
            return None

        path = os.path.join(self.location, self.repositories[repoName], repoName)
        return path

    def getUserPath(self, username):
        if username not in self.users.keys():
            print("username not exists")
            return None

        path = os.path.join(self.location, username)
        return path

    def getUserObject(self, username):
        userFilePath = os.path.join(self.getUserPath(username), username)

        userFile = open(userFilePath, 'rb')
        user = pickle.load(userFile)
        userFile.close()
        print(user.repositories)

        return user

