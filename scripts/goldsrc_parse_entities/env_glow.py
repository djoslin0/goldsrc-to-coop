from . import *

parse_classes['env_glow'] = {
    "classname": parse_string,
    "model": parse_string,

    "targetname": parse_string,
    "model": parse_string,
    "scale": parse_float,

    "angles": parse_angles,

    "renderfx": parse_int,
    "rendermode": parse_int,
    "renderamt": parse_int,
    "rendercolor": parse_color,

    # Exporting settings
    "_export_geo": False,
    "_export_col": False,
}
