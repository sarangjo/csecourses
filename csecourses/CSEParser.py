import csv
import json
import re
from enum import Enum
from html.parser import HTMLParser

__author__ = 'Sarang Joshi'

debug = False


def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


class Timings(Enum):
    pre = 0
    concurrent = 1


class ClassCode:
    def __init__(self, department="", num=0):
        self.department = department
        self.num = num

    def __str__(self):
        return self.department + " " + str(self.num)


class PROperator:
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

    def apply_gpa(self, gpa):
        # print(gpa)
        for op in self.operands:
            # if isinstance(op, PROperator):
            # Recursively apply gpa restriction on all sub pre-reqs
            op.apply_gpa(gpa)
            # elif isinstance(op, PreRequisite):
            #    op.min_gpa = gpa
            if not (isinstance(op, PROperator) or isinstance(op, PreRequisite)):
                print("fatal error!")

    def __str__(self):
        if self.is_none():
            return "NONE"
        return_string = "(" + str(self.operands[0]) + ")"
        for i in range(1, len(self.operands)):
            return_string += " " + self.op_type.upper() + " "
            return_string += "(" + str(self.operands[i]) + ")"
        return return_string

    def get_all_classes(self):
        """
        :return: list of PreRequisite objects
        Gets all classes contained in this operator, regardless of OR/AND
        """
        all_classes = []
        for op in self.operands:
            if isinstance(op, PreRequisite):
                all_classes.append(op.code)
            elif isinstance(op, PROperator):
                all_classes.extend(op.get_all_classes())
        return all_classes

    def is_none(self):
        return self.op_type is ""

    @staticmethod
    def parse(words, i=0):
        """Recursive method. Recursively constructs PROperators and sub-PROperators.
        :param words: collection of words
        :param i: index in words
        """
        if words[i] == 'minimum':
            # minimum grade of 2.5 in X
            # words = pr.split(" ")
            gpa = float(words[i + 3])
            i += 5
            # Parse rest of the code
            parsed = PROperator.parse(words, i)
            # Apply minimum gpa to all pre_reqs
            parsed.apply_gpa(gpa)
            # Return result
            return parsed
        elif words[i] == 'either':
            # Go through and add everything up until you hit "or", then add the last one
            i += 1
            sub_words = []
            prs = PROperator("or")

            while True:
                sub_words.append(words[i])
                if words[i + 1] == "or":
                    if words[i][-1] == ",":
                        # Take off last comma
                        sub_words[-1] = sub_words[-1][:-1]
                    # This is a complete pre requisite
                    prs.add(PROperator.parse(sub_words))
                    i += 2
                    sub_words.clear()
                    sub_words.extend(words[i:])
                    prs.add(PROperator.parse(sub_words))
                    break
                if words[i][-1] == ",":
                    # Take off last comma
                    sub_words[-1] = sub_words[-1][:-1]
                    # This is a complete pre requisite
                    prs.add(PROperator.parse(sub_words))
                    sub_words.clear()
                i += 1
            return prs
        elif words[i].isupper():
            # TODO: Confirm that this is correct
            # Keep traversing until we hit the course code
            try:
                dept_val = words[i]
                i += 1
                while not is_number(words[i][0]):
                    dept_val += " " + words[i]
                    i += 1
                num_val = int(re.findall(r'\d+', words[i])[0])
                parsed = PreRequisite()
                parsed.code = ClassCode(dept_val, num_val)
                return parsed
            except IndexError:
                pass

        # TODO: CSE 474/E E 474

        # Default
        return PreRequisite(" ".join(words))


class PreRequisite:
    def __init__(self, default=""):
        self.equiv = False
        self.timing = Timings.pre
        self.min_gpa = None
        self.code = None
        self.default = default

    def apply_gpa(self, gpa):
        self.min_gpa = gpa

    def __str__(self):
        if self.code is None or self.code.num is 0:
            return self.default
        return "[" + str(self.code) + "]"


class UWClass:
    def __init__(self, department=""):
        self.code = ClassCode(department)
        """:type : ClassCode"""
        self.name = ""
        self.description = ""
        # TODO: Make more efficient by not having any PROperator at all?
        self.pre_reqs = PROperator()
        # List of ClassCodes
        # TODO: rename AF
        self.post_reqs = []

    def __str__(self):
        string = "-----"
        string += ("\nCODE: " + str(self.code))
        string += ("\nNAME: " + self.name)
        string += ("\nPRE-REQS: " + str(self.pre_reqs))
        string += ("\nPOST-REQS: " + str([str(x) for x in self.post_reqs]))
        string += "\n-----"
        return string

    def get_json(self, id):
        json_output = {"id": id, "number": self.code.num, "name": self.name}
        return json_output


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
            cse_classes.append(self.cseClass)
            code_ids[self.cseClass.code.num] = len(cse_classes) - 1
            self.inP = False
        elif tag == "b" and self.inP:
            # set name of class
            self.inName = False
            if not self.inDesc:
                # start of description paragraph
                self.inDesc = True
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
        self.cseClass.code.num = int(code[0])

    def parse_description(self, desc):
        """
        Parses the description of a class into prerequisites.
        :param desc: the description
        """
        self.cseClass.description = desc
        self.set_pre_reqs(desc)

    def set_pre_reqs(self, desc):
        # 1. Check if the class has prereqs
        try:
            setup = desc[desc.index("Prereq"):]
        except ValueError:
            # No prerequisites
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
            self.cseClass.pre_reqs.add(PROperator.parse(pr.split(" ")))


def set_post_reqs():
    """
    Sets post-reqs. Go through all descriptions and extract prereqs + "post-req"s
    """
    for curr in cse_classes:
        pre_reqs = curr.pre_reqs
        # TODO: remove
        if not pre_reqs.is_none():
            # list of all codes
            pre_req_list = pre_reqs.get_all_classes()

            for pre_req_code in pre_req_list:
                # code is None if it's not a valid class
                if pre_req_code and pre_req_code.num is not 0 and pre_req_code.department == "CSE":
                    # YAY
                    try:
                        # Sets that class' post req
                        cse_classes[code_ids[pre_req_code.num]].post_reqs.append(curr.code)
                    except KeyError:
                        print("Invalid pre-req: " + str(pre_req_code) + " for " + str(curr.code))


def spit_json_data():
    levels = 4

    # NODES
    nodes = []
    id = 0
    for cl in cse_classes:
        if int(cl.code.num / 100) <= levels:
            nodes.append(cl.get_json(id))
            id += 1
        else:
            break

    json_nodes_file = open('testcourses2.json', 'w')
    json.dump(nodes, json_nodes_file, indent=4)
    # print(json.dumps(nodes))

    # LINKS
    links = []
    id = 0
    for i in range(0, len(cse_classes)):
        cl = cse_classes[i]
        if int(cl.code.num / 100) <= levels:
            pre_req_list = cl.pre_reqs.get_all_classes()
            for pre_req in pre_req_list:
                if pre_req.department == 'CSE':
                    try:
                        source = code_ids[pre_req.num]  # pre_req
                        target = i  # cl
                        links.append({'id': id, 'source': source, 'target': target})
                        id += 1
                    except KeyError:
                        print("whups")
        else:
            break

    json_links_file = open('testlinks2.json', 'w')
    json.dump(links, json_links_file, indent=4)
    # print(json.dumps(links, indent=4))



def spit_csv_data():
    csv_file = open('csecourses.csv', 'w', newline='')
    csv_writer = csv.writer(csv_file)

    csv_writer.writerow(['number', 'name'])
    for c in cse_classes:
        csv_writer.writerow([c.code.num, c.name])

    # Simply connect one class to the next
    # CSV?
    csv_file = open('courselinks.csv', 'w', newline='')
    csv_writer = csv.writer(csv_file)


# SETUP
cse_classes = []
code_ids = {}  # code --> id

# ALGORITHM
# 1. Go through all classes and store the pre-reqs
f = open('cse.html')
s = f.read()

parser = CSEHTMLParser()
parser.feed(s)

# cse_classes.sort(key=lambda x: x.code.num)
# class_codes.sort()

print("Finished parsing part 1.")

set_post_reqs()

print("Finished parsing part 2.")

# 3. Convert data from cse_classes into visualizable data
is_json = True
if not is_json:
    spit_csv_data()
else:
    spit_json_data()
