--------------------
-- trigger_hurt   --
--------------------

local TriggerHurt = {}
TriggerHurt.__index = TriggerHurt

TriggerHurt.Flags = {
    TARGET_ONCE      = 1 << 0,  -- 1
    START_OFF        = 1 << 1,  -- 2
    NO_CLIENTS       = 1 << 3,  -- 8
    FIRE_CLIENT_ONLY = 1 << 4,  -- 16
    TOUCH_CLIENT_ONLY= 1 << 5,  -- 32
}

local function has_flag(v, f)
    return (v & f) ~= 0
end

-------------------------------------------------
-- Constructor
-------------------------------------------------

function TriggerHurt:new(ent, obj)
    local self = setmetatable({}, TriggerHurt)

    ent._class = self
    self.ent = ent
    self.obj = obj

    local flags = ent.spawnflags or 0
    self.enabled  = not has_flag(flags, TriggerHurt.Flags.START_OFF)
    self.fired_once = false

    self.dmg = ent.dmg or 10
    self.damage_timer = 0

    return self
end

-------------------------------------------------
-- Internal helpers
-------------------------------------------------

function TriggerHurt:should_damage(target)
    local flags = self.ent.spawnflags or 0
    local is_player = goldsrc_get_type(target) == 'player'

    if has_flag(flags, TriggerHurt.Flags.NO_CLIENTS) and is_player then
        return false
    end

    if has_flag(flags, TriggerHurt.Flags.TOUCH_CLIENT_ONLY) and not is_player then
        return false
    end

    return true
end

function TriggerHurt:should_fire_target(target)
    local flags = self.ent.spawnflags or 0
    local is_player = goldsrc_get_type(target) == 'player'

    if has_flag(flags, TriggerHurt.Flags.FIRE_CLIENT_ONLY) and not is_player then
        return false
    end

    if has_flag(flags, TriggerHurt.Flags.TARGET_ONCE) and self.fired_once then
        return false
    end

    return true
end

function TriggerHurt:hurt_target(target)
    if not self.enabled then return end
    if not self:should_damage(target) then return end

    djui_chat_message_create('HURT!')

    -- Apply damage
    goldsrc_apply_damage(target, self.dmg, self.ent)

    -- Fire targets if allowed
    if self.ent.target and self:should_fire_target(target) then
        goldsrc_fire_target(self.ent.target, self.ent.targetname, self.ent.targetname, nil, nil, self.ent.delay or 0)
    end

    if self.ent.killtarget then
        goldsrc_kill_target(self.ent.killtarget, self.ent.delay or 0)
    end

    -- Mark as fired if TARGET_ONCE
    if has_flag(self.ent.spawnflags or 0, TriggerHurt.Flags.TARGET_ONCE) then
        self.fired_once = true
    end
end

-------------------------------------------------
-- Update
-------------------------------------------------

function TriggerHurt:update()
    if not self.enabled then return end
    local m = gMarioStates[0]

    -- run at 10hz
    self.damage_timer = self.damage_timer + 1
    if (self.damage_timer % 3) ~= 0 then
        return
    end

    -- Check player
    if goldsrc_intersects_aabb(m.pos, 80, self.ent) then
        self:hurt_target(m)
    end

    -- TODO: Check monsters/entities

end

-------------------------------------------------
-- Registration
-------------------------------------------------

goldsrc_add_class("trigger_hurt", function(ent, obj)
    return TriggerHurt:new(ent, obj)
end)
