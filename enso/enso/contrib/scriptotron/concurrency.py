from enso.contrib.scriptotron.tracebacks import safetyNetted
from enso.contrib.scriptotron.events import EventResponderList

class GeneratorManager( object ):
    """
    Responsible for managing generators in a way similar to tasklets
    in Stackless Python by iterating the state of all registered
    generators on every timer tick.
    """

    def __init__( self, eventManager ):
        self.__generators = EventResponderList(
            eventManager,
            "timer",
            self.__onTimer
            )

    @safetyNetted
    def __callGenerator( self, generator, keepAlives ):
        try:
            generator.next()
            keepAlives.append( generator )
        except StopIteration:
            pass

    def __onTimer( self, msPassed ):
        keepAlives = []
        for generator in self.__generators:
            self.__callGenerator( generator, keepAlives )
        self.__generators[:] = keepAlives

    def reset( self ):
        self.__generators[:] = []

    def add( self, generator ):
        self.__generators.append( generator )
