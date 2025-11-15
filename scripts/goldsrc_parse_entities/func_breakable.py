from . import *

parse_classes['func_breakable'] = {
    "classname": parse_string,
    "model": parse_string,

    "targetname": parse_string,
    "globalname": parse_string,

    "material": parse_int,
    "spawnobject": parse_int,
    "target": parse_string,
    "health": parse_int,
    "explosion": parse_int,
    "delay": parse_float,
    "gibmodel": parse_string,
    "explodemagnitude": parse_int,

    "renderfx": parse_int,
    "rendermode": parse_int,
    "renderamt": parse_int,
    "rendercolor": parse_color,

    "_minlight": parse_float,
    "light_origin": parse_string,
    "zhlt_lightflags": parse_int,

    "spawnflags": parse_int,
}
