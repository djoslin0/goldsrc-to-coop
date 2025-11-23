----------------
-- env_sprite --
----------------

local GoldsrcEntity = require("goldsrc_entity")
local GoldsrcSpr = require("goldsrc_spr")

local EnvSprite = {}
EnvSprite.__index = EnvSprite
setmetatable(EnvSprite, {__index = GoldsrcEntity})

EnvSprite.Flags = {
    STARTS_ON = 1 << 0,   -- 1
    PLAY_ONCE = 1 << 1,   -- 2
}

------------------------------------
-- Constructor
------------------------------------

function EnvSprite:new(ent, obj)
    local self = setmetatable(GoldsrcEntity:new(ent, obj), EnvSprite)

    local pitch = (ent.angles and ent.angles[3]) or 0
    local yaw   = (ent.angles and ent.angles[2]) or 0
    local roll  = (ent.angles and ent.angles[1]) or 0

    obj.oFaceAnglePitch = degrees_to_sm64(pitch)
    obj.oFaceAngleYaw   = degrees_to_sm64(yaw)
    obj.oFaceAngleRoll  = degrees_to_sm64(roll)

    local is_spr = ent.model:sub(-4) == ".spr"
    self.spr = nil

    if ent.model ~= nil and is_spr then
        local geo_name = GoldsrcSpr.geo_path(ent.model)
        local e_model_id = smlua_model_util_get_id(geo_name)
        obj_set_model_extended(obj, e_model_id)
        self.spr = GoldsrcSpr:new(self)
        self.sprite_data = self.spr.sprite_data  -- for animation tracking
    end

    -- Handle flags
    self.play_once = GoldsrcEntity.has_flag(ent.spawnflags or 0, EnvSprite.Flags.PLAY_ONCE)
    self.animation_playing = false
    self.animation_start_time = 0

    -- Set initial enabled state
    if ent.targetname then
        self.enabled = GoldsrcEntity.has_flag(ent.spawnflags or 0, EnvSprite.Flags.STARTS_ON)
    else
        self.enabled = true  -- unnamed sprites always start visible
    end

    -- Apply initial visibility
    if not self.enabled then
        obj.header.gfx.node.flags = obj.header.gfx.node.flags | GRAPH_RENDER_INVISIBLE
    end

    return self
end

function EnvSprite:trigger(target, activator, caller, use_type, value)
    if self.play_once then
        -- Play once mode: become visible and start animation if not already playing
        if not self.enabled or not self.animation_playing then
            self.enabled = true
            self.animation_playing = true
            self.animation_start_time = 0
            self.obj.header.gfx.node.flags = self.obj.header.gfx.node.flags & ~GRAPH_RENDER_INVISIBLE
            if self.spr then
                self.spr.frame_t = 0  -- reset animation
            end
        end
    else
        -- Toggle mode: just flip visibility
        self.enabled = not self.enabled
        if self.enabled then
            self.obj.header.gfx.node.flags = self.obj.header.gfx.node.flags & ~GRAPH_RENDER_INVISIBLE
        else
            self.obj.header.gfx.node.flags = self.obj.header.gfx.node.flags | GRAPH_RENDER_INVISIBLE
        end
    end
end

function EnvSprite:update()
    if self.spr then
        if self.play_once then
            -- For play once, track if animation completed
            if self.animation_playing then
                self.animation_start_time = self.animation_start_time + 1/30  -- dt is 1/30
                local total_time = (self.sprite_data and self.sprite_data.numframes or 1) / (self.ent.framerate or 10)
                if self.animation_start_time >= total_time then
                    -- Animation finished: hide and disable
                    self.enabled = false
                    self.animation_playing = false
                    self.obj.header.gfx.node.flags = self.obj.header.gfx.node.flags | GRAPH_RENDER_INVISIBLE
                else
                    -- Continue updating animation while playing
                    self.spr:update()
                end
            end
            -- If not playing, don't update animation
        else
            -- Normal loop mode: always update if sprite exists
            self.spr:update()
        end
    end
end

------------------------------------
-- Registration
------------------------------------
GoldsrcEntity.register("env_sprite", EnvSprite)

return EnvSprite
