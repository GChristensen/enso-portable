import enso.providers

_graphics = enso.providers.getInterface("graphics")

from enso.graphics.measurement import pointsToPixels, pixelsToPoints

def getDesktopOffset():
    left, top = _graphics.getDesktopOffset()
    left = pixelsToPoints(left)
    top = pixelsToPoints (top)
    return (left, top)

def getDesktopSize():
    width, height = _graphics.getDesktopSize()
    width = pixelsToPoints(width)
    height = pixelsToPoints(height)
    return (width, height)
