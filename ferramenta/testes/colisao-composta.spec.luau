-- Fixture isolada; injetar template de preparo e módulo reais.
local fixture=Instance.new("Folder")
local workspace=fixture
local container=Instance.new("Folder",fixture);container.Name="criaturas modeladas blockbench"
local function preparar()
-- @PREPARO@
end
local m=Instance.new("Model",container);m.Name="Pavao_F2"
local mesh=Instance.new("MeshPart",m);mesh.Name="Raiz";mesh.Size=Vector3.new(6,8,12)
mesh.CFrame=CFrame.new(10,4,0)*CFrame.Angles(0,math.rad(37),0)
local sa=Instance.new("SurfaceAppearance",mesh);sa.ColorMap="rbxassetid://123315715785564"
local body=Instance.new("Bone",mesh);body.Name="body"
local head=Instance.new("Bone",body);head.Name="head";head.CFrame=CFrame.new(0,3,-2)
local perfil={versao=2,tipo="composta_ossos",fonte_sha256="fixture",glb_sha256="fixture",pecas={
	{nome="tronco",osso="body",tamanho={16,32,48},cf={0,8,0,1,0,0,0,1,0,0,0,1}},
	{nome="cabeca",osso="head",tamanho={16,16,16},cf={0,0,0,1,0,0,0,1,0,0,0,1}}
}}
local HTTP=game:GetService("HttpService")
m:SetAttribute("PipelineColisao",HTTP:JSONEncode(perfil))
local ok,err=pcall(function()
	preparar()
	assert(not m.Hitbox.CanCollide and not m.Hitbox.CanQuery,"âncora cria caixa fantasma")
	assert(#m.ColisoresPipeline:GetChildren()==2,"quantidade de colisores")
	local col=m.ColisoresPipeline:FindFirstChild("002_cabeca")
	assert(col.CanCollide and not col.CanTouch and mesh.CanCollide==false,"flags de colisão")
	assert((col.Position-head.WorldPosition).Magnitude<1e-4,"colisor sem orientação/posição do osso")
	local modulo=require(m.ColisaoOssos)
	head.Transform=CFrame.new(.5,1,2)*CFrame.Angles(0,0,.3)
	modulo.Atualizar(m)
	assert((col.Position-head.TransformedWorldCFrame.Position).Magnitude<1e-4,"não acompanha Bone.Transform")
	assert((col.CFrame.LookVector-head.TransformedWorldCFrame.LookVector).Magnitude<1e-4,"giro do osso perdido")
	m:ScaleTo(2);modulo.Atualizar(m)
	assert((col.Size-Vector3.new(2,2,2)).Magnitude<1e-4,"escala aplicada duas vezes")
	head.Transform=CFrame.identity
	preparar()
	assert(#m.ColisoresPipeline:GetChildren()==2,"repetição duplica colisores")
	local antes=m.ColisoresPipeline
	perfil.pecas[2].osso="osso_inexistente"
	m:SetAttribute("PipelineColisao",HTTP:JSONEncode(perfil))
	local valido=pcall(preparar)
	assert(not valido and m.ColisoresPipeline==antes,"preflight alterou colisão válida")
end)
fixture:Destroy()
assert(ok,err)
return "OK: âncora sem colisão, caixas orientadas, Bone.Transform, escala, repetição e preflight"
