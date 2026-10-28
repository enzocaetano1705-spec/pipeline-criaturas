-- Gerado com os fontes locais. Execute em Edit no testesblockbench.rbxl.
assert(not game:GetService("RunService"):IsRunning(),"Pare o Play antes de instalar")
local History=game:GetService("ChangeHistoryService")
-- execute_luau já abre uma gravação no Studio; pela barra de comandos, abrimos a nossa.
local recording
if not History:IsRecordingInProgress() then recording=History:TryBeginRecording("PipelinePetTest","Instalar laboratório de pets");assert(recording,"Não foi possível iniciar histórico de alterações") end
local function owned(parent,name,class)
	local obj=parent:FindFirstChild(name)
	if obj then assert(obj:GetAttribute("PetTestOwned"),"Nome ocupado por conteúdo externo: "..obj:GetFullName());assert(obj:IsA(class),"Tipo incompatível")
	else obj=Instance.new(class);obj.Name=name;obj:SetAttribute("PetTestOwned",true);obj.Parent=parent end
	return obj
end
local ok,result=xpcall(function()
	local rs=owned(game:GetService("ReplicatedStorage"),"PipelinePetTest","Folder")
	local ss=owned(game:GetService("ServerScriptService"),"PipelinePetTest","Folder")
	local world=owned(workspace,"PipelinePetTest","Folder");owned(world,"Pets","Folder")
	local templates=owned(game:GetService("ServerStorage"),"PipelinePetTestTemplates","Folder")
	local animations=owned(rs,"Animations","Folder")
	owned(rs,"Command","RemoteEvent");owned(rs,"Feed","RemoteEvent")
	local function source(parent,name,class,code)
		local obj=owned(parent,name,class);obj.Source=code;return obj
	end
	local savedScales={}
	local previous=rs:FindFirstChild("Config")
	if previous then
		assert(previous:GetAttribute("PetTestOwned"),"Config existente não pertence ao teste")
		local temp=previous:Clone();local loaded,old=pcall(require,temp);temp:Destroy()
		assert(loaded,"Config existente inválida; corrigir antes de reinstalar")
		for id,form in old.Forms do if form.Scale~=nil then savedScales[id]=form.Scale end end
	end
	local config=source(rs,"Config","ModuleScript",-- SOURCE:Config
	)
	-- Preserva escalas editadas no Studio ao atualizar scripts/templates.
	for id,value in savedScales do
		assert(typeof(value)=="number" and value>0 and value<math.huge,"Scale inválido: "..id)
		local pattern="(config%.Forms%."..id.."%.Scale%s*=%s*)[^%s;]+"
		config.Source=string.gsub(config.Source,pattern,function(prefix) return prefix..string.format("%.17g",value) end)
	end
	local rigScale=source(rs,"RigScale","ModuleScript",-- SOURCE:RigScale
	)
	local scaleModule=require(rigScale:Clone())
	source(rs,"AnimationDriver","ModuleScript",-- SOURCE:AnimationDriver
	)
	source(ss,"Dummies","ModuleScript",-- SOURCE:Dummies
	)
	source(ss,"Server","Script",-- SOURCE:Server
	)
	source(game:GetService("StarterPlayer").StarterPlayerScripts,"PipelinePetClient","LocalScript",-- SOURCE:Client
	)
	local cfg=require(config:Clone())
	local gallery=workspace:FindFirstChild("criaturas modeladas blockbench")
	assert(gallery,"Pasta das criaturas não encontrada")
	local status={}
	for id,form in cfg.Forms do
		local sourceModel=gallery:FindFirstChild(form.Name)
		local seq=sourceModel and sourceModel:FindFirstChild("Animacoes")
		local ready=sourceModel and sourceModel:GetAttribute("PipelineFonteSHA256")==form.SourceHash and sourceModel:FindFirstChild("Hitbox") and seq
		if ready then for name in form.Animations do if not seq:FindFirstChild(name) then ready=false;break end end end
		if ready then
			local list=owned(animations,id,"Folder")
			for _,child in list:GetChildren() do child:Destroy() end
			for _,clip in seq:GetChildren() do
				if clip:IsA("KeyframeSequence") and form.Animations[clip.Name] then clip:Clone().Parent=list;task.wait() end
			end
			-- Clonar apenas o rig. Clipes compartilhados não se multiplicam a cada troca de pet.
			local flags={}
			for _,child in sourceModel:GetChildren() do if child.Name=="Animacoes" or child.Name=="AnimSaves" or child.Name=="InitialPoses" then flags[child]=child.Archivable;child.Archivable=false end end
			local cloned,copy=pcall(function() return sourceModel:Clone() end)
			for child,value in flags do child.Archivable=value end
			assert(cloned,copy)
			for _,item in copy:GetDescendants() do
				if item:IsA("BaseScript") then item.Enabled=false end
				if item:IsA("BasePart") then item.CanTouch=false end
			end
			copy:SetAttribute("PetBaseScale",copy:GetScale());scaleModule.Apply(copy,1);copy:SetAttribute("PetTestOwned",true)
			copy.Hitbox.Anchored=true
			local old=templates:FindFirstChild(form.Name);if old then assert(old:GetAttribute("PetTestOwned"));old:Destroy() end
			copy.Parent=templates;task.wait();status[id]="pronto ("..#list:GetChildren().." clipes)"
		else status[id]="aguardando importação atualizada" end
	end
	-- Também visíveis no modo de edição, sem precisar apertar Play.
	require(ss.Dummies:Clone()).new(world,cfg)
	return status
end,debug.traceback)
if recording then History:FinishRecording(recording,ok and Enum.FinishRecordingOperation.Commit or Enum.FinishRecordingOperation.Cancel) end
assert(ok,result)
return result
