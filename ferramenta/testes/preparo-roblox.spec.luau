-- Executar por MCP com o marcador substituído pelo preparar-criatura.luau vigente.
-- Fixtures fora do DataModel: testa o código real sem alterar os modelos do usuário.
local fixture = Instance.new("Folder")
local workspace = fixture
local container = Instance.new("Folder", fixture)
container.Name = "criaturas modeladas blockbench"
local fontes = Instance.new("Folder")
local function preparar()
-- @PREPARO@
end
local function caso(intermediario)
	local m = Instance.new("Model", container); m.Name = "Pavao_F2"
	local mesh = Instance.new("MeshPart", m); mesh.Name = "Raiz"
	mesh.Size = Vector3.new(2, 3, 8)
	mesh.CFrame = CFrame.new(10, 8, 2) * CFrame.Angles(0, math.rad(37), 0)
	local sa = Instance.new("SurfaceAppearance", mesh); sa.ColorMap = "rbxassetid://123315715785564"
	local pai = mesh
	if intermediario then pai = Instance.new("Bone", mesh); pai.Name = "root" end
	local body = Instance.new("Bone", pai); body.Name = "body"
	local ini = Instance.new("Folder", m); ini.Name = "InitialPoses"
	local R = CFrame.Angles(0, math.pi, 0)
	local inicial = Instance.new("CFrameValue", ini); inicial.Name = "body_Original"
	inicial.Value = CFrame.new(0, 1.070625, -0.5446625) * R
	local src = Instance.new("Folder", fontes)
	local ref = Instance.new("ObjectValue", m); ref.Name = "AnimSaves"; ref.Value = src
	local seq = Instance.new("KeyframeSequence", src); seq.Name = "walk"
	local kf = Instance.new("Keyframe", seq)
	local raiz = Instance.new("Pose", kf); raiz.Name = "Raiz"; raiz.CFrame = R
	local p = Instance.new("Pose", raiz); p.Name = "body"
	p.CFrame = intermediario and CFrame.new(0, 0.14, 0)
		or (R * CFrame.new(0, 0.03, 0) * CFrame.Angles(math.rad(4.7), 0, 0) + Vector3.new(0, 0, -1.089325))
	local original = p.CFrame
	preparar()
	local hpos, hsize = m.Hitbox.Position, m.Hitbox.Size
	for _ = 1, 2 do
		local topo = m.Animacoes.walk:GetKeyframes()[1]:GetPoses()[1]
		local b = topo:FindFirstChild("body", true)
		local _, angle = b.CFrame:ToAxisAngle()
		assert(math.abs(b.CFrame.Z) < 1e-5, "deslocamento extra no eixo Z")
		assert(math.abs(b.CFrame.Y - (intermediario and 0.14 or 0.03)) < 1e-5, "salto alterado")
		assert(math.abs(math.deg(angle) - (intermediario and 0 or 4.7)) < 0.01, "giro invertido")
		assert(b.Parent.Name == (intermediario and "root" or "Raiz"), "pai da Pose não coincide com Bone")
		assert(sa.ColorMap ~= "" and sa.ResampleMode == Enum.ResamplerMode.Pixelated, "mapa/filtro")
		assert(p.CFrame == original, "sequência original alterada")
		assert((m.Hitbox.Position - hpos).Magnitude < 0.001 and (m.Hitbox.Size - hsize).Magnitude < 0.001, "repetição deslocou hitbox")
		for _, x in {-1, 1} do for _, y in {-1, 1} do for _, z in {-1, 1} do
			local v = m.Hitbox.CFrame:PointToObjectSpace(mesh.CFrame:PointToWorldSpace(mesh.Size * Vector3.new(x, y, z) / 2))
			assert(math.abs(v.X) <= hsize.X/2 + 0.001 and math.abs(v.Y) <= hsize.Y/2 + 0.001 and math.abs(v.Z) <= hsize.Z/2 + 0.001, "malha fora da hitbox")
		end end end
		preparar()
	end
	m:Destroy(); src:Destroy()
end
local ok, err = pcall(function() caso(false); caso(true) end)
fixture:Destroy(); fontes:Destroy()
assert(ok, err)
return "OK: F2 sem offset, F1 com root intermediário, mapas, caixa girada, originais e repetição estáveis"
