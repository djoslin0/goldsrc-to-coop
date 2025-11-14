---------------
-- func_door --
---------------

local FuncDoor = {}
FuncDoor.__index = FuncDoor

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

local function has_flag(value, flag)
    return (value & flag) ~= 0
end

function FuncDoor:new(ent, obj)
    local self = setmetatable({}, FuncDoor)

    ent._class = self
    self.ent = ent
    self.obj = obj

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

    self.open_pos = self:compute_open_pos()

    self.state      = FuncDoor.State.CLOSED
    self.target_pos = self.closed_pos
    self.wait_timer = 0

    -- STARTS_OPEN flag
    if has_flag(ent.spawnflags or 0, FuncDoor.Flags.STARTS_OPEN) then
        self.state = FuncDoor.State.OPEN
        self.current_pos = { x = self.open_pos.x, y = self.open_pos.y, z = self.open_pos.z }
        self.target_pos = self.open_pos
    end

    return self
end

function FuncDoor:is_passable()
    return has_flag(self.ent.spawnflags or 0, FuncDoor.Flags.PASSABLE)
end

function FuncDoor:should_link()
    return not has_flag(self.ent.spawnflags or 0, FuncDoor.Flags.DONT_LINK)
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

    if has_flag(flags, f.TOGGLE) then
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

function FuncDoor:use()
    return self:trigger()
end

function FuncDoor:update_state_machine()
    local f = FuncDoor.Flags
    local flags = self.ent.spawnflags or 0

    -- OPENING
    if self.state == FuncDoor.State.OPENING then
        if self:move() then
            if has_flag(flags, f.TOGGLE) then
                -- Door has reached open pos; stay open until next trigger
                self.state = FuncDoor.State.OPEN
                self.target_pos = self.open_pos
            else
                -- Non-toggle: start WAITING timer before auto-closing
                self.state = FuncDoor.State.WAITING
                self.wait_timer = self.ent.wait or 2
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
            self.state = FuncDoor.State.CLOSED
        end
        return
    end

    local m = gMarioStates[0]
    local ent = self.ent

    -- Should we USE check?
    if has_flag(self.ent.spawnflags or 0, f.USE_ONLY) then
        return
    end

    -- Should we collision check?
    if self:is_passable() then
        return
    end

    -- Proximity trigger
    if (m.floor.object == self.obj and m.floorHeight < 1)
    or (m.wall and m.wall.object == self.obj)
    or goldsrc_intersects_aabb(m.pos, 80, ent)
    then
        self:trigger()
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

goldsrc_add_class("func_door", function(ent, obj) return FuncDoor:new(ent, obj) end)
