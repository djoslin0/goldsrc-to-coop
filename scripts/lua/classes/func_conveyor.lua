-------------------
-- func_conveyor --
-------------------

-- TODO: verify push direction and speed, its a complete guess at the moment
-- TODO: scroll texture

local GoldsrcEntity = require("/goldsrc/goldsrc_entity")

local FuncConveyor = {}
FuncConveyor.__index = FuncConveyor
setmetatable(FuncConveyor, {__index = GoldsrcEntity})

local dt = 1/30

FuncConveyor.Flags = {
    NO_PUSH   = 1 << 0,  -- 1
    NOT_SOLID = 1 << 1,  -- 2
}

-------------------------------------------------
-- Constructor
-------------------------------------------------

function FuncConveyor:new(ent, obj)
    local self = setmetatable(GoldsrcEntity:new(ent, obj), FuncConveyor)

    self.speed = ent.speed or 100
    self.current_speed = self.speed

    -- Compute push direction from yaw (assuming horizontal, pitch 0)
    local yaw = (ent.angles and ent.angles[2]) or 0
    local rad_yaw = math.rad(yaw)
    self.push_dir_x = math.cos(rad_yaw)
    self.push_dir_z = math.sin(rad_yaw)

    -- Set rendercolor for scrolling textures
    self:update_scroll_texture()

    return self
end

function FuncConveyor:update_scroll_texture()
    --local speed = self.current_speed
    --local r = (speed < 0) and 1 or 0
    --local g = math.floor(math.abs(speed) / 16)
    --local b = math.floor(math.abs(speed) * 16) % 256
    --self.ent.rendercolor = {r, g, b}
    -- Assume the rendering system uses this for scrolling
end

function FuncConveyor:trigger()
    self.current_speed = -self.current_speed
    self:update_scroll_texture()
    return true
end

-------------------------------------------------
-- Update
-------------------------------------------------

function FuncConveyor:update()
    local m = gMarioStates[0]
    local flags = self.ent.spawnflags or 0

    -- Push player if not no_push and standing on conveyor
    if not GoldsrcEntity.has_flag(flags, FuncConveyor.Flags.NO_PUSH) and goldsrc_is_standing_on_obj(m, self.obj) then
        local push_factor = self.current_speed * gGoldsrc.toSm64Scalar
        m.vel.x = m.vel.x + self.push_dir_x * push_factor
        m.vel.z = m.vel.z + self.push_dir_z * push_factor
    end

    -- Load collision if not solid
    if not GoldsrcEntity.has_flag(flags, FuncConveyor.Flags.NOT_SOLID) then
        load_object_collision_model()
    end
end

-------------------------------------------------
-- Registration
-------------------------------------------------

GoldsrcEntity.register("func_conveyor", FuncConveyor)

return FuncConveyor
