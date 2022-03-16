import sys
import os
import errno
try:
    import unicodedata
except ImportError:
    print("Please install the unicodedata module.")
    command = f"{sys.executable} -m pip install unicodedata"
    print(f"To install unicodedata, run: {command}")
    sys.exit(1)
from sre_constants import error
import re
import json

version = "1.6"

"""
    Function Name: call_condition
    Description:
        Used by some other functions in this module
        in order to call a function with an unknown
        number of arguments.
    return type: Any
    params:
        fun - The function that represents the condition here.
        value - The value to pass
        parent - The parent of the value
"""
def call_condition(fun, value, parent):
    arg_count = fun.__code__.co_argcount
    if arg_count == 1:
        return fun(value)
    elif arg_count == 2:
        return fun(value, parent)
    raise TypeError("Invalid argument count")

"""
    Function Name: enforced_input
    Description:
        Extends the input function to enforce that it be of
        a specific type with optional additional conditions.
        This function will keep asking for input until it gets
        something useable.
    return type: {target_type}
    params:
        prompt - The prompt message given before the user inputs.
        target_type - The type of value you want at the end.
            Works best with primitives. By default is str.
        invalid_message - The message given when the user inputs
            data that is invalid for the type. By default is "Invalid Input."
        condition - Used to enforce additional conditions than the type.
            If this function returns False with the (type transformed) input
            as an argument, the input will be rejected. You may also return
            "end" (case insensitive) to end the input loop and have
            the funtion return the default. By default, this returns True all the time.
        cancel - If the user inputs this value (case insensitive), the input loop
            will be broken and the function will return the default. By default is set to
            None, which means "cancelling" is impossible.
        default - The default value to return if the input is cancelled.
"""
def enforced_input(prompt, target_type=str, invalid_message="Invalid Input.", condition=lambda x: True,
                   cancel=None, default=None):
    # Wrap in try-except so that Ctrl+C doesn't end the program
    try:
        result = input(prompt)
    except:
        print("You cannot use Ctrl-C during input collection.")
        return enforced_input(prompt, target_type, invalid_message, condition, cancel, default)
    
    if cancel != None and result.lower() == cancel.lower():
        return default
    
    if (target_type is int) or (target_type is float):
        # Remove commas from the string in case the user used them in their number
        result = result.replace(",", "")
        # Remove leading dollar sign if necessary
        if len(result) >= 2 and result[0] == "$":
            result = result[1:]
        # Remove trailing "f" if necessary
        if len(result) >= 1 and result[-1] == "f":
            result = result[:-1]
    elif target_type is str:
        if cancel != None and result.lower() == cancel.lower():
          return default

        c = call_condition(condition, result, None)
        # Allow this function to explicitly end the loop if necessary.
        if type(c) is str and c.lower() == "end":
            return default
        # Keep asking until the condition suceeds
        while c == None or c == False:
            print(invalid_message)
            # Wrap in try-except so that Ctrl+C doesn't end the program
            try:
                result = input(prompt)
            except:
                print("You cannot use Ctrl-C during input collection.")
                return enforced_input(prompt, target_type, invalid_message, condition, cancel, default)

            if cancel != None and result.lower() == cancel.lower():
                return default

            c = call_condition(condition, result, None)
            # Allow this function to explicitly end the loop if necessary.
            if type(c) is str and c.lower() == "end":
                return default
        # the input is already the target type. Nothing else needs to be done.
        return result
    # Bool type doesn't work for casting. Override the behavior
    elif target_type is bool:
      if cancel != None and result.lower() == cancel.lower():
          return default

      c = call_condition(condition, result, None)

      # Allow this function to explicitly end the loop if necessary.
      if type(c) is str and c.lower() == "end":
          return default

      if result.lower() in ["yes", "y", "true"] and c:
          return True
      elif result.lower() in ["no", "n", "false"] and c:
          return False
      else:
          print(invalid_message)
          # Recurse the method so that the rest of the code doesn't cause unexpected behavior
          return enforced_input(prompt, target_type, invalid_message, condition)

    while type(result) is str:
        try:
            # Try to cast the input to the target type
            result = target_type(result)
            # Make sure the result actually exists and didn't return None.
            if result == None:
                raise TypeError("Invalid Input")

            c = call_condition(condition, result, None)

            # Allow this function to explicitly end the loop if necessary.
            if type(c) is str and c.lower() == "end":
                return default
            # If the condition fails throw an error
            if c == None or c == False:
                raise TypeError("Invalid input")
        except:
            # If there is an error casting, inform the user and ask for input agains
            print(invalid_message)
            # Wrap in try-except so that Ctrl+C doesn't end the program
            try:
                result = input(prompt)
            except:
                print("You cannot use Ctrl-C during input collection.")
                return enforced_input(prompt, target_type, invalid_message, condition, cancel, default)
            if cancel != None and result.lower() == cancel.lower():
                return default
            if (target_type is int) or (target_type is float):
                # Remove commas from the string in case the user used them in their number
                result = result.replace(",", "")
                # Remove leading dollar sign if necessary
                if len(result) >= 2 and result[0] == "$":
                    result = result[1:]
                # Remove trailing "f" if necessary
                if len(result) >= 1 and result[-1] == "f":
                    result = result[:-1]

    return result

"""
    Function Name: get_args
    Description:
        Given a list of arguments, checks if they have
        been given in the command line. If not, (optionally) runs
        enforced_input to get a value. If that is cancelled,
        returns the default. Finally returns a dict of
        the values of your arguments.
    return type: dict
    params:
        args (list) - A list of the arguments you are checking for.
            Each item should be a dict with the following format:
                {
                    name (str) - The name of this argument,
                    target_type (callable) - The function used to cast
                        the string input to the target type,
                    input_args* - The arguments for use when asking for input.
                        Should follow this format:
                            {
                                invalid_message (str) - The message given when the user
                                    inputs data that is invalid for the type. By default is "Invalid Input."
                                cancel* (str) - If the user inputs this value (case insensitive), the input loop
                                    will be broken and the function will return the default. By default is set to
                                    None, which means "cancelling" is impossible.
                            }
                    condition* (function) - Used to enforce additional conditions than the type.
                        If this function returns False with the (type transformed) input
                        as an argument, the input will be rejected. You may also return
                        "end" (case insensitive) to end the input loop and have
                        the funtion return the default. By default, this returns True all the time.
                        An optional second parameter provides the current value of result.
                    ask_condition* (function) -
                        If this function is defined and returns False, the input will set to the default
                        without prompting the user. Takes the current value of result as an argument.
                    default* - The default value to return if no other value is provided.
                        If unspecified, will be none.
                    required* (str[]) - Values that need to be specified (not None) for this
                        argument to be valid. If any of these are not specified, the value will be None.
                    input* - A value that can be specified in the command line to redirect this value
                        to the user's choice. By default is None.
                    inline_input* - A value that can be specified in the command line inline with an actual
                        argument that will be replaced with a value of the users choice.
                        Works best if target type is str. By default is None. You can change this to a list
                        of values to allow multiple values to behave this way.
                    inline_invalid_message* - The message given when the user inputs data that is invalid for the
                        inline_input type. By default is f"Invalid! Must be a string. Use {cancel} to cancel this argument or use the default."
                    raise_error* (bool) - If True, will raise an error if the argument is not valid. Otherwise, will use the default value (or None if
                        not explicitly specified). By default is False.
                }
            * - optional
        allow_input (bool) - If True, will allow the user to input values for arguments that are not specified.
"""
def get_args(args, allow_input=True):
    result = {}
    sys_arg_count = len(sys.argv) - 1
    for i in range(1, min(len(sys.argv), len(args) + 1)):
        sys_arg = sys.argv[i]
        arg = args[i - 1]
        required = arg["required"] if "required" in arg and arg["required"] else []
        cont = False
        for key in required:
            if not (key in result and result[key] != None):
                result[arg["name"]] = None
                cont = False
                break
            else:
                cont = True
        if "ask_condition" in arg and not arg["ask_condition"](result):
            result[arg["name"]] = arg["default"] if "default" in arg else None
            cont = False
        
        if len(required) == 0 or cont:
            cont = True
            if "input" in arg and sys_arg == arg["input"] and allow_input:
                result[arg["name"]] = enforced_input(f'Specify Argument \'{arg["name"]}\': ', arg["target_type"], arg["input_args"]["invalid_message"] if ("input_args" in arg) else None,
                        arg["condition"] if (
                            "condition" in arg and arg["condition"]) else lambda x: True,
                        arg["input_args"]["cancel"] if (
                            "input_args" in arg and "cancel" in arg["input_args"] and arg["input_args"]["cancel"]) else None,
                        arg["default"] if ("default" in arg and arg["default"] != None) else None)
            else:
                try:
                    if "inline_input" in arg and allow_input:
                        if type(arg["inline_input"]) is list:
                            for inline_input in arg["inline_input"]:
                                if cont:
                                    i = 1
                                    while inline_input in sys_arg:
                                        cancel = arg['input_args']['cancel'] if ("input_args" in arg and 'cancel' in arg['input_args'] and arg['input_args']['cancel']) else None
                                        new_input = enforced_input(f'Specify Argument Portion "{inline_input}" {i} of \'{arg["name"]}\': ', str, arg["inline_invalid_message"] if "inline_invalid_message" in arg else f"Invalid! Must be a string. Use {cancel} to cancel this argument or use the default.", cancel=cancel)
                                        if new_input == None:
                                            result[arg["name"]] = arg["default"] if "default" in arg else None
                                            cont = False
                                            break
                                        sys_arg = sys_arg.replace(inline_input, new_input, 1)
                                        if sys_arg == None:
                                            result[arg["name"]] = None
                                            continue
                                        i += 1
                        else:
                            inline_input = arg["inline_input"]
                            i = 1
                            while inline_input in sys_arg:
                                if cont:
                                    cancel = arg['input_args']['cancel'] if ("input_args" in arg and 'cancel' in arg['input_args'] and arg['input_args']['cancel']) else None
                                    new_input = enforced_input(f'Specify Argument Portion "{inline_input}" {i} of \'{arg["name"]}\': ', str, arg["inline_invalid_message"] if "inline_invalid_message" in arg else f"Invalid! Must be a string. Use {cancel} to cancel this argument or use the default.", cancel=cancel)
                                    if new_input == None:
                                        result[arg["name"]] = arg["default"] if "default" in arg else None
                                        cont = False
                                        break
                                    if sys_arg == None:
                                        result[arg["name"]] = None
                                        continue
                                    i += 1

                    if cont:
                        if arg["target_type"] is bool:
                            if sys_arg.lower() in ["yes", "true"]:
                                result[arg["name"]] = True
                            elif sys_arg.lower() in ["no", "false"]:
                                result[arg["name"]] = False
                            else:
                                raise TypeError("Invalid Input")
                        else:
                            result[arg["name"]] = arg["target_type"](sys_arg)

                        if "condition" in arg and arg["condition"]:
                            condition = arg["condition"]
                            c = call_condition(condition, result[arg["name"]], result)

                            if "input_args" in arg and "cancel" in arg["input_args"]:
                                cancel = arg['input_args']['cancel']
                                if str(result[arg["name"]]).lower() == cancel.lower():
                                    raise TypeError("Invalid Input")

                            # Allow this condition to explicitly end the loop if necessary.
                            if type(c) is str and c.lower() == "end":
                                result[arg["name"]] = arg["default"]
                            # If the condition fails throw an error
                            if c == None or c == False:
                                raise TypeError("Invalid input")
                        if result[arg["name"]] == None:
                            raise TypeError("Invalid Input")
                except Exception as e:
                    print(f'Invalid input passed as \'{arg["name"]}\' (index {i + 1} - {sys_arg})')
                    print(f'Message:\n\t{arg["input_args"]["invalid_message"]}')
                    if "input_args" in arg and arg["input_args"] and allow_input:
                        result[arg["name"]] = enforced_input(f'Specify Argument \'{arg["name"]}\': ', arg["target_type"], arg["input_args"]["invalid_message"],
                            arg["condition"] if (
                                "condition" in arg and arg["condition"]) else lambda x: True,
                            arg["input_args"]["cancel"] if (
                                "cancel" in arg["input_args"] and arg["input_args"]["cancel"]) else None,
                            arg["default"] if ("default" in arg and arg["default"] != None) else None)
                    elif "default" in arg:
                        if "raise" in arg and arg["raise"]:
                            raise e
                        else:
                            print(f'Using the default ({arg["default"]})')
                            result[arg["name"]] = arg["default"]
                    else:
                        if "raise" in arg and arg["raise"]:
                            raise e
                        else:
                            print('Using the default (None)')
                            result[arg["name"]] = None

    if len(args) > sys_arg_count:
        if allow_input:
            for i in range(sys_arg_count, len(args)):
                arg = args[i]
                required = arg["required"] if "required" in arg and arg["required"] else []
                cont = False
                for key in required:
                    if not (key in result and result[key] != None):
                        result[arg["name"]] = None
                        cont = False
                        break
                    else:
                        cont = True
                if "ask_condition" in arg and not arg["ask_condition"](result):
                    result[arg["name"]] = arg["default"] if "default" in arg else None
                    cont = False
                if len(required) == 0 or cont:
                    if "input_args" in arg and arg["input_args"]:
                        result[arg["name"]] = enforced_input(f'Specify Argument \'{arg["name"]}\': ', arg["target_type"], arg["input_args"]["invalid_message"],
                            arg["condition"] if (
                                "condition" in arg and arg["condition"]) else lambda x: True,
                            arg["input_args"]["cancel"] if (
                                "cancel" in arg["input_args"] and arg["input_args"]["cancel"]) else None,
                            arg["default"] if ("default" in arg and arg["default"] != None) else None)
                    elif "default" in arg:
                        print(f'No input specified for \'{arg["name"]}\' using the default ({arg["default"]})')
                        result[arg["name"]] = arg["default"]
                    else:
                        print(f'No input specified for \'{arg["name"]}\' using the default (None)')
                        result[arg["name"]] = None
        else:
            raise TypeError("Not enough arguments passed in the command line.")

    return(result)

#This comes from https://www.rexegg.com/regex-trick-numbers-in-english.html You need to use the extended regex library to use this correctly.
number_word_regex = """
((?x)           # free-spacing mode
(?(DEFINE)
# Within this DEFINE block, we'll define many subroutines
# They build on each other like lego until we can define
# a "big number"

(?<one_to_9>  
# The basic regex:
# one|two|three|four|five|six|seven|eight|nine
# We'll use an optimized version:
# Option 1: four|eight|(?:fiv|(?:ni|o)n)e|t(?:wo|hree)|
#                                          s(?:ix|even)
# Option 2:
(?:f(?:ive|our)|s(?:even|ix)|t(?:hree|wo)|(?:ni|o)ne|eight)
) # end one_to_9 definition

(?<ten_to_19>  
# The basic regex:
# ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|
#                                              eighteen|nineteen
# We'll use an optimized version:
# Option 1: twelve|(?:(?:elev|t)e|(?:fif|eigh|nine|(?:thi|fou)r|
#                                             s(?:ix|even))tee)n
# Option 2:
(?:(?:(?:s(?:even|ix)|f(?:our|if)|nine)te|e(?:ighte|lev))en|
                                        t(?:(?:hirte)?en|welve)) 
) # end ten_to_19 definition

(?<two_digit_prefix>
# The basic regex:
# twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety
# We'll use an optimized version:
# Option 1: (?:fif|six|eigh|nine|(?:tw|sev)en|(?:thi|fo)r)ty
# Option 2:
(?:s(?:even|ix)|t(?:hir|wen)|f(?:if|or)|eigh|nine)ty
) # end two_digit_prefix definition

(?<one_to_99>
(?&two_digit_prefix)(?:[- ](?&one_to_9))?|(?&ten_to_19)|
                                            (?&one_to_9)
) # end one_to_99 definition

(?<one_to_999>
(?&one_to_9)[ -]?hundred(?:[ -]?(?:and[ -]?)?(?&one_to_99))?|
                                            (?&one_to_99)
) # end one_to_999 definition

(?<one_to_999_999>
(?&one_to_999)[ -]?thousand(?:[ -]?(?&one_to_999))?|
                                    (?&one_to_999)
) # end one_to_999_999 definition

(?<one_to_999_999_999>
(?&one_to_999)[ -]?million(?:[ -]?(?&one_to_999_999))?|
                                (?&one_to_999_999)
) # end one_to_999_999_999 definition

(?<one_to_999_999_999_999>
(?&one_to_999)[ -]?billion(?:[ -]?(?&one_to_999_999_999))?|
                                (?&one_to_999_999_999)
) # end one_to_999_999_999_999 definition

(?<one_to_999_999_999_999_999>
(?&one_to_999)[ -]?trillion(?:[ -]?(?&one_to_999_999_999_999))?|
                                    (?&one_to_999_999_999_999)
) # end one_to_999_999_999_999_999 definition

(?<bignumber>
zero|(?&one_to_999_999_999_999_999)
) # end bignumber definition

(?<zero_to_9>
(?&one_to_9)|zero
) # end zero to 9 definition

(?<decimals>
point(?:[ -]?(?&zero_to_9))+
) # end decimals definition

) # End DEFINE
(?P>bignumber))
"""

"""
    Function Name: smart_equals
    Description:
        A Function that determines if strings s1 ad s2 can be considered
        to be equal to each other. They don't have to be the same - this
        function strips accents, converts to lowercase, considers all
        whitespace the same, removes any non-alphanumeric characters (replaced
        with spaces), and allows for the user to use acronyms or abbreviations.
    return type: bool
    params:
        s1 - The first String
        s2 - The second String
"""
def smart_equals(s1, s2):
    # Do some cleanp on the input, removing trailing/leading whitespace,
    # repeat whitespace, converting accented characters to normal,
    # replacing any whitespace with space, and converting to lowercase.
    s1 = strip_accents(re.sub(r"\s", " ", s1.strip())).lower()
    s2 = strip_accents(re.sub(r"\s", " ", s2.strip())).lower()

    #Remove double spaces
    s1 = re.sub(r"\s{2,}", " ", s1)
    s2 = re.sub(r"\s{2,}", " ", s2)

    #Remove any non-alphanumeric characters
    s1 = re.sub(r"[^A-Za-z0-9\- ]", "", s1)
    s2 = re.sub(r"[^A-Za-z0-9\- ]", "", s2)

    s1_no_dash = s1.replace("-", " ")
    s2_no_dash = s2.replace("-", " ")

    # If the strings are equal or either starts with the other, return True
    if s1_no_dash == s2_no_dash or s1_no_dash.startswith(s2_no_dash) or s2_no_dash.startswith(s1_no_dash):
        return True

    """
        Generate a regex for each string that matches each letter of each word
        and then either the next letter or the first letter of the next word, optionally
        preceded by a space. For words that are less than or equal to 3 letters long, the entire
        word is optional.
        This will detect acronyms and abbreviations.

        For example, if the string is "hello world", the regex will be:
            ^h(e(l(l(o)?)?)?)?\s?w(o(r(l(d)?)?)?)?$
        and will match strings like:
            "hello world"
            "helloworld"
            "hw"
            "h w"
            "hel w"
            "helw"
            "he wo"
            "hewo"
    """
    regex_1 = "^"
    s1_split = s1.split(" ")
    for i in range(0, len(s1_split)):
        regex_1 += "("
        word = s1_split[i]
        regex_1 += word[0]
        for j in range(1, len(word)):
            regex_1 += f"({word[j]}"
        regex_1 += ")?" * (len(word) - 1)
        regex_1 += ")" + ("?" if len(word) <= 3 else "")
        if not i == len(s1_split) - 1:
            regex_1 += "[\\s-]?"
    regex_1 += "$"

    regex_2 = "^"
    s2_split = s2.split(" ")
    for i in range(0, len(s2_split)):
        regex_2 += "("
        word = s2_split[i]
        regex_2 += word[0]
        for j in range(1, len(word)):
            regex_2 += f"({word[j]}"
        regex_2 += ")?" * (len(word) - 1)
        regex_2 += ")" + ("?" if len(word) <= 3 else "")
        if not i == len(s2_split) - 1:
            regex_2 += "[\\s-]?"
    regex_2 += "$"


    #If both strings match either regex, return True
    if re.match(regex_1, s1) and re.match(regex_1, s2):
        return True
    elif re.match(regex_2, s1) and re.match(regex_2, s2):
        return True

    return False

"""
    Function Name: strip_accents
    Description:
        Strip accents from input String.
    return type: string
    params:
    text - The input String
"""
def strip_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn')

# Sadly, Python fails to provide the following magic number for us.
ERROR_INVALID_NAME = 123
'''
Windows-specific error code indicating an invalid pathname.

See Also
----------
https://docs.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499-
    Official listing of all such codes.
'''

def is_valid_path(pathname: str) -> bool:
    '''
    `True` if the passed pathname is a valid pathname for the current OS;
    `False` otherwise.
    '''
    # If this pathname is either not a string or is but is empty, this pathname
    # is invalid.
    try:
        if not isinstance(pathname, str) or not pathname:
            return False

        # Strip this pathname's Windows-specific drive specifier (e.g., `C:\`)
        # if any. Since Windows prohibits path components from containing `:`
        # characters, failing to strip this `:`-suffixed prefix would
        # erroneously invalidate all valid absolute Windows pathnames.
        _, pathname = os.path.splitdrive(pathname)

        # Directory guaranteed to exist. If the current OS is Windows, this is
        # the drive to which Windows was installed (e.g., the "%HOMEDRIVE%"
        # environment variable); else, the typical root directory.
        root_dirname = os.environ.get('HOMEDRIVE', 'C:') \
            if sys.platform == 'win32' else os.path.sep
        assert os.path.isdir(root_dirname)   # ...Murphy and her ironclad Law

        # Append a path separator to this directory if needed.
        root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

        # Test whether each path component split from this pathname is valid or
        # not, ignoring non-existent and non-readable path components.
        for pathname_part in pathname.split(os.path.sep):
            try:
                os.lstat(root_dirname + pathname_part)
            # If an OS-specific exception is raised, its error code
            # indicates whether this pathname is valid or not. Unless this
            # is the case, this exception implies an ignorable kernel or
            # filesystem complaint (e.g., path not found or inaccessible).
            #
            # Only the following exceptions indicate invalid pathnames:
            #
            # * Instances of the Windows-specific "WindowsError" class
            #   defining the "winerror" attribute whose value is
            #   "ERROR_INVALID_NAME". Under Windows, "winerror" is more
            #   fine-grained and hence useful than the generic "errno"
            #   attribute. When a too-long pathname is passed, for example,
            #   "errno" is "ENOENT" (i.e., no such file or directory) rather
            #   than "ENAMETOOLONG" (i.e., file name too long).
            # * Instances of the cross-platform "OSError" class defining the
            #   generic "errno" attribute whose value is either:
            #   * Under most POSIX-compatible OSes, "ENAMETOOLONG".
            #   * Under some edge-case OSes (e.g., SunOS, *BSD), "ERANGE".
            except OSError as exc:
                if hasattr(exc, 'winerror'):
                    if exc.winerror == ERROR_INVALID_NAME:
                        return False
                elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False
    # If a "TypeError" exception was raised, it almost certainly has the
    # error message "embedded NUL character" indicating an invalid pathname.
    except TypeError as exc:
        return False
    # If no exception was raised, all path components and hence this
    # pathname itself are valid. (Praise be to the curmudgeonly python.)
    else:
        return True
    # If any other exception was raised, this is an unrelated fatal issue
    # (e.g., a bug). Permit this exception to unwind the call stack.
    #
    # Did we mention this should be shipped with Python already?

"""print(get_args([
    {
        "name": "float",
        "target_type": float,
        "default": 0.0
    },
    {
        "name": "dict",
        "target_type": json.loads,
        "default": {},
        "input_args": {
            "invalid_message": "Invalid! Must be JSON dict.",
            "cancel": "cancel",
            "condition": lambda x: type(x) is dict
        }
    },
    {
        "name": "int",
        "target_type": int,
        "default": 0,
        "input_args": {
            "invalid_message": "Invalid! Must be int",
        }
    }
], True))"""
