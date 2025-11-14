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

local function sphere_intersects_aabb(pos, radius, ent)
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

---------------
-- func_door --
---------------

local FuncDoorState = {
    CLOSED = 0,
    OPENING = 1,
    OPEN = 2,
    WAITING = 3,
    CLOSING = 4,
}

-- Compute the open position for a func_door entity
local function func_door_compute_open_pos(ent)
    local aabb = ent._aabb
    local lip = ent.lip or 0

    -- Compute movement direction vector from yaw (horizontal sliding)
    local yaw = (ent.angles and ent.angles[2]) or 0
    local pitch = (ent.angles and ent.angles[1]) or 0
    local rad_yaw = -math.rad(yaw)
    local rad_pitch = math.rad(pitch)

    -- Start with horizontal XY vector
    local dir = { x = math.cos(rad_yaw), y = 0, z = math.sin(rad_yaw) }

    -- If pitch indicates vertical movement (approximate threshold), use Z
    if math.abs(math.cos(rad_pitch)) < 0.01 then
        dir.x, dir.z = 0, 0
        dir.y = (pitch >= 0) and -1 or 1
    end

    -- Normalize direction vector
    local len = math.sqrt(dir.x*dir.x + dir.y*dir.y + dir.z*dir.z)
    if len ~= 0 then
        dir.x = dir.x / len
        dir.y = dir.y / len
        dir.z = dir.z / len
    end

    -- Compute all 8 AABB corners
    local corners = {
        {aabb.min[1], aabb.min[2], aabb.min[3]},
        {aabb.min[1], aabb.min[2], aabb.max[3]},
        {aabb.min[1], aabb.max[2], aabb.min[3]},
        {aabb.min[1], aabb.max[2], aabb.max[3]},
        {aabb.max[1], aabb.min[2], aabb.min[3]},
        {aabb.max[1], aabb.min[2], aabb.max[3]},
        {aabb.max[1], aabb.max[2], aabb.min[3]},
        {aabb.max[1], aabb.max[2], aabb.max[3]},
    }

    -- Project corners onto movement vector to find max extent
    local minProj, maxProj = nil, nil
    for _, c in ipairs(corners) do
        local proj = c[1]*dir.x + c[2]*dir.y + c[3]*dir.z
        if not minProj or proj < minProj then minProj = proj end
        if not maxProj or proj > maxProj then maxProj = proj end
    end

    -- Distance the door should move along dir, subtract lip
    local distance = (maxProj - minProj) - lip

    -- Compute open position
    local open_pos = {
        x = ent.closed_pos.x + dir.x * distance,
        y = ent.closed_pos.y + dir.y * distance,
        z = ent.closed_pos.z + dir.z * distance,
    }

    return open_pos
end

-- Linear move towards target
local function func_door_move(ent, dt)
    local target = ent.target_pos
    local cur = ent.current_pos
    local dx = target.x - cur.x
    local dy = target.y - cur.y
    local dz = target.z - cur.z
    local dist = math.sqrt(dx*dx + dy*dy + dz*dz)
    if dist <= 0 then
        ent.current_pos = { x = target.x, y = target.y, z = target.z }
        return true
    end
    local step = (ent.speed or 100) * dt
    if step >= dist then
        ent.current_pos = { x = target.x, y = target.y, z = target.z }
        return true
    end
    local scale = step / dist
    cur.x = cur.x + dx * scale
    cur.y = cur.y + dy * scale
    cur.z = cur.z + dz * scale
    return false
end

-- Initialization for func_door
local function func_door_init(ent)
    -- Closed pos = center of AABB
    ent.closed_pos = { x = 0, y = 0, z = 0 }
    ent.current_pos = { x = ent.closed_pos.x, y = ent.closed_pos.y, z = ent.closed_pos.z }
    ent.state = FuncDoorState.CLOSED
    ent.target_pos = ent.closed_pos
end

local function func_door_trigger(ent)
    if ent.state == FuncDoorState.CLOSED or ent.state == FuncDoorState.CLOSING then
        ent.state = FuncDoorState.OPENING
        ent.target_pos = func_door_compute_open_pos(ent)
    end
end

local function func_door_update(ent, dt)
    if ent.state == FuncDoorState.OPENING then
        if func_door_move(ent, dt) then
            ent.state = FuncDoorState.WAITING
            ent.wait_timer = ent.wait or 2
        end
    elseif ent.state == FuncDoorState.WAITING then
        ent.wait_timer = ent.wait_timer - dt
        if ent.wait_timer <= 0 then
            ent.state = FuncDoorState.CLOSING
            ent.target_pos = ent.closed_pos
        end
    elseif ent.state == FuncDoorState.CLOSING then
        if func_door_move(ent, dt) then
            ent.state = FuncDoorState.CLOSED
        end
    elseif sphere_intersects_aabb(gMarioStates[0].pos, 150, ent) then
        func_door_trigger(ent)
    end
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

    entity = goldsrc_get_entity(obj.oBehParams)
    if entity ~= nil then
        djui_chat_message_create(entity.classname .. ' ' .. obj.oBehParams)

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
        func_door_init(entity)
    end
end


function bhv_goldsrc_brush_loop(obj)
    entity = goldsrc_get_entity(obj.oBehParams)
    if entity ~= nil then
        func_door_update(entity, 1/30)
        obj.oPosX = entity.current_pos.x
        obj.oPosY = entity.current_pos.y
        obj.oPosZ = entity.current_pos.z
    end
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

--------------------
-- Remember AABBs --
--------------------

$AABBS
