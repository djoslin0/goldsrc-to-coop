-------------------
-- func_ladder   --
-------------------

local GoldsrcEntity = require("goldsrc_entity")

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

local ACT_GOLDSRC_LADDER = allocate_mario_action(ACT_GROUP_AIRBORNE | ACT_FLAG_AIR)

local function moving_into_wall_dot(m)
    if not m or not m.wall then return 0 end

    local ladder_normal = m.wall.normal -- Vec3f

    -- Check if player's intended direction is towards the ladder
    local dir_x = sins(m.intendedYaw)
    local dir_z = coss(m.intendedYaw)

    return -(dir_x * ladder_normal.x + dir_z * ladder_normal.z)
end

local function act_goldsrc_ladder(m)
    -- handle leaving ladder naturally
    if m.wall == nil or m.wall.object ~= m.usedObj then
        m.forwardVel = 10
        return set_mario_action(m, ACT_FREEFALL, 0)
    end

    -- handle player buttons
    if (m.input & INPUT_Z_PRESSED) ~= 0 then
        m.input = m.input & (~INPUT_Z_PRESSED)
        m.forwardVel = -10
        return set_mario_action(m, ACT_FREEFALL, 0);
    end

    if (m.input & INPUT_B_PRESSED) ~= 0 then
        m.input = m.input & (~INPUT_B_PRESSED)
        m.forwardVel = -10
        return set_mario_action(m, ACT_FREEFALL, 0);        
    end

    if (m.input & INPUT_A_PRESSED) ~= 0 then
        m.input = m.input & (~INPUT_A_PRESSED)
        m.vel.y = 52.0
        m.faceAngle.y = m.faceAngle.y + 0x8000
        return set_mario_action(m, ACT_WALL_KICK_AIR, 0)
    end

    -- handle animation
    set_character_animation(m, CHAR_ANIM_CRAWLING)
    local loop = m.marioObj.header.gfx.animInfo.curAnim.loopEnd
    set_anim_to_frame(m, (m.pos.y / 2) % loop)

    -- set visible marioObj for animation
    normal_yaw = math.atan2(m.wall.normal.z, m.wall.normal.x)
    m.marioObj.oPosX = m.marioObj.oPosX + sins(m.marioObj.oFaceAngleYaw) * 60
    m.marioObj.oPosZ = m.marioObj.oPosZ + coss(m.marioObj.oFaceAngleYaw) * 60
    m.marioObj.oFaceAngleYaw = radians_to_sm64(-(normal_yaw + math.pi/2))
    m.marioObj.oFaceAnglePitch = degrees_to_sm64(-90)
    obj_build_transform_from_pos_and_angle(m.marioObj, 0x06, 0x12)
    obj_set_throw_matrix_from_transform(m.marioObj)

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

    -- reset velocities
    m.vel.y = old_vel_y * 0.6
    m.vel.x = 0
    m.vel.z = 0
    m.forwardVel = 0

end

hook_mario_action(ACT_GOLDSRC_LADDER, act_goldsrc_ladder)


-------------------------------------------------
-- Update
-------------------------------------------------

function FuncLadder:update()
    local m = gMarioStates[0]

    if m.wall ~= nil and m.wall.object == self.obj and m.action ~= ACT_GOLDSRC_LADDER and m.intendedMag > 8 then
        if moving_into_wall_dot(m) > 0.2 then
            m.forwardVel = 0
            m.vel.x = 0
            m.vel.y = 0
            m.vel.z = 0
            m.usedObj = self.obj
            set_mario_action(m, ACT_GOLDSRC_LADDER, 0)
        end
    end

    load_object_collision_model()
end

-------------------------------------------------
-- Registration
-------------------------------------------------

GoldsrcEntity.register("func_ladder", FuncLadder)

return FuncLadder