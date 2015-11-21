import csv
import re
from collections import Iterable
from enum import Enum
from html.parser import HTMLParser

__author__ = 'Sarang Joshi'

debug = True


class Timings(Enum):
    pre = 0
    concurrent = 1


class PROperator(object):
    """
    Defines an operator between multiple prerequisites.
    """

    def __init__(self, op_type):
        self.op_type = op_type
        self.operands = []

    def add(self, op):
        self.operands.append(op)

    def __str__(self):
        if self.op_type == "None":
            return "None"
        return_string = str(self.operands[0])
        for i in range(1, len(self.operands)):
            return_string += (" " + self.op_type + " " + str(self.operands[i]))
        return return_string


class PreRequisite(object):
    def __init__(self, pr):
        self.equiv = False
        self.timing = Timings.pre
        self.min_gpa = None
        self.code = ""
        self.pr = pr
        self.parse()

    def parse(self):
        try:
            # REGULAR PREREQS
            # First, check to see if the prereq ends in a number
            code_val = int(self.pr[len(self.pr) - 3:])
            # TODO: generalize to non-CSE
            code = "CSE " + str(code_val)
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
        self.code = "???"

    def __str__(self):
        return self.code


class UWClass(object):
    def __init__(self):
        super().__init__()
        self.department = ""
        self.code = 0
        self.name = ""
        self.description = ""
        self.pre_reqs = None


class CSEClass(UWClass):
    def __init__(self):
        super().__init__()
        self.department = "CSE"

    def __str__(self):
        string = ("CODE: " + self.department + " " + str(self.code))
        string += ("\nNAME: " + self.name)
        string += ("\nDESC: " + self.description)
        string += ("\nPREREQS: " + str(self.pre_reqs))
        return string


class CSEHTMLParser(HTMLParser):
    def error(self, message):
        print("SOMEONE SCREWED UP: " + message)

    def __init__(self):
        super().__init__()
        # parsing fields
        self.inDesc = False
        self.inName = False
        self.inP = False
        self.inTitle = False
        # other fields
        self.nOfP = 0
        # self.classes = []
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
            classes.set(self.cseClass)
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
        # TODO: 7handle department
        self.cseClass.code = code[0]

    def parse_description(self, desc):
        """
        Parses the description of a class into prerequisites.
        :param desc: the description
        """
        self.cseClass.description = desc
        self.setup_pre_reqs(desc)
        if debug:
            print("Prereqs: " + str(self.cseClass.pre_reqs))

    def setup_pre_reqs(self, desc):
        # 1. Check if the class has prereqs
        try:
            setup = desc[desc.index("Prereq"):]
        except ValueError:
            # No prerequisites
            self.cseClass.pre_reqs = PROperator("None")
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
        if len(prs) > 0:
            self.cseClass.pre_reqs = PROperator("and")
        for pr in prs:
            # if debug:
            #     print("Prereq string: " + pr)
            # Convert from string to object and add to class
            self.cseClass.pre_reqs.add(PreRequisite(pr))


class CSEClasses(object):
    def __init__(self):
        self.c_list = {}

    def set(self, cse_class):
        # TODO: Only if CSE
        self.c_list[cse_class.code] = cse_class

    def get(self, code):
        return self.c_list[code]


# SETUP
classes = CSEClasses()

# ALGORITHM
# 1. Go through all classes and just store the description
f = open('cse.html')
s = f.read()

parser = CSEHTMLParser()
parser.feed(s)

# 2. Go through all descriptions and extract prereqs + reverse prereqs
class_list = classes.c_list
for c in sorted(class_list.keys()):
    # print(str(c))
    print(class_list[c])


# print(parser.classes[4].description)

# csv_file = open('csecourses.csv', 'w', newline='')
# csv_writer = csv.writer(csv_file)
#
# csv_writer.writerow(['Code', 'Name', 'Description'])
# for x in parser.classes:
#     csv_writer.writerow([x.code, x.name, x.description])
