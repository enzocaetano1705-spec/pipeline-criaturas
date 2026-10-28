local TweenService = game:GetService("TweenService")
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
