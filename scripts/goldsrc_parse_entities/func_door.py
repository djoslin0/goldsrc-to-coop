from . import *

parse_classes['func_door'] = {
    "classname": parse_string,
    "model": parse_string,

    "targetname": parse_string,
    "globalname": parse_string,
    "master": parse_string,

    "angles": parse_angles,
    "target": parse_string,
    "delay": parse_float,
    "killtarget": parse_string,
    "netname": parse_string,

    "speed": parse_float_scaled,
    "wait": parse_float,
    "lip": parse_float_scaled,

    "dmg": parse_int,
    "message": parse_string,
    "health": parse_int,
    "healthvalue": parse_int,

    "renderfx": parse_int,
    "rendermode": parse_int,
    "renderamt": parse_int,
    "rendercolor": parse_color,

    "movesnd": parse_int,
    "stopsnd": parse_int,
    "locked_sound": parse_int,
    "unlocked_sound": parse_int,
    "locked_sentence": parse_int,
    "unlocked_sentence": parse_int,

    "_minlight": parse_float,
    "light_origin": parse_string,
    "zhgt_lightflags": parse_int,

    "spawnflags": parse_int,
}
