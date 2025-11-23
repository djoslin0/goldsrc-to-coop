local goldsrc = require('goldsrc/goldsrc')
$CLASS_REQUIRES

--------------------
-- Register level --
--------------------

LEVEL_$LEVELUNAME = level_register("level_$LEVELNAME_entry", COURSE_BOB, "$LEVELNAME", "$LEVELNAME", 28000, 0x28, 0x28, 0x28)

--------------------
-- Level Entities --
--------------------

goldsrc.levels[LEVEL_$LEVELUNAME] = {
    entities = {
$ENTITIES
    },
    sprites = {}
}

local entities = goldsrc.levels[LEVEL_$LEVELUNAME].entities
local sprites =  goldsrc.levels[LEVEL_$LEVELUNAME].sprites

----------------------
-- Register objects --
----------------------

$REGISTER_OBJECTS

--------------------
-- Remember AABBs --
--------------------

$AABBS

-----------------
-- Sprite Data --
-----------------

$SPRITE_DATA

------------------------

goldsrc_after_level_defined(goldsrc.levels[LEVEL_$LEVELUNAME])