-- Auto-generated list of GoldSrc entities

------------------------
-- Set coop constants --
------------------------

gLevelValues.fixCollisionBugs = 1

----------------------
-- Create variables --
----------------------

if gGoldsrc == nil then
    gGoldsrc = {
        classes = {},
        levels = {},
        toSm64Scalar = 100/25,
    }
end

-- These variables must be cleared on level init
local sAttackCache = {}
local sObjToEnt = {}
local sCachedLevelNum = -1
local sEventQueue = {}
local sGoldsrcTime = 0

---------------
-- Utilities --
---------------

function goldsrc_after_level_defined(level_dict)
    -- remember targetnameToEnt
    level_dict.targetnameToEnt = {}
    for _, ent in ipairs(level_dict.entities) do
        if ent.targetname ~= nil then
            should_link = true
            if ent._class and ent._class.should_link then
                should_link = ent._class:should_link()
            end
            if should_link then
                level_dict.targetnameToEnt[ent.targetname] = ent
            end
        end
    end
end

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

function goldsrc_get_entities()
    local levelnum = gNetworkPlayers[0].currLevelNum
    return gGoldsrc.levels[levelnum].entities
end

function goldsrc_get_ent_from_target_name(target_name)
    local level_dict = gGoldsrc.levels[sCachedLevelNum]
    if not level_dict then return nil end
    return level_dict.targetnameToEnt[target_name]
end

function goldsrc_queue_event(delay, fn)
    if delay <= 0 then
        fn()
    else
        sEventQueue[#sEventQueue+1] = { sGoldsrcTime + delay, fn }
    end
end

function goldsrc_fire_target(target_name, activator, caller, use_type, value, delay)
    -- get and validate target
    local target = goldsrc_get_ent_from_target_name(target_name)
    if target == nil then return end
    if target._class == nil then return end
    if target._class.trigger == nil then return end

    -- trigger or queue
    goldsrc_queue_event(delay, function()
        target._class:trigger(target_name, activator, caller, use_type, value)
    end)
end

function goldsrc_kill_target(target_name, delay)
    -- get and validate target
    local target = goldsrc_get_ent_from_target_name(target_name)
    if target == nil then return end
    if target._class == nil then return end

    -- trigger or queue
    goldsrc_queue_event(delay, function()
        -- delete obj
        if target._class.obj ~= nil then
            obj_mark_for_deletion(target._class.obj)
        end

        -- delete class
        target._class = nil
    end)
end

function goldsrc_message(message)
    djui_chat_message_create(message)
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

function goldsrc_apply_radius_damage(x, y, z, radius, damage)
    local entities = gGoldsrc.levels[sCachedLevelNum].entities
    for _, ent in ipairs(entities) do
        if ent._class and ent._class.obj and ent._class.apply_damage then
            local class = ent._class
            local obj = class.obj

            local dx = obj.oPosX - x
            local dy = obj.oPosY - y
            local dz = obj.oPosZ - z
            local dist = math.sqrt(dx*dx + dy*dy + dz*dz)

            if dist <= radius then
                local dmgToApply = damage * (1 - dist / radius)
                dmgToApply = math.max(0, dmgToApply)
                class:apply_damage(dmgToApply)

                -- TODO: push?
                --if obj.is_pushable then
                --    obj.vx = obj.vx + dx/dist * dmgToApply
                --    obj.vy = obj.vy + dy/dist * dmgToApply
                --    obj.vz = obj.vz + dz/dist * dmgToApply
                --end
            end
        end
    end
end

function goldsrc_is_standing_on_obj(m, obj)
    return m.floor.object == obj and (m.action & (ACT_FLAG_STATIONARY|ACT_FLAG_MOVING)) ~= 0
end

function goldsrc_is_touching_obj(m, obj)
    return (m.floor.object == obj and (m.action & (ACT_FLAG_STATIONARY|ACT_FLAG_MOVING)) ~= 0)
        or (m.wall and m.wall.object == obj)
end

local function is_attacking_obj(m, obj)
    if not goldsrc_is_touching_obj(m, obj) then
        return false
    end

    local action = m.action

    -- Must be an attacking action
    if (action & ACT_FLAG_ATTACKING) == 0 then
        return false
    end

    -- Standard attacks
    if (m.flags & (MARIO_PUNCHING | MARIO_KICKING | MARIO_TRIPPING)) ~= 0 then
        return true
    end

    -- Ground pound actions
    if (action == ACT_GROUND_POUND and m.vel.y < 0) or
       (action == ACT_GROUND_POUND_LAND and m.vel.y < 0 and m.actionState == 0) then
        return true
    end

    -- Slide kick actions
    if action == ACT_SLIDE_KICK or action == ACT_SLIDE_KICK_SLIDE then
        return true
    end

    -- Shell riding
    if (action & ACT_FLAG_RIDING_SHELL) ~= 0 then
        return true
    end

    return false
end

function goldsrc_is_attacking_obj(m, obj)
    if sAttackCache[obj] == m then
        return false
    end

    attacking = is_attacking_obj(m, obj)

    -- Save in cache to prevent double attacks
    if attacking then
        sAttackCache[obj] = m
    end

    return attacking
end

-------------
-- Effects --
-------------

function goldsrc_spawn_triangle_break_particles(obj, numTris, triModel, triSize, triAnimState)
    for i = 1, numTris do
        local triangle = spawn_non_sync_object(id_bhvBreakBoxTriangle, triModel, obj.oPosX, obj.oPosY, obj.oPosZ, nil)
        if triangle == nil then
            goto continue
        end

        triangle.oAnimState = triAnimState
        triangle.oPosY = triangle.oPosY + 100.0
        triangle.oMoveAngleYaw = random_u16()
        triangle.oFaceAngleYaw = triangle.oMoveAngleYaw
        triangle.oFaceAnglePitch = random_u16()
        triangle.oVelY = random_f32_around_zero(50.0)

        if triModel == 138 or triModel == 56 then
            triangle.oAngleVelPitch = 0xF00
            triangle.oAngleVelYaw = 0x500
            triangle.oForwardVel = 30.0
        else
            triangle.oAngleVelPitch = 0x80 * (math.floor(random_float() + 50.0))
            triangle.oForwardVel = 30.0
        end

        obj_scale(triangle, triSize)

        ::continue::
    end
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
        sObjToEnt[obj] = entity
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

-----------
-- Hooks --
-----------

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
        if ray.surface and ray.surface.object and vec3f_dist(ray.hitPos, m.pos) < 80 * gGoldsrc.toSm64Scalar then
            local obj = ray.surface.object
            if sObjToEnt[obj] ~= nil then
                local ent = sObjToEnt[obj]
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

local function update()
    -- update time
    sGoldsrcTime = sGoldsrcTime + 1 / 30

    -- update attack cache
    if next(sAttackCache) ~= nil then
        -- figure out which attack events to forget
        local remove = {}
        for k, v in pairs(sAttackCache) do
            if not is_attacking_obj(v, k) then
                table.insert(remove, k)
            end
        end

        -- Remove the collected keys
        for _, k in ipairs(remove) do
            sAttackCache[k] = nil
        end
    end

    -- trigger queues and remove from them
    local i = 1
    while i <= #sEventQueue do
        local t = sEventQueue[i]
        if t[1] <= sGoldsrcTime then
            t[2]()
            table.remove(sEventQueue, i)
        else
            i = i + 1
        end
    end
end

hook_event(HOOK_UPDATE, update)

local function on_level_init()
    local level_dict = gGoldsrc.levels[sCachedLevelNum]
    if level_dict ~= nil then
        for _, ent in ipairs(level_dict.entities) do
            ent._class = nil
        end
    end

    sAttackCache = {}
    sObjToEnt = {}
    sCachedLevelNum = gNetworkPlayers[0].currLevelNum
    sGoldsrcTime = 0
end

hook_event(HOOK_ON_LEVEL_INIT, on_level_init)