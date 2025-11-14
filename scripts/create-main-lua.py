import os
import sys

template = """
-- name: Goldsrc Port - $LEVELNAME
-- description: Goldsrc Port - $LEVELNAME

gLevelValues.fixCollisionBugs = 1

LEVEL_$LEVELUNAME = level_register("level_$LEVELNAME_entry", COURSE_BOB, "$LEVELNAME", "$LEVELNAME", 28000, 0x28, 0x28, 0x28)

hook_event(HOOK_ON_SYNC_VALID, function()
    if gNetworkPlayers[0].currLevelNum ~= LEVEL_$LEVELUNAME then
        warp_to_level(LEVEL_$LEVELUNAME, 1, 0)
    end
end)
"""

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_level_script.py <levelname>")
        sys.exit(1)

    levelname = sys.argv[1]
    leveluname = levelname.upper()

    # Replace placeholders
    result = (
        template
        .replace("$LEVELNAME", levelname)
        .replace("$LEVELUNAME", leveluname)
        .strip()
    )

    # Build output path
    output_dir = os.path.join("output", levelname, "mod")
    output_path = os.path.join(output_dir, "main.lua")

    # Create directories if needed
    os.makedirs(output_dir, exist_ok=True)

    # Write file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"✅ File generated at: {output_path}")

if __name__ == "__main__":
    main()
