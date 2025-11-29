-------------------------
-- func_breakable.lua  --
-------------------------

-- TODO: implement
-- material-specific gibs and sounds
-- fix up explosion
-- func_breakables can get crushed by other brushes

local GoldsrcEntity = require("/goldsrc/goldsrc_entity")
local GoldsrcFx = require("/goldsrc/goldsrc_fx")

local FuncBreakable = {}
FuncBreakable.__index = FuncBreakable
setmetatable(FuncBreakable, {__index = GoldsrcEntity})

-- Spawnflags
FuncBreakable.Flags = {
    ONLY_TRIGGER    = 1 << 0,  -- can't take damage
    TOUCH           = 1 << 1,  -- breaks when touched
    PRESSURE        = 1 << 2,  -- breaks under pressure
    INSTANT_CROWBAR = 1 << 8,  -- breaks instantly to crowbar
}

-------------------------------------------------
-- Constructor
-------------------------------------------------

function FuncBreakable:new(ent, obj)
    local self = setmetatable(GoldsrcEntity:new(ent, obj), FuncBreakable)

    self.health = ent.health or 1

    return self
end

function FuncBreakable:spawn_gibs()
    -- TODO: spawn pieces based on material type
    GoldsrcFx.spawn_triangle_break_particles(self.obj, 30, E_MODEL_DIRT_ANIMATION, 3.0, 4)
end

function FuncBreakable:play_break_sound()
    -- TODO: play break sounds based on material
    play_sound(SOUND_GENERAL_BREAK_BOX, self.obj.header.gfx.cameraToObject)
end

function FuncBreakable:play_damaged_sound()
    -- TODO: play break sounds based on material
    play_sound(SOUND_OBJ_UNK23, self.obj.header.gfx.cameraToObject)
end

function FuncBreakable:break_now()
    if not self.enabled then
        return
    end

    self.enabled = false

    self:play_break_sound()
    self:spawn_gibs()

    -- Explode
    local magnitude = self.ent.explodemagnitude or 0
    if magnitude > 0 then
        local obj = self.obj
        local explosion = spawn_non_sync_object(id_bhvExplosion, E_MODEL_EXPLOSION, obj.oPosX, obj.oPosY, obj.oPosZ, nil)
        if explosion then explosion.oGraphYOffset = explosion.oGraphYOffset + 100 end

        -- TODO: while this calculation more-or-less matches what I can find online.. it isn't 1-to-1. Online the 5 is 2.5, but it didn't match what I saw
        local radius = magnitude * gGoldsrc.toSm64Scalar * 5
        local damage = magnitude
        goldsrc_apply_radius_damage(obj.oPosX, obj.oPosY, obj.oPosZ, radius, damage)
    end

    -- Hide object / disable collision
    self.obj.header.gfx.node.flags = self.obj.header.gfx.node.flags | GRAPH_RENDER_INVISIBLE

    -- Trigger output
    local ent = self.ent
    if ent.target then
        goldsrc_fire_target(self.ent.target, self.ent.targetname, self.ent.targetname, nil, nil, ent.delay or 0)
    end
end

function FuncBreakable:apply_damage(dmg, damager)
    if not self.enabled then
        return
    end

    -- check for unbreakable
    if self.ent.health == -1 then
        return
    end

    local flags = self.ent.spawnflags or 0

    -- ONLY_TRIGGER means damage does nothing
    if GoldsrcEntity.has_flag(flags, FuncBreakable.Flags.ONLY_TRIGGER) then
        return
    end

    self.health = self.health - dmg
    if self.health <= 0 then
        self:break_now()
    else
        self:play_damaged_sound()
    end
end

function FuncBreakable:trigger()
    self:break_now()
    return true
end

function FuncBreakable:update_touch()
    local flags = self.ent.spawnflags or 0
    local m = gMarioStates[0]

    -- TOUCH breaks instantly if touched
    if GoldsrcEntity.has_flag(flags, FuncBreakable.Flags.TOUCH) and goldsrc_is_touching_obj(m, self.obj) then
        self:break_now()
    end

    -- PRESSURE: Mario stands on top
    if GoldsrcEntity.has_flag(flags, FuncBreakable.Flags.PRESSURE) and goldsrc_is_standing_on_obj(m, self.obj) then
        self:break_now()
    end
end

function FuncBreakable:update()
    local flags = self.ent.spawnflags or 0

    if not GoldsrcEntity.has_flag(flags, FuncBreakable.Flags.ONLY_TRIGGER) then
        self:update_touch()
    end

    if goldsrc_is_attacking_obj(gMarioStates[0], self.obj) then
        if GoldsrcEntity.has_flag(flags, FuncBreakable.Flags.INSTANT_CROWBAR) then
            self:break_now()
        else
            self:apply_damage(34)
        end
    end

    if self.enabled then
        load_object_collision_model()
    end
end

-------------------------------------------------
-- Registration
-------------------------------------------------
GoldsrcEntity.register("func_breakable", FuncBreakable)

return FuncBreakable