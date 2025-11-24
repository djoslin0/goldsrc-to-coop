from . import *

parse_classes['trigger_teleport'] = {
    "classname": parse_string,
    "model": parse_string,

    "target": parse_string,
    "targetname": parse_string,
    "master": parse_string,

    "delay": parse_float,
    "killtarget": parse_string,
    "netname": parse_string,

    "spawnflags": parse_int,

    # unused
    "angles": parse_angles,
    "killtarget": parse_string,
    "netname": parse_string,
    "sounds": parse_string, # unsure of type? unused anyway
    "message": parse_string,

    # Exporting settings
    "_export_geo": True,
    "_export_col": True,
}
