import csv
import re
from enum import Enum
from html.parser import HTMLParser

__author__ = 'Sarang'

debug = True


# MyHTMLParser extends the HTMLParser class

class MyHTMLParser(HTMLParser):
    def error(self, message):
        pass

    def __init__(self):
        super().__init__()
        # parsing fields
        self.inDesc = False
        self.inName = False
        self.inP = False
        self.inTitle = False
        # other fields
        self.nOfP = 0
        self.classes = []
        self.cseClass = CSEClass()

    def handle_starttag(self, tag, attrs):
        if tag == "a" and not self.inP:
            # class code before paragraph
            self.cseClass = CSEClass()
            self.parse_code(attrs[0][1])
        elif tag == "p":
            # entered a new class paragraph
            self.inP = True
        elif tag == "b" and self.inP:
            # set name
            self.inName = True

    def handle_data(self, data):
        if self.inName:
            self.parse_name(data)
        elif self.inDesc:
            self.parse_description(data)

    def handle_endtag(self, tag):
        if tag == "p" and self.inP:
            # Finished reading a single class
            self.classes.append(self.cseClass)
            self.nOfP += 1
            self.inP = False
        elif tag == "b" and self.inP:
            # set name of class
            self.inName = False
            if not self.inDesc:
                # start of description paragraph
                self.inDesc = True
        elif tag == "end":
            # finished file
            print('Finished!')
        elif tag == "a" and self.inDesc:
            # finished description paragraph
            self.inDesc = False

    def parse_name(self, name):
        """Parses the name of the class.
        :param name:
        """
        self.cseClass.name = name

    def parse_code(self, name):
        code = re.findall(r'\d+', name)
        self.cseClass.code = code[0]

    def parse_description(self, desc):
        self.cseClass.description = desc
        # 1. Check if the class has prereqs
        try:
            setup = desc[desc.index("Prereq"):]
        except ValueError:
            # No prerequisites
            self.cseClass.pre_reqs = "None"
            if debug:
                print("None")
            return

        # 2. Extract actual prereq string
        try:
            # TODO: Handle not ending with a period (not terribly necessary)
            # There is other text after the prerequisite
            end_index = setup.index(". ")
        except ValueError:
            # Prereq is the last thing in the description
            end_index = len(setup) - 1
        setup = setup[(setup.index(" ") + 1):end_index]

        # 3. Parse out individual pre_reqs
        prs = setup.split("; ")
        pre_reqs = []
        for pr in prs:
            if debug:
                print(pr)
            # Convert from string to object
            pre_req = PreRequisite(pr)
            pre_reqs.append(pre_req)
            if debug:
                pre_req.print()


class Timing(Enum):
    pre = 0
    conc = 1
    

class PROperator(object):
    def __init__(self, opType, *ops):
        self.operands = ops
        self.opType = opType
    
    def add(self, op):
        operands.append(op)
        


class PreRequisite(object):
    def __init__(self, pr):
        self.equiv = False
        self.timing = Timing.pre
        self.min_gpa = None
        self.code = ""
        self.pr = pr
        self.parse()

    def parse(self):
        try:
            # REGULAR PREREQS
            # First, check to see if the prereq ends in a number
            code = int(self.pr[len(self.pr) - 3:])
            regular = True
            # Then, check to see if the text before the numbers are only caps
            for i in self.pr:
                if i != " " and i.islower():
                    regular = False
                    break
            if regular:
                self.code = code
                return
        except ValueError:
            pass

        # MIN GPA

    def print(self):
        print(self.code)


class CSEClass(object):
    def __init__(self):
        super().__init__()
        self.code = 0
        self.name = ""
        self.description = ""
        self.pre_reqs = []

    @property
    def __str__(self):
        string = ("CODE: " + str(self.code))
        string += ("\nNAME: " + self.name)
        string += ("\nDESC: " + self.description)
        string += ("\nPREREQS: " + str(self.pre_reqs))
        return string


f = open('cse.html')
s = f.read()

parser = MyHTMLParser()
parser.feed(s)

# print(parser.classes[4].description)

csv_file = open('csecourses.csv', 'w', newline='')
csv_writer = csv.writer(csv_file)

csv_writer.writerow(['Code', 'Name', 'Description'])
for x in parser.classes:
    csv_writer.writerow([x.code, x.name, x.description])