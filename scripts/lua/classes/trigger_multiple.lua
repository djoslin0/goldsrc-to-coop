----------------------
-- trigger_multiple --
----------------------

local GoldsrcEntity = require("goldsrc_entity")

local TriggerMultiple = {}
TriggerMultiple.__index = TriggerMultiple
setmetatable(TriggerMultiple, {__index = GoldsrcEntity})

local dt = 1/30

TriggerMultiple.Flags = {
    MONSTERS       = 1 << 0,  -- 1
    NO_CLIENTS     = 1 << 1,  -- 2
    PUSHABLES      = 1 << 2,  -- 4
}

------------------------------------
-- Constructor
------------------------------------

function TriggerMultiple:new(ent, obj)
    local self = setmetatable(GoldsrcEntity:new(ent, obj), TriggerMultiple)

    ent.wait = ent.wait or 0.2
    self.cooldown = 0

    return self
end

function TriggerMultiple:touch_allowed(target)
    local flags = self.ent.spawnflags or 0
    local is_player = (goldsrc_get_type(target) == "player")

    if GoldsrcEntity.has_flag(flags, TriggerMultiple.Flags.NO_CLIENTS) and is_player then
        return false
    end

    --if GoldsrcEntity.has_flag(flags, TriggerMultiple.Flags.MONSTERS) and goldsrc_get_type(target) == "monster" then
    --    return false
    --end

    return true
end

function TriggerMultiple:fire(from)
    local ent = self.ent

    -- Check master (TODO)
    -- if ent.master and not goldsrc_master_is_active(ent.master) then
    --     return
    -- end

    -- Fire target
    if ent.target then
        goldsrc_fire_target(ent.target, ent.targetname, ent.targetname, nil, nil, ent.delay or 0)
    end

    -- Killtarget
    if ent.killtarget then
        goldsrc_kill_target(ent.killtarget, ent.delay or 0)
    end

    -- Apply wait time cooldown
    if ent.wait > 0 then
        self.cooldown = ent.wait
    elseif ent.wait == -1 then
        self.enabled = false
    end
end

------------------------------------
-- Update (runs every frame)
------------------------------------

function TriggerMultiple:update()
    local ent = self.ent

    -- Do cooldown
    if self.cooldown > 0 then
        self.cooldown = self.cooldown - dt
        if self.cooldown > 0 then
            return
        end
    end

    -- Right now we only support the player as target (expand later)
    local m = gMarioStates[0]

    -- AABB-based trigger check (same pattern as trigger_hurt)
    if goldsrc_intersects_aabb(m.pos, 80, ent) and self:touch_allowed(m) then
        self:fire(m)
    end
end

------------------------------------
-- Registration
------------------------------------
GoldsrcEntity.register("trigger_multiple", TriggerMultiple)

return TriggerMultiple