import math
from math import *
import re
import logging

from enso.messages import displayMessage
from enso import selection


last_calculation = ""

def cmd_calculate(ensoapi, expression = None):
    """ Calculate the given expression
    Calculate mathematical expression.<br/><br/>
    Supported operators:<br/>
    <code>
    -, +, /, *, ^, **, (, ), %, mod
    </code><br/>
    functions:<br/>
    <code>
    mod, acos, asin, atan, atan2, ceil, cos, cosh,
    degrees, exp, fabs, floor, fmod, frexp, hypot, ldexp,
    log, log10, modf, pow, radians, sin, sinh, sqrt, tan, tanh
    </code><br/>
    constants:<br/>
    <code>
    pi, e
    </code><br/>
    conversions:<br/>
    <code>
    abs, chr, hex
    </code>
    """
    seldict = ensoapi.get_selection()
    if seldict.get("text"):
        selected_text = seldict['text'].strip().strip("\0")
    else:
        selected_text = None

    got_selection = False
    if expression is None:
        if selected_text:
            expression = selected_text
            got_selection = expression is not None

    if expression is None:
        ensoapi.display_message("No expression given.")
        return        
    
    math_funcs = [f for f in dir(math) if f[:2] != '__']

    whitelist = '|'.join(
        # oprators, digits
        [' ', '\.', ',', '\-', '\+', '/', '\\', '\*', '\^', '\*\*', '\(', '\)', '%', '\d+']
        + ['abs', 'chr\([0-9]+\)', 'hex\([0-9]+\)', 'mod']
        # functions of math module (ex. __xxx__)
        + math_funcs)

    print(whitelist)

    math_funcs_dict = dict([ (mf, eval('math.%s' % mf)) for mf in math_funcs])
    math_funcs_dict['abs'] = abs
    math_funcs_dict['chr'] = chr
    math_funcs_dict['hex'] = hex

    expression = expression.replace(' mod ', ' % ')

    if re.match(whitelist, expression):
        if expression.endswith("="):
            expression = expression[:-1]
            append_result = True
        else:
            append_result = False
        
        try:
            result = eval(expression, {"__builtins__": None}, math_funcs_dict)
            global last_calculation
            last_calculation = result

            pasted = False
            if got_selection:
                if append_result:
                    pasted = selection.set({ "text" : expression.strip() + " = " + str(result) })
                else:
                    pasted = selection.set({ "text" : str(result) })
            
            if not pasted:
                displayMessage("<p>%s</p><caption>%s</caption>" % (result, expression))
        except Exception as e:
            logging.info(e)
            ensoapi.display_message("Invalid syntax", "Error")
    else:
        ensoapi.display_message("Invalid expression", "Error")


#from enso.commands import CommandManager
#paste_command = CommandManager.get().getCommand("paste")
#if paste_command:
#    print(dir(paste_command))

def cmd_calculation_paste(ensoapi):
    """ Paste the results of the last calculation """
    global last_calculation
    
    #paste_command = CommandManager.get().getCommand("paste")
    #if paste_command:
    #    print dir(paste_command)
    #    paste_command.valid_args

    selection.set({ "text": str(last_calculation) })


CATEGORY = "calculation"

# vim:set tabstop=4 shiftwidth=4 expandtab:
