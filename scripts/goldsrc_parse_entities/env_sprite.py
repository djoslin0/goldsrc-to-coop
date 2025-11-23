from . import *

parse_classes['env_sprite'] = {
    "classname": parse_string,
    "model": parse_string,

    "targetname": parse_string,
    "angles": parse_angles,
    "model": parse_string,
    "scale": parse_float,
    "sequence": parse_int,

    "renderfx": parse_int,
    "rendermode": parse_int,
    "renderamt": parse_int,
    "rendercolor": parse_color,

    # Exporting settings
    "_export_geo": False,
    "_export_col": False,
}
