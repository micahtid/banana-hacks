class User:

    def __init__(self, userID):
        self.userID = userID
        self.dollar = 1000
        self.bc = 1000

    def getUserID(self):
        return self.userID
    
    def getDollar(self):
        return self.dollar
    
    def getBC(self):
        return self.bc
            
    def buyBC(self, amount):
        self.dollar = self.dollar - amount
        self.bc = self.bc + amount
    
    def sellBC(self, amount):
        self.dollar = self.dollar + amount
        self.bc = self.bc - amount
    
