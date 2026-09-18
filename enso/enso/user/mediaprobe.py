# Deprecated: kept for backward compatibility with existing user scripts.
# Use enso.user.menu_constructors instead.

from enso.user import menu_constructors


def dictionary_probe(category, dictionary, player="", all="", findfirst=False):
    return menu_constructors.dictionary_menu(category, dictionary, player, all, findfirst)


def directory_probe(category, directory, player="", additional=None):
    return menu_constructors.directory_menu(category, directory, player, additional)


def findfirst_probe(category, dictionary, player=""):
    return menu_constructors.findfirst_menu(category, dictionary, player)