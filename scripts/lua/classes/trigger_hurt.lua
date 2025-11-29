--------------------
-- trigger_hurt   --
--------------------

local GoldsrcEntity = require("/goldsrc/goldsrc_entity")

local TriggerHurt = {}
TriggerHurt.__index = TriggerHurt
setmetatable(TriggerHurt, {__index = GoldsrcEntity})

TriggerHurt.Flags = {
    TARGET_ONCE      = 1 << 0,  -- 1
    START_OFF        = 1 << 1,  -- 2
    NO_CLIENTS       = 1 << 3,  -- 8
    FIRE_CLIENT_ONLY = 1 << 4,  -- 16
    TOUCH_CLIENT_ONLY= 1 << 5,  -- 32
}

-------------------------------------------------
-- Constructor
-------------------------------------------------

function TriggerHurt:new(ent, obj)
    local self = setmetatable(GoldsrcEntity:new(ent, obj), TriggerHurt)
    ent.dmg = ent.dmg or 10

    local flags = ent.spawnflags or 0
    self.enabled = not GoldsrcEntity.has_flag(flags, TriggerHurt.Flags.START_OFF)
    self.fired_once = false
    self.damage_timer = 0

    return self
end

-------------------------------------------------
-- Internal helpers
-------------------------------------------------

function TriggerHurt:should_damage(target)
    local flags = self.ent.spawnflags or 0
    local is_player = goldsrc_get_type(target) == 'player'

    if GoldsrcEntity.has_flag(flags, TriggerHurt.Flags.NO_CLIENTS) and is_player then
        return false
    end

    if GoldsrcEntity.has_flag(flags, TriggerHurt.Flags.TOUCH_CLIENT_ONLY) and not is_player then
        return false
    end

    return true
end

function TriggerHurt:should_fire_target(target)
    local flags = self.ent.spawnflags or 0
    local is_player = goldsrc_get_type(target) == 'player'

    if GoldsrcEntity.has_flag(flags, TriggerHurt.Flags.FIRE_CLIENT_ONLY) and not is_player then
        return false
    end

    if GoldsrcEntity.has_flag(flags, TriggerHurt.Flags.TARGET_ONCE) and self.fired_once then
        return false
    end

    return true
end

function TriggerHurt:hurt_target(target)
    if not self:should_damage(target) then return end

    -- Apply damage
    goldsrc_apply_damage(target, self.ent.dmg, self.ent)

    -- Fire targets if allowed
    if self.ent.target and self:should_fire_target(target) then
        goldsrc_fire_target(self.ent.target, self.ent.targetname, self.ent.targetname, nil, nil, self.ent.delay or 0)
    end

    if self.ent.killtarget then
        goldsrc_kill_target(self.ent.killtarget, self.ent.delay or 0)
    end

    -- Mark as fired if TARGET_ONCE
    if GoldsrcEntity.has_flag(self.ent.spawnflags or 0, TriggerHurt.Flags.TARGET_ONCE) then
        self.fired_once = true
    end
end

-------------------------------------------------
-- Update
-------------------------------------------------

function TriggerHurt:update()
    local m = gMarioStates[0]

    -- run at 10hz
    self.damage_timer = self.damage_timer + 1
    if (self.damage_timer % 3) ~= 0 then
        return
    end

    -- Check player
    if goldsrc_intersects_aabb(m.pos, 80, self.ent._aabb) then
        self:hurt_target(m)
    end

    -- TODO: Check monsters/entities
end

-------------------------------------------------
-- Registration
-------------------------------------------------

GoldsrcEntity.register("trigger_hurt", TriggerHurt)

return TriggerHurt