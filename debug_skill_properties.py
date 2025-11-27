"""Debug what properties are available on grantedEffect for skill processing."""

import lupa

# Initialize Lua to access PoB data
lua = lupa.LuaRuntime(unpack_returned_tuples=True)

# Load MinimalCalc to get access to data.skills
with open("src/calculator/MinimalCalc.lua", "r", encoding="utf-8") as f:
    lua_code = f.read()

# Execute MinimalCalc bootstrap
lua.execute(lua_code)

# Get the Lightning Arrow skill data
lua_code_check = """
local skill = data.skills["LightningArrowPlayer"]
if skill then
    print("=== Lightning Arrow Skill Properties ===")
    print("name:", skill.name)
    print("color:", skill.color)
    print("baseFlags:", type(skill.baseFlags))

    if skill.baseFlags then
        print("\\nbaseFlags contents:")
        for k, v in pairs(skill.baseFlags) do
            print("  ", k, "=", v)
        end
    end

    print("\\nOther properties:")
    for k, v in pairs(skill) do
        if type(v) ~= "table" and type(v) ~= "function" then
            print("  ", k, "=", v)
        elseif type(v) == "table" and k ~= "baseFlags" then
            print("  ", k, "= <table>")
        end
    end
else
    print("ERROR: Lightning Arrow skill not found in data.skills")
end
"""

try:
    lua.execute(lua_code_check)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
