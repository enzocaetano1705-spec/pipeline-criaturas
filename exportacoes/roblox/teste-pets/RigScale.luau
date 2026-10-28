-- Scale é um multiplicador do template preparado: 1 mantém o tamanho atual.
local RigScale={}

function RigScale.IsValid(value)
	return typeof(value)=="number" and value>0 and value<math.huge
end

function RigScale.Apply(model,multiplier)
	assert(RigScale.IsValid(multiplier),"Scale precisa ser um número positivo e finito")
	local base=model:GetAttribute("PetBaseScale") or model:GetScale()
	assert(RigScale.IsValid(base),"Escala de referência inválida")
	model:ScaleTo(base*multiplier)
	local body
	for _,item in model:GetDescendants() do if item:IsA("Bone") and item.Name=="body" then body=item;break end end
	assert(body and model:FindFirstChild("Hitbox"),"Rig preparado sem body/Hitbox")
	local box,size=model:GetBoundingBox()
	local anchor=CFrame.new(body.WorldPosition.X,box.Position.Y-size.Y/2,body.WorldPosition.Z)*model.Hitbox.CFrame.Rotation
	local offset=anchor:ToObjectSpace(model:GetPivot())
	model:SetAttribute("PetBaseScale",base)
	model:SetAttribute("PetScaleMultiplier",multiplier)
	model:SetAttribute("PetAnchorToPivot",offset)
	return offset
end

return RigScale
