--[[ Preparo de uma criatura importada (File › Import 3D, Rig Type: Custom) no Roblox Studio.

Rode na barra de comandos do Studio ou pelo MCP (execute_luau, datamodel Edit). Pode ser rodado de novo: não duplica nada.
Use a receita gerada por scripts/preparar-roblox.py. O registro fica em exportacoes/roblox/criaturas.json.

O que faz:
  1. Textura: SurfaceAppearance com AlphaMode.Transparency (com TextureID o alfa mostra a cor da peça) e
     ResampleMode.Pixelated (sem isso o Roblox borra a pixel art com filtro bilinear).
  2. Escala (Model:ScaleTo) e base no chão.
  3. Perfil v1: Hitbox do corpo até o chão. Perfil v2: caixas orientadas por peça/opacidade,
     com Hitbox só de referência (não colide) e módulo que acompanha Bones na prévia.
  4. Animator no AnimationController; poses das animações embaixo da Raiz (o topo não é animado pelo Roblox);
     ModelStreamingMode Persistent (o modelo inteiro sempre no cliente); cópia das animações em <Model>.Animacoes e,
     se pedido, um Script de prévia que roda NO CLIENTE e toca uma animação no Play/Run.
  5. Frente: a Hitbox (PrimaryPart) olha para a cabeça; mova a criatura pelo LookVector da Hitbox.
Tudo dentro de uma gravação do ChangeHistoryService (Ctrl+Z desfaz).
]]

-- CONFIGURAÇÃO ---------------------------------------------------------------
local NOME = "Pavao_F1"          -- nome do Model no Workspace (= nome do .glb)
local PASTA = "criaturas modeladas blockbench" -- pasta no Workspace para as novas importações
local ESCALA = 3               -- nil preserva a escala atual; receita gerada usa escala_studio
local PERFIL_JSON = [==[{"versao":2,"tipo":"composta_ossos","pecas":[{"nome":"feather_left_rise","cubo_uuid":"542ca9ec-3df9-4edc-8236-0b62eb5a8461","osso":"feather_left_1","tamanho":[2.0,2.0,0.25],"cf":[-0.5,1.0,0.0,1.0,0.0,0.0,0.0,1.0,-0.0,0.0,-0.0,1.0],"plano":true},{"nome":"feather_left_rise","cubo_uuid":"542ca9ec-3df9-4edc-8236-0b62eb5a8461","osso":"feather_left_1","tamanho":[3.0,1.0,0.25],"cf":[-1.0,2.5,0.0,1.0,0.0,0.0,0.0,1.0,-0.0,0.0,-0.0,1.0],"plano":true},{"nome":"feather_left_rise","cubo_uuid":"542ca9ec-3df9-4edc-8236-0b62eb5a8461","osso":"feather_left_1","tamanho":[5.0,1.0,0.25],"cf":[-3.0,3.5,0.0,1.0,0.0,0.0,0.0,1.0,-0.0,0.0,-0.0,1.0],"plano":true},{"nome":"feather_left_rise","cubo_uuid":"542ca9ec-3df9-4edc-8236-0b62eb5a8461","osso":"feather_left_1","tamanho":[4.0,1.0,0.25],"cf":[-3.5,4.5,0.0,1.0,0.0,0.0,0.0,1.0,-0.0,0.0,-0.0,1.0],"plano":true},{"nome":"feather_left_top","cubo_uuid":"4b125b7a-f537-4822-9935-b7b07f895b6a","osso":"feather_left_2","tamanho":[4.0,0.25,1.0],"cf":[0.091311192,0.141125264,0.267692411,0.991444863,4.5e-08,0.130526178,0.005693417,0.999048225,-0.043246143,-0.130401949,0.043619307,0.990501231],"plano":true},{"nome":"feather_left_top","cubo_uuid":"4b125b7a-f537-4822-9935-b7b07f895b6a","osso":"feather_left_2","tamanho":[6.0,0.25,1.0],"cf":[-0.769607493,0.092185704,1.38859559,0.991444863,4.5e-08,0.130526178,0.005693417,0.999048225,-0.043246143,-0.130401949,0.043619307,0.990501231],"plano":true},{"nome":"feather_left_top","cubo_uuid":"4b125b7a-f537-4822-9935-b7b07f895b6a","osso":"feather_left_2","tamanho":[5.0,0.25,1.0],"cf":[-1.134803747,0.046092852,2.444297795,0.991444863,4.5e-08,0.130526178,0.005693417,0.999048225,-0.043246143,-0.130401949,0.043619307,0.990501231],"plano":true},{"nome":"feather_left_top","cubo_uuid":"4b125b7a-f537-4822-9935-b7b07f895b6a","osso":"feather_left_2","tamanho":[6.0,0.25,2.0],"cf":[-1.434736911,-0.021623072,3.995250615,0.991444863,4.5e-08,0.130526178,0.005693417,0.999048225,-0.043246143,-0.130401949,0.043619307,0.990501231],"plano":true},{"nome":"feather_left_top","cubo_uuid":"4b125b7a-f537-4822-9935-b7b07f895b6a","osso":"feather_left_2","tamanho":[5.0,0.25,1.0],"cf":[-1.734670075,-0.089338995,5.546203436,0.991444863,4.5e-08,0.130526178,0.005693417,0.999048225,-0.043246143,-0.130401949,0.043619307,0.990501231],"plano":true},{"nome":"feather_left_top","cubo_uuid":"4b125b7a-f537-4822-9935-b7b07f895b6a","osso":"feather_left_2","tamanho":[4.0,0.25,1.0],"cf":[-2.099866328,-0.135431847,6.601905641,0.991444863,4.5e-08,0.130526178,0.005693417,0.999048225,-0.043246143,-0.130401949,0.043619307,0.990501231],"plano":true},{"nome":"feather_left_eye","cubo_uuid":"9adb646a-1927-491c-bd6f-633b63b2ec78","osso":"feather_left_3","tamanho":[5.0,1.0,0.25],"cf":[4.292444914,-2.627681805,3.945069723,-0.220242459,-0.974720817,0.037584404,0.497576622,-0.079122085,0.863803914,-0.8389939,0.208947418,0.502424334],"plano":true},{"nome":"feather_left_eye","cubo_uuid":"9adb646a-1927-491c-bd6f-633b63b2ec78","osso":"feather_left_3","tamanho":[6.0,1.0,0.25],"cf":[3.207602867,-2.458015579,3.734520191,-0.220242459,-0.974720817,0.037584404,0.497576622,-0.079122085,0.863803914,-0.8389939,0.208947418,0.502424334],"plano":true},{"nome":"feather_left_eye","cubo_uuid":"9adb646a-1927-491c-bd6f-633b63b2ec78","osso":"feather_left_3","tamanho":[8.0,2.0,0.25],"cf":[1.525279183,-2.079122085,3.208947418,-0.220242459,-0.974720817,0.037584404,0.497576622,-0.079122085,0.863803914,-0.8389939,0.208947418,0.502424334],"plano":true},{"nome":"feather_left_eye","cubo_uuid":"9adb646a-1927-491c-bd6f-633b63b2ec78","osso":"feather_left_3","tamanho":[7.0,1.0,0.25],"cf":[-0.046923273,-1.949016902,3.102871596,-0.220242459,-0.974720817,0.037584404,0.497576622,-0.079122085,0.863803914,-0.8389939,0.208947418,0.502424334],"plano":true},{"nome":"feather_right_rise","cubo_uuid":"f8d3badc-8b74-4782-8df4-cbfb2c47dd53","osso":"feather_right_1","tamanho":[2.0,2.0,0.25],"cf":[0.5,1.0,0.0,1.0,0.0,0.0,0.0,1.0,-0.0,0.0,-0.0,1.0],"plano":true},{"nome":"feather_right_rise","cubo_uuid":"f8d3badc-8b74-4782-8df4-cbfb2c47dd53","osso":"feather_right_1","tamanho":[3.0,1.0,0.25],"cf":[1.0,2.5,0.0,1.0,0.0,0.0,0.0,1.0,-0.0,0.0,-0.0,1.0],"plano":true},{"nome":"feather_right_rise","cubo_uuid":"f8d3badc-8b74-4782-8df4-cbfb2c47dd53","osso":"feather_right_1","tamanho":[5.0,1.0,0.25],"cf":[3.0,3.5,0.0,1.0,0.0,0.0,0.0,1.0,-0.0,0.0,-0.0,1.0],"plano":true},{"nome":"feather_right_rise","cubo_uuid":"f8d3badc-8b74-4782-8df4-cbfb2c47dd53","osso":"feather_right_1","tamanho":[4.0,1.0,0.25],"cf":[3.5,4.5,0.0,1.0,0.0,0.0,0.0,1.0,-0.0,0.0,-0.0,1.0],"plano":true},{"nome":"feather_right_top","cubo_uuid":"bba2afd1-1257-42e8-8546-e036a77c036c","osso":"feather_right_2","tamanho":[4.0,0.25,1.0],"cf":[-0.091311192,0.141125264,0.267692411,0.991444863,-4.5e-08,-0.130526178,-0.005693417,0.999048225,-0.043246143,0.130401949,0.043619307,0.990501231],"plano":true},{"nome":"feather_right_top","cubo_uuid":"bba2afd1-1257-42e8-8546-e036a77c036c","osso":"feather_right_2","tamanho":[6.0,0.25,1.0],"cf":[0.769607493,0.092185704,1.38859559,0.991444863,-4.5e-08,-0.130526178,-0.005693417,0.999048225,-0.043246143,0.130401949,0.043619307,0.990501231],"plano":true},{"nome":"feather_right_top","cubo_uuid":"bba2afd1-1257-42e8-8546-e036a77c036c","osso":"feather_right_2","tamanho":[5.0,0.25,1.0],"cf":[1.134803747,0.046092852,2.444297795,0.991444863,-4.5e-08,-0.130526178,-0.005693417,0.999048225,-0.043246143,0.130401949,0.043619307,0.990501231],"plano":true},{"nome":"feather_right_top","cubo_uuid":"bba2afd1-1257-42e8-8546-e036a77c036c","osso":"feather_right_2","tamanho":[6.0,0.25,2.0],"cf":[1.434736911,-0.021623072,3.995250615,0.991444863,-4.5e-08,-0.130526178,-0.005693417,0.999048225,-0.043246143,0.130401949,0.043619307,0.990501231],"plano":true},{"nome":"feather_right_top","cubo_uuid":"bba2afd1-1257-42e8-8546-e036a77c036c","osso":"feather_right_2","tamanho":[5.0,0.25,1.0],"cf":[1.734670075,-0.089338995,5.546203436,0.991444863,-4.5e-08,-0.130526178,-0.005693417,0.999048225,-0.043246143,0.130401949,0.043619307,0.990501231],"plano":true},{"nome":"feather_right_top","cubo_uuid":"bba2afd1-1257-42e8-8546-e036a77c036c","osso":"feather_right_2","tamanho":[4.0,0.25,1.0],"cf":[2.099866328,-0.135431847,6.601905641,0.991444863,-4.5e-08,-0.130526178,-0.005693417,0.999048225,-0.043246143,0.130401949,0.043619307,0.990501231],"plano":true},{"nome":"feather_right_eye","cubo_uuid":"41bb77b1-bdb1-4a45-a136-257f7ae85c19","osso":"feather_right_3","tamanho":[5.0,1.0,0.25],"cf":[-4.292444914,-2.627681805,3.945069723,-0.220242459,0.974720817,-0.037584404,-0.497576622,-0.079122085,0.863803914,0.8389939,0.208947418,0.502424334],"plano":true},{"nome":"feather_right_eye","cubo_uuid":"41bb77b1-bdb1-4a45-a136-257f7ae85c19","osso":"feather_right_3","tamanho":[6.0,1.0,0.25],"cf":[-3.207602867,-2.458015579,3.734520191,-0.220242459,0.974720817,-0.037584404,-0.497576622,-0.079122085,0.863803914,0.8389939,0.208947418,0.502424334],"plano":true},{"nome":"feather_right_eye","cubo_uuid":"41bb77b1-bdb1-4a45-a136-257f7ae85c19","osso":"feather_right_3","tamanho":[8.0,2.0,0.25],"cf":[-1.525279183,-2.079122085,3.208947418,-0.220242459,0.974720817,-0.037584404,-0.497576622,-0.079122085,0.863803914,0.8389939,0.208947418,0.502424334],"plano":true},{"nome":"feather_right_eye","cubo_uuid":"41bb77b1-bdb1-4a45-a136-257f7ae85c19","osso":"feather_right_3","tamanho":[7.0,1.0,0.25],"cf":[0.046923273,-1.949016902,3.102871596,-0.220242459,0.974720817,-0.037584404,-0.497576622,-0.079122085,0.863803914,0.8389939,0.208947418,0.502424334],"plano":true},{"nome":"body_upper","cubo_uuid":"9c075072-5bf1-4361-bd8a-658f17319039","osso":"body","tamanho":[13.0,7.0,12.0],"cf":[0.0,1.0,1.0,1.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,1.0],"plano":false},{"nome":"body_lower","cubo_uuid":"f4fbabbe-28d3-0d35-6d12-11f87acbbfee","osso":"body","tamanho":[13.0,4.0,13.0],"cf":[0.0,-4.5,0.5,1.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,1.0],"plano":false}],"cubos":["542ca9ec-3df9-4edc-8236-0b62eb5a8461","4b125b7a-f537-4822-9935-b7b07f895b6a","9adb646a-1927-491c-bd6f-633b63b2ec78","f8d3badc-8b74-4782-8df4-cbfb2c47dd53","bba2afd1-1257-42e8-8546-e036a77c036c","41bb77b1-bdb1-4a45-a136-257f7ae85c19","9c075072-5bf1-4361-bd8a-658f17319039","f4fbabbe-28d3-0d35-6d12-11f87acbbfee"],"fonte_sha256":"9604fa4c679be7e52ea95941735099613ecc0fe54eadfd33f1df95125c0185eb","espessura_planos":0.25,"glb_sha256":"d3a8ce0715a901fdcd9834dbc889cfe8ab4697187db18914fdef36265d5aac5d"}]==]          -- preenchido por scripts/preparar-roblox.py; ou usa atributo já registrado
local PREVIA = "walk"            -- "idle", "walk" ou nil (sem script de prévia)
local OSSO_CABECA = "head"       -- ossos usados para conferir a frente (cabeça à frente da cauda)
local OSSO_CAUDA = "tail_1"
local MODULO_COLISAO = [====[
-- Segue os Bones no mesmo simulador que toca a animação.
-- A prévia chama no cliente; integração com animações publicadas deve escolher sua autoridade física.
-- Não implementa montaria, transporte de passageiros ou detecção de dano.
local M = {}
local estados = setmetatable({}, {__mode = "k"})
local function estado(modelo)
	if estados[modelo] then return estados[modelo] end
	local e = {partes={}, offsets={}, tamanhos={}, ossos={}}
	for _, p in ipairs(modelo:WaitForChild("ColisoresPipeline"):GetChildren()) do
		if p:IsA("BasePart") then
			local bone = assert(p:FindFirstChild("Osso"), "Colisor sem referência de osso").Value
			assert(bone and bone:IsA("Bone"), "Osso do colisor ausente")
			table.insert(e.partes,p)
			table.insert(e.offsets,p:GetAttribute("PipelineOffset"))
			table.insert(e.tamanhos,p:GetAttribute("PipelineTamanho"))
			table.insert(e.ossos,bone)
		end
	end
	estados[modelo]=e
	return e
end
function M.Atualizar(modelo)
	local e = estado(modelo)
	local escala = modelo:GetScale()/16
	if escala ~= e.escala then
		e.locais={}
		for i,p in ipairs(e.partes) do
			local offset=e.offsets[i]
			e.locais[i]=CFrame.new(offset.Position*escala)*(offset-offset.Position)
			p.Size=e.tamanhos[i]*escala
		end
		e.escala=escala
	end
	local mundo, cframes = {}, {}
	for i,bone in ipairs(e.ossos) do
		if not mundo[bone] then mundo[bone]=bone.TransformedWorldCFrame end
		cframes[i]=mundo[bone]*e.locais[i]
	end
	if modelo:IsDescendantOf(workspace) then
		workspace:BulkMoveTo(e.partes,cframes,Enum.BulkMoveMode.FireCFrameChanged)
	else -- fixtures isoladas fora do place
		for i,p in ipairs(e.partes) do p.CFrame=cframes[i] end
	end
end
function M.Iniciar(modelo)
	local e = estado(modelo)
	if e.conexao then return end
	M.Atualizar(modelo)
	e.conexao=game:GetService("RunService").PreSimulation:Connect(function()
		M.Atualizar(modelo)
	end)
	modelo.Destroying:Once(function()
		e.conexao:Disconnect()
		estados[modelo]=nil
	end)
end
return M

]====]
--------------------------------------------------------------------------------

local CHS = game:GetService("ChangeHistoryService")
local container = assert(workspace:FindFirstChild(PASTA), "Falta a pasta Workspace." .. PASTA)
local modelo
for _, filho in ipairs(container:GetChildren()) do
	if filho.Name == NOME and filho:IsA("Model") then
		assert(not modelo, "Há dois modelos chamados " .. NOME .. " na pasta de importação")
		modelo = filho
	end
end
assert(modelo, "Model '" .. NOME .. "' não está na pasta de importação")
-- Animacoes contém Poses com os mesmos nomes dos Bones; buscar pelo tipo antes de alterar.
local ossosPorNome = {}
for _, d in ipairs(modelo:GetDescendants()) do
	if d:IsA("Bone") then
		assert(not ossosPorNome[d.Name], "Nome de Bone duplicado: " .. d.Name)
		ossosPorNome[d.Name] = d
	end
end
local perfilJSON = PERFIL_JSON or modelo:GetAttribute("PipelineColisao")
assert(perfilJSON, "Falta perfil físico: gere a receita com scripts/preparar-roblox.py")
local perfil = game:GetService("HttpService"):JSONDecode(perfilJSON)
local composto = perfil.versao == 2 and perfil.tipo == "composta_ossos"
assert(composto or (perfil.versao == 1 and perfil.tipo == "corpo_estatico_ate_o_chao"), "Perfil físico incompatível")
local ossoFisico
local ossosFisicos = {}
if composto then
	assert(not MODULO_COLISAO:find("@COLISAO_OSSOS@",1,true), "Gere a receita com o módulo de colisão")
	assert(#perfil.pecas > 0 and #perfil.pecas <= 192, "Orçamento físico excedido")
	for _, p in ipairs(perfil.pecas) do
		local bone = ossosPorNome[p.osso]
		assert(bone and bone:IsA("Bone"), "Osso físico ausente: " .. p.osso)
		assert(#p.cf == 12 and #p.tamanho == 3, "Peça física inválida: " .. p.nome)
		for _, v in ipairs(p.tamanho) do assert(v > 0, "Colisor degenerado: " .. p.nome) end
		ossosFisicos[p.osso] = bone
	end
else
	ossoFisico = ossosPorNome[perfil.osso]
	assert(ossoFisico and ossoFisico:IsA("Bone"), "Osso físico ausente: " .. perfil.osso)
end

-- a malha principal é a que tem os ossos (Raiz); criaturas com textura separada (ex.: cabeça) têm outras MeshParts
local malhas = {}
for _, p in ipairs(modelo:GetDescendants()) do if p:IsA("MeshPart") then table.insert(malhas, p) end end
assert(#malhas > 0, "o Model não tem MeshPart (importou como Rig Type Custom?)")
local malha = modelo:FindFirstChild("Raiz", true) or malhas[1]
assert(malha:IsA("MeshPart"), "Raiz precisa ser a MeshPart do rig Custom")
-- Validar antes de alterar: nunca atribuir uma string vazia por cima do mapa importado.
for _, m in ipairs(malhas) do
	local sa = m:FindFirstChildOfClass("SurfaceAppearance")
	assert((sa and sa.ColorMapContent.SourceType ~= Enum.ContentSourceType.None) or m.TextureID ~= "",
		m:GetFullName() .. ": nenhuma textura importada (ColorMap e TextureID vazios)")
end
local rec = CHS:TryBeginRecording("Preparar " .. NOME)

-- 1) transparência das penas/orelhas, em cada malha
for _, m in ipairs(malhas) do
	local sa = m:FindFirstChildOfClass("SurfaceAppearance") or Instance.new("SurfaceAppearance")
	if sa.ColorMapContent.SourceType == Enum.ContentSourceType.None then sa.ColorMap = m.TextureID end
	sa.AlphaMode = Enum.AlphaMode.Transparency
	sa.ResampleMode = Enum.ResamplerMode.Pixelated
	sa.Color = Color3.new(1, 1, 1)
	m.Color = Color3.new(1, 1, 1)
	m.Material = Enum.Material.SmoothPlastic
	m.Reflectance = 0
	sa.Parent = m
end

-- 2) escala e chão (antes da hitbox, para ela nascer do tamanho certo)
local hitbox = modelo:FindFirstChild("Hitbox")
if hitbox then hitbox:Destroy() end -- refeita abaixo
local antigosColisores = modelo:FindFirstChild("ColisoresPipeline")
if antigosColisores then antigosColisores:Destroy() end
local antigoModulo = modelo:FindFirstChild("ColisaoOssos")
if antigoModulo then antigoModulo:Destroy() end
if ESCALA and math.abs(modelo:GetScale() - ESCALA) > 1e-3 then
	modelo:ScaleTo(ESCALA)
end
-- Medir as malhas no referencial da frente somente para apoiar a base no chão.
-- O bloqueio físico será calculado separadamente a partir do perfil do corpo.
local cabeca = ossosPorNome[OSSO_CABECA]
local cauda = ossosPorNome[OSSO_CAUDA]
local frente_dir = -malha.CFrame.LookVector * Vector3.new(1, 0, 1)
if cabeca and cauda then
	local d = (cabeca.WorldPosition - cauda.WorldPosition) * Vector3.new(1, 0, 1)
	if d.Magnitude > 1e-3 then frente_dir = d.Unit end
end
assert(frente_dir.Magnitude > 1e-3, "Não foi possível determinar a frente horizontal")
local eixos = CFrame.lookAt(Vector3.zero, frente_dir.Unit)
local menor, maior = Vector3.new(math.huge, math.huge, math.huge), Vector3.new(-math.huge, -math.huge, -math.huge)
for _, m in ipairs(malhas) do
	for _, x in ipairs({-1, 1}) do for _, y in ipairs({-1, 1}) do for _, z in ipairs({-1, 1}) do
		local p = eixos:PointToObjectSpace(m.CFrame:PointToWorldSpace(m.Size * Vector3.new(x, y, z) / 2))
		menor = Vector3.new(math.min(menor.X, p.X), math.min(menor.Y, p.Y), math.min(menor.Z, p.Z))
		maior = Vector3.new(math.max(maior.X, p.X), math.max(maior.Y, p.Y), math.max(maior.Z, p.Z))
	end end end
end
local tamanho = maior - menor
local cf = eixos * CFrame.new((menor + maior) / 2)
local chao = 0
local base = workspace:FindFirstChild("Baseplate")
if base then chao = base.Position.Y + base.Size.Y / 2 end
modelo:PivotTo(modelo:GetPivot() + Vector3.new(0, chao - (cf.Position.Y - tamanho.Y / 2), 0))
cf = cf + Vector3.new(0, chao - (cf.Position.Y - tamanho.Y / 2), 0)

-- A caixa visual inclui penas/crista/cauda. O bloqueio físico usa o corpo sólido,
-- calculado da fonte .bbmodel, e se estende até a base para locomoção.
local baseFisica = cf.Position.Y - tamanho.Y / 2
if composto then
	-- Referência de movimento sem superfície física; cada peça abaixo tem sua própria colisão.
	tamanho = Vector3.new(.2,.2,.2) * modelo:GetScale()
	cf = eixos * CFrame.new(eixos:PointToObjectSpace(malha.Position))
else
local inf, sup = Vector3.new(table.unpack(perfil.min)), Vector3.new(table.unpack(perfil.max))
local lo, hi = Vector3.new(math.huge, math.huge, math.huge), Vector3.new(-math.huge, -math.huge, -math.huge)
for _, x in ipairs({inf.X, sup.X}) do for _, y in ipairs({inf.Y, sup.Y}) do for _, z in ipairs({inf.Z, sup.Z}) do
	local p = eixos:PointToObjectSpace(ossoFisico.WorldCFrame:PointToWorldSpace(Vector3.new(x,y,z) * modelo:GetScale() / 16))
	lo = Vector3.new(math.min(lo.X,p.X), math.min(lo.Y,p.Y), math.min(lo.Z,p.Z))
	hi = Vector3.new(math.max(hi.X,p.X), math.max(hi.Y,p.Y), math.max(hi.Z,p.Z))
end end end
lo = Vector3.new(lo.X, baseFisica, lo.Z)
tamanho = hi - lo
assert(tamanho.X > 0 and tamanho.Y > 0 and tamanho.Z > 0, "Colisão degenerada")
cf = eixos * CFrame.new((lo + hi) / 2)
end
modelo:SetAttribute("PipelineColisao", perfilJSON)
modelo:SetAttribute("PipelineCriaturaId", NOME)
modelo:SetAttribute("PipelineFonteSHA256", perfil.fonte_sha256)
modelo:SetAttribute("PipelineGLBSHA256", perfil.glb_sha256)

-- 3) hitbox: colisão estável e PrimaryPart (gira junto com a criatura, frente = LookVector)
hitbox = Instance.new("Part")
hitbox.Name = "Hitbox"
hitbox.Size = tamanho
hitbox.CFrame = cf
hitbox.Transparency = 1
hitbox.CanCollide = not composto
hitbox.CanQuery = not composto
hitbox.CanTouch = false
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
if composto then
	local grupo = Instance.new("Folder"); grupo.Name = "ColisoresPipeline"
	for i,p in ipairs(perfil.pecas) do
		local colisor = Instance.new("Part")
		colisor.Name = ("%03d_%s"):format(i,p.nome)
		colisor:SetAttribute("PipelineOffset",CFrame.new(table.unpack(p.cf)))
		colisor:SetAttribute("PipelineTamanho",Vector3.new(table.unpack(p.tamanho)))
		colisor:SetAttribute("PipelineCuboUUID",p.cubo_uuid)
		colisor:SetAttribute("PipelinePlano",p.plano)
		local bone = Instance.new("ObjectValue"); bone.Name="Osso"; bone.Value=ossosFisicos[p.osso]; bone.Parent=colisor
		colisor.Transparency=1; colisor.CastShadow=false
		colisor.Anchored=true; colisor.CanCollide=true; colisor.CanTouch=false
		local offset = colisor:GetAttribute("PipelineOffset")
		local k = modelo:GetScale()/16
		colisor.Size=Vector3.new(table.unpack(p.tamanho))*k
		colisor.CFrame=bone.Value.WorldCFrame*CFrame.new(offset.Position*k)*(offset-offset.Position)
		colisor.Parent=grupo
	end
	grupo.Parent=modelo
	local modulo=Instance.new("ModuleScript"); modulo.Name="ColisaoOssos"; modulo.Source=MODULO_COLISAO; modulo.Parent=modelo
end

-- 4) animação
local controlador = modelo:FindFirstChildOfClass("AnimationController") or Instance.new("AnimationController", modelo)
if not controlador:FindFirstChildOfClass("Animator") then
	Instance.new("Animator").Parent = controlador
end
-- 4b) o Roblox não anima a pose do topo da KeyframeSequence (é a peça raiz): se o topo não for a Raiz,
--     embrulha as poses numa pose "Raiz" neutra para o `body` (balanço do corpo) voltar a tocar
local fonte = (modelo:FindFirstChild("AnimSaves") and modelo.AnimSaves.Value) or modelo:FindFirstChild("Animacoes")
local pasta = Instance.new("Folder") -- corrigir cópias; conservar as sequências originais do importador
if fonte then
	for _, seq in ipairs(fonte:GetChildren()) do
		if seq:IsA("KeyframeSequence") then seq:Clone().Parent = pasta end
	end
end
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
				if math.abs(math.abs(ang) - math.pi) < 0.01 then
					for _, filho in ipairs(raiz:GetSubPoses()) do
						local osso = malha:FindFirstChild(filho.Name, true)
						-- Só o osso diretamente sob a malha herda o giro de importação.
						-- F1 tem um root intermediário omitido nas poses; body já está no referencial correto.
						if osso and osso:IsA("Bone") and osso.Parent == malha then
							filho.CFrame = R:Inverse() * filho.CFrame
							local iniciais = modelo:FindFirstChild("InitialPoses")
							local inicial = iniciais and iniciais:FindFirstChild(filho.Name .. "_Original")
							if inicial then
								-- O importador também girou a posição de repouso: compensar só a
								-- rotação deixa um deslocamento de 2x o pivô (3,27 studs no F2).
								local p = inicial.Value.Position
								filho.CFrame += p - R:Inverse():VectorToWorldSpace(p)
							end
						end
					end
					raiz.CFrame = CFrame.new(raiz.CFrame.Position)
				elseif math.abs(ang) > 1e-3 then
					warn("Rotação inesperada da Raiz em " .. seq.Name .. ": " .. math.deg(ang) .. " graus; conferir antes de usar")
				end
			end
		end
	end
end

-- O caminho das Poses precisa coincidir com o dos Bones. O importador omite ossos
-- sem canais, como root no F1: inserir poses neutras e reconstruir os pais reais.
for _, seq in ipairs(pasta:GetChildren()) do
	for _, kf in ipairs(seq:GetKeyframes()) do
		local topo = kf:GetPoses()[1]
		local porNome = {}
		for _, p in ipairs(topo:GetDescendants()) do if p:IsA("Pose") then porNome[p.Name] = p end end
		local function garantir(osso)
			local p = porNome[osso.Name]
			if not p then p = Instance.new("Pose"); p.Name = osso.Name; porNome[osso.Name] = p end
			local pai = osso.Parent:IsA("Bone") and garantir(osso.Parent) or topo
			p.Parent = pai
			return p
		end
		for _, osso in ipairs(malha:GetDescendants()) do
			if osso:IsA("Bone") and porNome[osso.Name] then garantir(osso) end
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
pasta:Destroy()
local velho = modelo:FindFirstChild("TocarAnimacao")
if velho then velho:Destroy() end
if PREVIA and animacoes:FindFirstChild(PREVIA) then
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
local colisao = modelo:FindFirstChild("ColisaoOssos")
if colisao then require(colisao).Iniciar(modelo) end
]]):format(PREVIA, PREVIA)
	s.Parent = modelo
end

-- 5) conferência da frente
local frente = (cabeca and cauda) and "pela cabeça (ossos)" or "assumida +Z da malha (sem ossos de cabeça/cauda)"

if rec then CHS:FinishRecording(rec, Enum.FinishRecordingOperation.Commit) end
print(("[preparar] %s: escala %.1f, %.1f x %.1f x %.1f studs, frente %s"):format(
	NOME, modelo:GetScale(), tamanho.X, tamanho.Y, tamanho.Z, frente))
