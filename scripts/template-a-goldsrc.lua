-- Auto-generated list of GoldSrc entities

------------------------
-- Set coop constants --
------------------------

gLevelValues.fixCollisionBugs = 1

-----------------------
-- Create dictionary --
-----------------------

if gGoldsrc == nil then
  gGoldsrc = { levels = {} }
end

--------------------
-- Register level --
--------------------

LEVEL_$LEVELUNAME = level_register("level_$LEVELNAME_entry", COURSE_BOB, "$LEVELNAME", "$LEVELNAME", 28000, 0x28, 0x28, 0x28)

---------------
-- Utilities --
---------------

function goldsrc_get_entity(entity_index)
    local levelnum = gNetworkPlayers[0].currLevelNum

    local entities = gGoldsrc.levels[levelnum].entities
    if not entities then return nil end

    local idx = entity_index + 1
    if idx < 1 or idx > #entities then
        return nil
    end

    return entities[idx]
end

------------------
-- Brush entity --
------------------


function bhv_goldsrc_brush_init(obj)
    obj.oFlags = OBJ_FLAG_UPDATE_GFX_POS_AND_ANGLE
    obj.header.gfx.skipInViewCheck = true
    obj.oOpacity = 255
    obj.oFaceAnglePitch = 0
    obj.oFaceAngleYaw = 0
    obj.oFaceAngleRoll = 0
    obj.oMoveAnglePitch = 0
    obj.oMoveAngleYaw = 0
    obj.oMoveAngleRoll = 0

    goldsrcEntity = goldsrc_get_entity(obj.oBehParams)
    if goldsrcEntity ~= nil then
        djui_chat_message_create(goldsrcEntity.classname .. ' ' .. obj.oBehParams)

        if goldsrcEntity._geo ~= nil then
            obj_set_model_extended(obj, goldsrcEntity._geo)
        else
            djui_chat_message_create('couldnt find geo ' .. obj.oBehParams)
        end

        if goldsrcEntity._col ~= nil then
            obj.oCollisionDistance = 999999999
            obj.collisionData = goldsrcEntity._col
        else
            djui_chat_message_create('couldnt find col' .. obj.oBehParams)
        end
    end
end


function bhv_goldsrc_brush_loop(obj)
    load_object_collision_model()
end

id_bhvGoldsrcBrush = hook_behavior(nil, OBJ_LIST_SURFACE, true, bhv_goldsrc_brush_init, bhv_goldsrc_brush_loop)

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
