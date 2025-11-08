import numpy as np
import firebase_admin
from firebase_admin import firestore

class Market:
    def __init__(self):
        self.gameID
        self.userIDs = []
        self.totalDollar = 1000000
        self.totalBC = 1000000
        self.price = [self.totalDollar / self.totalBC]

    def addUser(self, userID):
        self.userIDs.append(userID)
        self.totalDollar += 1000
    
    def removeUser(self, userID):
        self.userIDs.remove(userID)
        self.totalDollar -= 1000
    
    def getTotalDollar(self):
        return self.totalDollar
    
    def getTotalBC(self):
        return self.totalBC
    
    def getUserIDs(self):
        return self.userIDs
    
    def getPrice(self):
        return self.price
    
    def updateMarket(self):
        self.price.append(self.totalDollar / self.totalBC)
    


