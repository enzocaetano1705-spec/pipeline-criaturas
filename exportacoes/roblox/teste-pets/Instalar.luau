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
	local config=source(rs,"Config","ModuleScript",[========[-- Gerado por scripts/gerar-teste-pets.py
return game:GetService("HttpService"):JSONDecode([====[{"Version":1,"WalkSpeed":16,"RunSpeed":28,"FollowOffset":[-7,0,11],"Acceleration":38,"Deceleration":55,"DummyRespawn":3,"SkillCooldown":3,"SkillRadius":17,"Forms":{"F1":{"Id":"F1","Name":"Pavao_F1","Animations":{"idle":{"Length":2.4,"Loop":true},"walk":{"Length":1.33,"Loop":true}},"WalkUnits":13.333333,"RunUnits":37.414966,"CombatWalkUnits":11.111111,"CombatRunUnits":28.882576,"Range":2.8,"SourceHash":"9604fa4c679be7e52ea95941735099613ecc0fe54eadfd33f1df95125c0185eb"},"F2":{"Id":"F2","Name":"Pavao_F2","Animations":{"idle":{"Length":2.4,"Loop":true},"walk":{"Length":1.2,"Loop":true},"attack_stomp":{"Length":1.25,"Loop":false},"attack_spin":{"Length":1.65,"Loop":false},"attack_tail_kick":{"Length":2.15,"Loop":false},"walk_blend":{"Length":1.2,"Loop":true},"idle_blend":{"Length":2.4,"Loop":true},"run":{"Length":0.72,"Loop":true},"run_start":{"Length":0.54,"Loop":false},"run_stop":{"Length":0.6,"Loop":false}},"WalkUnits":11.111111,"RunUnits":44.444444,"CombatWalkUnits":11.111111,"CombatRunUnits":28.882576,"Range":6.5,"SourceHash":"a387d4f84d3913d1f717b1c2cda92f17d794157331ad65f57448e8de29eacd0a","Phases":{"run_start":0.432,"run_stop":0.8}},"F3":{"Id":"F3","Name":"Pavao_F3","Animations":{"idle":{"Length":3.2,"Loop":true},"walk":{"Length":1.5,"Loop":true},"combat_walk":{"Length":1.8,"Loop":true},"combat_ready":{"Length":2.4,"Loop":true},"combat_enter":{"Length":1.65,"Loop":false},"combat_enter_walk":{"Length":1.65,"Loop":false},"combat_walk_start":{"Length":0.6,"Loop":false},"combat_walk_stop":{"Length":0.6,"Loop":false},"combat_idle_resume":{"Length":1.1,"Loop":false},"combat_exit":{"Length":1.8,"Loop":false},"combat_enter_upper":{"Length":1.65,"Loop":false},"combat_exit_upper":{"Length":1.8,"Loop":false},"combat_idle":{"Length":7.1499999999999995,"Loop":false},"run":{"Length":0.84,"Loop":true},"run_start":{"Length":0.6,"Loop":false},"run_stop":{"Length":0.66,"Loop":false},"combat_run":{"Length":0.96,"Loop":true},"combat_run_start":{"Length":0.66,"Loop":false},"combat_run_stop":{"Length":0.72,"Loop":false},"attack_low":{"Length":1.42,"Loop":false},"attack_combo":{"Length":2.2,"Loop":false},"attack_left":{"Length":1.32,"Loop":false}},"WalkUnits":13.333333,"RunUnits":37.414966,"CombatWalkUnits":11.111111,"CombatRunUnits":28.882576,"Range":9.5,"SourceHash":"aa1d03d8bd586bb1efc8e9de121aca1e804b57ea64f03b95be960347c5bf45d1","UpperBones":["tail_1","tail_2","tail_fan_01","tail_fan_02","tail_fan_03","tail_fan_04","tail_fan_05","tail_fan_06","waist","torso","arm_left","arm_right","back_feathers_left","back_feathers_left3","back_feathers_right","back_feathers_right2","forearm_left","forearm_right","hand_left","feather_sword_left","hand_right","feather_sword_right","neck_1","neck_2","head","feather_left_1","feather_left_2","feather_right_1","feather_right_2","wing_left","wing_right"],"Phases":{"run_start":0.46799999999999997,"run_stop":0.9192857142857143,"combat_run_start":0.506,"combat_run_stop":1.0350000000000001,"combat_walk_start":0.3}}},"Dummies":{"Small":{"Name":"AlvoPequeno","Label":"Alvo pequeno","Size":[3,3,3],"HP":250,"X":-7,"Z":-32},"Large":{"Name":"AlvoGrande","Label":"Alvo médio / grande","Size":[10,10,10],"HP":1200,"X":9,"Z":-32}},"Attacks":{"F1":{"Duration":0.7,"Hits":[{"Time":0.3,"Damage":6}]},"attack_stomp":{"Duration":1.25,"Hits":[{"Time":0.575,"Damage":14}]},"attack_tail_kick":{"Duration":2.15,"Hits":[{"Time":0.762857,"Damage":24}]},"attack_spin":{"Duration":1.65,"Area":true,"Hits":[{"Time":0.64,"Damage":22}]},"attack_low":{"Duration":1.42,"Hits":[{"Time":0.54,"Damage":22}]},"attack_left":{"Duration":1.32,"Hits":[{"Time":0.42538078,"Damage":28}]},"attack_combo":{"Duration":2.2,"Hits":[{"Time":0.49,"Damage":22},{"Time":1.19,"Damage":44}]}}}]====])
]========]
	)
	source(rs,"AnimationDriver","ModuleScript",[========[-- IDs temporários são registrados no cliente que os reproduz (teste no Studio).
local RunService=game:GetService("RunService")
local Provider=game:GetService("KeyframeSequenceProvider")
local Driver={};Driver.__index=Driver
local Registered={}

function Driver.new(model, form, config)
	local self=setmetatable({Model=model,Form=form,Config=config,Tracks={},Ids={},Connections={},Current=nil,Transition=nil,Action=nil,Token=0,LastMotion=nil,LastCombat=false,LastSerial=-1},Driver)
	self.Animator=model:WaitForChild("AnimationController"):WaitForChild("Animator")
	self.Sequences=game:GetService("ReplicatedStorage"):WaitForChild("PipelinePetTest"):WaitForChild("Animations"):WaitForChild(form.Id)
	local collision=model:FindFirstChild("ColisaoOssos");if collision then require(collision).Iniciar(model) end
	table.insert(self.Connections,RunService.Heartbeat:Connect(function(dt) self:Step(dt) end))
	table.insert(self.Connections,model.Destroying:Connect(function() self:Destroy() end))
	task.spawn(function()
		local names={"idle","walk","idle_blend","walk_blend","run","combat_ready","combat_walk","combat_run","combat_enter_upper","combat_exit_upper","attack_stomp","attack_tail_kick","attack_spin","attack_low","attack_left","attack_combo"}
		for _,name in names do
			if self.Destroyed then break end
			if self.Form.Animations[name] then self:Load(name,string.sub(name,1,7)=="attack_" and "action" or (string.sub(name,-6)=="_upper" and "upper" or "base")) end
			task.wait()
		end
	end)
	return self
end

function Driver:Load(name, role)
	local key=role..":"..name;if self.Tracks[key] then return self.Tracks[key] end
	local sequence=self.Sequences:FindFirstChild(name);if not sequence then return nil end
	local cacheKey=self.Form.SourceHash..":"..name
	if Registered[cacheKey] then self.Ids[name]=Registered[cacheKey] end
	if not self.Ids[name] then
		if role=="upper" then
			sequence=sequence:Clone()
			local allowed={};for _,bone in self.Form.UpperBones do allowed[bone]=true end
			-- Pais estruturais existem para resolver a hierarquia, sem sobrepor as pernas.
			for _,pose in sequence:GetDescendants() do if pose:IsA("Pose") and not allowed[pose.Name] then pose.Weight=0 end end
			self.Ids[name]=Provider:RegisterKeyframeSequence(sequence);sequence:Destroy()
		else self.Ids[name]=Provider:RegisterKeyframeSequence(sequence) end
		Registered[cacheKey]=self.Ids[name]
	end
	local animation=Instance.new("Animation");animation.Name=name;animation.AnimationId=self.Ids[name]
	local ok,track=pcall(function() return self.Animator:LoadAnimation(animation) end);animation:Destroy()
	if not ok then warn("PetTest: animação "..name..": "..tostring(track));return nil end
	track.Priority=role=="action" and Enum.AnimationPriority.Action4 or (role=="upper" and Enum.AnimationPriority.Action2 or Enum.AnimationPriority.Movement)
	self.Tracks[key]=track;return track
end

function Driver:BaseName(motion, combat)
	if combat and self.Form.Id=="F3" then return ({Idle="combat_ready",Walk="combat_walk",Run="combat_run"})[motion] end
	if self.Form.Id=="F2" then return ({Idle="idle_blend",Walk="walk_blend",Run="run"})[motion] end
	return ({Idle="idle",Walk="walk",Run=self.Form.Id=="F1" and "walk" or "run"})[motion]
end

function Driver:Loop(name, phase)
	local nextTrack=self:Load(name,"base");if not nextTrack then return end
	if self.Current and self.Current~=nextTrack then self.Current:Stop(.16) end
	if self.Transition then self.Transition:Stop(.12);self.Transition=nil end
	if not nextTrack.IsPlaying then nextTrack.Looped=true;nextTrack:Play(.16);if phase and nextTrack.Length>0 then nextTrack.TimePosition=phase%nextTrack.Length end end
	self.Current=nextTrack;self.CurrentName=name
end

function Driver:Motion(motion, combat)
	local name=self:BaseName(motion,combat)
	self.Token+=1;local token=self.Token
	local prefix=combat and self.Form.Id=="F3" and "combat_" or ""
	local transition
	if motion=="Run" and self.LastMotion~="Run" then transition=prefix.."run_start"
	elseif self.LastMotion=="Run" and motion~="Run" then transition=prefix.."run_stop"
	elseif combat and self.Form.Id=="F3" and motion=="Walk" and self.LastMotion=="Idle" then transition="combat_walk_start"
	elseif combat and self.Form.Id=="F3" and motion=="Idle" and self.LastMotion=="Walk" then transition="combat_walk_stop" end
	self.LastMotion=motion
	local track=transition and self:Load(transition,"transition")
	local actionName=self.Model:GetAttribute("ActionClip")
	if track and (not actionName or actionName=="") then
		if self.Current then self.Current:Stop(.13) end
		if self.Transition then self.Transition:Stop(.12) end
		track.Looped=false;track:Play(.13);track.TimePosition=0;track:AdjustSpeed(1);self.Transition=track
		local duration=self.Form.Animations[transition].Length
		task.delay(duration,function()
			if token~=self.Token or not self.Model.Parent then return end
			local phase=self.Form.Phases and self.Form.Phases[transition] or 0
			self:Loop(name,phase)
		end)
	else self:Loop(name) end
end

function Driver:Upper(combat)
	if self.Form.Id~="F3" then return end
	self.UpperToken=(self.UpperToken or 0)+1;local token=self.UpperToken
	if self.UpperTrack then self.UpperTrack:Stop(.18) end
	local name=combat and "combat_enter_upper" or "combat_exit_upper";local track=self:Load(name,"upper")
	if track then
		track.Looped=false;track:Play(.18);track.TimePosition=0;self.UpperTrack=track
		task.delay(self.Form.Animations[name].Length,function() if not self.Destroyed and token==self.UpperToken then track:Stop(.15) end end)
	end
end

function Driver:ActionChanged(serial)
	if self.Action then self.Action:Stop(.13);self.Action=nil end
	local name=self.Model:GetAttribute("ActionClip")
	if not name or name=="" then return end
	local track=self:Load(name,"action");if not track then return end
	local start=self.Model:GetAttribute("ActionStart") or workspace:GetServerTimeNow()
	track.Looped=false;track:Play(.10);track.TimePosition=math.clamp(workspace:GetServerTimeNow()-start,0,math.max(.001,self.Form.Animations[name].Length-.001))
	track:AdjustSpeed(1);self.Action=track
end

function Driver:Step(dt)
	if not self.Model.Parent then return end
	local motion=self.Model:GetAttribute("Motion") or "Idle";local combat=self.Model:GetAttribute("Combat")==true
	if combat~=self.LastCombat then self:Upper(combat);self.LastCombat=combat;self.LastMotion=nil end
	if motion~=self.LastMotion then self:Motion(motion,combat) end
	local serial=self.Model:GetAttribute("ActionSerial") or 0
	if serial~=self.LastSerial then self:ActionChanged(serial);self.LastSerial=serial end
	if self.Current and self.Current.IsPlaying and motion~="Idle" then
		local units=(motion=="Run" and (combat and self.Form.CombatRunUnits or self.Form.RunUnits) or (combat and self.Form.CombatWalkUnits or self.Form.WalkUnits))
		local reference=units*self.Model:GetScale()/16
		self.Current:AdjustSpeed(math.clamp((self.Model:GetAttribute("Speed") or 0)/math.max(.1,reference),.5,3))
	end
end

function Driver:Destroy()
	if self.Destroyed then return end;self.Destroyed=true;self.Token+=1
	for _,connection in self.Connections do connection:Disconnect() end
	for _,track in self.Tracks do track:Stop(0);track:Destroy() end
end

return Driver
]========]
	)
	source(ss,"Dummies","ModuleScript",[========[local TweenService = game:GetService("TweenService")
local Dummies = {}
Dummies.__index = Dummies
local RED = Color3.fromRGB(214, 49, 57)

local function label(parent, name, pos, size, text)
	local x=Instance.new("TextLabel");x.Name=name;x.Position=pos;x.Size=size;x.BackgroundTransparency=1
	x.Text=text;x.TextColor3=Color3.new(1,1,1);x.Font=Enum.Font.GothamBold;x.TextSize=14;x.Parent=parent;return x
end

function Dummies.new(world, config, feedback)
	local self=setmetatable({Items={},Feedback=feedback,Config=config},Dummies)
	local folder=world:FindFirstChild("Dummies") or Instance.new("Folder");folder.Name="Dummies";folder.Parent=world
	local spawn=workspace:FindFirstChildWhichIsA("SpawnLocation");local origin=spawn and spawn.Position or Vector3.new(0,3,0)
	for id,spec in config.Dummies do
		local model=folder:FindFirstChild(spec.Name)
		if model then assert(model:GetAttribute("PetTestOwned"),"Alvo existente não pertence ao teste") else
			model=Instance.new("Model");model.Name=spec.Name;model:SetAttribute("PetTestOwned",true)
			local part=Instance.new("Part");part.Name="Cubo";part.Size=Vector3.new(table.unpack(spec.Size));part.Anchored=true
			part.Material=Enum.Material.SmoothPlastic;part.Color=RED;part.TopSurface=Enum.SurfaceType.Smooth;part.BottomSurface=Enum.SurfaceType.Smooth
			local x,z=origin.X+spec.X,origin.Z+spec.Z
			local params=RaycastParams.new();params.FilterType=Enum.RaycastFilterType.Exclude;params.FilterDescendantsInstances={world,workspace:FindFirstChild("criaturas modeladas blockbench")}
			local hit=workspace:Raycast(Vector3.new(x,500,z),Vector3.new(0,-1000,0),params)
			part.CFrame=CFrame.new(x,(hit and hit.Position.Y or 0)+part.Size.Y/2,z);part.Parent=model;model.PrimaryPart=part
			local gui=Instance.new("BillboardGui");gui.Name="Vida";gui.Size=UDim2.fromOffset(170,52);gui.StudsOffsetWorldSpace=Vector3.new(0,part.Size.Y/2+2,0)
			gui.Adornee=part;gui.AlwaysOnTop=true;gui.MaxDistance=250;gui.Parent=part
			label(gui,"Nome",UDim2.fromScale(0,0),UDim2.new(1,0,0,21),spec.Label)
			local bar=Instance.new("Frame");bar.Name="Barra";bar.Position=UDim2.fromOffset(0,24);bar.Size=UDim2.new(1,0,0,20);bar.BackgroundColor3=Color3.fromRGB(36,23,28);bar.BorderSizePixel=0;bar.Parent=gui
			local fill=Instance.new("Frame");fill.Name="HP";fill.Size=UDim2.fromScale(1,1);fill.BackgroundColor3=Color3.fromRGB(74,211,125);fill.BorderSizePixel=0;fill.Parent=bar
			label(bar,"Valor",UDim2.fromScale(0,0),UDim2.fromScale(1,1),"")
			model.Parent=folder
		end
		model:SetAttribute("PetDummyId",id);model:SetAttribute("MaxHP",spec.HP)
		self.Items[id]={Model=model,Core=model.PrimaryPart,Spec=spec,Token=0}
		self:Reset(id)
	end
	return self
end

function Dummies:Update(id)
	local e=self.Items[id];local hp=e.Model:GetAttribute("HP");local bar=e.Core.Vida.Barra
	bar.HP.Size=UDim2.fromScale(hp/e.Spec.HP,1);bar.Valor.Text=string.format("%d / %d",math.ceil(hp),e.Spec.HP)
end

function Dummies:Reset(id)
	local e=self.Items[id];e.Token+=1;e.Model:SetAttribute("HP",e.Spec.HP);e.Model:SetAttribute("Alive",true)
	e.Core.Transparency=0;e.Core.CanCollide=true;e.Core.Color=RED;self:Update(id)
end

function Dummies:ResetAll() for id in self.Items do self:Reset(id) end end
function Dummies:Get(id) return self.Items[id] end
function Dummies:Alive(id) local e=self.Items[id];return e and e.Model:GetAttribute("Alive")==true end

function Dummies:Distance(id, position)
	local e=self.Items[id];if not e then return math.huge end
	local p=e.Core.CFrame:PointToObjectSpace(position);local h=e.Core.Size/2
	return Vector2.new(math.max(math.abs(p.X)-h.X,0),math.max(math.abs(p.Z)-h.Z,0)).Magnitude
end

function Dummies:Damage(id, amount, player)
	local e=self.Items[id];if not self:Alive(id) or amount<=0 then return false end
	local old=e.Model:GetAttribute("HP");local actual=math.min(old,amount);local hp=math.max(0,old-amount)
	e.Model:SetAttribute("HP",hp);self:Update(id)
	e.Core.Color=Color3.fromRGB(255,224,140);TweenService:Create(e.Core,TweenInfo.new(.16),{Color=RED}):Play()
	if self.Feedback then self.Feedback({Kind="Damage",Target=id,Amount=actual,Position=e.Core.Position+Vector3.new(0,e.Core.Size.Y/2+1,0),Owner=player.UserId}) end
	if hp==0 then
		e.Model:SetAttribute("Alive",false);e.Core.CanCollide=false;e.Core.Transparency=.55;e.Token+=1
		local token=e.Token
		task.delay(self.Config.DummyRespawn,function() if e.Model.Parent and token==e.Token then self:Reset(id) end end)
		return true
	end
	return false
end

return Dummies
]========]
	)
	source(ss,"Server","Script",[========[-- Laboratório local: estado e dano autoritativos, sem persistência/economia de jogo.
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local ServerStorage=game:GetService("ServerStorage")
local RunService=game:GetService("RunService")
local kit=ReplicatedStorage:WaitForChild("PipelinePetTest")
local Config=require(kit.Config)
local Command,Feed=kit.Command,kit.Feed
local world=workspace:WaitForChild("PipelinePetTest")
local pets=world:WaitForChild("Pets")
local templates=ServerStorage:WaitForChild("PipelinePetTestTemplates")
local targets=require(script.Parent.Dummies).new(world,Config,function(data) Feed:FireAllClients(data) end)
local states={}
local MODES={Auto=true,Low=true,Left=true,Combo=true}
local function flat(v) return Vector3.new(v.X,0,v.Z) end
local function now() return workspace:GetServerTimeNow() end
local function approach(v,target,step) if v<target then return math.min(v+step,target) end;return math.max(v-step,target) end

local function ground(p)
	local exclude={world};local gallery=workspace:FindFirstChild("criaturas modeladas blockbench");if gallery then table.insert(exclude,gallery) end
	for _,p1 in Players:GetPlayers() do if p1.Character then table.insert(exclude,p1.Character) end end
	local params=RaycastParams.new();params.FilterType=Enum.RaycastFilterType.Exclude;params.FilterDescendantsInstances=exclude
	local hit=workspace:Raycast(Vector3.new(p.X,p.Y+80,p.Z),Vector3.new(0,-240,0),params)
	return Vector3.new(p.X,hit and hit.Position.Y or p.Y,p.Z)
end

local function send(player,s,message)
	local available={};for id,form in Config.Forms do available[id]=templates:FindFirstChild(form.Name)~=nil end
	Feed:FireClient(player,{Kind="State",Form=s.Form,Level=s.Level,XP=s.XP,NextXP=s.Level*100,Target=s.Target or "",Sprint=s.Sprint,
		CooldownUntil=s.CooldownUntil,SkillQueued=s.SkillQueued,AttackMode=s.Mode,Available=available,Message=message or ""})
end

local function action(s,name)
	s.Model:SetAttribute("ActionClip",name)
	s.Model:SetAttribute("ActionStart",now());s.Serial+=1;s.Model:SetAttribute("ActionSerial",s.Serial)
end
local function clearAction(s)
	s.Attack=nil
	if s.Model then action(s,nil) end
end
local function combat(s,value)
	if s.Combat==value then return end;s.Combat=value
	if s.Model then s.Model:SetAttribute("Combat",value) end
	if s.Form=="F3" then s.ReadyAt=now()+(value and 1.65 or 1.8) else s.ReadyAt=now() end
end

local function spawnPet(player,s,id)
	local form=Config.Forms[id];local template=form and templates:FindFirstChild(form.Name)
	if not template then send(player,s,"Essa forma ainda precisa da importação atualizada.");return end
	local root=player.Character and player.Character:FindFirstChild("HumanoidRootPart");if not root then return end
	local clone=template:Clone();clone.Name="Pet_"..player.UserId
	if s.Model then s.Model:Destroy() end
	s.Form=id;s.Model=clone;s.Attack=nil;s.Target=nil;s.Combat=false;s.Speed=0;s.Serial=0;s.SkillQueued=false;s.ReadyAt=0;s.ComboIndex=0
	clone:SetAttribute("OwnerUserId",player.UserId);clone:SetAttribute("FormId",id);clone:SetAttribute("Level",s.Level)
	clone:SetAttribute("Motion","Idle");clone:SetAttribute("Combat",false);clone:SetAttribute("ActionSerial",0);clone:SetAttribute("Speed",0)
	s.Offset=clone:GetAttribute("PetAnchorToPivot");assert(typeof(s.Offset)=="CFrame","Template sem referencial")
	local offset=Vector3.new(table.unpack(Config.FollowOffset));local p=ground(root.CFrame:PointToWorldSpace(offset))
	s.Anchor=CFrame.lookAt(p,p+flat(root.CFrame.LookVector));s.Model:PivotTo(s.Anchor*s.Offset);s.Model.Parent=pets
	s.Model:SetAttribute("Status","Seguindo");send(player,s)
end

local function xp(player,s,amount)
	s.XP+=amount
	while s.Level<100 and s.XP>=s.Level*100 do s.XP-=s.Level*100;s.Level+=1 end
	if s.Model then s.Model:SetAttribute("Level",s.Level) end
	send(player,s)
end
local function damage(player,s,id,amount)
	if targets:Damage(id,math.floor(amount*(1+(s.Level-1)*.08)),player) then xp(player,s,id=="Small" and 25 or 50) end
end

local function beginAttack(s,clip)
	local spec=Config.Attacks[clip];if not spec then return end
	s.Attack={Clip=clip,Spec=spec,Started=now(),NextHit=1,Target=s.Target}
	if clip=="attack_spin" then s.CooldownUntil=now()+Config.SkillCooldown;s.SkillQueued=false end
	local animationClip;if clip~="F1" then animationClip=clip end
	action(s,animationClip);s.Model:SetAttribute("Status",clip=="F1" and "Ataque provisório F1" or clip)
end

local function updateAttack(player,s,t)
	local a=s.Attack;if not a then return end
	local elapsed=t-a.Started
	while a.NextHit<=#a.Spec.Hits and elapsed>=a.Spec.Hits[a.NextHit].Time do
		local hit=a.Spec.Hits[a.NextHit];a.NextHit+=1
		if a.Spec.Area then
			for id in targets.Items do if targets:Distance(id,s.Anchor.Position)<=Config.SkillRadius then damage(player,s,id,hit.Damage) end end
		elseif s.Target==a.Target and targets:Alive(a.Target) and targets:Distance(a.Target,s.Anchor.Position)<=Config.Forms[s.Form].Range+2 then
			damage(player,s,a.Target,hit.Damage)
		end
	end
	if elapsed>=a.Spec.Duration then clearAction(s);s.NextAttack=t+.12 end
end

local function update(player,s,dt,t)
	local model=s.Model;if not model or not model.Parent then return end
	local char=player.Character;local root=char and char:FindFirstChild("HumanoidRootPart");local hum=char and char:FindFirstChildOfClass("Humanoid")
	if not root or not hum or hum.Health<=0 then return end
	local form=Config.Forms[s.Form]
	local destination=root.CFrame:PointToWorldSpace(Vector3.new(table.unpack(Config.FollowOffset)))
	local face=flat(root.CFrame.LookVector);local target=s.Target and targets:Get(s.Target)
	local inRange=false
	if target then
		local delta=flat(target.Core.Position-s.Anchor.Position)
		if delta.Magnitude>.01 then face=delta.Unit end
		local radius=math.max(target.Core.Size.X,target.Core.Size.Z)*.5
		-- A tolerância de parada deve ficar inteiramente dentro do alcance do golpe.
		destination=target.Core.Position-face*(radius+form.Range-.8)
		inRange=targets:Distance(s.Target,s.Anchor.Position)<=form.Range+.15
		if inRange then destination=s.Anchor.Position end
	end
	updateAttack(player,s,t)
	if target and not s.Attack and inRange and targets:Alive(s.Target) and t>=s.ReadyAt and t>=(s.NextAttack or 0) then
		local clip
		if s.Form=="F1" then clip="F1"
		elseif s.Form=="F2" then clip=s.SkillQueued and t>=s.CooldownUntil and "attack_spin" or (s.Target=="Small" and "attack_stomp" or "attack_tail_kick")
		else
			if s.Mode=="Auto" then s.ComboIndex=s.ComboIndex%3+1;clip=({"attack_low","attack_left","attack_combo"})[s.ComboIndex]
			else clip=({Low="attack_low",Left="attack_left",Combo="attack_combo"})[s.Mode] end
		end
		beginAttack(s,clip)
	elseif not target and s.SkillQueued and s.Form=="F2" and not s.Attack and t>=s.CooldownUntil then beginAttack(s,"attack_spin") end
	local delta=flat(destination-s.Anchor.Position);local distance=delta.Magnitude
	local movingOwner=hum.MoveDirection.Magnitude>.05
	local maxSpeed=(s.Sprint and movingOwner and Config.RunSpeed or Config.WalkSpeed)+(target and 0 or 3)
	local stopTolerance=target and .2 or .65
	local desired=distance>stopTolerance and math.min(maxSpeed,distance*3) or 0
	if s.Attack then desired=0 end
	s.Speed=approach(s.Speed,desired,dt*(desired<s.Speed and Config.Deceleration or Config.Acceleration))
	local step=math.min(distance,s.Speed*dt);local pos=s.Anchor.Position
	if distance>.01 and step>0 then pos+=delta.Unit*step;if not target then face=delta.Unit end end
	pos=ground(pos)
	local rotation=s.Anchor.Rotation:Lerp(CFrame.lookAt(Vector3.zero,face),1-math.exp(-10*dt))
	s.Anchor=CFrame.new(pos)*rotation
	local lunge=0
	if s.Attack and s.Attack.Clip=="F1" then lunge=.55*math.sin(math.clamp((t-s.Attack.Started)/.7,0,1)*math.pi) end
	model:PivotTo(s.Anchor*CFrame.new(0,0,-lunge)*s.Offset)
	local motion="Idle"
	if distance>28 then s.Catching=true elseif distance<12 then s.Catching=false end
	if s.Speed>.7 then motion=((s.Sprint and movingOwner) or s.Catching) and "Run" or "Walk" end
	model:SetAttribute("Motion",motion);model:SetAttribute("Speed",s.Speed)
	if not s.Attack then model:SetAttribute("Status",target and (inRange and "Em combate" or "Indo ao alvo") or "Seguindo") end
end

local function add(player)
	if states[player] then return end
	local s={Form="F1",Level=1,XP=0,Sprint=false,CooldownUntil=0,Mode="Auto",Serial=0,LastCommand={},SkillQueued=false};states[player]=s
	player.DevEnableMouseLock=false
	local function character(char)
		s.Sprint=false;s.Target=nil;s.SkillQueued=false
		local hum=char:WaitForChild("Humanoid");hum.WalkSpeed=Config.WalkSpeed
		task.wait(.3);if player.Character==char then spawnPet(player,s,s.Form) end
	end
	player.CharacterAdded:Connect(character);if player.Character then task.spawn(character,player.Character) end
end
Players.PlayerAdded:Connect(add);for _,p in Players:GetPlayers() do add(p) end
Players.PlayerRemoving:Connect(function(player) local s=states[player];if s and s.Model then s.Model:Destroy() end;states[player]=nil end)

Command.OnServerEvent:Connect(function(player,verb,value)
	local s=states[player];if not s or typeof(verb)~="string" then return end
	local t=now();if verb~="Sprint" or value~=false then if t-(s.LastCommand[verb] or 0)<.09 then return end end
	s.LastCommand[verb]=t
	if verb=="Sprint" and typeof(value)=="boolean" then
		s.Sprint=value;local hum=player.Character and player.Character:FindFirstChildOfClass("Humanoid");if hum then hum.WalkSpeed=value and Config.RunSpeed or Config.WalkSpeed end
	elseif verb=="SetForm" and typeof(value)=="string" and Config.Forms[value] then spawnPet(player,s,value)
	elseif verb=="SelectTarget" and typeof(value)=="string" and targets:Get(value) and s.Model then
		local root=player.Character and player.Character:FindFirstChild("HumanoidRootPart");if root and (root.Position-targets:Get(value).Core.Position).Magnitude<300 then s.Target=value;combat(s,true) end
	elseif verb=="Recall" then s.Target=nil;s.SkillQueued=false;clearAction(s);combat(s,false)
	elseif verb=="Skill" and s.Form=="F2" and s.Model and t>=s.CooldownUntil then s.SkillQueued=true
	elseif verb=="SetLevel" and typeof(value)=="number" and value==value and math.abs(value)<1000 then s.Level=math.clamp(math.floor(value),1,100);s.XP=0;if s.Model then s.Model:SetAttribute("Level",s.Level) end
	elseif verb=="AttackMode" and typeof(value)=="string" and MODES[value] then s.Mode=value
	elseif verb=="ResetDummies" then targets:ResetAll()
	elseif verb~="Sync" then return end
	send(player,s)
end)

local stateClock=0
RunService.Heartbeat:Connect(function(dt)
	local t=now();dt=math.min(dt,.1)
	for player,s in states do update(player,s,dt,t) end
	stateClock+=dt;if stateClock>.25 then stateClock=0;for player,s in states do send(player,s) end end
end)
print("PipelinePetTest pronto: Shift correr, clique no cubo, Q área F2, R recall.")
]========]
	)
	source(game:GetService("StarterPlayer").StarterPlayerScripts,"PipelinePetClient","LocalScript",[========[local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local CAS=game:GetService("ContextActionService")
local UIS=game:GetService("UserInputService")
local RunService=game:GetService("RunService")
local player=Players.LocalPlayer
local kit=ReplicatedStorage:WaitForChild("PipelinePetTest")
local Config=require(kit:WaitForChild("Config"));local Driver=require(kit:WaitForChild("AnimationDriver"))
local Command=kit:WaitForChild("Command");local Feed=kit:WaitForChild("Feed")
local world=workspace:WaitForChild("PipelinePetTest")
local state={Form="F1",Level=1,CooldownUntil=0,Available={},AttackMode="Auto"}
local drivers={};local keys={};local modeIndex=1;local modes={"Auto","Low","Left","Combo"}
local gui=Instance.new("ScreenGui");gui.Name="PipelinePetHUD";gui.ResetOnSpawn=false;gui.IgnoreGuiInset=true;gui.DisplayOrder=20;gui.ZIndexBehavior=Enum.ZIndexBehavior.Sibling
local panel=Instance.new("Frame");panel.Name="Painel";panel.Size=UDim2.fromOffset(336,300);panel.Position=UDim2.new(0,16,0,60);panel.BackgroundColor3=Color3.fromRGB(22,30,40);panel.BackgroundTransparency=.08;panel.BorderSizePixel=0;panel.Parent=gui
Instance.new("UICorner",panel).CornerRadius=UDim.new(0,10)
local function text(name,value,x,y,w,h,size)
	local t=Instance.new("TextLabel");t.Name=name;t.Text=value;t.Position=UDim2.fromOffset(x,y);t.Size=UDim2.fromOffset(w,h);t.BackgroundTransparency=1;t.TextColor3=Color3.fromRGB(230,238,245);t.Font=Enum.Font.Gotham;t.TextSize=size or 14;t.TextXAlignment=Enum.TextXAlignment.Left;t.TextWrapped=true;t.Parent=panel;return t
end
local function button(name,value,x,y,w,fn)
	local b=Instance.new("TextButton");b.Name=name;b.Text=value;b.Position=UDim2.fromOffset(x,y);b.Size=UDim2.fromOffset(w,32);b.BackgroundColor3=Color3.fromRGB(48,65,82);b.TextColor3=Color3.new(1,1,1);b.BorderSizePixel=0;b.Font=Enum.Font.GothamMedium;b.TextSize=14;b.Parent=panel
	Instance.new("UICorner",b).CornerRadius=UDim.new(0,6);b.Activated:Connect(fn);return b
end
text("Titulo","LABORATÓRIO DE PETS",14,10,310,24,17)
local forms={};for i,id in {"F1","F2","F3"} do forms[id]=button(id,id,14+(i-1)*105,42,99,function() Command:FireServer("SetForm",id) end) end
local level=text("Level","Nível 1 · XP 0 / 100",14,82,230,24)
button("Menos","−",254,78,28,function() Command:FireServer("SetLevel",state.Level-1) end)
button("Mais","+",288,78,32,function() Command:FireServer("SetLevel",state.Level+1) end)
local target=text("Alvo","Alvo: nenhum",14,110,310,24)
local skill=button("Skill","Q · Área F2",14,142,150,function() Command:FireServer("Skill") end)
button("Recall","R · Recall",174,142,146,function() Command:FireServer("Recall") end)
local mode=button("Modo","F3: sequência Low → Left → Combo",14,182,306,function() modeIndex=modeIndex%#modes+1;Command:FireServer("AttackMode",modes[modeIndex]) end)
button("Reset","Restaurar HP",14,222,140,function() Command:FireServer("ResetDummies") end)
local status=text("Status","Conectando…",164,218,156,40,12)
text("Ajuda","Shift: correr · clique no cubo para atacar",14,267,310,21,12)
gui.Parent=player:WaitForChild("PlayerGui")
local uiScale=Instance.new("UIScale",panel)
local highlight=Instance.new("Highlight");highlight.Name="AlvoSelecionado";highlight.FillTransparency=.85;highlight.OutlineColor=Color3.fromRGB(255,223,92);highlight.DepthMode=Enum.HighlightDepthMode.AlwaysOnTop;highlight.Parent=gui
-- Barras projetadas no HUD permanecem legíveis também nas capturas do laboratório.
local health={};local floating={}
for id,spec in Config.Dummies do
	local model=world.Dummies:WaitForChild(spec.Name);local core=model:WaitForChild("Cubo")
	local original=core:WaitForChild("Vida",10);if original then original.Enabled=false end
	local frame=Instance.new("Frame");frame.Name="Vida_"..id;frame.Size=UDim2.fromOffset(170,48);frame.AnchorPoint=Vector2.new(.5,1);frame.BackgroundTransparency=1;frame.Parent=gui
	local title=Instance.new("TextLabel");title.Size=UDim2.new(1,0,0,23);title.Text=spec.Label;title.Font=Enum.Font.GothamBold;title.TextSize=14;title.TextColor3=Color3.new(1,1,1);title.TextStrokeTransparency=.3;title.BackgroundTransparency=1;title.Parent=frame
	local bar=Instance.new("Frame");bar.Position=UDim2.fromOffset(0,25);bar.Size=UDim2.fromOffset(170,20);bar.BackgroundColor3=Color3.fromRGB(35,25,32);bar.BorderSizePixel=0;bar.Parent=frame
	local fill=Instance.new("Frame");fill.Size=UDim2.fromScale(1,1);fill.BackgroundColor3=Color3.fromRGB(74,211,125);fill.BorderSizePixel=0;fill.Parent=bar
	local value=title:Clone();value.Name="HP";value.Size=UDim2.fromScale(1,1);value.TextSize=13;value.Parent=bar
	table.insert(health,{Model=model,Core=core,Frame=frame,Fill=fill,Value=value,MaxHP=spec.HP})
end

local function attach(model)
	if not model:IsA("Model") or drivers[model] then return end
	task.spawn(function()
		local id=model:GetAttribute("FormId");if not Config.Forms[id] then return end
		local ok,result=pcall(Driver.new,model,Config.Forms[id],Config)
		if ok then drivers[model]=result else warn("PetTest driver: "..tostring(result)) end
	end)
end
world.Pets.ChildAdded:Connect(attach);world.Pets.ChildRemoved:Connect(function(model) if drivers[model] then drivers[model]:Destroy();drivers[model]=nil end end)
for _,model in world.Pets:GetChildren() do attach(model) end

local function sprint(_,input,key)
	if UIS:GetFocusedTextBox() then return Enum.ContextActionResult.Pass end
	if input==Enum.UserInputState.Begin then keys[key.KeyCode]=true elseif input==Enum.UserInputState.End or input==Enum.UserInputState.Cancel then keys[key.KeyCode]=nil end
	Command:FireServer("Sprint",next(keys)~=nil);return Enum.ContextActionResult.Sink
end
CAS:BindActionAtPriority("PetTestSprint",sprint,false,3000,Enum.KeyCode.LeftShift,Enum.KeyCode.RightShift)
UIS.WindowFocusReleased:Connect(function() table.clear(keys);Command:FireServer("Sprint",false) end)
CAS:BindActionAtPriority("PetTestRecall",function(_,input) if input==Enum.UserInputState.Begin and not UIS:GetFocusedTextBox() then Command:FireServer("Recall") end;return Enum.ContextActionResult.Sink end,false,3000,Enum.KeyCode.R)
CAS:BindActionAtPriority("PetTestSkill",function(_,input) if input==Enum.UserInputState.Begin and not UIS:GetFocusedTextBox() then Command:FireServer("Skill") end;return Enum.ContextActionResult.Sink end,false,3000,Enum.KeyCode.Q)

local mouse=player:GetMouse()
UIS.InputBegan:Connect(function(input,processed)
	if processed or input.UserInputType~=Enum.UserInputType.MouseButton1 then return end
	local hit=mouse.Target
	while hit and hit~=workspace do
		local id=hit:GetAttribute("PetDummyId");if id then Command:FireServer("SelectTarget",id);break end
		hit=hit.Parent
	end
end)

local function damage(data)
	local label=Instance.new("TextLabel");label.Size=UDim2.fromOffset(110,44);label.AnchorPoint=Vector2.new(.5,1);label.BackgroundTransparency=1;label.Text="−"..data.Amount;label.Font=Enum.Font.GothamBold;label.TextSize=26;label.TextColor3=Color3.fromRGB(255,230,143);label.TextStrokeTransparency=.2;label.ZIndex=4;label.Parent=gui
	table.insert(floating,{Label=label,Position=data.Position+Vector3.new(math.random(-10,10)/10,0,0),Born=os.clock()})
end
Feed.OnClientEvent:Connect(function(data)
	if data.Kind=="Damage" then damage(data);return end
	if data.Kind~="State" then return end;state=data
	level.Text=string.format("Nível %d · XP %d / %d",data.Level,data.XP,data.NextXP)
	target.Text="Alvo: "..(data.Target=="" and "nenhum" or (data.Target=="Small" and "pequeno" or "médio / grande"))
	for id,b in forms do b.Text=id..(data.Available[id] and "" or " · importar");b.BackgroundColor3=id==data.Form and Color3.fromRGB(26,125,125) or Color3.fromRGB(48,65,82) end
	mode.Text=data.AttackMode=="Auto" and "F3: sequência Low → Left → Combo" or "F3: testar "..data.AttackMode
	if data.Message~="" then status:SetAttribute("Auto",false);status.Text=data.Message;task.delay(3,function() if status.Text==data.Message then status.Text="" end end) end
	local selected=data.Target~="" and world.Dummies:FindFirstChild(Config.Dummies[data.Target].Name);highlight.Adornee=selected or nil
end)
RunService.RenderStepped:Connect(function()
	local remaining=math.max(0,(state.CooldownUntil or 0)-workspace:GetServerTimeNow())
	skill.Text=state.Form~="F2" and "Q · Skill somente F2" or (state.SkillQueued and "Q · Área na fila" or (remaining>0 and string.format("Q · Área %.1fs",remaining) or "Q · Área pronta"))
	skill.BackgroundColor3=state.Form=="F2" and Color3.fromRGB(32,111,111) or Color3.fromRGB(48,65,82)
	if status.Text=="" or status.Text=="Conectando…" or status:GetAttribute("Auto") then
		local model=world.Pets:FindFirstChild("Pet_"..player.UserId)
		status.Text=model and ((model:GetAttribute("Status") or "").." · "..(model:GetAttribute("Motion") or "")) or "Aguardando pet";status:SetAttribute("Auto",true)
	end
	local camera=workspace.CurrentCamera
	if camera then
		uiScale.Scale=math.clamp(math.min(camera.ViewportSize.X/1000,camera.ViewportSize.Y/660),.65,1)
		for _,entry in health do
			local point,visible=camera:WorldToViewportPoint(entry.Core.Position+Vector3.new(0,entry.Core.Size.Y/2+2,0))
			entry.Frame.Visible=visible and point.Z<250;entry.Frame.Position=UDim2.fromOffset(point.X,point.Y)
			local hp,max=entry.Model:GetAttribute("HP") or entry.MaxHP,entry.Model:GetAttribute("MaxHP") or entry.MaxHP
			entry.Fill.Size=UDim2.fromScale(hp/max,1);entry.Value.Text=string.format("%d / %d",hp,max)
		end
		for i=#floating,1,-1 do
			local entry=floating[i];local age=os.clock()-entry.Born
			if age>.85 then entry.Label:Destroy();table.remove(floating,i) else
				local point,visible=camera:WorldToViewportPoint(entry.Position+Vector3.new(0,age*4,0));entry.Label.Visible=visible
				entry.Label.Position=UDim2.fromOffset(point.X,point.Y);entry.Label.TextTransparency=math.clamp(age/.85,0,1);entry.Label.TextStrokeTransparency=.2+.8*age/.85
			end
		end
	end
end)
player.CameraMaxZoomDistance=120
local oldMin=player.CameraMinZoomDistance;player.CameraMinZoomDistance=30;task.delay(.8,function() player.CameraMinZoomDistance=oldMin end)
Command:FireServer("Sync")
]========]
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
			local box,size=copy:GetBoundingBox();local body
			for _,item in copy:GetDescendants() do if item:IsA("Bone") and item.Name=="body" then body=item;break end end
			assert(body,"Rig sem body")
			local anchor=CFrame.new(body.WorldPosition.X,box.Position.Y-size.Y/2,body.WorldPosition.Z)*copy.Hitbox.CFrame.Rotation
			copy:SetAttribute("PetAnchorToPivot",anchor:ToObjectSpace(copy:GetPivot()));copy:SetAttribute("PetTestOwned",true)
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
