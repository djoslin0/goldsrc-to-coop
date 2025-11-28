------------------
-- func_button  --
------------------

local GoldsrcEntity = require("goldsrc_entity")

local FuncButton = {}
FuncButton.__index = FuncButton
setmetatable(FuncButton, {__index = GoldsrcEntity})

local dt = 1/30

FuncButton.State = {
    AT_REST     = 0,
    MOVING_UP   = 1,
    WAITING     = 2,
    MOVING_DOWN = 3,
}

FuncButton.Flags = {
    DONT_MOVE       = 1 << 0,
    TOGGLE          = 1 << 5,
    SPARKS          = 1 << 6,
    TOUCH_ACTIVATES = 1 << 8,
}

-------------------------------------------------
-- Constructor
-------------------------------------------------

function FuncButton:new(ent, obj)
    local self = setmetatable(GoldsrcEntity:new(ent, obj), FuncButton)

    self.rest_pos = {
        x = obj.oPosX,
        y = obj.oPosY,
        z = obj.oPosZ,
    }

    self.current_pos = {
        x = obj.oPosX,
        y = obj.oPosY,
        z = obj.oPosZ,
    }

    self.open_pos = self:compute_open_pos()

    self.state = FuncButton.State.AT_REST
    self.target_pos = self.rest_pos
    self.wait_timer = 0

    return self
end

function FuncButton:compute_open_pos()
    local ent = self.ent
    local aabb = ent._aabb
    local lip = ent.lip or 0

    -- Convert angles to movedir (GoldSrc forwards vector)
    local pitch = (ent.angles and ent.angles[1] or 0)
    local yaw   = (ent.angles and ent.angles[2] or 0)

    local sp, cp = math.sin(math.rad(pitch)), math.cos(math.rad(pitch))
    local sy, cy = math.sin(math.rad(yaw)),   math.cos(math.rad(yaw))

    local dir = {
        x = cp * cy,
        y = cp * sy,
        z = -sp,
    }

    -- Reset angles just like GoldSrc
    ent.angles = {0, 0, 0}

    -- Compute total movement distance along movedir
    local size = {
        x = math.abs(aabb.max[1] - aabb.min[1]),
        y = math.abs(aabb.max[2] - aabb.min[2]),
        z = math.abs(aabb.max[3] - aabb.min[3]),
    }

    local dist =
        size.x * math.abs(dir.x) +
        size.y * math.abs(dir.y) +
        size.z * math.abs(dir.z) -
        lip

    return {
        x = self.rest_pos.x + dir.x * dist,
        y = self.rest_pos.y + dir.y * dist,
        z = self.rest_pos.z + dir.z * dist,
    }
end

function FuncButton:move()
    local cur = self.current_pos
    local target = self.target_pos

    local dx = target.x - cur.x
    local dy = target.y - cur.y
    local dz = target.z - cur.z

    local dist = math.sqrt(dx*dx + dy*dy + dz*dz)
    if dist <= 0 then
        cur.x, cur.y, cur.z = target.x, target.y, target.z
        return true
    end

    local step = (self.ent.speed or 40) * dt
    if step >= dist then
        cur.x, cur.y, cur.z = target.x, target.y, target.z
        return true
    end

    local s = step / dist
    cur.x = cur.x + dx*s
    cur.y = cur.y + dy*s
    cur.z = cur.z + dz*s

    return false
end

function FuncButton:is_locked()
    -- TODO: GoldSrc master system
    return false
end

function FuncButton:trigger(activator)
    local ent = self.ent
    local flags = ent.spawnflags or 0
    local toggle = GoldsrcEntity.has_flag(flags, FuncButton.Flags.TOGGLE)

    -- DONT MOVE — fire only, no animation
    if GoldsrcEntity.has_flag(flags, FuncButton.Flags.DONT_MOVE) then
        if ent.target then
            goldsrc_fire_target(ent.target, activator, ent, nil, nil, ent.delay or 0)
        end
        return true
    end

    -- TOGGLE
    if toggle then
        if self.state == FuncButton.State.AT_REST then
            self.state = FuncButton.State.MOVING_UP
            self.target_pos = self.open_pos
            return true

        elseif self.state == FuncButton.State.MOVING_UP
            or self.state == FuncButton.State.WAITING then
            -- Reverse direction mid-motion
            self.state = FuncButton.State.MOVING_DOWN
            self.target_pos = self.rest_pos
            return true

        elseif self.state == FuncButton.State.MOVING_DOWN then
            self.state = FuncButton.State.MOVING_UP
            self.target_pos = self.open_pos
            return true
        end

    -- NON-TOGGLE
    else
        if self.state == FuncButton.State.AT_REST then
            self.state = FuncButton.State.MOVING_UP
            self.target_pos = self.open_pos
            return true
        end
    end

    return false
end

function FuncButton:use(activator)
    if self:is_locked() then
        if self.ent.message then
            goldsrc_message(self.ent.message)
        end
        return false
    end

    return self:trigger(activator)
end

-------------------------------------------------
-- State Machine
-------------------------------------------------

function FuncButton:update_state_machine()
    local ent = self.ent
    local flags = ent.spawnflags or 0
    local wait = ent.wait or 1

    -- MOVING UP
    if self.state == FuncButton.State.MOVING_UP then
        if self:move() then
            -- Reached top -> fire target
            if ent.target then
                goldsrc_fire_target(ent.target, ent, ent, nil, nil, ent.delay or 0)
            end

            if GoldsrcEntity.has_flag(flags, FuncButton.Flags.TOGGLE) then
                self.state = FuncButton.State.WAITING
                self.wait_timer = -1     -- stay up forever
            else
                self.state = FuncButton.State.WAITING
                self.wait_timer = wait  -- auto-return
            end
        end
        return
    end

    -- WAITING
    if self.state == FuncButton.State.WAITING then
        if self.wait_timer ~= -1 then
            self.wait_timer = self.wait_timer - dt
            if self.wait_timer <= 0 then
                self.state = FuncButton.State.MOVING_DOWN
                self.target_pos = self.rest_pos
            end
        end
        return
    end

    -- MOVING DOWN
    if self.state == FuncButton.State.MOVING_DOWN then
        if self:move() then
            self.state = FuncButton.State.AT_REST
        end
        return
    end

    -- AT REST -> check for TOUCH_ACTIVATES
    if GoldsrcEntity.has_flag(flags, FuncButton.Flags.TOUCH_ACTIVATES) then
        if goldsrc_is_touching_obj(gMarioStates[0], self.obj) then
            self:trigger(self.ent)
        end
    end
end

------------
function FuncButton:update()
    self:update_state_machine()

    self.obj.oPosX = self.current_pos.x
    self.obj.oPosY = self.current_pos.y
    self.obj.oPosZ = self.current_pos.z

    load_object_collision_model()
end

-------------------------------------------------
-- Registration
-------------------------------------------------

GoldsrcEntity.register("func_button", FuncButton)

return FuncButton
