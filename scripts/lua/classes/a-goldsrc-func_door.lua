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

    return self
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
    if self.state == FuncDoor.State.CLOSED
    or self.state == FuncDoor.State.CLOSING then

        self.state = FuncDoor.State.OPENING
        self.target_pos = self.open_pos
    end
end

function FuncDoor:update_state_machine()
    -- OPENING
    if self.state == FuncDoor.State.OPENING then
        if self:move() then
            self.state = FuncDoor.State.WAITING
            self.wait_timer = self.ent.wait or 2
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

    -- Proximity trigger
    local m = gMarioStates[0]
    local ent = self.ent

    if m.floor.object == self.obj
    or (m.wall and m.wall.object == self.obj)
    or goldsrc_intersects_aabb(m.pos, 150, ent)
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
end

-------------------------------------------------
-- Registration
-------------------------------------------------

goldsrc_add_class("func_door", function(ent, obj) return FuncDoor:new(ent, obj) end)
