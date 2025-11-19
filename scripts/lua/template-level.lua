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
    }
}

local entities = goldsrc.levels[LEVEL_$LEVELUNAME].entities

----------------------
-- Register objects --
----------------------

$REGISTER_OBJECTS

--------------------
-- Remember AABBs --
--------------------

$AABBS

------------------------

goldsrc_after_level_defined(goldsrc.levels[LEVEL_$LEVELUNAME])