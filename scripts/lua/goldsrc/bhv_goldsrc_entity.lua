gGoldsrcObjToEnt = {}

local GoldsrcGfxUtils = require("/goldsrc/goldsrc_gfx_utils")

local function bhv_goldsrc_entity_init(obj)
    -- force non-sync object
    if (obj.coopFlags & COOP_OBJ_FLAG_NON_SYNC) == 0 then
        spawn_non_sync_object(id_bhvGoldsrcEntity, obj_get_model_id_extended(obj), obj.oPosX, obj.oPosY, obj.oPosZ, function(o)
            o.oBehParams = obj.oBehParams
        end)
        obj_mark_for_deletion(obj)
        return
    end
    obj.oFlags = OBJ_FLAG_UPDATE_GFX_POS_AND_ANGLE
    obj.header.gfx.skipInViewCheck = true
    obj.oOpacity = 255
    obj.oFaceAnglePitch = 0
    obj.oFaceAngleYaw = 0
    obj.oFaceAngleRoll = 0
    obj.oMoveAnglePitch = 0
    obj.oMoveAngleYaw = 0
    obj.oMoveAngleRoll = 0

    local entity = goldsrc_get_entity(obj.oBehParams)
    if entity ~= nil then
        gGoldsrcObjToEnt[obj] = entity
        if entity._geo ~= nil then
            obj_set_model_extended(obj, entity._geo)
            GoldsrcGfxUtils.replace_gfx_textures(obj.header.gfx.sharedChild)
        end

        if entity._col ~= nil then
            obj.oCollisionDistance = 999999999
            obj.collisionData = entity._col
        end

        if gGoldsrc.classes[entity.classname] ~= nil then
            gGoldsrc.classes[entity.classname](entity, obj)
        end
    end
end

local function bhv_goldsrc_entity_loop(obj)
    local entity = goldsrc_get_entity(obj.oBehParams)
    if entity ~= nil and entity._class ~= nil and entity._class.enabled then
        entity._class:update()
    end
end

id_bhvGoldsrcEntity = hook_behavior(nil, OBJ_LIST_SURFACE, true, bhv_goldsrc_entity_init, bhv_goldsrc_entity_loop)
