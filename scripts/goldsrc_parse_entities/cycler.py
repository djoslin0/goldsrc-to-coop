from . import *

parse_classes['cycler'] = {
    "classname": parse_string,
    "model": parse_string,

    "framerate": parse_float,
    "targetname": parse_string,
    "angles": parse_angles,
    "sequence": parse_int,

    "model": parse_string,
    "body": parse_int,

    "renderfx": parse_int,
    "rendermode": parse_int,
    "renderamt": parse_int,
    "rendercolor": parse_color,

    "scale": parse_float,

    # Exporting settings
    "_export_geo": False,
    "_export_col": False,
}
