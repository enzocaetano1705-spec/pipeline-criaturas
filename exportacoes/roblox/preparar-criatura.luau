--[[ Preparo de uma criatura importada (File › Import 3D, Rig Type: Custom) no Roblox Studio.

Rode na barra de comandos do Studio ou pelo MCP (execute_luau, datamodel Edit). Pode ser rodado de novo: não duplica nada.
Ajuste a CONFIGURAÇÃO. Os valores de cada criatura estão em exportacoes/roblox/criaturas.json.

O que faz:
  1. Textura: SurfaceAppearance com AlphaMode.Transparency (com TextureID o alfa mostra a cor da peça) e
     ResampleMode.Pixelated (sem isso o Roblox borra a pixel art com filtro bilinear).
  2. Escala (Model:ScaleTo) e base no chão.
  3. Hitbox: Part invisível do tamanho da criatura, que colide e vira o PrimaryPart. A malha não colide
     (a malha animada não serve de colisão estável).
  4. Animator no AnimationController; poses das animações embaixo da Raiz (o topo não é animado pelo Roblox);
     ModelStreamingMode Persistent (o modelo inteiro sempre no cliente); cópia das animações em <Model>.Animacoes e,
     se pedido, um Script de prévia que roda NO CLIENTE e toca uma animação no Play/Run.
  5. Frente: a Hitbox (PrimaryPart) olha para a cabeça; mova a criatura pelo LookVector da Hitbox.
Tudo dentro de uma gravação do ChangeHistoryService (Ctrl+Z desfaz).
]]

-- CONFIGURAÇÃO ---------------------------------------------------------------
local NOME = "Pavao_F2"          -- nome do Model no Workspace (= nome do .glb)
local ESCALA = 3                 -- escala_studio do criaturas.json
local PREVIA = "walk"            -- "idle", "walk" ou nil (sem script de prévia)
local OSSO_CABECA = "head"       -- ossos usados para conferir a frente (cabeça à frente da cauda)
local OSSO_CAUDA = "tail_1"
--------------------------------------------------------------------------------

local CHS = game:GetService("ChangeHistoryService")
local modelo = workspace:FindFirstChild(NOME)
assert(modelo and modelo:IsA("Model"), "Model '" .. NOME .. "' não está no Workspace")
local rec = CHS:TryBeginRecording("Preparar " .. NOME)

-- a malha principal é a que tem os ossos (Raiz); criaturas com textura separada (ex.: cabeça) têm outras MeshParts
local malhas = {}
for _, p in ipairs(modelo:GetChildren()) do if p:IsA("MeshPart") then table.insert(malhas, p) end end
assert(#malhas > 0, "o Model não tem MeshPart (importou como Rig Type Custom?)")
local malha = modelo:FindFirstChild("Raiz") or malhas[1]

-- 1) transparência das penas/orelhas, em cada malha
for _, m in ipairs(malhas) do
	local sa = m:FindFirstChildOfClass("SurfaceAppearance") or Instance.new("SurfaceAppearance")
	sa.ColorMap = m.TextureID
	sa.AlphaMode = Enum.AlphaMode.Transparency
	pcall(function() sa.ResampleMode = Enum.ResamplerMode.Pixelated end)
	sa.Parent = m
end

-- 2) escala e chão (antes da hitbox, para ela nascer do tamanho certo)
local hitbox = modelo:FindFirstChild("Hitbox")
if hitbox then hitbox:Destroy() end -- refeita abaixo
if math.abs(modelo:GetScale() - ESCALA) > 1e-3 then
	modelo:ScaleTo(ESCALA)
end
local cf, tamanho = modelo:GetBoundingBox()
local chao = 0
local base = workspace:FindFirstChild("Baseplate")
if base then chao = base.Position.Y + base.Size.Y / 2 end
modelo:PivotTo(modelo:GetPivot() + Vector3.new(0, chao - (cf.Position.Y - tamanho.Y / 2), 0))
cf, tamanho = modelo:GetBoundingBox()

-- 3) hitbox: colisão estável e PrimaryPart (gira junto com a criatura, frente = LookVector)
hitbox = Instance.new("Part")
hitbox.Name = "Hitbox"
hitbox.Size = tamanho
-- frente: da cauda para a cabeça, se os ossos existirem; senão +Z da malha (o Blockbench exporta a frente em +Z)
local cabeca = modelo:FindFirstChild(OSSO_CABECA, true)
local cauda = modelo:FindFirstChild(OSSO_CAUDA, true)
local frente_dir = -malha.CFrame.LookVector
if cabeca and cauda then
	local d = (cabeca.WorldPosition - cauda.WorldPosition) * Vector3.new(1, 0, 1)
	if d.Magnitude > 1e-3 then frente_dir = d.Unit end
end
hitbox.CFrame = CFrame.lookAt(cf.Position, cf.Position + frente_dir)
hitbox.Transparency = 1
hitbox.CanCollide = true
hitbox.Anchored = true
hitbox.Parent = modelo
for _, m in ipairs(malhas) do
	m.CanCollide = false
	m.CanTouch = false
	m.Massless = true
	m.Anchored = false
	local solda = m:FindFirstChild("SoldaHitbox") or Instance.new("WeldConstraint")
	solda.Name = "SoldaHitbox"
	solda.Part0, solda.Part1 = hitbox, m
	solda.Parent = m
end
modelo.PrimaryPart = hitbox

-- 4) animação
local controlador = modelo:FindFirstChildOfClass("AnimationController")
if controlador and not controlador:FindFirstChildOfClass("Animator") then
	Instance.new("Animator").Parent = controlador
end
-- 4b) o Roblox não anima a pose do topo da KeyframeSequence (é a peça raiz): se o topo não for a Raiz,
--     embrulha as poses numa pose "Raiz" neutra para o `body` (balanço do corpo) voltar a tocar
local pasta = modelo:FindFirstChild("AnimSaves") and modelo.AnimSaves.Value
if pasta then
	for _, seq in ipairs(pasta:GetChildren()) do
		for _, kf in ipairs(seq:GetKeyframes()) do
			local topo = kf:GetPoses()
			if not (#topo == 1 and topo[1].Name == malha.Name) then
				local raiz = Instance.new("Pose")
				raiz.Name = malha.Name
				for _, p in ipairs(topo) do kf:RemovePose(p); raiz:AddSubPose(p) end
				kf:AddPose(raiz)
			end
		end
	end
end
-- 4b2) giro na pose do topo: dependendo das opções do Import 3D, o importador grava ~180° na pose da Raiz e no
--      body, e a criatura vira de lado no walk. Tira o giro da Raiz e compensa nas poses filhas (testado: o body
--      volta a girar no máximo 4,7°, como no Blockbench).
if pasta then
	for _, seq in ipairs(pasta:GetChildren()) do
		for _, kf in ipairs(seq:GetKeyframes()) do
			for _, raiz in ipairs(kf:GetPoses()) do
				local R = raiz.CFrame - raiz.CFrame.Position
				local _, ang = R:ToAxisAngle()
				if math.abs(ang) > 1e-3 then
					for _, filho in ipairs(raiz:GetSubPoses()) do filho.CFrame = R:Inverse() * filho.CFrame end
					raiz.CFrame = CFrame.new(raiz.CFrame.Position)
				end
			end
		end
	end
end

-- 4c) streaming: Persistent, o modelo inteiro sempre no cliente (com StreamingEnabled, sem isto o cliente recebia só a malha,
--     sem Hitbox, sem animações e sem o script de prévia)
modelo.ModelStreamingMode = Enum.ModelStreamingMode.Persistent

-- 4d) prévia NO CLIENTE: o Play desenha pelo cliente, e o cliente não carrega ids temporários criados no servidor
--     nem enxerga o ServerStorage. As KeyframeSequences vão para <Model>.Animacoes e o script roda no cliente.
local animacoes = modelo:FindFirstChild("Animacoes") or Instance.new("Folder")
animacoes.Name = "Animacoes"
animacoes:ClearAllChildren()
if pasta then
	for _, seq in ipairs(pasta:GetChildren()) do seq:Clone().Parent = animacoes end
end
animacoes.Parent = modelo
local velho = modelo:FindFirstChild("TocarAnimacao")
if velho then velho:Destroy() end
if PREVIA then
	local s = Instance.new("Script")
	s.Name = "TocarAnimacao"
	s.RunContext = Enum.RunContext.Client
	s.Source = ([[
-- Prévia de animação (RunContext = Client). Toca "%s" em loop no Play e no Run.
-- O id gerado aqui é temporário (só vale no Studio); no jogo publicado use os AnimationIds publicados (GUIA-IA-ROBLOX.md).
local modelo = script.Parent
local seq = modelo:WaitForChild("Animacoes"):WaitForChild("%s")
local controlador = modelo:WaitForChild("AnimationController")
local animator = controlador:FindFirstChildOfClass("Animator") or Instance.new("Animator", controlador)
local anim = Instance.new("Animation")
anim.AnimationId = game:GetService("KeyframeSequenceProvider"):RegisterKeyframeSequence(seq)
local faixa = animator:LoadAnimation(anim)
faixa.Looped = true
faixa:Play()
]]):format(PREVIA, PREVIA)
	s.Parent = modelo
end

-- 5) conferência da frente
local frente = (cabeca and cauda) and "pela cabeça (ossos)" or "assumida +Z da malha (sem ossos de cabeça/cauda)"

if rec then CHS:FinishRecording(rec, Enum.FinishRecordingOperation.Commit) end
print(("[preparar] %s: escala %.1f, %.1f x %.1f x %.1f studs, frente %s"):format(
	NOME, modelo:GetScale(), tamanho.X, tamanho.Y, tamanho.Z, frente))
