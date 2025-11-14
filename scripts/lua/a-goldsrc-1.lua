-- Auto-generated list of GoldSrc entities

------------------------
-- Set coop constants --
------------------------

gLevelValues.fixCollisionBugs = 1

---------------------------
-- Create goldsrc global --
---------------------------

if gGoldsrc == nil then
    gGoldsrc = {
        classes = {},
        levels = {},
        objToEnt = {},
    }
end

---------------
-- Utilities --
---------------

function goldsrc_add_class(classname, init_function)
    gGoldsrc.classes[classname] = init_function
end

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

function goldsrc_intersects_aabb(pos, radius, ent)
    local min = ent._aabb.min
    local max = ent._aabb.max

    -- Find the closest point on the AABB to the sphere center
    local closest_x = math.max(min[1], math.min(pos.x, max[1]))
    local closest_y = math.max(min[2], math.min(pos.y, max[2]))
    local closest_z = math.max(min[3], math.min(pos.z, max[3]))

    -- Compute squared distance from sphere center to closest point
    local dx = pos.x - closest_x
    local dy = pos.y - closest_y
    local dz = pos.z - closest_z
    local dist_sq = dx*dx + dy*dy + dz*dz

    return dist_sq <= radius*radius
end

------------------
-- Brush entity --
------------------

local function bhv_goldsrc_brush_init(obj)
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
        gGoldsrc.objToEnt[obj] = entity
        if entity._geo ~= nil then
            obj_set_model_extended(obj, entity._geo)
        else
            djui_chat_message_create('couldnt find geo ' .. obj.oBehParams)
        end

        if entity._col ~= nil then
            obj.oCollisionDistance = 999999999
            obj.collisionData = entity._col
        else
            djui_chat_message_create('couldnt find col' .. obj.oBehParams)
        end

        if gGoldsrc.classes[entity.classname] ~= nil then
            gGoldsrc.classes[entity.classname](entity, obj)
        end
    end
end

local function bhv_goldsrc_brush_loop(obj)
    local entity = goldsrc_get_entity(obj.oBehParams)
    if entity ~= nil and entity._class ~= nil then
        entity._class:update()
    end
end

id_bhvGoldsrcBrush = hook_behavior(nil, OBJ_LIST_SURFACE, true, bhv_goldsrc_brush_init, bhv_goldsrc_brush_loop)

-------------------
-- Mario Actions --
-------------------

local function before_mario_update(m)
    if m.playerIndex ~= 0 then
        return
    end

    if m.controller.buttonPressed & B_BUTTON ~= 0 then
        -- figure out dir
        local yaw = m.faceAngle.y
        local dir_x = sins(yaw) * 300
        local dir_y = 120
        local dir_z = coss(yaw) * 300

        -- raycast for user
        local ray = collision_find_surface_on_ray(m.pos.x, m.pos.y, m.pos.z, dir_x, dir_y, dir_z)
        if ray.surface and ray.surface.object and vec3f_dist(ray.hitPos, m.pos) < 300 then
            local obj = ray.surface.object
            if gGoldsrc.objToEnt[obj] ~= nil then
                local ent = gGoldsrc.objToEnt[obj]
                local class = ent._class
                if class ~= nil and class.use ~= nil and class:use() then
                    m.controller.buttonPressed = (m.controller.buttonPressed & ~B_BUTTON)
                    play_sound(SOUND_MENU_CLICK_FILE_SELECT, gGlobalSoundSource)
                end
            end
        end
    end
end


hook_event(HOOK_BEFORE_MARIO_UPDATE, before_mario_update)