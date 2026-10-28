local Players=game:GetService("Players")
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
