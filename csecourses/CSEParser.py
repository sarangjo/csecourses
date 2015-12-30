# Parser helpers
import re


def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def get_code_from_tag(tag):
    code = re.findall(r'\d+', tag)
    # TODO: handle department
    return int(code[0])


def get_name_from_data(data):
    # TODO: Remove the code
    words = data.split(" ")
    i = 0
    for i in range(0, len(words)):
        if words[i][0].isdigit():
            break

    words = words[i + 1:]
    return " ".join(words)


def get_pre_reqs_from_description(desc):
    # 1. Check if the class has prereqs
    try:
        setup = desc[desc.index("Prereq"):]
    except ValueError:
        # No prerequisites
        return []

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
    return prs
