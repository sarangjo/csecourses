import json
import re
from html.parser import HTMLParser

import CSEParser

intro = [142, 143]
reqd = [311, 312, 332, 351]
reqdCS = [331]
reqdCE = [369, 371]


class CSEHTMLParser(HTMLParser):
    def error(self, message):
        print("SOMEONE SCREWED UP: " + message)

    def __init__(self):
        super().__init__()
        # parsing fields
        self.inName = False
        self.inP = False
        self.inDesc = False
        # TODO: Figure out issue with calling close() when done
        self.isDone = False
        # other fields
        self.num = 0

    def handle_starttag(self, tag, attrs):
        if not self.isDone:
            if tag == "a" and not self.inP:
                # class code before paragraph
                self.num = CSEParser.get_code_from_tag(attrs[0][1])
                if int(self.num / 100) > levels:
                    self.isDone = True
                    return
                nodes[self.num] = {"number": self.num}
                if self.num in reqd:
                    nodes[self.num]["classification"] = "required"
                elif self.num in reqdCS:
                    nodes[self.num]["classification"] = "cs"
                elif self.num in reqdCE:
                    nodes[self.num]["classification"] = "ce"
                elif self.num in intro:
                    nodes[self.num]["classification"] = "intro"
            elif tag == "p":
                # entered a new class paragraph
                self.inP = True
            elif tag == "b" and self.inP:
                # set name
                self.inName = True
            elif tag == "br" and self.inP:
                self.inDesc = True

    def handle_data(self, data):
        if not self.isDone:
            if self.inName:
                nodes[self.num]["name"] = CSEParser.get_name_from_data(data)
            elif self.inDesc:
                nodes[self.num]["description"] = data

    def handle_endtag(self, tag):
        if not self.isDone:
            if tag == "p" and self.inP:
                # finished a single class
                self.inP = False
            elif tag == "b" and self.inName:
                # finished name
                self.inName = False
            elif tag == "a" and self.inDesc:
                # finished description paragraph
                self.inDesc = False


def parse_links_from_pre_req(target, words, i=0):
    """Recursively adds links to the links list, for a single pre-req string.
    :param target: end node
    :param words: collection of words
    :param i: index in words
    :returns: list of links
    """
    # TODO: Return something or directly append?
    if words[i] == 'minimum':
        # minimum grade of 2.5 in X
        gpa = float(words[i + 3])
        i += 5
        # Parse rest of the code
        parsed = parse_links_from_pre_req(target, words, i)
        # Apply minimum gpa to all pre_reqs
        # TODO: make more efficient
        for link in parsed:
            link["gpa"] = gpa
        return parsed
    elif words[i] == 'either':
        # Go through and add everything up until you hit "or", then add the last one
        i += 1
        sub_words = []

        # TODO: Everything after this should be an OR link
        or_links = []

        while True:
            sub_words.append(words[i])
            if words[i + 1] == "or":
                if words[i][-1] == ",":
                    # Take off last comma
                    sub_words[-1] = sub_words[-1][:-1]
                # This is a complete pre requisite
                or_links.extend(parse_links_from_pre_req(target, sub_words))
                i += 2
                sub_words.clear()
                sub_words.extend(words[i:])
                or_links.extend(parse_links_from_pre_req(target, sub_words))
                break
            if words[i][-1] == ",":
                # Take off last comma
                sub_words[-1] = sub_words[-1][:-1]
                # This is a complete pre requisite
                or_links.extend(parse_links_from_pre_req(target, sub_words))
                sub_words.clear()
            i += 1

        # TODO: Remove
        # for or_link in or_links:
        #    or_link["or"] = True

        return or_links
    elif words[i].isupper():
        # Keep traversing until we hit the course code
        try:
            dept_val = words[i]
            i += 1
            while not CSEParser.is_number(words[i][0]):
                dept_val += " " + words[i]
                i += 1
            num_val = int(re.findall(r'\d+', words[i])[0])

            if dept_val == "CSE":
                if num_val in nodes:
                    singleton = {"source": str(num_val), "target": str(target)}
                    return [singleton]
        except IndexError:
            pass

    # Default
    # TODO: Return None or empty list?
    return []  # PreRequisite(" ".join(words))


# ALGORITHM 2
# 0. Setup
nodes = {}
links = []
levels = 3

# 1. Use the alternate parser. First run, simply construct the nodes map, which maps from class code
# to a map of all the details
f = open('cse.html')
s = f.read()

parser = CSEHTMLParser()
parser.feed(s)

# 2. Then, go through each of the prerequisites and set up the links list, with source and target attributes
# that correspond to course numbers
for code in sorted(nodes):
    node = nodes[code]

    try:
        desc = node["description"]
        prs = CSEParser.get_pre_reqs_from_description(desc)

        for pr in prs:
            links.extend(parse_links_from_pre_req(code, pr.split(" ")))
    except KeyError:
        # If the node doesn't have a description
        pass

# 3. Output all the unsorted nodes to a nodes file, links to a links file.
nodes_file = open('testcourses' + str(levels) + '-alt.json', 'w')
json.dump(nodes, nodes_file, indent=4)
links_file = open('testlinks' + str(levels) + '-alt.json', 'w')
json.dump(links, links_file, indent=4)
