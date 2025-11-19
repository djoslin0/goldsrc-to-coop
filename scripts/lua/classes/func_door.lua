---------------
-- func_door --
---------------

-- TODO: implement
-- Master (master) <targetname> Name of a master entity. If the master hasn't been activated, this entity will not activate. A door with a master will be locked until the master condition is fulfilled. The name of a multisource (or game_team_master) entity. A master must usually be active in order for the entity to work. Thus they act almost like an on/off switch, in their simplest form, and like an AND gate in the case of the multisource.
-- Damage inflicted when blocked (dmg) - How much damage the player receives if he gets stuck between the door and something solid.
-- Players blocking a door should cause it to go back

local GoldsrcEntity = require("goldsrc_entity")

local FuncDoor = {}
FuncDoor.__index = FuncDoor
setmetatable(FuncDoor, {__index = GoldsrcEntity})

local dt = 1/30

-- States
FuncDoor.State = {
    CLOSED   = 0,
    OPENING  = 1,
    OPEN     = 2,
    WAITING  = 3,
    CLOSING  = 4,
}

FuncDoor.Flags = {
    STARTS_OPEN       = 1 << 0,   -- 1
    DONT_LINK         = 1 << 2,   -- 4
    PASSABLE          = 1 << 3,   -- 8
    TOGGLE            = 1 << 5,   -- 32
    USE_ONLY          = 1 << 8,   -- 256
    MONSTERS_CANT     = 1 << 9,   -- 512
    NOT_IN_DEATHMATCH = 1 << 11,  -- 2048
}

-------------------------------------------------
-- Constructor
-------------------------------------------------

function FuncDoor:new(ent, obj)
    local self = setmetatable(GoldsrcEntity:new(ent, obj), FuncDoor)

    self.closed_pos = {
        x = obj.oPosX,
        y = obj.oPosY,
        z = obj.oPosZ,
    }

    self.current_pos = {
        x = obj.oPosX,
        y = obj.oPosY,
        z = obj.oPosZ,
    }

    -- deal with undocumented 'angle'
    if not self.ent.angles and self.ent.angle ~= nil then
        local yaw = self.ent.angle
        if yaw == -1 then
            self.ent.angles = { -90, 0, 0 }
        elseif yaw == -2 then
            self.ent.angles = { 90, 0, 0 }
        else
            self.ent.angles = { 0, yaw, 0 }
        end
    end

    self.open_pos = self:compute_open_pos()

    self.state      = FuncDoor.State.CLOSED
    self.target_pos = self.closed_pos
    self.wait_timer = 0

    -- STARTS_OPEN flag
    if GoldsrcEntity.has_flag(ent.spawnflags or 0, FuncDoor.Flags.STARTS_OPEN) then
        self.state = FuncDoor.State.OPEN
        self.current_pos = { x = self.open_pos.x, y = self.open_pos.y, z = self.open_pos.z }
        self.target_pos = self.open_pos
    end

    return self
end

function FuncDoor:is_locked()
    local ent = self.ent

    -- TODO: figure out 'master' logic to decide when a door is locked or not
    
    -- Should we look for player triggers?
    if ent.targetname ~= nil and ent.targetname ~= '' then
        return true
    end

    return false
end

function FuncDoor:is_passable()
    return GoldsrcEntity.has_flag(self.ent.spawnflags or 0, FuncDoor.Flags.PASSABLE)
end

function FuncDoor:should_link()
    return not GoldsrcEntity.has_flag(self.ent.spawnflags or 0, FuncDoor.Flags.DONT_LINK)
end

function FuncDoor:compute_open_pos()
    local ent = self.ent
    local aabb = ent._aabb
    local lip = ent.lip or 0

    local yaw   = (ent.angles and ent.angles[2]) or 0
    local pitch = (ent.angles and ent.angles[1]) or 0

    local rad_yaw   = -math.rad(yaw)
    local rad_pitch =  math.rad(pitch)

    -- XY sliding
    local dir = { x = math.cos(rad_yaw), y = 0, z = math.sin(rad_yaw) }

    -- Vertical sliding (up/down)
    if math.abs(math.cos(rad_pitch)) < 0.01 then
        dir.x, dir.z = 0, 0
        dir.y = (pitch >= 0) and -1 or 1
    end

    -- Normalize
    local len = math.sqrt(dir.x*dir.x + dir.y*dir.y + dir.z*dir.z)
    if len ~= 0 then
        dir.x, dir.y, dir.z = dir.x/len, dir.y/len, dir.z/len
    end

    -- AABB 8 corners
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

    -- Projections
    local minProj, maxProj
    for _, c in ipairs(corners) do
        local proj = c[1]*dir.x + c[2]*dir.y + c[3]*dir.z
        if not minProj or proj < minProj then minProj = proj end
        if not maxProj or proj > maxProj then maxProj = proj end
    end

    -- Distance minus lip
    local distance = (maxProj - minProj) - lip

    -- Open position
    return {
        x = self.closed_pos.x + dir.x * distance,
        y = self.closed_pos.y + dir.y * distance,
        z = self.closed_pos.z + dir.z * distance,
    }
end

function FuncDoor:move()
    local target = self.target_pos
    local cur = self.current_pos

    local dx = target.x - cur.x
    local dy = target.y - cur.y
    local dz = target.z - cur.z

    local dist = math.sqrt(dx*dx + dy*dy + dz*dz)
    if dist <= 0 then
        cur.x, cur.y, cur.z = target.x, target.y, target.z
        return true
    end

    local step = (self.ent.speed or 100) * dt
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

function FuncDoor:trigger()
    local f = FuncDoor.Flags
    local flags = self.ent.spawnflags or 0
    local ent = self.ent

    if ent.killtarget then
        goldsrc_kill_target(ent.killtarget, ent.delay or 0)
    end

    if GoldsrcEntity.has_flag(flags, f.TOGGLE) then
        if self.state == FuncDoor.State.OPEN then
            self.state = FuncDoor.State.CLOSING
            self.target_pos = self.closed_pos
            return true
        elseif self.state == FuncDoor.State.CLOSED then
            self.state = FuncDoor.State.OPENING
            self.target_pos = self.open_pos
            return true
        end
    else
        if self.state == FuncDoor.State.CLOSED
        or self.state == FuncDoor.State.CLOSING then
            self.state = FuncDoor.State.OPENING
            self.target_pos = self.open_pos
            return true
        end
    end
    return false
end

function FuncDoor:trigger_from_player()
    local ent = self.ent

    if self:is_locked() then
        if ent.message then
            goldsrc_message(ent.message)
        end
        return false
    else
        return self:trigger()
    end
end

function FuncDoor:use()
    local flags = self.ent.spawnflags or 0

    if not self:should_link() then
        return false
    end

    if not GoldsrcEntity.has_flag(flags, FuncDoor.Flags.USE_ONLY) then
        return false
    end

    return self:trigger_from_player()
end

function FuncDoor:update_state_machine()
    local f = FuncDoor.Flags
    local flags = self.ent.spawnflags or 0
    local ent = self.ent

    -- OPENING
    if self.state == FuncDoor.State.OPENING then
        if self:move() then
            -- Trigger output
            if ent.target then
                goldsrc_fire_target(ent.target, ent.targetname, ent.targetname, nil, nil, ent.delay or 0)
            end

            if GoldsrcEntity.has_flag(flags, f.TOGGLE) then
                -- Door has reached open pos; stay open until next trigger
                self.state = FuncDoor.State.OPEN
                self.target_pos = self.open_pos
            else
                -- Non-toggle: check for infinite wait
                if (ent.wait or 2) == -1 then
                    -- Infinite open
                    self.state = FuncDoor.State.OPEN
                    self.target_pos = self.open_pos
                else
                    -- Start WAITING timer before auto-closing
                    self.state = FuncDoor.State.WAITING
                    self.wait_timer = ent.wait or 2
                end
            end
        end
        return
    end

    -- WAITING
    if self.state == FuncDoor.State.WAITING then
        self.wait_timer = self.wait_timer - dt
        if self.wait_timer <= 0 then
            self.state = FuncDoor.State.CLOSING
            self.target_pos = self.closed_pos
        end
        return
    end

    -- CLOSING
    if self.state == FuncDoor.State.CLOSING then
        if self:move() then
            -- Trigger fire on close
            if ent.netname then
                goldsrc_fire_target(ent.netname, ent.targetname, ent.targetname, nil, nil, 0)
            end

            self.state = FuncDoor.State.CLOSED
        end
        return
    end

    local m = gMarioStates[0]

    -- Should we USE check?
    if GoldsrcEntity.has_flag(ent.spawnflags or 0, f.USE_ONLY) then
        return
    end

    -- Should we link check?
    if not self:should_link() then
        return
    end

    -- Should we collision check?
    if self:is_passable() then
        return
    end

    -- Proximity trigger
    if goldsrc_is_touching_obj(m, self.obj) then
        self:trigger_from_player()
    end
end

function FuncDoor:update()
    self:update_state_machine()

    local obj = self.obj
    obj.oPosX = self.current_pos.x
    obj.oPosY = self.current_pos.y
    obj.oPosZ = self.current_pos.z

    if not self:is_passable() then
        load_object_collision_model()
    end
end

-------------------------------------------------
-- Registration
-------------------------------------------------

GoldsrcEntity.register("func_door", FuncDoor)

return FuncDoor