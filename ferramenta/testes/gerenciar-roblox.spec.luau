-- Fixtures isoladas: substituir o marcador pelo gerenciar-criaturas.luau vigente.
local realGame = game
local workspace = Instance.new("Folder")
local storage = Instance.new("Folder")
local pasta = Instance.new("Folder",workspace); pasta.Name="criaturas modeladas blockbench"
local selecionados = {}
local game = {GetService=function(_,nome)
	if nome=="ServerStorage" then return storage end
	if nome=="Selection" then return {Get=function() return selecionados end} end
	return realGame:GetService(nome)
end}
local function executar(acao)
-- @GERENTE@
end
local function modelo(nome,pai,gerenciado)
	local m=Instance.new("Model",pai);m.Name=nome
	if gerenciado then m:SetAttribute("PipelineCriaturaId",nome) end
	return m
end
local ok,err=pcall(function()
	local a=modelo("Pavao_F1",pasta,true)
	local b=modelo("Pavao_F2",pasta,false)
	local novo=modelo("Pavao_F1",workspace,false)
	local outro=modelo("OutroProjeto",workspace,false)
	selecionados={novo};executar("ADOTAR")
	local hist=storage.HistoricoCriaturasBlockbench
	assert(a.Parent==hist and novo.Parent==pasta,"adoção não preservou anterior")
	selecionados={novo,b};assert(not pcall(executar,"ARQUIVAR"),"aceitou modelo não preparado")
	assert(novo.Parent==pasta and b.Parent==pasta,"preflight moveu lote parcialmente")
	b:SetAttribute("PipelineCriaturaId","Pavao_F2")
	selecionados={novo,b};executar("ARQUIVAR")
	assert(novo.Parent==hist and b.Parent==hist,"arquivo em lote")
	executar("RESTAURAR")
	assert(novo.Name=="Pavao_F1" and b.Name=="Pavao_F2" and novo.Parent==pasta and b.Parent==pasta,"restauro em lote")
	selecionados={a};assert(not pcall(executar,"RESTAURAR"),"sobrescreveu ativo")
	selecionados={outro};assert(not pcall(executar,"ADOTAR"),"aceitou outro projeto")
	assert(outro.Parent==workspace,"alterou outro projeto")
	local report=game:GetService("HttpService"):JSONDecode(executar("AUDITAR"))
	assert(#report.ativos==2 and #report.historico==1 and #report.outros==1,"auditoria inconsistente")
end)
workspace:Destroy();storage:Destroy()
assert(ok,err)
return "OK: adoção, histórico, lote, restauro, duplicatas, preflight e isolamento de outro projeto"
