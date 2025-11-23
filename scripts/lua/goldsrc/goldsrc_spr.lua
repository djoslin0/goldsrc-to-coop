local GoldsrcSpr = {}
GoldsrcSpr.__index = GoldsrcSpr

local dt = 1/30

function GoldsrcSpr.alter_path(model)
    return model:gsub("/", "_"):gsub("%.", "_")
end

function GoldsrcSpr.geo_path(model)
    return GoldsrcSpr.alter_path(model) .. "_geo"
end

function GoldsrcSpr:new(goldsrc_entity)
    local self = setmetatable({}, self)

    local ent = goldsrc_entity.ent
    local obj = goldsrc_entity.obj

    self.ent = ent
    self.obj = obj

    self.sprite_data = nil
    self.frame_t = 0
    self.spr_animate = false

    -- set sprite orientation
    local curr_level = gNetworkPlayers[0].currLevelNum
    local sprites = gGoldsrc.levels[curr_level].sprites
    local altered_path = GoldsrcSpr.alter_path(ent.model)
    if sprites and sprites[altered_path] then
        local data = sprites[altered_path]
        self.sprite_data = data
        if data['type'] == 0 then
            obj_set_cylboard(obj)
        elseif data['type'] ~= 3 then
            obj_set_billboard(obj)
        end
    end

    -- set sprite scale
    if ent and ent.scale then
        obj_scale(obj, ent.scale)
    end

    self.spr_animate = ent and ent.framerate and self.sprite_data
    self:set_anim_state(0)

    return self
end

local TEX_FORMAT_SPR_NORMAL     = 0
local TEX_FORMAT_SPR_ADDITIVE   = 1
local TEX_FORMAT_SPR_INDEXALPHA = 2
local TEX_FORMAT_SPR_ALPHTEST   = 3

local RENDER_MODE_NORMAL   = 0
local RENDER_MODE_COLOR    = 1
local RENDER_MODE_TEXTURE  = 2
local RENDER_MODE_GLOW     = 3
local RENDER_MODE_SOLID    = 4
local RENDER_MODE_ADDITIVE = 5

local RENDER_OFF_OPAQUE = 0
local RENDER_OFF_ALPHA  = 1
local RENDER_OFF_CUTOUT = 2

local render_offset_table = {
    [TEX_FORMAT_SPR_ADDITIVE] = {
        [RENDER_MODE_NORMAL  ] = RENDER_OFF_OPAQUE,
        [RENDER_MODE_COLOR   ] = RENDER_OFF_OPAQUE,
        [RENDER_MODE_TEXTURE ] = RENDER_OFF_ALPHA,
        [RENDER_MODE_GLOW    ] = RENDER_OFF_ALPHA,
        [RENDER_MODE_SOLID   ] = RENDER_OFF_ALPHA,
        [RENDER_MODE_ADDITIVE] = RENDER_OFF_ALPHA,
    },
    [TEX_FORMAT_SPR_INDEXALPHA] = {
        [RENDER_MODE_NORMAL  ] = RENDER_OFF_ALPHA,
        [RENDER_MODE_COLOR   ] = RENDER_OFF_ALPHA,
        [RENDER_MODE_TEXTURE ] = RENDER_OFF_ALPHA,
        [RENDER_MODE_GLOW    ] = RENDER_OFF_CUTOUT,
        [RENDER_MODE_SOLID   ] = RENDER_OFF_ALPHA,
        [RENDER_MODE_ADDITIVE] = RENDER_OFF_CUTOUT,
    },
    [TEX_FORMAT_SPR_ALPHTEST] = {
        [RENDER_MODE_NORMAL  ] = RENDER_OFF_CUTOUT,
        [RENDER_MODE_COLOR   ] = RENDER_OFF_CUTOUT,
        [RENDER_MODE_TEXTURE ] = RENDER_OFF_CUTOUT,
        [RENDER_MODE_GLOW    ] = RENDER_OFF_CUTOUT,
        [RENDER_MODE_SOLID   ] = RENDER_OFF_CUTOUT,
        [RENDER_MODE_ADDITIVE] = RENDER_OFF_CUTOUT,
    },
}

function GoldsrcSpr:set_anim_state(frame)
    local render_offset = RENDER_OFF_OPAQUE

    -- figure out how self.ent.rendermode interacts with the sprite's built-in texture format
    local rendermode = self.ent.rendermode
    local tex_format = self.sprite_data['texFormat']
    if render_offset_table[tex_format] and render_offset_table[tex_format][rendermode] then
        render_offset = render_offset_table[tex_format][rendermode]
    end

    self.obj.oAnimState = frame + render_offset * self.sprite_data.numframes
end

function GoldsrcSpr:update()
    if not self.spr_animate then
        return
    end
    self.frame_t = self.frame_t + dt
    local frame = (self.frame_t * self.ent.framerate) % (self.sprite_data.numframes)
    self:set_anim_state(frame)
end

return GoldsrcSpr
