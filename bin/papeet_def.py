# -*- coding: utf-8 -*-
from enum import IntEnum

class LEDCntrl(IntEnum):
    NONE = 0
    START = 1
    STOP = 2

class LEDPattern(IntEnum):
    NONE = 0
    WIPE = 1
    BRIGHT = 2
    BRIGHT2 = 3

class ServCntrl(IntEnum):
    NONE = 0
    START = 1
    STOP = 2
    ON = 3
    OFF = 4

class ServType(IntEnum):
    MOUSE = 0
    HEAD = 1
    BODY = 2

class ServPattern(IntEnum):
    NONE = 0
    MOUSE_OPEN = 1
    MOUSE_CLOSE = 2
    MOUSE_PAKUPAKU = 3
    HEAD_CENTER = 4
    HEAD_UP = 5
    HEAD_DOWN = 6
    HEAD_UNUN = 7
    BODY_CENTER = 8
    BODY_RIGHT = 9
    BODY_RIGHT_SMALL =10
    BODY_LEFT = 11
    BODY_LEFT_SMALL = 12
    BODY_SWING = 13
