import bpy
import bmesh
import os
import sys
from mathutils import Vector
from mathutils.kdtree import KDTree

# Threshold for "near edge" and merge distance
THRESHOLD = 0.005

# -------------------------------
# Helper function: process a single mesh object
# -------------------------------
def process_object(obj, phase):
    if obj.type != 'MESH':
        return 0

    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)

    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # Count vertices at start
    verts_before = len(bm.verts)

    # -------------------------------
    # 1) INITIAL MERGE BY DISTANCE
    # -------------------------------
    removed = bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=THRESHOLD) or {}
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # -------------------------------
    # 2) INITIAL TRIANGULATE
    # -------------------------------
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    if len(bm.verts) == 0 or len(bm.edges) == 0:
        bm.to_mesh(me)
        bm.free()
        return 0

    # -------------------------------
    # 3) BUILD KD TREE FOR EDGE CENTERS
    # -------------------------------
    edge_count = len(bm.edges)
    kd = KDTree(edge_count)
    edge_map = []
    max_half = 0.0

    for i, e in enumerate(bm.edges):
        v1, v2 = e.verts
        center = (v1.co + v2.co) * 0.5
        kd.insert(center, i)
        edge_map.append(e)
        half = (v2.co - v1.co).length * 0.5
        if half > max_half:
            max_half = half
    kd.balance()
    search_radius = THRESHOLD + max_half

    def closest_point_and_t(pt, a, b):
        ab = b - a
        ab_len_sq = ab.length_squared
        if ab_len_sq == 0:
            return a.copy(), 0.0
        t = max(0.0, min(1.0, (pt - a).dot(ab) / ab_len_sq))
        return a + ab * t, t

    # -------------------------------
    # 4) COLLECT EDGE SPLIT REQUESTS
    # -------------------------------
    pending_splits = {}
    for v in bm.verts:
        A = v.co
        hits = kd.find_range(A, search_radius)
        for hit in hits:
            idx = hit[1] if len(hit) == 3 else hit[1]
            e = edge_map[idx]
            if v in e.verts:
                continue
            v1, v2 = e.verts
            B, t = closest_point_and_t(A, v1.co, v2.co)
            if (A - B).length < THRESHOLD:
                pending_splits.setdefault(e, []).append(t)

    # -------------------------------
    # 5) APPLY EDGE SPLITS
    # -------------------------------
    for e, t_list in pending_splits.items():
        unique_t = sorted(set(t_list))
        for t in unique_t:
            try:
                bmesh.utils.edge_split(e, e.verts[0], t)
            except:
                pass

    # -------------------------------
    # 6) POST-SPLIT MERGE BY DISTANCE
    # -------------------------------
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=THRESHOLD) or {}

    # -------------------------------
    # 7) FINAL TRIANGULATE
    # -------------------------------
    bmesh.ops.triangulate(bm, faces=bm.faces)

    # -------------------------------
    # 8) SHADE FLAT
    # -------------------------------
    for face in bm.faces:
        face.smooth = False

    # -------------------------------
    # 9) WRITE BACK TO MESH
    # -------------------------------
    bm.to_mesh(me)
    bm.free()

    # Count vertices after processing
    verts_after = len(me.vertices)
    created_count = verts_after - verts_before
    
    print(f"\nProcessed object '{obj.name}', phase {phase}: {created_count} vertices")

    return created_count

# -------------------------------
# MAIN: process all mesh objects in the scene
# -------------------------------
def process_objects():
    total_created = 0
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            for i in range(3):
                total_created += process_object(obj, i)
    print(f"Total vertices created across scene: {total_created}")

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
    print("Usage: blender --background --python fix-up-mesh.py -- BLEND_FILE")
    sys.exit(1)

blend_file_path = argv[0]
if not os.path.isfile(blend_file_path):
    print(f"Error: .blend file does not exist: {blend_file_path}")
    sys.exit(1)

# Open the .blend file
bpy.ops.wm.open_mainfile(filepath=blend_file_path)

# Run the UV combine logic
process_objects()

# Save to a new file in the same folder
folder = os.path.dirname(blend_file_path)
save_path = os.path.join(folder, "3-fix-up-mesh.blend")
bpy.ops.wm.save_mainfile(filepath=save_path)
print(f"Blender file saved: {save_path}")
