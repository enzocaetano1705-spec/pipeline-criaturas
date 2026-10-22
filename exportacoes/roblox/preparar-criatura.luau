--[[ Preparo de uma criatura importada (File › Import 3D, Rig Type: Custom) no Roblox Studio.

Rode na barra de comandos do Studio ou pelo MCP (execute_luau, datamodel Edit). Pode ser rodado de novo: não duplica nada.
Ajuste a CONFIGURAÇÃO. Os valores de cada criatura estão em exportacoes/roblox/criaturas.json.

O que faz:
  1. Transparência: SurfaceAppearance com a textura e AlphaMode.Transparency (com TextureID o alfa mostra a cor da peça).
  2. Escala (Model:ScaleTo) e base no chão.
  3. Hitbox: Part invisível do tamanho da criatura, que colide e vira o PrimaryPart. A malha não colide
     (a malha animada não serve de colisão estável).
  4. Animator no AnimationController; poses das animações embaixo da Raiz (o topo não é animado pelo Roblox);
     e, se pedido, um Script de prévia que toca uma animação no Run/Play.
  5. Confere a frente: o bico/cabeça deve estar no sentido do LookVector do PrimaryPart.
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

local malha = modelo:FindFirstChildWhichIsA("MeshPart")
assert(malha, "o Model não tem MeshPart (importou como Rig Type Custom?)")

-- 1) transparência das penas/orelhas
local sa = malha:FindFirstChildOfClass("SurfaceAppearance") or Instance.new("SurfaceAppearance")
sa.ColorMap = malha.TextureID
sa.AlphaMode = Enum.AlphaMode.Transparency
sa.Parent = malha

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
hitbox.CFrame = CFrame.lookAt(cf.Position, cf.Position + malha.CFrame.LookVector)
hitbox.Transparency = 1
hitbox.CanCollide = true
hitbox.Anchored = true
hitbox.Parent = modelo
malha.CanCollide = false
malha.CanTouch = false
malha.Massless = true
malha.Anchored = false
local solda = malha:FindFirstChild("SoldaHitbox") or Instance.new("WeldConstraint")
solda.Name = "SoldaHitbox"
solda.Part0, solda.Part1 = hitbox, malha
solda.Parent = malha
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
				raiz.Weight = 0
				for _, p in ipairs(topo) do kf:RemovePose(p); raiz:AddSubPose(p) end
				kf:AddPose(raiz)
			end
		end
	end
end
local velho = modelo:FindFirstChild("TocarAnimacao")
if velho then velho:Destroy() end
if PREVIA then
	local s = Instance.new("Script")
	s.Name = "TocarAnimacao"
	s.Source = ([[
-- Prévia: toca "%s" em loop no Run/Play. O id gerado aqui é temporário (só vale nos testes do Studio);
-- no jogo publicado use o AnimationId da animação publicada (veja GUIA-IA-ROBLOX.md).
local modelo = script.Parent
local seq = modelo.AnimSaves.Value["%s"]
local anim = Instance.new("Animation")
anim.AnimationId = game:GetService("KeyframeSequenceProvider"):RegisterKeyframeSequence(seq)
local faixa = modelo.AnimationController:FindFirstChildOfClass("Animator"):LoadAnimation(anim)
faixa.Looped = true
faixa:Play()
]]):format(PREVIA, PREVIA)
	s.Parent = modelo
end

-- 5) conferência da frente
local cabeca = modelo:FindFirstChild(OSSO_CABECA, true)
local cauda = modelo:FindFirstChild(OSSO_CAUDA, true)
local frente = "não conferida (sem os ossos " .. OSSO_CABECA .. "/" .. OSSO_CAUDA .. ")"
if cabeca and cauda then
	local d = (cabeca.WorldPosition - cauda.WorldPosition) * Vector3.new(1, 0, 1)
	frente = (d.Magnitude > 0 and d.Unit:Dot(hitbox.CFrame.LookVector) > 0.3) and "ok" or "INVERTIDA (reexporte com a Raiz girada)"
end

if rec then CHS:FinishRecording(rec, Enum.FinishRecordingOperation.Commit) end
print(("[preparar] %s: escala %.1f, %.1f x %.1f x %.1f studs, frente %s"):format(
	NOME, modelo:GetScale(), tamanho.X, tamanho.Y, tamanho.Z, frente))
