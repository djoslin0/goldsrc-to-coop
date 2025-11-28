------------------------
-- func_door_rotating --
------------------------

-- TODO: implement
-- Master (master) <targetname> Name of a master entity. If the master hasn't been activated, this entity will not activate. A door with a master will be locked until the master condition is fulfilled. The name of a multisource (or game_team_master) entity. A master must usually be active in order for the entity to work. Thus they act almost like an on/off switch, in their simplest form, and like an AND gate in the case of the multisource.
-- Damage inflicted when blocked (dmg) - How much damage the player receives if he gets stuck between the door and something solid.
-- Players blocking a door should cause it to go back
-- The door opens in the direction of the player's view

local GoldsrcEntity = require("goldsrc_entity")
local FuncDoor = require("func_door")
local dt = 1/30

local FuncDoorRotating = {}
FuncDoorRotating.__index = FuncDoorRotating
setmetatable(FuncDoorRotating, {__index = FuncDoor})

-- Additional flags for func_door_rotating
FuncDoor.Flags.REVERSE_DIR = 1 << 1  -- 2
FuncDoor.Flags.ONE_WAY     = 1 << 4  -- 16
FuncDoor.Flags.X_AXIS      = 1 << 6  -- 64
FuncDoor.Flags.Y_AXIS      = 1 << 7  -- 128

-------------------------------------------------
-- Constructor
-------------------------------------------------
function FuncDoorRotating:new(ent, obj)
    local self = setmetatable(FuncDoor:new(ent, obj), FuncDoorRotating)

    self.current_angle = 0
    self.target_angle = 0
    self.state = FuncDoor.State.CLOSED
    self.wait_timer = 0

    -- Determine rotation axis
    self.axis = 'z'  -- default
    if GoldsrcEntity.has_flag(ent.spawnflags or 0, FuncDoor.Flags.X_AXIS) then
        self.axis = 'x'
    elseif GoldsrcEntity.has_flag(ent.spawnflags or 0, FuncDoor.Flags.Y_AXIS) then
        self.axis = 'y'
    end

    -- Open angle (default 90 degrees, can be negative)
    local distance = ent.distance or 90
    if GoldsrcEntity.has_flag(ent.spawnflags or 0, FuncDoor.Flags.REVERSE_DIR) then
        distance = -math.abs(distance)
    end
    self.open_angle = distance

    -- If STARTS_OPEN flag, set initial state
    if GoldsrcEntity.has_flag(ent.spawnflags or 0, FuncDoor.Flags.STARTS_OPEN) then
        self.state = FuncDoor.State.OPEN
        self.current_angle = self.open_angle
        self.target_angle = self.open_angle
    end

    return self
end

function FuncDoorRotating:move()
    local cur = self.current_angle
    local target = self.target_angle
    local speed = self.ent.speed or 100
    local step = speed * dt

    local diff = target - cur
    if math.abs(diff) <= step then
        self.current_angle = target
        return true
    end

    self.current_angle = cur + (diff > 0 and step or -step)
    return false
end

function FuncDoorRotating:trigger()
    local flags = self.ent.spawnflags or 0
    local f = FuncDoor.Flags

    if GoldsrcEntity.has_flag(flags, f.TOGGLE) then
        if self.state == FuncDoor.State.OPEN then
            self.state = FuncDoor.State.CLOSING
            self.target_angle = 0
            return true
        elseif self.state == FuncDoor.State.CLOSED then
            self.state = FuncDoor.State.OPENING
            self.target_angle = self.open_angle
            return true
        end
    else
        if self.state == FuncDoor.State.CLOSED or self.state == FuncDoor.State.CLOSING then
            self.state = FuncDoor.State.OPENING
            self.target_angle = self.open_angle
            return true
        end
    end
    return false
end

function FuncDoorRotating:update_state_machine()
    local ent = self.ent
    local flags = ent.spawnflags or 0
    local f = FuncDoor.Flags

    if self.state == FuncDoor.State.OPENING then
        if self:move() then
            if ent.target then
                goldsrc_fire_target(ent.target, ent.targetname, ent.targetname, nil, nil, ent.delay or 0)
            end

            if GoldsrcEntity.has_flag(flags, f.TOGGLE) then
                self.state = FuncDoor.State.OPEN
            else
                -- Non-toggle: check for infinite wait
                if (ent.wait or 2) == -1 then
                    -- Infinite open
                    self.state = FuncDoor.State.OPEN
                    self.target_angle = self.open_angle
                else
                    -- Start WAITING timer before auto-closing
                    self.state = FuncDoor.State.WAITING
                    self.wait_timer = ent.wait or 2
                end
            end
        end
        return
    end

    if self.state == FuncDoor.State.WAITING then
        self.wait_timer = self.wait_timer - dt
        if self.wait_timer <= 0 then
            self.state = FuncDoor.State.CLOSING
            self.target_angle = 0
        end
        return
    end

    if self.state == FuncDoor.State.CLOSING then
        if self:move() then
            self.state = FuncDoor.State.CLOSED
        end
        return
    end

    -- Optional: auto-trigger from player if not USE_ONLY
    if not GoldsrcEntity.has_flag(flags, f.USE_ONLY) then
        local m = gMarioStates[0]
        if goldsrc_is_touching_obj(m, self.obj) then
            self:trigger_from_player()
        end
    end
end

function FuncDoorRotating:update()
    self:update_state_machine()

    local obj = self.obj
    -- Rotate based on axis
    if self.axis == 'x' then
        obj.oFaceAnglePitch = degrees_to_sm64(self.current_angle)
    elseif self.axis == 'y' then
        obj.oFaceAngleRoll = degrees_to_sm64(self.current_angle)
    else  -- 'z' default
        obj.oFaceAngleYaw = degrees_to_sm64(self.current_angle)
    end

    if not self:is_passable() then
        load_object_collision_model()
    end
end

-------------------------------------------------
-- Registration
-------------------------------------------------
GoldsrcEntity.register("func_door_rotating", FuncDoorRotating)

return FuncDoorRotating
