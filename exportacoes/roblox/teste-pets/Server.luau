-- Laboratório local: estado e dano autoritativos, sem persistência/economia de jogo.
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
