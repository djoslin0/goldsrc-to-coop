---------------------
-- Goldsrc Entity  --
---------------------

local GoldsrcEntity = {}
GoldsrcEntity.__index = GoldsrcEntity

-- Flag checking helper
function GoldsrcEntity.has_flag(value, flag)
    return (value & flag) ~= 0
end

-- Constructor
function GoldsrcEntity:new(ent, obj)
    local self = setmetatable({}, self)
    ent._class = self
    self.ent = ent
    self.obj = obj
    self.enabled = true
    return self
end

-- Update method (virtual - subclasses override)
function GoldsrcEntity:update()
    -- Subclasses implement their update logic here
end

-- Registration helper
function GoldsrcEntity.register(class_name, subclass)
    goldsrc_add_class(class_name, function(ent, obj) return subclass:new(ent, obj) end)
end

return GoldsrcEntity
