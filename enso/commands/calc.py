import math
from math import *
import re
import logging

from enso.messages import displayMessage
from enso import selection


last_calculation = ""

_from_currencies = {}
_to_currencies = {}


def _get_html(url):
    import urllib
    import urllib2

    html = None
    try:
        resp = urllib2.urlopen(url)
        html = resp.read()
    except Exception, e:
        logging.error(e)
        html = None
    return html


def _cache_currencies():
    html = _get_html("http://www.google.com/finance/converter")

    if html is None:
        logging.error("Error caching currencies, no HTML data returned.")
        return

    sel_start = html.find("<select name=\"from\"")
    if sel_start == -1:
        sel_start = html.find("<select name=from")
    if sel_start > -1:
        sel_end = html.find("</select>", sel_start)
        r = re.compile(r"<option .*value=\"(.*)\".*>(.*)</option>", re.IGNORECASE)
        for item in r.finditer(html, sel_start, sel_end):
            currency, currency_desc = item.groups()
            _from_currencies[currency] = currency_desc

    sel_start = html.find("<select name=\"to\"")
    if sel_start == -1:
        sel_start = html.find("<select name=to")
    if sel_start > -1:
        sel_end = html.find("</select>", sel_start)
        r = re.compile(r"<option .*value=\"(.*)\".*>(.*)</option>", re.IGNORECASE)
        for item in r.finditer(html, sel_start, sel_end):
            currency, currency_desc = item.groups()
            _to_currencies[currency] = currency_desc

_cache_currencies()
complete_currency_re = re.compile(
    r"(.*)(" + 
    "|".join(_from_currencies.keys()) + 
    ") (in|to) (" +
    "|".join(_to_currencies.keys()) + 
    ")(.*)", 
    re.IGNORECASE)


partial_currency_re = re.compile(
    r"(in|to) (" +
    "|".join(_to_currencies.keys()) + 
    ")(.*)", 
    re.IGNORECASE)

#print r"(.*)\S?((" + "|".join(_from_currencies.keys()) + "){3}) in (.*)"
#print _from_currencies
#print _to_currencies


def currency(amount, from_curr, to_curr):
    result = 1.0 * float(amount)
    url= "http://download.finance.yahoo.com/d/quotes.csv?s=%s%s=X&f=sl1d1t1ba&e=.csv" % (from_curr.upper(), to_curr.upper())
    #url = "http://www.google.com/finance/converter?a=%d&from=%s&to=%s" % (amount, from_curr.upper(), to_curr.upper())

    logging.debug(url)
    html = _get_html(url)
    logging.debug(html)
    code, rate = html.split(",")[:2]
    if not (from_curr.upper() + to_curr.upper() in code):
        return result

    result = float(rate) * float(amount)
    logging.debug(result)
    #logging.debug("%s, %s, %f" % (repr(code), repr(rate), result))

    """
    r = re.compile(r"<div id=\"?currency_converter_result\"?[^>]*>(.*?)</div>", re.IGNORECASE | re.DOTALL)
    m = r.search(html)
    if m:
        result_text = re.sub(r'<[^>]*?>', '', m.group(1).strip()).replace("&nbsp;", " ")
        m = re.search(r"\= ([0-9\.]+) [A-Z]{3}", result_text)
        if m:
            result = 1.0 * float(m.group(1))
            print result
    """
    return result


def _handle_currency_symbols(expression):
    import logging
    logging.info(expression)
    symbol_table = [
        (r"€([0-9\.]+)", "EUR"),
        (r"£([0-9\.]+)", "GBP"),
        (r"\$([0-9\.]+)", "USD"),
        (r"¥([0-9\.]+)", "JPY"),
        (u"([0-9\.]+)(,-)?K\u010d", "CZK")
    ]
    fixed_expression = expression
    currency = None
    amount = None
    for r, symbol in symbol_table:
        m = re.search(r, expression, re.IGNORECASE | re.UNICODE)
        if m:
            fixed_expression = "%s%s" % (m.group(1), symbol)
            currency = symbol
            amount = m.group(1)
            break
        
    return fixed_expression, currency, amount

# £264.00
# $115.50
# ¥100
def cmd_calculate(ensoapi, expression = None):
    u""" Calculate %s
    <p>
    Calculate mathematical expression.<br/><br/>
    Supported operators:<br/>
    <code>
    -, +, /, *, ^, **, (, ), %, mod
    </code><br/>
    functions:<br/>
    <code>
    mod, currency, acos, asin, atan, atan2, ceil, cos, cosh,
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
    </code><br/>
    currency conversion:<br/>
    <code>150eur in usd</code><br/>
    <code>1 gbp to eur</code><br/>
    <code>usd in eur</code><br/>
    <code>to eur</code> 
    (when some text representing amount + currency is selected, 
    like $1000, gbp10, €4.5, 10 GBP)<br/>
    </p>
    """
    #_cache_currencies()
    #print "TO CURRENCIES: " + "|".join(_to_currencies.keys())
    seldict = ensoapi.get_selection()
    if seldict.get(u"text"):
        selected_text = seldict[u'text'].strip().strip("\0")
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
        + ['abs', 'chr\([0-9]+\)', 'hex\([0-9]+\)', 'mod', 'currency']
        # functions of math module (ex. __xxx__)
        + math_funcs)

    print whitelist

    math_funcs_dict = dict([ (mf, eval('math.%s' % mf)) for mf in math_funcs])
    math_funcs_dict['abs'] = abs
    math_funcs_dict['chr'] = chr
    math_funcs_dict['hex'] = hex
    math_funcs_dict['currency'] = currency

    expression = expression.replace(' mod ', ' % ')

    currconv_match = complete_currency_re.search(expression)
    if currconv_match:
        #print "currconv match"
        if currconv_match.group(1):
            amount = currconv_match.group(1)
            print amount
        else:
            amount_str = (selected_text if selected_text else "1").replace(" ", "")
            print amount_str
            try:
                amount = float(amount_str)
            except:
                amount = 1
        
        #print  r"(.*)(" + "|".join(_from_currencies.keys()) + ") (in|to) (" + "|".join(_to_currencies.keys()) + ")(.*)"
        expression = "currency(%s, '%s', '%s') %s" % (
            amount, 
            currconv_match.group(2).upper(), 
            currconv_match.group(4).upper(), 
            currconv_match.group(5))
        #print expression
    else:
        currconv_match = partial_currency_re.match(expression.strip())
        if currconv_match:
            #print "partial match"
            amount_str, from_currency, amount = _handle_currency_symbols(
                (selected_text if selected_text else "1").replace(" ", ""))
            #print amount_str, from_currency, amount
            #print currconv_match.groups()
            expression = "currency(%s, '%s', '%s') %s" % (
                amount, 
                from_currency, 
                currconv_match.group(2).upper(),
                currconv_match.group(3)
            )
        #print expression

    #print expression = expression.replace(' in ', ' % ')

    #print math_funcs_dict

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
                    pasted = selection.set({ "text" : expression.strip() + " = " + unicode(result) })
                else:
                    pasted = selection.set({ "text" : unicode(result) })
            
            if not pasted:
                displayMessage(u"<p>%s</p><caption>%s</caption>" % (result, expression))
        except Exception, e:
            logging.info(e)
            ensoapi.display_message("Invalid syntax", "Error")
    else:
        ensoapi.display_message("Invalid expression", "Error")


from enso.commands import CommandManager
paste_command = CommandManager.get().getCommand("paste")
if paste_command:
    print dir(paste_command)

def cmd_calculation_paste(ensoapi):
    global last_calculation
    
    #paste_command = CommandManager.get().getCommand("paste")
    #if paste_command:
    #    print dir(paste_command)
    #    paste_command.valid_args

    selection.set({ "text": unicode(last_calculation) })

# vim:set tabstop=4 shiftwidth=4 expandtab:
