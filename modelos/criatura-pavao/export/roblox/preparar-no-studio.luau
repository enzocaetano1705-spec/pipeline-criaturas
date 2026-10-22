-- Preparo de uma criatura importada do Blockbench (.glb) no Roblox Studio.
-- Rode na barra de comandos do Studio (ou pelo MCP) depois de File › Import 3D (Rig Type: Custom).
-- Validado com o pavão em 21/10/2026: transparência das penas, escala 3× e idle tocando no Run.
local MODELO = workspace.blockbench_export -- nome que o importador dá
local ESCALA = 3 -- 1 bloco do Blockbench vira 1 stud; 3× deixa um bebê na altura do joelho do avatar

local CHS = game:GetService("ChangeHistoryService")
local rec = CHS:TryBeginRecording("Preparar criatura importada")
local p = MODELO:FindFirstChildWhichIsA("MeshPart")

-- 1) Transparência: com TextureID, o alfa mostra a cor da peça (o fundo das penas fica escuro).
--    Um SurfaceAppearance com AlphaMode.Transparency recorta o alfa de verdade.
local sa = p:FindFirstChildOfClass("SurfaceAppearance") or Instance.new("SurfaceAppearance")
sa.ColorMap = p.TextureID
sa.AlphaMode = Enum.AlphaMode.Transparency
sa.Parent = p

-- 2) Escala e base no chão
MODELO:ScaleTo(ESCALA)
local cf, size = MODELO:GetBoundingBox()
MODELO:PivotTo(MODELO:GetPivot() + Vector3.new(0, -(cf.Position.Y - size.Y / 2), 0))
p.Anchored = true

-- 3) Animator e um script de prévia que toca o idle no Run/Play
local ac = MODELO:FindFirstChildOfClass("AnimationController")
if not ac:FindFirstChildOfClass("Animator") then Instance.new("Animator").Parent = ac end
local s = MODELO:FindFirstChild("TocarIdle") or Instance.new("Script")
s.Name = "TocarIdle"
s.Source = [[
-- Prévia: toca o idle importado (id temporário, vale só nos testes do Studio).
-- No jogo publicado, publique a animação e troque pelo id dela.
local modelo = script.Parent
local seq = game:GetService("ServerStorage").RBX_ANIMSAVES[modelo.Name].idle
local anim = Instance.new("Animation")
anim.AnimationId = game:GetService("KeyframeSequenceProvider"):RegisterKeyframeSequence(seq)
local faixa = modelo.AnimationController:FindFirstChildOfClass("Animator"):LoadAnimation(anim)
faixa.Looped = true
faixa:Play()
]]
s.Parent = MODELO
if rec then CHS:FinishRecording(rec, Enum.FinishRecordingOperation.Commit) end
