import re
import sys
import uuid
import random

def cmd_guid(ensoapi, format = "lowercase"):
    """
    Replaces selected text with a guid.
    format must be one of "lowecase", "uppercase" or "numeric".
    """
    if format == "numeric":
        ensoapi.set_selection({"text": str(uuid.uuid4().hex)})
    elif format == "uppercase":
        ensoapi.set_selection({"text": str(uuid.uuid4()).upper()})
    else:
        ensoapi.set_selection({"text": str(uuid.uuid4())})
        
cmd_guid.valid_args = ["lowercase", "uppercase", "numeric"]


random.seed()

boundsParser = re.compile(r"(?:from ?(\d+))? ?(?:to ?(\d+))?")

def cmd_random(ensoapi, from_num_to_num = ""):
    """Replaces selected text with a random number"""
    m = boundsParser.match(from_num_to_num)

    from_ = 0
    s_from = m.group(1)
    if not s_from is None:
        from_ = int(s_from)

    to = sys.maxint
    s_to = m.group(2)
    if not s_to is None:
        to = int(s_to)

    ensoapi.set_selection({"text": str(random.randint(from_, to))})
