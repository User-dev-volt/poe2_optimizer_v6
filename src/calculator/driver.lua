--@ src/calculator/driver.lua
-- ============================================================================
-- PEBO Truth Engine -- headless driver.lua  (Story 4.1 spike deliverable)
-- ============================================================================
-- Boots Path of Building's REAL Launch->Main->Data calculation chain headless,
-- under BOTH lanes with the SAME file:
--   (a) embedded lupa.luajit21 inside a respawnable Python worker process, and
--   (b) a true `luajit.exe driver.lua` subprocess (fallback lane).
--
-- This is MODELLED ON external/pob-engine/src/HeadlessWrapper.lua (the pure-Lua
-- GUI/render/image stub surface, lines 6-171, is copied VERBATIM below -- "do
-- NOT reinvent") but adds, BEFORE dofile("Launch.lua"), the native-module
-- package.loaded pre-stub block that is the fix for the boot-time SEH
-- 0xe24c4a02 that crashes Lupa when PoB's Common.lua `require`s the native
-- lua-utf8 / lcurl.safe C libraries.  It then appends a thin JSON stdin/stdout
-- command layer (LOAD_BUILD / GET_STATS / EVAL_NEIGHBORS-stub / APPLY_MOVE-stub).
--
-- The INVERSE-OF-MINIMALCALC RULE is honoured: base64 / sha1 / xml / sha2 /
-- dkjson are pure-Lua libraries in runtime/lua/ and are LET LOAD REAL (they are
-- NOT stubbed).  Only the two genuinely-native requires are pre-seeded.  This is
-- the whole reason the driver reproduces GUI DPS instead of MinimalCalc's
-- ~4%-of-GUI coverage gap.
--
-- NEVER edit HeadlessWrapper.lua in the submodule -- pob_env.verify() invariant
-- (e) fails every parity test if the engine tree is touched.  This file lives
-- OUTSIDE external/pob-engine/ by design.
--
-- Contract with the host:
--   * env POB_SRC_DIR  -> absolute path to external/pob-engine/src (both lanes)
--   * cwd MUST be POB_SRC_DIR before this file runs (Launch.lua reads
--     ../manifest.xml relative to cwd; LoadModule uses relative loadfile).
--   * global HEADLESS_EMBED == true  -> host drives via Driver.handle_command;
--     do NOT auto-start the io.read serve loop (that would block the parent).
--     Unset (luajit.exe lane) -> run Driver.serve() at end of file.
-- [Source: external/pob-engine/src/HeadlessWrapper.lua:6-211;
--          src/calculator/full_pob_engine.py:137-161,231,349;
--          docs/stories/4-1-truth-engine-driver-spike.md AC-4.1.1/2/3/9]
-- ============================================================================

-- ---------------------------------------------------------------------------
-- (0) package.path -- so the luajit.exe lane (no Python) resolves PoB modules
--     and the pure-Lua runtime libs. Mirrors src/calculator/pob_engine.py:564-579
--     and full_pob_engine.py:125-133. Idempotent-enough to also run under embed.
-- ---------------------------------------------------------------------------
local POB_SRC = os.getenv("POB_SRC_DIR")
if not POB_SRC or POB_SRC == "" then
	error("driver.lua: POB_SRC_DIR env var must point to external/pob-engine/src")
end
POB_SRC = POB_SRC:gsub("\\", "/")
local POB_RUNTIME = POB_SRC .. "/../runtime/lua"
package.path = table.concat({
	POB_SRC .. "/?.lua",
	POB_SRC .. "/Modules/?.lua",
	POB_SRC .. "/Classes/?.lua",
	POB_SRC .. "/Data/?.lua",
	POB_RUNTIME .. "/?.lua",
	POB_RUNTIME .. "/?/init.lua",
	package.path,
}, ";")

-- ---------------------------------------------------------------------------
-- (1) NATIVE-MODULE PRE-STUB BLOCK -- the SEH fix. MUST run before Launch.lua.
--     Copied from full_pob_engine.py:137-161 MINUS its base64/sha1 identity
--     stubs (those are the MinimalCalc anti-pattern). Use package.loaded (NOT
--     package.preload -- preload still re-invokes the C loader -> SEH).
-- [Source: external/pob-engine/src/Modules/Common.lua:25,29;
--          src/calculator/full_pob_engine.py:137-161;
--          docs/stories/story-1.4.md:947-967]
-- ---------------------------------------------------------------------------
arg = arg or {} -- Main.lua:58 expects a global arg table (REQUIRED, not optional)

-- lua-utf8: native (lua-utf8.dll). Prefer LuaJIT's built-in utf8; keep `len`.
package.loaded["lua-utf8"] = utf8 or {
	reverse = function(s) return s:reverse() end,
	gsub = string.gsub,
	find = string.find,
	sub = string.sub,
	len = function(s) return #s end,
}

-- lcurl.safe: native (lcurl.dll), only used for update/http -- not calculations.
package.loaded["lcurl.safe"] = {}

-- STDOUT DISCIPLINE (spike deviation from the verbatim ConPrintf copy, required
-- for a line-delimited stdout JSON protocol): PoB boot emits heavy ConPrintf /
-- direct-print noise ("Loading main script...", "missing node ...", "Validating
-- auth token"). Route ALL print() to stderr so stdout carries ONLY protocol
-- responses. ConPrintf (copied below) calls print(), so it inherits this.
do
	local _write = io.stderr
	print = function(...)
		local n = select("#", ...)
		local parts = {}
		for i = 1, n do parts[i] = tostring((select(i, ...))) end
		_write:write(table.concat(parts, "\t"), "\n")
	end
end

-- NOTE (inverse-of-MinimalCalc): base64 / sha1 / sha2 / xml / dkjson are
-- deliberately NOT stubbed. They are pure-Lua in runtime/lua/ and MUST load
-- REAL so the genuine import/decode path runs. Stubbing them reproduces the
-- coverage gap this spike exists to close.

-- ===========================================================================
-- (2) HeadlessWrapper.lua stub surface -- copied VERBATIM from
--     external/pob-engine/src/HeadlessWrapper.lua:6-180 (pinned v0.15.0).
--     "do NOT reinvent". Only cosmetic: this comment banner.
-- ===========================================================================

-- Callbacks
local callbackTable = { }
local mainObject
function runCallback(name, ...)
	if callbackTable[name] then
		return callbackTable[name](...)
	elseif mainObject and mainObject[name] then
		return mainObject[name](mainObject, ...)
	end
end
function SetCallback(name, func)
	callbackTable[name] = func
end
function GetCallback(name)
	return callbackTable[name]
end
function SetMainObject(obj)
	mainObject = obj
end

-- Image Handles
local imageHandleClass = { }
imageHandleClass.__index = imageHandleClass
function NewImageHandle()
	return setmetatable({ }, imageHandleClass)
end
function imageHandleClass:Load(fileName, ...)
	self.valid = true
end
function imageHandleClass:Unload()
	self.valid = false
end
function imageHandleClass:IsValid()
	return self.valid
end
function imageHandleClass:SetLoadingPriority(pri) end
function imageHandleClass:ImageSize()
	return 1, 1
end

-- Rendering
function RenderInit(flag, ...) end
function GetScreenSize()
	return 1920, 1080
end
function GetScreenScale()
	return 1
end
function GetDPIScaleOverridePercent()
	return 1
end
function SetDPIScaleOverridePercent(scale) end
function SetClearColor(r, g, b, a) end
function SetDrawLayer(layer, subLayer) end
function SetViewport(x, y, width, height) end
function SetDrawColor(r, g, b, a) end
function GetDrawColor(r, g, b, a) end
function DrawImage(imgHandle, left, top, width, height, tcLeft, tcTop, tcRight, tcBottom) end
function DrawImageQuad(imageHandle, x1, y1, x2, y2, x3, y3, x4, y4, s1, t1, s2, t2, s3, t3, s4, t4) end
function DrawString(left, top, align, height, font, text) end
function DrawStringWidth(height, font, text)
	return 1
end
function DrawStringCursorIndex(height, font, text, cursorX, cursorY)
	return 0
end
function StripEscapes(text)
	return text:gsub("%^%d",""):gsub("%^x%x%x%x%x%x%x","")
end
function GetAsyncCount()
	return 0
end

-- Search Handles
function NewFileSearch() end

-- General Functions
function SetWindowTitle(title) end
function GetCursorPos()
	return 0, 0
end
function SetCursorPos(x, y) end
function ShowCursor(doShow) end
function IsKeyDown(keyName) end
function Copy(text) end
function Paste() end
function Deflate(data)
	-- TODO: Might need this
	return ""
end
function Inflate(data)
	-- TODO: And this
	return ""
end
function GetTime()
	return 0
end
function GetScriptPath()
	return ""
end
function GetRuntimePath()
	return ""
end
function GetUserPath()
	return ""
end
function MakeDir(path) end
function RemoveDir(path) end
function SetWorkDir(path) end
function GetWorkDir()
	return ""
end
function LaunchSubScript(scriptText, funcList, subList, ...) end
function AbortSubScript(ssID) end
function IsSubScriptRunning(ssID) end
function LoadModule(fileName, ...)
	if not fileName:match("%.lua") then
		fileName = fileName .. ".lua"
	end
	local func, err = loadfile(fileName)
	if func then
		return func(...)
	else
		error("LoadModule() error loading '"..fileName.."': "..err)
	end
end
function PLoadModule(fileName, ...)
	if not fileName:match("%.lua") then
		fileName = fileName .. ".lua"
	end
	local func, err = loadfile(fileName)
	if func then
		return PCall(func, ...)
	else
		error("PLoadModule() error loading '"..fileName.."': "..err)
	end
end
function PCall(func, ...)
	local ret = { pcall(func, ...) }
	if ret[1] then
		table.remove(ret, 1)
		return nil, unpack(ret)
	else
		return ret[2]
	end
end
function ConPrintf(fmt, ...)
	-- Optional
	print(string.format(fmt, ...))
end
function ConPrintTable(tbl, noRecurse) end
function ConExecute(cmd) end
function ConClear() end
function SpawnProcess(cmdName, args) end
function OpenURL(url) end
function SetProfiling(isEnabled) end
function Restart() end
function Exit() end
function TakeScreenshot() end

function GetCloudProvider(fullPath)
	return nil, nil, nil
end

local l_require = require
function require(name)
	-- Hack to stop it looking for lcurl, which we don't really need
	if name == "lcurl.safe" then
		return
	end
	return l_require(name)
end

-- ===========================================================================
-- (3) BOOT the real engine -- models HeadlessWrapper.lua:183-211. cwd MUST be
--     POB_SRC_DIR (the host guarantees it) so relative dofile/loadfile resolve.
-- ===========================================================================
dofile("Launch.lua")

-- Prevents loading of ModCache (matches HeadlessWrapper:188). CI unset locally
-- -> false -> normal ModCache path, which is exactly what the GUI baselines used.
mainObject.continuousIntegrationMode = os.getenv("CI")

runCallback("OnInit")
runCallback("OnFrame") -- Need at least one frame for everything to initialise

if mainObject.promptMsg then
	-- Something went wrong during startup
	error("driver.lua: startup prompt: " .. tostring(mainObject.promptMsg))
end

-- The build module; once a build is loaded, all the good stuff is in here.
build = mainObject.main.modes["BUILD"]

function newBuild()
	mainObject.main:SetMode("BUILD", false, "Help, I'm stuck in Path of Building!")
	runCallback("OnFrame")
end
function loadBuildFromXML(xmlText, name)
	-- XML-DIRECT (AC-4.1.9): original PoB XML fed straight to PoB's own
	-- PassiveSpec (convert=true) -- NO parse_pob_code re-encoding.
	mainObject.main:SetMode("BUILD", false, name or "", xmlText)
	runCallback("OnFrame")
end

-- ===========================================================================
-- (4) DRIVER COMMAND LAYER -- the thin JSON protocol shared by both lanes.
--     Reuses the PROVEN stat read path build.calcsTab.mainOutput[stat]
--     (== mainEnv.player.output[stat]) exactly as full_pob_engine.py:231,349.
-- [Source: src/calculator/full_pob_engine.py:231,349;
--          external/pob-engine/src/Classes/CalcsTab.lua:484-485;
--          external/pob-engine/src/Modules/Build.lua:666-667,1020,1028-1030]
-- ===========================================================================
local dkjson = require("dkjson") -- pure-Lua, loads REAL from runtime/lua/

Driver = {}

-- Default stat set returned when a command omits an explicit stat list.
local DEFAULT_STATS = {
	"TotalDPS", "CombinedDPS", "FullDPS", "TotalDot", "TotalDotDPS",
	"AverageDamage", "Speed", "Life", "Mana", "EnergyShield", "TotalEHP",
	"FireResist", "ColdResist", "LightningResist", "ChaosResist",
}

function Driver.load_build(xmlText, name)
	loadBuildFromXML(xmlText, name or "spike")
	-- Build:Init runs the first calc; pump a second frame to guarantee settle
	-- (Build.lua:666-667 first calc; 1144-1152 recalc gate).
	runCallback("OnFrame")
	return true
end

-- Read the archetype-correct stats from the real calc output table.
function Driver.get_stats(statList)
	if not build or not build.calcsTab or not build.calcsTab.mainOutput then
		error("GET_STATS: mainOutput unavailable -- no build loaded / calc failed")
	end
	local out = build.calcsTab.mainOutput
	local keys = statList
	if not keys or #keys == 0 then
		keys = DEFAULT_STATS
	end
	local result = {}
	for _, k in ipairs(keys) do
		local v = out[k]
		if type(v) == "number" then
			result[k] = v
		elseif v == nil then
			result[k] = nil
		else
			result[k] = tostring(v)
		end
	end
	return result
end

-- Allocated-node count -- lets the worker prove EVAL_NEIGHBORS/APPLY_MOVE are
-- loadable (Task 4) without building the Epic-4 optimizer rewire.
function Driver.node_count()
	if not build or not build.spec or not build.spec.allocNodes then
		return 0
	end
	local n = 0
	for _ in pairs(build.spec.allocNodes) do n = n + 1 end
	return n
end

-- STUB (Epic 4 item 2/4): prove the command is wired + reachable, do NOT
-- implement neighbour generation or the optimizer rewire in this spike.
function Driver.eval_neighbors(_)
	return { stub = true, note = "EVAL_NEIGHBORS deferred to Epic 4 item 2/4", nodes = Driver.node_count() }
end
function Driver.apply_move(_)
	return { stub = true, note = "APPLY_MOVE deferred to Epic 4 item 2/4" }
end

-- Single JSON request line -> single JSON response line. THE command processor
-- for BOTH lanes (embedded host calls this via Lupa; luajit.exe serve() loop
-- calls it from io.lines). Never raises across the boundary -- errors are
-- captured and returned as {ok=false, error=...}.
function Driver.handle_command(line)
	local ok, resp = pcall(function()
		local req = dkjson.decode(line)
		if type(req) ~= "table" or not req.cmd then
			return { ok = false, error = "malformed request (need {cmd=...})" }
		end
		local cmd = req.cmd
		if cmd == "PING" then
			return { ok = true, cmd = cmd, pong = true }
		elseif cmd == "LOAD_BUILD" then
			Driver.load_build(req.xml, req.name)
			return { ok = true, cmd = cmd, nodes = Driver.node_count() }
		elseif cmd == "GET_STATS" then
			return { ok = true, cmd = cmd, stats = Driver.get_stats(req.stats) }
		elseif cmd == "EVAL_NEIGHBORS" then
			return { ok = true, cmd = cmd, result = Driver.eval_neighbors(req) }
		elseif cmd == "APPLY_MOVE" then
			return { ok = true, cmd = cmd, result = Driver.apply_move(req) }
		elseif cmd == "GC" then
			collectgarbage("collect")
			return { ok = true, cmd = cmd, kb = collectgarbage("count") }
		elseif cmd == "SHUTDOWN" then
			return { ok = true, cmd = cmd, bye = true }
		else
			return { ok = false, error = "unknown cmd: " .. tostring(cmd) }
		end
	end)
	if not ok then
		return dkjson.encode({ ok = false, error = tostring(resp) })
	end
	return dkjson.encode(resp)
end

-- luajit.exe subprocess lane (AC-4.1.5): read JSON commands from stdin, write
-- JSON responses to stdout, one per line. Not run under embed (HEADLESS_EMBED).
function Driver.serve()
	io.stdout:setvbuf("no")
	for line in io.lines() do
		if line ~= "" then
			io.write(Driver.handle_command(line), "\n")
			io.flush()
			local dec = dkjson.decode(line)
			if type(dec) == "table" and dec.cmd == "SHUTDOWN" then
				break
			end
		end
	end
end

-- ===========================================================================
-- (5) Lane selection. Embedded host sets HEADLESS_EMBED=true and drives via
--     Driver.handle_command; the standalone luajit.exe lane runs the loop.
-- ===========================================================================
if not HEADLESS_EMBED then
	-- Signal boot success to the parent before blocking on stdin.
	io.write(dkjson.encode({ ok = true, ready = true, lane = "luajit.exe" }), "\n")
	io.flush()
	Driver.serve()
end
