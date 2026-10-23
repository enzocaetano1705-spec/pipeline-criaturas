-- Operações em lote sobre MODELOS DESTE PLACE. Não arquiva nem apaga assets da conta Roblox.
-- Selecione Models no Explorer (Ctrl/Shift) e execute por MCP/barra de comandos.
-- AUDITAR é somente leitura. ARQUIVAR move para ServerStorage; Ctrl+Z desfaz o lote.
local ACAO = "AUDITAR" -- AUDITAR | ADOTAR | ARQUIVAR | RESTAURAR
local NOMES_CONHECIDOS = game:GetService("HttpService"):JSONDecode([==[["Pavao_F1", "Pavao_F2"]]==]) -- @REGISTRO@
local NOME_PASTA = "criaturas modeladas blockbench"
local HTTP = game:GetService("HttpService")
local conhecidos = {}
for _, nome in ipairs(NOMES_CONHECIDOS) do conhecidos[nome] = true end
local pasta = workspace:FindFirstChild(NOME_PASTA)
local storage = game:GetService("ServerStorage")
local historico = storage:FindFirstChild("HistoricoCriaturasBlockbench")
local selecionados = game:GetService("Selection"):Get()
local function identidade(m)
	return m:GetAttribute("PipelineCriaturaId") or m:GetAttribute("PipelineNomeOriginal") or m.Name
end
local function resumir(m)
	local assets = {}
	for _, d in ipairs(m:GetDescendants()) do
		if d:IsA("MeshPart") then
			local sa = d:FindFirstChildOfClass("SurfaceAppearance")
			table.insert(assets, {malha=d.MeshId, cor=sa and sa.ColorMap or d.TextureID})
		end
	end
	return {id=identidade(m), nome=m.Name, caminho=m:GetFullName(), escala=m:GetScale(), assets=assets,
		fonte=m:GetAttribute("PipelineFonteSHA256"), revisao=m:GetAttribute("PipelineGLBSHA256"),
		colisao=m:GetAttribute("PipelineColisao") ~= nil}
end
if ACAO == "AUDITAR" then
	local ativos, antigos, outros = {}, {}, {}
	if pasta then for _, m in ipairs(pasta:GetChildren()) do if m:IsA("Model") then table.insert(ativos, resumir(m)) end end end
	if historico then for _, m in ipairs(historico:GetChildren()) do if m:IsA("Model") then table.insert(antigos, resumir(m)) end end end
	for _, m in ipairs(workspace:GetChildren()) do if m:IsA("Model") then table.insert(outros, resumir(m)) end end
	print(("[biblioteca] %d ativos, %d no histórico, %d outros Models no Workspace"):format(#ativos,#antigos,#outros))
	return HTTP:JSONEncode({ativos=ativos, historico=antigos, outros=outros})
end
assert(ACAO == "ADOTAR" or ACAO == "ARQUIVAR" or ACAO == "RESTAURAR", "Ação desconhecida")
assert(pasta and pasta:IsA("Folder"), "Pasta da biblioteca ausente")
assert(#selecionados > 0, "Selecione os Models no Explorer")
local vistos, antigos = {}, {}
-- Preflight completo antes de mover qualquer instância.
for _, m in ipairs(selecionados) do
	assert(m:IsA("Model"), "Selecione somente Models inteiros")
	local id = identidade(m)
	assert(conhecidos[id], "Model fora do registro: " .. id)
	assert(not vistos[id], "Duas seleções para a mesma criatura: " .. id); vistos[id] = true
	if ACAO == "ARQUIVAR" then
		assert(m.Parent == pasta and m:GetAttribute("PipelineCriaturaId"), "Só arquiva modelos preparados desta biblioteca")
	elseif ACAO == "RESTAURAR" then
		assert(historico and m.Parent == historico, "Selecione uma revisão do histórico desta biblioteca")
		assert(not pasta:FindFirstChild(id), "Já existe um modelo ativo: " .. id)
	else
		assert(m:IsDescendantOf(workspace) and m.Parent ~= pasta, "Selecione a importação candidata fora da pasta ativa")
		local velho
		for _, o in ipairs(pasta:GetChildren()) do if o:IsA("Model") and identidade(o) == id then
			assert(not velho, "Duplicatas ativas: " .. id); velho=o
		end end
		if velho then assert(velho:GetAttribute("PipelineCriaturaId"), "Ativo anterior não gerenciado"); antigos[m] = velho end
	end
end
local CHS = game:GetService("ChangeHistoryService")
-- O executor MCP pode já ter uma gravação externa; nesse caso ele é dono do Undo.
local rec = CHS:TryBeginRecording("Biblioteca: " .. ACAO)
local function arquivar(m)
	if not historico then historico=Instance.new("Folder",storage); historico.Name="HistoricoCriaturasBlockbench" end
	local id = identidade(m)
	m:SetAttribute("PipelineNomeOriginal", id)
	m:SetAttribute("PipelineArquivadoEm", DateTime.now().UnixTimestamp)
	m.Name = id .. "__" .. HTTP:GenerateGUID(false):sub(1,8)
	m.Parent = historico
end
local ok, err = pcall(function()
	for i, m in ipairs(selecionados) do
		if ACAO == "ARQUIVAR" then arquivar(m)
		else
			local id = identidade(m)
			if antigos[m] then arquivar(antigos[m]) end
			m.Name=id; m.Parent=pasta; m:SetAttribute("PipelineCriaturaId", id)
		end
		if i % 100 == 0 then task.wait() end
	end
end)
if rec then CHS:FinishRecording(rec, Enum.FinishRecordingOperation.Commit) end
assert(ok, tostring(err) .. "; Ctrl+Z desfaz o lote")
print(("[biblioteca] %s: %d modelos; Ctrl+Z desfaz. Adoção/restauro requerem receita de preparo."):format(ACAO,#selecionados))
return HTTP:JSONEncode({acao=ACAO,quantidade=#selecionados,precisa_preparo=ACAO~="ARQUIVAR"})
