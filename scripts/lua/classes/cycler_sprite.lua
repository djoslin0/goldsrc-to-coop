-------------------
-- cycler_sprite --
-------------------

local GoldsrcEntity = require("/goldsrc/goldsrc_entity")
local Cycler = require("/goldsrc/cycler")

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