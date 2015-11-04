import re

__author__ = 'Sarang'

from html.parser import HTMLParser


# MyHTMLParser extends the HTMLParser class
class MyHTMLParser(HTMLParser):
    def error(self, message):
        pass

    def __init__(self):
        super().__init__()
        self.inName = False
        self.nOfP = 0
        self.inP = False
        self.classes = []
        self.inTitle = False
        self.cseClass = None

    def handle_starttag(self, tag, attrs):
        if (tag == "a" and not self.inP):
            self.cseClass = CSEClass(self.parseCode(attrs[0][1]))
        if (tag == "p"):
            self.inP = True
        if tag == "b" and self.inP:
            # set name
            self.inName = True

    def handle_data(self, data):
        if self.inName:
            self.cseClass.name = self.parseName(data)

    def handle_endtag(self, tag):
        if self.inP and tag == "p":
            # Finished reading a single class
            self.classes.append(self.cseClass)
            self.nOfP += 1
            self.inP = False
        if tag == "b" and self.inP:
            # Set name of class
            self.inName = False
        if tag == "end":
            print(self.nOfP)

    def getclass(self, i):
        return self.classes[i]

    def parseName(self, data):
        return data

    def parseCode(self, name):
        code = re.findall(r'\d+', name)
        return code[0]


class CSEClass(object):
    def __init__(self, code):
        super().__init__()
        self.code = code
        self.name = ""

    def setName(self, name):
        self.name = name

    def __str__(self):
        s = ("CODE: " + str(self.code))
        s += ("\nNAME: " + self.name)
        return s


f = open('cse.html')
s = f.read()

cse351 = CSEClass(351)
print(cse351)

parser = MyHTMLParser()
parser.feed(s)

for x in range(0, len(parser.classes) - 1):
    print(parser.getclass(x))
