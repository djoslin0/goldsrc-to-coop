--------------
-- Requires --
--------------

require('bhv_goldsrc_entity')
local GoldsrcGfxUtils = require("goldsrc_gfx_utils")

------------------------
-- Set coop constants --
------------------------

gLevelValues.fixCollisionBugs = 1
gLevelValues.cellHeightLimit = 32760
gLevelValues.floorLowerLimit = -32760
gLevelValues.floorLowerLimitMisc = -32760
gLevelValues.floorLowerLimitShadow = -32760
gLevelValues.floorNormalMinY = 0.1
gLevelValues.ceilNormalMaxY = -0.1

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

local dt = 1/30

-- These variables must be cleared on level init
local sAttackCache = {}
local sCachedLevelNum = -1
local sEventQueue = {}
local sGoldsrcTime = 0

--------------
-- Localize --
--------------
local max = math.max
local min = math.min

---------------
-- Utilities --
---------------

function goldsrc_get_type(ent)
    if ent.marioObj ~= nil then
        return 'player'
    elseif ent.ent ~= nil then
        return ent.ent.classname
    end

    return nil
end

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
                if level_dict.targetnameToEnt[ent.targetname] then
                    table.insert(level_dict.targetnameToEnt[ent.targetname], ent)
                else
                    level_dict.targetnameToEnt[ent.targetname] = { ent }
                end
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

function goldsrc_get_entities_from_target_name(target_name)
    local level_dict = gGoldsrc.levels[sCachedLevelNum]
    if not level_dict then return {} end
    return level_dict.targetnameToEnt[target_name]
end

function goldsrc_queue_event(delay, fn)
    if delay <= 0 then
        fn()
    else
        sEventQueue[#sEventQueue+1] = { sGoldsrcTime + delay, fn }
    end
end

function goldsrc_apply_damage(target, dmg, damager)
    -- get and validate target
    if target == nil then return end

    if target.marioObj ~= nil then
        local scaled_damage = (0x880 - 0xFF) * (dmg / 100.0) * dt
        if scaled_damage < 1 and dmg > 0 then
            scaled_damage = 1
        end
        target.health = target.health - scaled_damage
        if target.health < 0xFF then
            target.health = 0xFF
        end
        if target.health > 0x880 then
            target.health = 0x880
        end
        return
    end


    if target._class == nil then return end
    if target._class.apply_damage == nil then return end

    target._class:apply_damage(dmg, damager)
end

function goldsrc_fire_target(target_name, activator, caller, use_type, value, delay)
    local targets = goldsrc_get_entities_from_target_name(target_name)
    if not targets then return end

    for _, target in ipairs(targets) do
        if target and target._class and target._class.trigger then
            goldsrc_queue_event(delay, function()
                target._class:trigger(target, activator, caller, use_type, value)
            end)
        end
    end
end

function goldsrc_kill_target(target_name, delay)
    local targets = goldsrc_get_entities_from_target_name(target_name)
    if not targets then return end

    for _, target in ipairs(targets) do
        if target and target._class then
            goldsrc_queue_event(delay, function()
                target._class.enabled = false
                local obj = target._class.obj
                if obj ~= nil then
                    obj.header.gfx.node.flags = obj.header.gfx.node.flags | GRAPH_RENDER_INVISIBLE
                end
            end)
        end
    end
end

function goldsrc_message(message)
    djui_chat_message_create(message)
end

function goldsrc_intersects_aabb(pos, radius, aabb)
    local aabb_min = aabb.min
    local aabb_max = aabb.max

    -- Find the closest point on the AABB to the sphere center
    local closest_x = max(aabb_min[1], min(pos.x, aabb_max[1]))
    local closest_y = max(aabb_min[2], min(pos.y, aabb_max[2]))
    local closest_z = max(aabb_min[3], min(pos.z, aabb_max[3]))

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
                dmgToApply = max(0, dmgToApply)
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

-----------
-- Hooks --
-----------

local function update_water_level(m)
    local pos = m.pos
    local px = pos.x
    local py = pos.y
    local pz = pos.z

    local radiusSq = 80*80

    local level_data = gGoldsrc.levels[gNetworkPlayers[0].currLevelNum]
    if not level_data then return end

    local water_aabbs = gGoldsrc.levels[gNetworkPlayers[0].currLevelNum].water_aabbs
    local water_level = gLevelValues.floorLowerLimit

    for i = 1, #water_aabbs do
        local aabb = water_aabbs[i]
        local minv = aabb.min
        local maxv = aabb.max

        local cx = (px < minv[1]) and minv[1] or (px > maxv[1] and maxv[1] or px)
        local cy = (py < minv[2]) and minv[2] or (py > maxv[2] and maxv[2] or py)
        local cz = (pz < minv[3]) and minv[3] or (pz > maxv[3] and maxv[3] or pz)

        local dx = px - cx
        local dy = py - cy
        local dz = pz - cz

        if dx*dx + dy*dy + dz*dz <= radiusSq then
            local maxy = maxv[2]
            if maxy > water_level then
                water_level = maxy
            end
        end
    end

    set_water_level(0, water_level, false)
end


local function before_mario_update(m)
    update_water_level(m)

    if m.playerIndex ~= 0 then
        return
    end

    -- use key detection
    if m.controller.buttonPressed & B_BUTTON ~= 0 then
        -- figure out dir
        local yaw = m.faceAngle.y
        local dir_dist = 80 * gGoldsrc.toSm64Scalar
        local dir_x = sins(yaw) * dir_dist
        local dir_y = 120
        local dir_z = coss(yaw) * dir_dist

        -- raycast for user
        local ray = collision_find_surface_on_ray(m.pos.x, m.pos.y, m.pos.z, dir_x, dir_y, dir_z)
        if ray.surface and ray.surface.object then
            local obj = ray.surface.object
            if gGoldsrcObjToEnt[obj] ~= nil then
                local ent = gGoldsrcObjToEnt[obj]
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
    gGoldsrcObjToEnt = {}
    sCachedLevelNum = gNetworkPlayers[0].currLevelNum
    sGoldsrcTime = 0

    if gGoldsrc.levels[sCachedLevelNum] ~= nil then
        GoldsrcGfxUtils.replace_gfx_textures(gMarioStates[0].area.root.node)
    end
end

hook_event(HOOK_ON_LEVEL_INIT, on_level_init)

-------------

return gGoldsrc