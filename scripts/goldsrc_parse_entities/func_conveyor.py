from . import *

parse_classes['func_conveyor'] = {
    "classname": parse_string,
    "model": parse_string,

    "targetname": parse_string,
    "target": parse_string,

    "renderfx": parse_int,
    "rendermode": parse_int,
    "renderamt": parse_int,
    "rendercolor": parse_color,

    "angles": parse_angles,
    "speed": parse_int,

    "_minlight": parse_float,
    "light_origin": parse_string,
    "zhlt_lightflags": parse_int,

    "spawnflags": parse_int,

    # Exporting settings
    "_export_geo": True,
    "_export_col": True,
}
