import bpy
import sys
import os

####################
# combine into uv2 #
####################

def get_mesh_signature(obj):
    """Return a simple signature for comparing mesh geometry."""
    if obj.type != 'MESH':
        return None
    mesh = obj.data
    return (len(mesh.vertices), len(mesh.polygons))

def assign_lightmap_texture(orig_mat, dup_mat):
    """
    Assign the diffuse/lightmap texture from dup_mat to orig_mat.
    Assumes both materials are node-based.
    """
    if not orig_mat.use_nodes or not dup_mat.use_nodes:
        return

    orig_mat["lightmap_texture"] = dup_mat.name + '.png'

def assign_materials_per_face(original, duplicate):
    """
    For each polygon in 'original', assign a material that corresponds to the
    material index on the duplicate. Duplicates materials as needed and tags
    each with its lightmap index.
    """
    if not original.material_slots or not duplicate.material_slots:
        return
    
    if len(original.data.polygons) != len(duplicate.data.polygons):
        return

    # Mapping: (original material name, lightmap index) -> material slot index
    mat_map = {}

    for poly_idx, poly in enumerate(original.data.polygons):
        dup_mat_index = duplicate.data.polygons[poly_idx].material_index
        orig_mat_index = poly.material_index
        
        if dup_mat_index >= len(duplicate.material_slots) or orig_mat_index >= len(original.material_slots):
            continue
        
        orig_mat = original.material_slots[orig_mat_index].material
        dupe_mat = duplicate.material_slots[dup_mat_index].material

        key = (orig_mat.name, dup_mat_index)
        if key in mat_map:
            # Already have a material for this lightmap index
            poly.material_index = mat_map[key]
        else:
            # Need to assign or duplicate material
            if "lightmap_texture" in orig_mat and orig_mat["lightmap_texture"] != dupe_mat.name:
                # Duplicate material for this lightmap index
                mat_copy = orig_mat.copy()
                mat_copy.name = f"{orig_mat.name}#LM{dup_mat_index}"
                mat_copy["lightmap_texture"] = dupe_mat.name
                # Add new material slot
                original.data.materials.append(mat_copy)
                slot_index = len(original.material_slots) - 1
                mat_map[key] = slot_index
                poly.material_index = slot_index
                print(f"Duplicated material {orig_mat.name} → {mat_copy.name} for face {poly_idx}")
            else:
                # Assign lightmap index property to original material
                orig_mat["lightmap_texture"] = dupe_mat.name
                mat_map[key] = orig_mat_index
                poly.material_index = orig_mat_index

def combine_duplicate_uvs():
    """
    For each mesh object in the current Blender scene, if there is a duplicate
    (NAME.001) with the same geometry, copy its UVs to a new UVMap_2 on the original
    and assign materials per-face to correspond to the lightmap.
    """
    pairs = []
    for obj in bpy.data.objects:
        if obj.type != 'MESH' or '.' in obj.name:
            continue

        base_name = obj.name
        dup_name = base_name + ".001"

        if dup_name in bpy.data.objects:
            pairs.append((base_name, dup_name))

    for base_name, dup_name in pairs:
        original = bpy.data.objects.get(base_name)
        duplicate = bpy.data.objects.get(dup_name)
        if not original or not duplicate:
            continue

        if get_mesh_signature(original) != get_mesh_signature(duplicate):
            continue

        if not duplicate.data.uv_layers:
            print(f"{dup_name} has no UVs, skipping")
            continue

        dup_uv = duplicate.data.uv_layers.active
        if not dup_uv:
            print(f"{dup_name} has no active UV map, skipping")
            continue

        # --- Create new UV map ---
        uv_layers = original.data.uv_layers
        new_uv = uv_layers.new(name="Lightmap")
        print(f"Created Lightmap on {base_name}")

        # Copy UVs
        src_uv_layer = dup_uv.data
        dst_uv_layer = new_uv.data
        if len(src_uv_layer) == len(dst_uv_layer):
            for i in range(len(src_uv_layer)):
                dst_uv_layer[i].uv = src_uv_layer[i].uv
            print(f"Copied UVs from {dup_name} → {base_name}")
        else:
            print(f"UV data mismatch between {base_name} and {dup_name}, skipping")
            continue

        # --- Material per-face assignment ---
        assign_materials_per_face(original, duplicate)

        # Remove duplicate object
        bpy.data.objects.remove(duplicate, do_unlink=True)
        print(f"Deleted {dup_name}")

# -----------------------
# Main script entry
# -----------------------

# Get .blend file from command-line arguments after "--"
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]  # keep argv as a list
else:
    argv = []

if len(argv) < 1:
    print("Usage: blender --background --python combine-into-uv2.py -- BLEND_FILE")
    sys.exit(1)

blend_file_path = argv[0]
if not os.path.isfile(blend_file_path):
    print(f"Error: .blend file does not exist: {blend_file_path}")
    sys.exit(1)

# Open the .blend file
bpy.ops.wm.open_mainfile(filepath=blend_file_path)

# Run the UV combine logic
combine_duplicate_uvs()

# Save to a new file in the same folder
folder = os.path.dirname(blend_file_path)
save_path = os.path.join(folder, "2-combine-uv2.blend")
bpy.ops.wm.save_mainfile(filepath=save_path)
print(f"Blender file saved: {save_path}")
