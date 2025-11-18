from . import *

parse_classes['trigger_hurt'] = {
    "classname": parse_string,
    "model": parse_string,

    "targetname": parse_string,
    "target": parse_string,
    "master": parse_string,

    "delay": parse_float,

    "dmg": parse_int,
    "damagetype": parse_int,

    # Exporting settings
    "_export_geo": False,
    "_export_col": False,
}
