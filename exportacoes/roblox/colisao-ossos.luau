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
