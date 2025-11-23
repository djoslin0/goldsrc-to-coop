-------------------
-- cycler_sprite --
-------------------

local GoldsrcEntity = require("goldsrc_entity")
local Cycler = require("cycler")

local CyclerSprite = {}
CyclerSprite.__index = CyclerSprite
setmetatable(CyclerSprite, {__index = Cycler})

------------------------------------
-- Constructor
------------------------------------

function CyclerSprite:new(ent, obj)
    local self = setmetatable(Cycler:new(ent, obj), CyclerSprite)
    return self
end

------------------------------------
-- Registration
------------------------------------
GoldsrcEntity.register("cycler_sprite", CyclerSprite)

return CyclerSprite