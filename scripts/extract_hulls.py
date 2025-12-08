import os
import json
from extract_clipnode_contents import extract_clipnode_contents_from_model, extract_node_and_leaves_contents, CONTENTS_WATER, CONTENTS_SOLID

export_model_classnames = [
    "trigger_teleport"
]

def fmt_num(n, precision=2):
    s = f"{n:.{precision}f}"
    s = s.rstrip('0').rstrip('.')   # remove trailing zeros and dot
    return s

def fmt_vec3(v, precision=2):
    return f"{fmt_num(v[0], precision)}, {fmt_num(v[1], precision)}, {fmt_num(v[2], precision)}"


def fmt_plane(p):
    return f"{{ n = {{ {fmt_vec3(p['normal'], 6)} }}, d = {fmt_num(p['dist'])} }}"

def fmt_hulls(hulls, scalar, space_indent=8):
    output = ''
    for hull in hulls:
        n_hull = convert_hull(hull, scalar)
        planes_str = ", ".join(fmt_plane(p) for p in n_hull['planes'])
        output += ( " " * space_indent + "{"
            f" min = {{ {fmt_vec3(n_hull['mins'])} }},"
            f" max = {{ {fmt_vec3(n_hull['maxs'])} }},"
            f" planes = {{ {planes_str} }},"
            " },\n"
        )
    return output

def convert_hull(hull, scalar):
    e_min = hull['mins']
    e_max = hull['maxs']

    n_hull = {}

    n_hull['mins'] = [
        e_min[0] * scalar,
        e_min[2] * scalar,
        e_max[1] * -scalar,
    ]

    n_hull['maxs'] = [
        e_max[0] * scalar,
        e_max[2] * scalar,
        e_min[1] * -scalar,
    ]

    n_planes = []
    inv_s = 1.0 / scalar

    for plane in hull['planes']:
        n = plane['normal']
        d = plane['dist']

        # Transform normal (using inverse-transpose)
        nx = n[0] * inv_s
        ny = n[2] * inv_s
        nz = -n[1] * inv_s

        # Renormalize
        length = (nx*nx + ny*ny + nz*nz) ** 0.5
        nx /= length
        ny /= length
        nz /= length

        # Dist scales with the same uniform scale
        d_new = d * scalar

        n_planes.append({
            'normal': [nx, ny, nz],
            'dist': d_new,
        })

    n_hull['planes'] = n_planes

    return n_hull


def get_model_hulls(path, bspguy_scale):
    if not os.path.exists(path):
        return ''

    scalar = 100 / -bspguy_scale
    output = ''

    # read bsp.json
    with open(path, 'r') as f:
        bsp_json = json.loads(f.read())

    # convert model hulls and export them
    for model_idx, model in bsp_json['models'].items():
        if model_idx == "0":
            continue

        if model['entity_info']['classname'] not in export_model_classnames:
            continue

        nl_hulls = extract_node_and_leaves_contents(bsp_json['nodes'], bsp_json['leaves'], model['hulls'][0]['headnode'], CONTENTS_SOLID)
        if len(nl_hulls) > 0:
            output += f"        [{model_idx}] = {{\n"
            output += fmt_hulls(nl_hulls, scalar, space_indent=12)
            output += "        },\n"

    return output

def get_water_hulls(path, bspguy_scale):
    if not os.path.exists(path):
        return ''

    scalar = 100 / -bspguy_scale
    models_with_water = []
    output = ''

    # read bsp.json
    with open(path, 'r') as f:
        bsp_json = json.loads(f.read())

    # convert node and leaf hulls from root and export them
    root_hulls = extract_node_and_leaves_contents(bsp_json['nodes'], bsp_json['leaves'], 0, CONTENTS_WATER)
    output += fmt_hulls(root_hulls, scalar)

    # convert model hulls and export them
    for model_idx, model in bsp_json['models'].items():
        if model_idx == "0":
            continue

        if model_idx in models_with_water:
            continue

        nl_hulls = extract_node_and_leaves_contents(bsp_json['nodes'], bsp_json['leaves'], model['hulls'][0]['headnode'], CONTENTS_WATER)
        if len(nl_hulls) > 0:
            output += fmt_hulls(nl_hulls, scalar)
            models_with_water.append(model_idx)

        if model_idx in models_with_water:
            continue

        hulls = extract_clipnode_contents_from_model(model, CONTENTS_WATER)
        if len(hulls) > 0:
            output += fmt_hulls(hulls, scalar)
            models_with_water.append(model_idx)

    # find entities with a skin of CONTENTS_WATER and replace their CONTENTS_SOLID
    for entity_idx, entity in bsp_json['entities'].items():
        if 'keyvalues' not in entity:
            continue
        if 'skin' not in entity['keyvalues']:
            continue
        if 'model' not in entity['keyvalues']:
            continue
        if not entity['keyvalues']['model'].startswith('*'):
            continue
        if entity['keyvalues']['skin'] != str(CONTENTS_WATER):
            continue

        model_idx = entity['keyvalues']['model'].lstrip('*')
        if model_idx in models_with_water or model_idx == '0':
            continue

        model = bsp_json['models'][model_idx]

        nl_hulls = extract_node_and_leaves_contents(bsp_json['nodes'], bsp_json['leaves'], model['hulls'][0]['headnode'], CONTENTS_SOLID)
        if len(nl_hulls) > 0:
            output += fmt_hulls(nl_hulls, scalar)
            models_with_water.append(model_idx)

    return output
