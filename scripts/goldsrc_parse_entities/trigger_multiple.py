from . import *

parse_classes['trigger_multiple'] = {
    "classname": parse_string,
    "model": parse_string,

    "targetname": parse_string,
    "target": parse_string,
    "master": parse_string,

    "delay": parse_float,
    "wait": parse_float,
    "killtarget": parse_string,

    "netname": parse_string,
    "sounds": parse_string,
    "message": parse_string,

    # Exporting settings
    "_export_geo": False,
    "_export_col": False,
}
