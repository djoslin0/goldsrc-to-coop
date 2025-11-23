----------------
-- env_sprite --
----------------

local GoldsrcEntity = require("goldsrc_entity")
local GoldsrcSpr = require("goldsrc_spr")

local EnvSprite = {}
EnvSprite.__index = EnvSprite
setmetatable(EnvSprite, {__index = GoldsrcEntity})

------------------------------------
-- Constructor
------------------------------------

function EnvSprite:new(ent, obj)
    local self = setmetatable(GoldsrcEntity:new(ent, obj), EnvSprite)

    local is_spr = ent.model:sub(-4) == ".spr"
    self.spr = nil

    if ent.model ~= nil and is_spr then
        local geo_name = GoldsrcSpr.geo_path(ent.model)
        local e_model_id = smlua_model_util_get_id(geo_name)
        obj_set_model_extended(obj, e_model_id)
        self.spr = GoldsrcSpr:new(self)
    end

    return self
end

function EnvSprite:update()
    if self.spr then
        self.spr:update()
    end
end

------------------------------------
-- Registration
------------------------------------

goldsrc_add_class("env_sprite", function(ent, obj)
    return EnvSprite:new(ent, obj)
end)

return EnvSprite