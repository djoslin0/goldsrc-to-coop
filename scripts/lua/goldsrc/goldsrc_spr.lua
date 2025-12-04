local GoldsrcSpr = {}
GoldsrcSpr.__index = GoldsrcSpr

local dt = 1/30

local sObjToSpr = {}

local sDefaultRenderColor = {255, 255, 255}

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

-- the interaction between the TEX_FORMAT and the RENDER_MODE is very complicated :(
local render_table = {
    [TEX_FORMAT_SPR_NORMAL] = {
        -- TODO: verify, none of these in TEX_FORMAT_SPR_NORMAL were tested
        [RENDER_MODE_NORMAL  ] = { offset = RENDER_OFF_OPAQUE, use_rendercolor = true,  use_renderamt = false },
        [RENDER_MODE_COLOR   ] = { offset = RENDER_OFF_OPAQUE, use_rendercolor = false, use_renderamt = false },
        [RENDER_MODE_TEXTURE ] = { offset = RENDER_OFF_ALPHA,  use_rendercolor = true,  use_renderamt = true  },
        [RENDER_MODE_GLOW    ] = { offset = RENDER_OFF_ALPHA,  use_rendercolor = true,  use_renderamt = true  },
        [RENDER_MODE_SOLID   ] = { offset = RENDER_OFF_ALPHA,  use_rendercolor = true,  use_renderamt = true  },
        [RENDER_MODE_ADDITIVE] = { offset = RENDER_OFF_ALPHA,  use_rendercolor = true,  use_renderamt = true  },
    },
    [TEX_FORMAT_SPR_ADDITIVE] = {
        [RENDER_MODE_NORMAL  ] = { offset = RENDER_OFF_OPAQUE, use_rendercolor = true,  use_renderamt = false },
        [RENDER_MODE_COLOR   ] = { offset = RENDER_OFF_OPAQUE, use_rendercolor = false, use_renderamt = false },
        [RENDER_MODE_TEXTURE ] = { offset = RENDER_OFF_ALPHA,  use_rendercolor = true,  use_renderamt = true  },
        [RENDER_MODE_GLOW    ] = { offset = RENDER_OFF_ALPHA,  use_rendercolor = true,  use_renderamt = true  },
        [RENDER_MODE_SOLID   ] = { offset = RENDER_OFF_ALPHA,  use_rendercolor = true,  use_renderamt = true  },
        [RENDER_MODE_ADDITIVE] = { offset = RENDER_OFF_ALPHA,  use_rendercolor = true,  use_renderamt = true  },
    },
    [TEX_FORMAT_SPR_INDEXALPHA] = {
        [RENDER_MODE_NORMAL  ] = { offset = RENDER_OFF_ALPHA,  use_rendercolor = true,  use_renderamt = true },
        [RENDER_MODE_COLOR   ] = { offset = RENDER_OFF_ALPHA,  use_rendercolor = false, use_renderamt = true },
        [RENDER_MODE_TEXTURE ] = { offset = RENDER_OFF_ALPHA,  use_rendercolor = true,  use_renderamt = true },
        [RENDER_MODE_GLOW    ] = { offset = RENDER_OFF_CUTOUT, use_rendercolor = true,  use_renderamt = true },
        [RENDER_MODE_SOLID   ] = { offset = RENDER_OFF_ALPHA,  use_rendercolor = true,  use_renderamt = true },
        [RENDER_MODE_ADDITIVE] = { offset = RENDER_OFF_CUTOUT, use_rendercolor = true,  use_renderamt = true },
    },
    [TEX_FORMAT_SPR_ALPHTEST] = {
        [RENDER_MODE_NORMAL  ] = { offset = RENDER_OFF_CUTOUT, use_rendercolor = true,  use_renderamt = false },
        [RENDER_MODE_COLOR   ] = { offset = RENDER_OFF_CUTOUT, use_rendercolor = false, use_renderamt = false },
        [RENDER_MODE_TEXTURE ] = { offset = RENDER_OFF_ALPHA,  use_rendercolor = true,  use_renderamt = true  },
        [RENDER_MODE_GLOW    ] = { offset = RENDER_OFF_ALPHA,  use_rendercolor = true,  use_renderamt = true  },
        [RENDER_MODE_SOLID   ] = { offset = RENDER_OFF_ALPHA,  use_rendercolor = true,  use_renderamt = true  },
        [RENDER_MODE_ADDITIVE] = { offset = RENDER_OFF_ALPHA,  use_rendercolor = true,  use_renderamt = true  },
    },
}


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
    self.update_render = true

    -- set default rendercolor
    if ent.rendercolor and ent.rendercolor[1] == 0 and ent.rendercolor[2] == 0 and ent.rendercolor[3] == 0 then
        ent.rendercolor[1] = 255
        ent.rendercolor[2] = 255
        ent.rendercolor[3] = 255
    end

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

    -- set render
    local rendermode = self.ent.rendermode
    local tex_format = self.sprite_data['texFormat']
    if render_table[tex_format] and render_table[tex_format][rendermode] then
        self.render = render_table[tex_format][rendermode]
    end

    self.spr_animate = ent and ent.framerate and self.sprite_data
    self:set_anim_state(0)

    sObjToSpr[obj] = self

    return self
end


function GoldsrcSpr:set_anim_state(frame)
    local render_offset = RENDER_OFF_OPAQUE

    -- figure out how self.ent.rendermode interacts with the sprite's built-in texture format
    if self.render then
        render_offset = self.render.offset
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


----------------------
-- Gfx Manipulation --
----------------------

--- @param obj Object
--- Get a unique identifier for gfx and vtx allocation.
local function get_obj_identifier(obj)
    return tostring(obj._pointer)
end

--- @param node GraphNode
--- @param matStackIndex integer
function g_goldsrc_spr(node, matStackIndex)
    local obj = geo_get_current_object()

    local spr = sObjToSpr[obj]
    if spr == nil then return end

    local gfx_name = "goldsrc_spr_dl_" .. get_obj_identifier(obj)
    local gfx = gfx_get_from_name(gfx_name)

    if gfx == nil then
        gfx = gfx_create(gfx_name, 2)
    end

    if spr.update_render then
        local ent = spr.ent
        local rendercolor = sDefaultRenderColor
        local renderamt = 255

        if spr.render then
            local render = spr.render
            if render.use_rendercolor and ent.rendercolor then
                rendercolor = ent.rendercolor
            end

            if render.use_renderamt and ent.renderamt then
                renderamt = ent.renderamt
            end
        end

        -- Change the env color
        gfx_set_command(gfx_get_command(gfx, 0), "gsDPSetEnvColor(%i, %i, %i, %i)", rendercolor[1], rendercolor[2], rendercolor[3], renderamt)
        gfx_set_command(gfx_get_command(gfx, 1), "gsSPEndDisplayList()")

        spr.update_render = false
    end

    -- Update the graph node display list
    local current = node.next
    for i = 1, 3 do
        cast_graph_node(current).displayList = gfx
        current = current.next
    end

end

--- @param obj Object
--- Delete allocated gfx and vtx for this object.
local function on_object_unload(obj)
    sObjToSpr[obj] = nil
    local gfx = gfx_get_from_name("goldsrc_spr_dl_" .. get_obj_identifier(obj))
    if gfx then gfx_delete(gfx) end
end



hook_event(HOOK_ON_OBJECT_UNLOAD, on_object_unload)

return GoldsrcSpr
