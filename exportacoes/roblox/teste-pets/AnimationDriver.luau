-- IDs temporários são registrados no cliente que os reproduz (teste no Studio).
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
