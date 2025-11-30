
-----------------------------------------------

local BhvGoldsrcSkybox = {}

-----------------------------------------------

local function bhv_goldsrc_skybox_init(obj)
    obj.oFlags = OBJ_FLAG_UPDATE_GFX_POS_AND_ANGLE
    obj.header.gfx.skipInViewCheck = true
    obj_set_gfx_scale(obj, 10000, 10000, 10000)
end

local function bhv_goldsrc_skybox_loop(obj)
    local c = gMarioStates[0].area.camera
    if not c then return end
    obj.oPosX = c.pos.x
    obj.oPosY = c.pos.y - 70000
    obj.oPosZ = c.pos.z
end

id_bhvGoldsrcSkybox = hook_behavior(
    nil,
    OBJ_LIST_GENACTOR,
    true,
    bhv_goldsrc_skybox_init,
    bhv_goldsrc_skybox_loop
)

BhvGoldsrcSkybox.id = id_bhvGoldsrcSkybox

-----------------------------------------------

return BhvGoldsrcSkybox
