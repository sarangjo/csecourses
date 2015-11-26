# import csv
import re
from enum import Enum
from html.parser import HTMLParser

__author__ = 'Sarang Joshi'

debug = True


class Timings(Enum):
    pre = 0
    concurrent = 1


class ClassCode(object):
    def __init__(self, department="", num=0):
        self.department = department
        self.num = num

    def __str__(self):
        return self.department + " " + str(self.num)


class PROperator(object):
    """
    Defines an operator between multiple prerequisites.
    """

    def __init__(self, op_type=""):
        """
        :param op_type: and, or
        :return:
        """
        self.op_type = op_type
        self.operands = []

    def add(self, op):
        self.operands.append(op)

    def __str__(self):
        if self.op_type is "":
            return "NONE"
        return_string = "(" + str(self.operands[0]) + ")"
        for i in range(1, len(self.operands)):
            return_string += " " + self.op_type.upper() + " "
            return_string += "(" + str(self.operands[i]) + ")"
        return return_string


class PreRequisite(object):
    def __init__(self, pr):
        self.equiv = False
        self.timing = Timings.pre
        self.min_gpa = None
        self.code = None
        self.default = ""
        self.parse_old(pr)

    def parse_old(self, pr):
        # APPROACH 2; Go word by word and interpret accordingly

        # APPROACH 1: Try one style or another
        code = PreRequisite.parse_single_code(pr)
        if code:
            self.code = code
            return

        # MIN GPA
        if pr.startswith('minimum grade of'):
            # minimum grade of 2.5 in X
            words = pr.split(" ")
            gpa = float(words[3])
            words = words[5:]
            # Parse rest of the code
            # parsed = parse(words)
        # EITHER-OR
        # CONCURRENTLY
        self.default = pr
        self.code = ClassCode()

    @staticmethod
    def parse(words, i=0):
        """Recursive method. Recursively constructs PROperators and sub-PROperators."""
        return PROperator()

    @staticmethod
    def parse_single_code(pr):
        try:
            # REGULAR PRE REQS
            # First, check to see if the pre-req ends in a number
            # CSE 143
            code_val = int(pr[len(pr) - 3:])
            regular = True
            # Then, check to see if the text before the numbers are only caps
            for i in pr:
                if i != " " and i.islower():
                    regular = False
                    break
            if regular:
                # TODO: generalize to non-CSE
                dept_val = pr[:len(pr) - 4]
                return ClassCode(dept_val, code_val)
        except ValueError:
            return None

    def __str__(self):
        if self.code.num == 0:
            return self.default
        return "[" + str(self.code) + "]"


class UWClass(object):
    def __init__(self, department=""):
        self.code = ClassCode(department)
        """:type : ClassCode"""
        self.name = ""
        self.description = ""
        self.pre_reqs = None
        """:type : PROperator"""
        # TODO: rename AF
        # List of ClassCodes
        self.post_reqs = []

    def __str__(self):
        string = "-----"
        string += ("\nCODE: " + str(self.code))
        string += ("\nNAME: " + self.name)
        string += ("\nDESC: " + self.description)
        string += ("\nPRE-REQS: " + str(self.pre_reqs))
        string += ("\nPOST-REQS: " + str([str(x) for x in self.post_reqs]))
        string += "\n-----"
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
        self.cseClass = None

    def handle_starttag(self, tag, attrs):
        if tag == "a" and not self.inP:
            # class code before paragraph
            self.cseClass = UWClass("CSE")
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
            cse_classes[int(self.cseClass.code.num)] = self.cseClass
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
        # TODO: Remove the code
        words = name.split(" ")
        i = 0
        for i in range(0, len(words)):
            if words[i][0].isdigit():
                break

        words = words[i + 1:]
        self.cseClass.name = " ".join(words)

    def parse_code(self, name):
        code = re.findall(r'\d+', name)
        # TODO: handle department
        self.cseClass.code.num = code[0]

    def parse_description(self, desc):
        """
        Parses the description of a class into prerequisites.
        :param desc: the description
        """
        self.cseClass.description = desc
        self.setup_pre_reqs(desc)
        # if debug:
        #    print("Prereqs: " + str(self.cseClass.pre_reqs))

    def setup_pre_reqs(self, desc):
        # 1. Check if the class has prereqs
        try:
            setup = desc[desc.index("Prereq"):]
        except ValueError:
            # No prerequisites
            self.cseClass.pre_reqs = PROperator()
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
            # Convert from string to object and add to class
            self.cseClass.pre_reqs.add(PreRequisite(pr))


# SETUP
cse_classes = {}

# ALGORITHM
# 1. Go through all classes and store the pre-reqs
f = open('cse.html')
s = f.read()

parser = CSEHTMLParser()
parser.feed(s)

# 2. Go through all descriptions and extract prereqs + reverse prereqs
for c in sorted(cse_classes.keys()):
    curr = cse_classes[c]
    pre_reqs = curr.pre_reqs
    if pre_reqs is not None:
        # TODO: make PROperator iterable?
        for pr in pre_reqs.operands:
            # TODO: Make better?
            if pr.code.num != 0:
                if pr.code.department == "CSE":
                    # YAY
                    pr_class = cse_classes[pr.code.num]
                    pr_class.post_reqs.append(curr.code)

for c in sorted(cse_classes.keys()):
    print(cse_classes[c])


    # print(parser.classes[4].description)

    # csv_file = open('csecourses.csv', 'w', newline='')
    # csv_writer = csv.writer(csv_file)
    # csv_writer.writerow(['Code', 'Name', 'Description'])
    # for x in parser.classes:
    #     csv_writer.writerow([x.code, x.name, x.description])
