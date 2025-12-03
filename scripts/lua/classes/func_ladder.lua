-------------------
-- func_ladder   --
-------------------

local GoldsrcEntity = require("/goldsrc/goldsrc_entity")

local FuncLadder = {}
FuncLadder.__index = FuncLadder
setmetatable(FuncLadder, {__index = GoldsrcEntity})

-------------------------------------------------
-- Constructor
-------------------------------------------------

function FuncLadder:new(ent, obj)
    local self = setmetatable(GoldsrcEntity:new(ent, obj), FuncLadder)
    return self
end

-------------------------------------------------
-- Action
-------------------------------------------------

local sLadderYaw = nil

local ACT_GOLDSRC_LADDER = allocate_mario_action(ACT_GROUP_AIRBORNE | ACT_FLAG_AIR)

local function moving_into_wall_dot(m)
    if not m or not m.wall then return 0 end

    local ladder_normal = m.wall.normal -- Vec3f

    -- Check if player's intended direction is towards the ladder
    local dir_x = sins(m.intendedYaw)
    local dir_z = coss(m.intendedYaw)

    return -(dir_x * ladder_normal.x + dir_z * ladder_normal.z)
end

local function raycast_to_ladder(m, obj, yaw)
        -- try to find ladder nearby
        local dir_x = math.sin(yaw) * 200
        local dir_y = 0
        local dir_z = math.cos(yaw) * 200
        local ray = collision_find_surface_on_ray(m.pos.x, m.pos.y + 100, m.pos.z, dir_x, dir_y, dir_z, 10)

        if ray.surface and ray.surface.object == obj then
            m.wall = ray.surface
            return ray
        else
            return nil
        end
end

local function act_goldsrc_ladder(m)
    if m.playerIndex == 0 then
        -- handle leaving ladder naturally
        ray = raycast_to_ladder(m, m.usedObj, sLadderYaw)
        if ray then
            local norm = ray.surface.normal
            sLadderYaw = math.atan2(norm.x, norm.z) + math.pi
            m.pos.x = ray.hitPos.x + norm.x * 50
            m.pos.z = ray.hitPos.z + norm.z * 50
        else
            m.forwardVel = 10
            return set_mario_action(m, ACT_FREEFALL, 0)
        end

        -- handle player buttons
        if (m.input & INPUT_Z_PRESSED) ~= 0 then
            m.input = m.input & (~INPUT_Z_PRESSED)
            m.forwardVel = -10
            return set_mario_action(m, ACT_FREEFALL, 0)
        end

        if (m.input & INPUT_B_PRESSED) ~= 0 then
            m.input = m.input & (~INPUT_B_PRESSED)
            m.forwardVel = -10
            return set_mario_action(m, ACT_FREEFALL, 0)
        end

        if (m.input & INPUT_A_PRESSED) ~= 0 then
            m.input = m.input & (~INPUT_A_PRESSED)
            m.vel.y = 52.0
            m.faceAngle.y = m.faceAngle.y + 0x8000
            return set_mario_action(m, ACT_WALL_KICK_AIR, 0)
        end
    end

    -- handle animation
    set_character_animation(m, CHAR_ANIM_CRAWLING)
    local loop = m.marioObj.header.gfx.animInfo.curAnim.loopEnd
    set_anim_to_frame(m, (m.pos.y / 2) % loop)

    -- Check if player's intended direction is towards the ladder
    local dot = moving_into_wall_dot(m)

    -- Move player up/down the ladder
    local move_speed = m.intendedMag * 0.4
    if dot > 0 then
        m.vel.y = m.vel.y + move_speed
    else
        m.vel.y = m.vel.y - move_speed
    end

    -- update yaw
    local intendedDYaw = m.intendedYaw - m.faceAngle.y;
    m.faceAngle.y = m.faceAngle.y + 512 * sins(intendedDYaw) * m.intendedMag / 16;

    -- update side-to-side movement
    m.forwardVel = m.intendedMag * 0.3
    m.vel.x = m.forwardVel * sins(m.faceAngle.y)
    m.vel.z = m.forwardVel * coss(m.faceAngle.y)

    -- perform mmovement
    local old_vel_y = m.vel.y
    step = perform_air_step(m,  0)
    if step == AIR_STEP_LANDED then
        if check_fall_damage_or_get_stuck(m, ACT_HARD_BACKWARD_GROUND_KB) == 0 then
           return set_mario_action(m, ACT_FREEFALL_LAND, 0)
        end
    end

    -- set visuals
    local gfx = m.marioObj.header.gfx
    local l_yaw = 0
    if m.playerIndex == 0 and sLadderYaw then
        l_yaw = sLadderYaw
    elseif m.playerIndex == 0 and m.wall and m.wall.object == m.usedObj and m.wall.normal then
        l_yaw = sm64_to_radians(m.wall.normal)
    else
        l_yaw = sm64_to_radians(m.faceAngle.y)
    end
    gfx.pos.x = m.pos.x + math.sin(l_yaw) * 60
    gfx.pos.z = m.pos.z + math.cos(l_yaw) * 60
    gfx.angle.x = degrees_to_sm64(-90)
    gfx.angle.y = radians_to_sm64(l_yaw)

    -- reset velocities
    m.vel.y = old_vel_y * 0.6
    m.vel.x = 0
    m.vel.z = 0
    m.forwardVel = 0

end

hook_mario_action(ACT_GOLDSRC_LADDER, act_goldsrc_ladder)


function FuncLadder:could_attach(m)
    local ray1 = raycast_to_ladder(m, self.obj, sm64_to_radians(m.faceAngle.y))
    if ray1 then
        sLadderYaw = math.atan2(ray1.surface.normal.x, ray1.surface.normal.z) + math.pi
        local ray2 = raycast_to_ladder(m, self.obj, sLadderYaw)
        if ray2 then
            m.forwardVel = 0
            m.vel.x = 0
            m.vel.y = 0
            m.vel.z = 0
            m.usedObj = self.obj
            return true
        end
    end
    return false
end

-- prevent bonking on ladders -- attach instead
hook_event(HOOK_MARIO_UPDATE, function (m)
    if m.playerIndex ~= 0 then return end
    if (m.action & ACT_FLAG_AIR) == 0 then return end
    if (m.action & (ACT_FLAG_INVULNERABLE|ACT_FLAG_INTANGIBLE)) ~= 0 then return end
    if m.action == ACT_BUBBLED then return end
    if m.forwardVel < 5 then return end

    local yaw = sm64_to_radians(m.faceAngle.y)
    local dir_x = math.sin(yaw) * 150
    local dir_y = 0
    local dir_z = math.cos(yaw) * 150
    local ray = collision_find_surface_on_ray(m.pos.x, m.pos.y + 100, m.pos.z, dir_x, dir_y, dir_z, 10)

    if ray.surface and ray.surface.object then
        local obj = ray.surface.object
        local ent = gGoldsrcObjToEnt[obj]
        if ent then
            local class = ent._class
            if class and getmetatable(class) == FuncLadder and class:could_attach(m) then
                set_mario_action(m, ACT_GOLDSRC_LADDER, 0)
            end
        end
    end
end)

-------------------------------------------------
-- Update
-------------------------------------------------

function FuncLadder:update()
    local m = gMarioStates[0]

    load_object_collision_model()

    if m.wall ~= nil and m.wall.object == self.obj and m.action ~= ACT_GOLDSRC_LADDER and m.intendedMag > 8 and moving_into_wall_dot(m) > 0.2 then
        if self:could_attach(m) then
            set_mario_action(m, ACT_GOLDSRC_LADDER, 0)
        end
    end
end

-------------------------------------------------
-- Registration
-------------------------------------------------

GoldsrcEntity.register("func_ladder", FuncLadder)

return FuncLadder