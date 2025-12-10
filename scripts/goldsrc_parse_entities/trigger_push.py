from . import *

parse_classes['trigger_push'] = {
    "classname": parse_string,
    "model": parse_string,

    "target": parse_string,
    "targetname": parse_string,
    "master": parse_string,

    "delay": parse_float,
    "killtarget": parse_string,
    "netname": parse_string,

    "sounds": parse_int,
    "message": parse_string,
    "angles": parse_angles,
    "speed": parse_int,

    "spawnflags": parse_int,

    # Exporting settings
    "_export_geo": True,
    "_export_col": True,
}
