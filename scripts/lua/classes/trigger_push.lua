--------------------
-- trigger_push   --
--------------------

local GoldsrcEntity = require("/goldsrc/goldsrc_entity")

local TriggerPush = {}
TriggerPush.__index = TriggerPush
setmetatable(TriggerPush, {__index = GoldsrcEntity})

TriggerPush.Flags = {
    ONCE_ONLY = 1,
    START_OFF = 2,
}

-------------------------------------------------
-- Constructor
-------------------------------------------------

function TriggerPush:new(ent, obj)
    local self = setmetatable(GoldsrcEntity:new(ent, obj), TriggerPush)

    self.speed = (ent.speed and ent.speed > 0) and ent.speed or 100

    -- Compute push direction from angles (Pitch, Yaw, Roll)
    local pitch = (ent.angles and ent.angles[1]) or 0
    local yaw   = (ent.angles and ent.angles[2]) or 0

    local rad_pitch = math.rad(pitch)
    local rad_yaw = math.rad(yaw)

    self.push_dir_x = math.cos(rad_yaw) * math.cos(rad_pitch)
    self.push_dir_y = -math.sin(rad_pitch)
    self.push_dir_z = math.sin(rad_yaw) * math.cos(rad_pitch)

    -- Handle spawnflags
    local flags = ent.spawnflags or 0
    self.once_only = GoldsrcEntity.has_flag(flags, TriggerPush.Flags.ONCE_ONLY)
    self.start_off = GoldsrcEntity.has_flag(flags, TriggerPush.Flags.START_OFF)
    self.enabled = not self.start_off

    return self
end

function TriggerPush:trigger(activator)
    self.enabled = not self.enabled
end

-------------------------------------------------
-- Update
-------------------------------------------------

function TriggerPush:update()
    local m = gMarioStates[0]

    if goldsrc_intersects_aabb(m.pos, 80, self.ent._aabb) and self.enabled then
        -- Apply push velocity
        local push_vel = self.speed * gGoldsrc.toSm64Scalar / 30
        -- TODO: figure out how to apply velocity correctly...
        --m.vel.x = m.vel.x + self.push_dir_x * push_vel
        --m.vel.y = m.vel.y + self.push_dir_y * push_vel
        --m.vel.z = m.vel.z + self.push_dir_z * push_vel

        -- HACK
        m.pos.x = m.pos.x + self.push_dir_x * push_vel
        m.pos.y = m.pos.y + self.push_dir_y * push_vel
        m.pos.z = m.pos.z + self.push_dir_z * push_vel
        if self.push_dir_y > 0.5 then
            m.vel.y = 0
        end

        -- If once only, disable after pushing
        if self.once_only then
            self.enabled = false
        end
    end
end

-------------------------------------------------
-- Registration
-------------------------------------------------

GoldsrcEntity.register("trigger_push", TriggerPush)

return TriggerPush
