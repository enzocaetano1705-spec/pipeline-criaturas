-- Ensaio em cópias descartáveis, em Edit; nenhum template/original é redimensionado.
local kit=game.ReplicatedStorage.PipelinePetTest
local Scaling=require(kit.RigScale:Clone())
local results={}
for _,template in game.ServerStorage.PipelinePetTestTemplates:GetChildren() do
	local originalScale=template:GetScale()
	local originalCF,originalSize=template:GetBoundingBox()
	local originalOffset=template:GetAttribute("PetAnchorToPivot")
	local records={}
	for _,factor in {.5,1,1.5} do
		local model=template:Clone()
		local ok,record=xpcall(function()
			local offset=Scaling.Apply(model,factor)
			assert(math.abs(model:GetScale()-originalScale*factor)<.0001,"Escala inesperada")
			local _,size=model:GetBoundingBox()
			assert((size-originalSize*factor).Magnitude<.06,"Dimensões não acompanharam a escala")
			local first=offset.Position
			local second=Scaling.Apply(model,factor)
			assert((first-second.Position).Magnitude<.002,"Reaplicação acumulou escala/offset")
			model:PivotTo(second)
			require(model.ColisaoOssos).Atualizar(model)
			local box,boxSize=model:GetBoundingBox()
			local floorError=box.Position.Y-boxSize.Y/2
			assert(math.abs(floorError)<.06,"Apoio fora do chão: "..floorError)
			local worstSize,worstOffset=0,0
			for _,part in model.ColisoresPipeline:GetChildren() do
				local expectedSize=part:GetAttribute("PipelineTamanho")*(model:GetScale()/16)
				worstSize=math.max(worstSize,(part.Size-expectedSize).Magnitude)
				local offsetCF=part:GetAttribute("PipelineOffset")
				local localCF=CFrame.new(offsetCF.Position*(model:GetScale()/16))*offsetCF.Rotation
				local expected=part.Osso.Value.TransformedWorldCFrame*localCF
				worstOffset=math.max(worstOffset,(part.Position-expected.Position).Magnitude)
			end
			assert(worstSize<.06 and worstOffset<.002,"Colisor não acompanhou o rig")
			local scaleBefore=model:GetScale()
			for _,invalid in {0,-1,math.huge,0/0,"2"} do assert(not pcall(Scaling.Apply,model,invalid),"Scale inválido aceito") end
			assert(model:GetScale()==scaleBefore,"Scale inválido alterou o rig")
			return {factor=factor,scale=model:GetScale(),floorError=floorError,colliderSizeError=worstSize,colliderOffsetError=worstOffset}
		end,debug.traceback)
		model:Destroy();assert(ok,record);table.insert(records,record)
	end
	local currentCF,currentSize=template:GetBoundingBox()
	assert(template:GetScale()==originalScale and (currentCF.Position-originalCF.Position).Magnitude<.001 and (currentSize-originalSize).Magnitude<.001,"Template original alterado")
	assert(template:GetAttribute("PetAnchorToPivot")==originalOffset,"Offset do template alterado")
	results[template.Name]=records
	task.wait()
end
return results
