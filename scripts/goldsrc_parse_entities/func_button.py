from . import *

parse_classes['func_button'] = {
    "classname": parse_string,
    "model": parse_string,

    "targetname": parse_string,
    "globalname": parse_string,
    "angles": parse_angles,
    "master": parse_string,

    "target": parse_string,
    "delay": parse_float,
    "killtarget": parse_string,
    "netname": parse_string,

    "speed": parse_float,
    "health": parse_int,
    "lip": parse_float_scaled,
    "wait": parse_float,

    "renderfx": parse_int,
    "rendermode": parse_int,
    "renderamt": parse_int,
    "rendercolor": parse_color,

    "sounds": parse_int,
    "locked_sound": parse_int,
    "unlocked_sound": parse_int,
    "locked_sentence": parse_int,
    "unlocked_sentence": parse_int,

    "_minlight": parse_float,
    "light_origin": parse_string,
    "zhgt_lightflags": parse_int,

    "spawnflags": parse_int,

    # func_door_rotating
    "distance": parse_float,

    # Exporting settings
    "_export_geo": True,
    "_export_col": True,
}
