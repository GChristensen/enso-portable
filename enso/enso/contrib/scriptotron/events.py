class EventResponderList( object ):
    """
    Behaves like a list with limited functionality.  When the list is
    non-empty, an event handler is registered for a particular event
    and called whenever the event occurs.  When the list is empty, the
    event handler is unregistered and will not be called until it
    becomes non-empty again.
    """

    def __init__( self, eventManager, eventName, responderFunc ):
        self.__eventManager = eventManager
        self.__eventName = eventName
        self.__responderFunc = responderFunc
        self.__isRegistered = False
        self.__items = []

    def append( self, item ):
        self.__items.append( item )
        self.__onItemsChanged()

    def __setitem__( self, i, j ):
        if ( not isinstance( i, slice ) or 
             not (i.start == None and i.stop == None) ):
            raise NotImplementedError()
        self.__items[:] = j
        self.__onItemsChanged()

    def __iter__( self ):
        for item in self.__items:
            yield item

    def __onItemsChanged( self ):
        if self.__items and (not self.__isRegistered):
            self.__eventManager.registerResponder(
                self.__responderFunc,
                self.__eventName
                )
            self.__isRegistered = True
        elif self.__isRegistered and (not self.__items):
            self.__eventManager.removeResponder( self.__responderFunc )
            self.__isRegistered = False
