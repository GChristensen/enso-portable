import re
import win32com.client

from win32com.client import gencache
gencache.EnsureModule('{6B73A708-B5CD-408D-B20D-4690130C494E}', 0, 14, 0)

ERROR_MESSAGE = "Can not communicate with Lingvo"

LINGVO_PRIMARY_LANG = "en" # provide the primary language
LINGVO_SECONDARY_LANG = "en"

lang2code = {
    "de": 32775,
    "fr": 1036,
    "it": 1040,
    "es": 1034,
    "ua": 1058,
    "la": 1540,
    "en": 1033,
    "pt": 2070,
    "ru": 1049
    }

wordParser = re.compile(r"^(.*?)(?:\s*(?:(?=from)|(?=to)|$))")
directionParser = re.compile(r"(?:from ?(\w{2,3}))? ?(?:to ?(\w{2,3}))?$")
latinMatcher = re.compile(r"[\x00-\x7F]*");

def translate_word(ensoapi, suffix):
    word = ""
    m = wordParser.match(suffix)
    if not m is None:
        word = m.group(1)
    if word.strip() == "":
        sel = ensoapi.get_selection()
        if "text" in sel.keys():
            word = sel.get("text")

    isLatin = not(latinMatcher.match(word) is None)
    
    m = directionParser.search(suffix)
    
    from_ = m.group(1)
    if not from_ in lang2code.keys():
        from_ = LINGVO_SECONDARY_LANG if isLatin else LINGVO_PRIMARY_LANG
    
    to = m.group(2)
    if not to in lang2code.keys():
        to = LINGVO_PRIMARY_LANG if isLatin else LINGVO_SECONDARY_LANG

    lingvo = win32com.client.Dispatch("Lingvo.Application")
    try:
        lingvo.TranslateTextInDirection(word, lang2code[from_], lang2code[to])
    except:
        ensoapi.display_message(ERROR_MESSAGE)

def cmd_lingvo(ensoapi, word_from_lang_to_lang = ""):
    """Translate a word with the Abbyy Lingvo dictionary software
    Use this command to translate an argument word or
    a current selection with the Abbyy Lingvo dictionary
    software.<br/>
    You can (optionally) specify source and destination languages
    after the <i>from</i> or <i>to</i> keywords respectively, for example:
    <br/><br/>lingvo espoir from fr to ru<br/><br/>
    Supported language abbreviations are:<br/>
    de - German<br/>
    en - English<br/>
    es - Spanish<br/>
    fr - French<br/>
    it - Italian<br/>
    la - Latin<br/>
    pt - Portuguese<br/>
    ru - Russian<br/>
    ua - Ukrainan<br/>"""
    
    translate_word(ensoapi, word_from_lang_to_lang)

def cmd_quit_lingvo(ensoapi):
    """ Quit the Abbyy Lingvo dictionary software """
    lingvo = win32com.client.Dispatch("Lingvo.Application")
    try:
        lingvo.Quit()
    except:
        ensoapi.display_message(ERROR_MESSAGE)

