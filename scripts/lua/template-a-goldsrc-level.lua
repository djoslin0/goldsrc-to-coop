
--------------------
-- Register level --
--------------------

LEVEL_$LEVELUNAME = level_register("level_$LEVELNAME_entry", COURSE_BOB, "$LEVELNAME", "$LEVELNAME", 28000, 0x28, 0x28, 0x28)

--------------------
-- Level Entities --
--------------------

gGoldsrc.levels[LEVEL_$LEVELUNAME] = {
    entities = {
$ENTITIES
    }
}

local entities = gGoldsrc.levels[LEVEL_$LEVELUNAME].entities

----------------------
-- Register objects --
----------------------

$REGISTER_OBJECTS

--------------------
-- Remember AABBs --
--------------------

$AABBS

------------------------

goldsrc_after_level_defined(gGoldsrc.levels[LEVEL_$LEVELUNAME])