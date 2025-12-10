local GoldsrcGfxUtils = {}
local sReplaced = {}

function GoldsrcGfxUtils.replace_gfx_textures(node)
    if sReplaced[node] then return end
    sReplaced[node] = true

    local function get_tex_file_from_gfx_texture(gfx_texture)
        if not gfx_texture then return nil end

        local gfx_name = get_texture_name(gfx_texture)
        if not gfx_name then return nil end

        local name = nil
        if not name then name = gfx_name:match("_dl_(.-)_rgba16$") end
        if not name then name = gfx_name:match("_%d+_(.-)_rgba16$") end
        if not name then return nil end

        name = string.lower(name) .. '.rgba16'
        local tex = get_texture_info(name)
        if not tex then return nil end

        return tex.texture
    end

    local function parse_dl(cmd, op)
        if op == G_SETTIMG then
            local tex = get_tex_file_from_gfx_texture(gfx_get_texture(cmd))
            if tex then
                gfx_set_command(cmd, "gsDPSetTextureImage(G_IM_FMT_RGBA, G_IM_SIZ_16b_LOAD_BLOCK, 1, %t)", tex)
            end
        end
    end

    local function geo_traverse(node, toplevel, sanity, traversed)
        if node == nil or sanity > 2000 or traversed[node] then
            return
        end
        traversed[node] = true

        if node.type == GRAPH_NODE_TYPE_DISPLAY_LIST then
            local displaylist_node = cast_graph_node(node)
            if displaylist_node then
                gfx_parse(displaylist_node.displayList, parse_dl)
            end
        end

        if not toplevel then
            geo_traverse(node.next, toplevel, sanity + 1, traversed)
        end

        geo_traverse(node.children, false, sanity + 1, traversed)
    end

    local traversed = {}
    geo_traverse(node, true, 0, traversed)
end

return GoldsrcGfxUtils
