#Noesis Python model import+export test module, imports/exports some data from/to a made-up format

from inc_noesis import *

import noesis
import struct


#rapi methods should only be used during handler callbacks
import rapi

#registerNoesisTypes is called by Noesis to allow the script to register formats.
#Do not implement this function in script files unless you want them to be dedicated format modules!
def registerNoesisTypes():
	handle = noesis.register("Koudelka Model .SDR", ".SDR")
	noesis.setHandlerTypeCheck(handle, koudelkaModelHeaderCheck)
	noesis.setHandlerLoadModel(handle, koudelkaReadModel)

	handle = noesis.register("Koudelka Model Package .SDP", ".SDP")
	noesis.setHandlerTypeCheck(handle, koudelkaSDPHeaderCheck)
	noesis.setHandlerLoadModel(handle, koudelkaReadSDP)

	handle = noesis.register("Koudelka Battle Arenas .BDT", ".BDT")
	noesis.setHandlerTypeCheck(handle, koudelkaBDTHeaderCheck)
	noesis.setHandlerLoadRGBA(handle, koudelkaReadBDT)

	handle = noesis.register("Koudelka Environment Textures .MDT", ".MDT")
	noesis.setHandlerTypeCheck(handle, koudelkaMDTHeaderCheck)
	noesis.setHandlerLoadRGBA(handle, koudelkaReadMDT)

	handle = noesis.register("Koudelka Textures .TEX", ".TEX")
	noesis.setHandlerTypeCheck(handle, koudelkaTEXHeaderCheck)
	noesis.setHandlerLoadRGBA(handle, koudelkaReadTEX)
	
	handle = noesis.register("Koudelka Greyscale Textures .TX4", ".TX4")
	noesis.setHandlerTypeCheck(handle, koudelkaTX4HeaderCheck)
	noesis.setHandlerLoadRGBA(handle, koudelkaReadTX4)
	
	handle = noesis.register("Koudelka Font .FT4", ".FT4")
	noesis.setHandlerTypeCheck(handle, koudelkaFT4HeaderCheck)
	noesis.setHandlerLoadRGBA(handle, koudelkaReadFT4)

	handle = noesis.register("Koudelka Textures .TX8", ".TX8;.KD8")
	noesis.setHandlerTypeCheck(handle, koudelkaTX8HeaderCheck)
	noesis.setHandlerLoadRGBA(handle, koudelkaReadTX8)

	handle = noesis.register("Koudelka Monster Archive BIM.AR", ".AR")
	noesis.setHandlerTypeCheck(handle, koudelkaARCheck)
	noesis.setHandlerExtractArc(handle, extractAR)
	#noesis.setHandlerLoadModel(handle, koudelkaReadAR)

	handle = noesis.register("Koudelka Effects .PMF", ".PMF")
	noesis.setHandlerTypeCheck(handle, koudelkaPMFHeaderCheck)
	noesis.setHandlerLoadRGBA(handle, koudelkaReadPMF)

	#noesis.logPopup()
	#print("The log can be useful for catching debug prints from preview loads.\nBut don't leave it on when you release your script, or it will probably annoy people.")
	return 1

KOUDELKA_MODEL_HEADER = b"0112"
KOUDELKA_SDP_HEADER = b"SDR_PACK"
KOUDELKA_BDT_HEADER = b"bdt0"
KOUDELKA_MDT_HEADER = b"mdt0"
KOUDELKA_TEX_HEADER = 0xFFFFFFFF
KOUDELKA_TX4_HEADER = b"TX4"
KOUDELKA_FT4_HEADER = b"FT40"
KOUDELKA_TX8_HEADER = b"TX8"
KOUDELKA_PMF_HEADER = b"0117"

def koudelkaSDPHeaderCheck(data):
	if len(data) < 8:
		return 0
	bs = NoeBitStream(data)
	header = bs.read("8s")[0]
	if header != KOUDELKA_SDP_HEADER:
		return 0
	return 1
def koudelkaReadSDP(data, mdlList):
	bs = NoeBitStream(data)
	header = bs.read("8s")[0]
	nums = bs.read("2HI")
	print(repr(nums))
	numModels = nums[2]

	for i in range(0, numModels):
		n = bs.read("2H")

	for i in range(0, numModels):
		header = bs.read("4s")[0]
		if header == KOUDELKA_MODEL_HEADER:
			mdl = SDRParser(bs)
			mdlList.append(mdl)

	return 1

def koudelkaModelHeaderCheck(data):
	if len(data) < 8:
		return 0
	bs = NoeBitStream(data)
	header = bs.read("4s")[0]
	if header != KOUDELKA_MODEL_HEADER:
		return 0
	return 1
def SDRParser(bs):
	numBones = bs.read('H')[0]
	#print("numBones ? : "+str(numBones))
	numMesh = bs.read('H')[0]
	#print("numMesh ? : "+str(numMesh))
	footerPtr = bs.getOffset()+bs.read('I')[0]+4 # maybe somthing interesting in the footer
	#print("footerPtr : "+str(footerPtr))

	# Texture section
	num2 = bs.read('H')[0] # 1 number of pallets ?
	#print("num2 : "+str(num2))
	texW = bs.read('H')[0] # tex width
	#print("texW : "+str(texW))
	texH = bs.read('H')[0] # tex height
	#print("texH : "+str(texH))
	num5 = bs.read('B')[0] # 1
	#print("num5 : "+str(num5))
	num6 = bs.read('B')[0] # 8
	#print("num6 : "+str(num6))
	pad = bs.read('B')[0] # 0 padding
	#print("pad : "+str(pad))
	unkn = bs.read('3B') # ?
	#print("unkn : "+str(unkn))

	# colors
	colors = []
	for i in range (0, 256):
		colors.append(bs.readBits(16))

	# cluts
	cluts = []
	for i in range (0, texW):
		for j in range (0, texH):
			cluts.append(bs.read('B')[0])

	textures = []
	materials = []

	
	textures.append(drawTexture(texW, texH, colors, cluts))
	materials.append(NoeMaterial("mat_0", textures[0].name))


	# Groups section
	groups = []
	meshes = []

	for i in range(0, numBones):
		g = KGroup()
		g.hydrate(bs)
		groups.append(g)
		g.setParentName(groups)

		if g.numVertex > 0:
			vertices = []
			posList = []
			idxList = []
			uvList = []
			normalList = []
			wList = []
			for j in range(0, g.numVertex):
				v = KVertex(texW, texH)
				v.hydrate(bs)
				vertices.append(v)

			if g.numPoly[0] > 0: # triangles
				for j in range (0, int(g.numPoly[0])):
					poly = KPoly(True)
					poly.hydrate(bs, g.infos[1])
					poly.addIdx(idxList, posList, g, vertices, uvList, texW, texH, normalList, wList)

			if g.numPoly[1] > 0: # quads
				for j in range (0, int(g.numPoly[1])):
					poly = KPoly(False)
					poly.hydrate(bs, g.infos[1])
					poly.addIdx(idxList, posList, g, vertices, uvList, texW, texH, normalList, wList)

			mesh = NoeMesh(idxList, posList, g.name, "mat_0")
			mesh.setUVs(uvList)
			mesh.setWeights(wList)
			#mesh.setNormals(normalList)
			meshes.append(mesh)	
	
	bones = []
	for i in range(0, numBones):
		g = groups[i]
		matrix = NoeMat43([NoeVec3((1.0, 0.0, 0.0)), NoeVec3((0.0, 1.0, 0.0)), NoeVec3((0.0, 0.0, 1.0)), g.offset])
		bones.append(NoeBone(g.index, g.name, matrix, g.parentName, g.parentId))
	
	anims = []

	NMM = NoeModelMaterials(textures, materials)
	mdl = NoeModel(meshes, bones, anims, NMM)

	ptr = bs.getOffset()
	#print(str(ptr)+' -> '+str(footerPtr)+'->'+str(bs.getSize()))
	#nums = bs.read('6h') # ?
	#print("nums : "+str(nums))
	#bs.setOffset(ptr)

	#print("footerPtr : "+str(footerPtr)+' - curPtr : '+str(ptr))


	#nums = bs.read('4h') # 
	#print("nums : "+str(nums))
	#print("//-----------------------------------------------")
	bs.setOffset(footerPtr)
	return mdl
def koudelkaReadModel(data, mdlList):
	bs = NoeBitStream(data)
	header = bs.read("4s")[0]
	mdl = SDRParser(bs)
	mdlList.append(mdl)
	return 1

class KPoly():
	def __init__(self, isTri = True):
		self.type = 0
		self.isTri = isTri
		self.vertices = []
		self.normals = []
		self.uvs = []
		self.size = 0
		self.h = []
		self.alpha = 1
	def hydrate(self, bs, size):
		if self.isTri:
			self.h = bs.read("2B")
			self.vertices = bs.read("3H") # vertices indexes
		else :
			self.h = bs.read("4b")
			self.vertices = bs.read("4H") # vertices indexes

		if self.h[0] != 1:
			self.normals = bs.read('8B') # normals ?
		else:
			self.alpha = 0 # ?
		
		if self.h[0] == 44:
			footer = bs.read('4b')
			self.uvs = bs.read('8B')
		elif self.h[0] == 45:
			footer = bs.read('4b')
			self.uvs = bs.read('8B')
		elif self.h[0] == 12:
			footer = bs.read('4b')
			self.uvs = bs.read('8B')
		elif self.h[0] == 13:
			footer = bs.read('4b')
			self.uvs = bs.read('8B')
		else:
			self.uvs = bs.read('8B')
			footer = bs.read('4b')

		#print("h : "+str(self.h)+"	coords : "+str(self.vertices)+"		normals : "+str(self.normals)+"		uvs : "+str(self.uvs)+"		footer : "+str(footer))
	def addIdx(self, idxList, posList, group, vertices, uvList, texW, texH, normalList, wList):
		if self.alpha == 1:
			if self.isTri:
				idxList.append(len(posList))
				posList.append(vertices[self.vertices[2]].position + group.offset)
				idxList.append(len(posList))
				posList.append(vertices[self.vertices[1]].position + group.offset)
				idxList.append(len(posList))
				posList.append(vertices[self.vertices[0]].position + group.offset)
				uvList.append(NoeVec3([self.uvs[4]/texW, self.uvs[5]/texH, 0]))
				uvList.append(NoeVec3([self.uvs[2]/texW, self.uvs[3]/texH, 0]))
				uvList.append(NoeVec3([self.uvs[0]/texW, self.uvs[1]/texH, 0]))

				normalList.append(vertices[self.vertices[2]].normals)
				normalList.append(vertices[self.vertices[1]].normals)
				normalList.append(vertices[self.vertices[0]].normals)

				wList.append(NoeVertWeight([group.index], [1]))
				wList.append(NoeVertWeight([group.index], [1]))
				wList.append(NoeVertWeight([group.index], [1]))
			else :
				idxList.append(len(posList))
				posList.append(vertices[self.vertices[2]].position + group.offset)
				idxList.append(len(posList))
				posList.append(vertices[self.vertices[1]].position + group.offset)
				idxList.append(len(posList))
				posList.append(vertices[self.vertices[0]].position + group.offset)
				uvList.append(NoeVec3([self.uvs[4]/texW, self.uvs[5]/texH, 0]))
				uvList.append(NoeVec3([self.uvs[2]/texW, self.uvs[3]/texH, 0]))
				uvList.append(NoeVec3([self.uvs[0]/texW, self.uvs[1]/texH, 0]))
				normalList.append(vertices[self.vertices[2]].normals)
				normalList.append(vertices[self.vertices[1]].normals)
				normalList.append(vertices[self.vertices[0]].normals)

				idxList.append(len(posList))
				posList.append(vertices[self.vertices[1]].position + group.offset)
				idxList.append(len(posList))
				posList.append(vertices[self.vertices[2]].position + group.offset)
				idxList.append(len(posList))
				posList.append(vertices[self.vertices[3]].position + group.offset)
				uvList.append(NoeVec3([self.uvs[2]/texW, self.uvs[3]/texH, 0]))
				uvList.append(NoeVec3([self.uvs[4]/texW, self.uvs[5]/texH, 0]))
				uvList.append(NoeVec3([self.uvs[6]/texW, self.uvs[7]/texH, 0]))
				normalList.append(vertices[self.vertices[1]].normals)
				normalList.append(vertices[self.vertices[2]].normals)
				normalList.append(vertices[self.vertices[3]].normals)

				wList.append(NoeVertWeight([group.index], [1]))
				wList.append(NoeVertWeight([group.index], [1]))
				wList.append(NoeVertWeight([group.index], [1]))
				wList.append(NoeVertWeight([group.index], [1]))
				wList.append(NoeVertWeight([group.index], [1]))
				wList.append(NoeVertWeight([group.index], [1]))
		else:
			if self.isTri:
				posList.append(vertices[self.vertices[2]].position + group.offset)
				posList.append(vertices[self.vertices[1]].position + group.offset)
				posList.append(vertices[self.vertices[0]].position + group.offset)
				wList.append(NoeVertWeight([group.index], [1]))
				wList.append(NoeVertWeight([group.index], [1]))
				wList.append(NoeVertWeight([group.index], [1]))
			else :
				posList.append(vertices[self.vertices[3]].position + group.offset)
				posList.append(vertices[self.vertices[2]].position + group.offset)
				posList.append(vertices[self.vertices[1]].position + group.offset)
				posList.append(vertices[self.vertices[0]].position + group.offset)
				wList.append(NoeVertWeight([group.index], [1]))
				wList.append(NoeVertWeight([group.index], [1]))
				wList.append(NoeVertWeight([group.index], [1]))
				wList.append(NoeVertWeight([group.index], [1]))
class KGroup():
	def __init__(self):
		self.index = 0
		self.name = ""
		self.numVertex = 0
		self.parent = None
		self.parentId = -1
		self.parentName = None
		self.numPoly = []
		self.offset = NoeVec3()
		self.infos = [] 
	def hydrate(self, bs):
		self.index = bs.read('H')[0]
		#print("group index : "+str(self.index))
		self.numVertex = bs.read('H')[0]
		#print("numVertex : "+str(self.numVertex))
		self.infos = bs.read('2b') # Mode ?
		#print("infos : "+str(self.infos))
		self.numPoly = bs.read('2H')
		#print("numPoly : "+str(self.numPoly))
		self.parentId = bs.read('h')[0] # -1
		#print("parentId : "+str(self.parentId))
		self.offset = NoeVec3(bs.read('3i')) 
		#print("nums : "+str(nums))
		nums3 = bs.read('4h')
		#print("nums3 : "+str(nums3)) # ?? 1200, 1200, {0, -1}, {0-20}
		self.name = str(bs.readBytes(8))
		#print("group name : "+str(self.name))
		nums4 = bs.read('6i')
		#print("nums4 : "+str(nums4)) # padding ?
		#print("group index : "+str(self.index)+"	name :"+str(self.name)+"	numVertex : "+str(self.numVertex)+"	numPoly : "+str(self.numPoly)+"	parentId : "+str(self.parentId)+"	infos : "+str(self.infos)+"	offset ? : "+str(self.offset)+"	nums3 : "+str(nums3)+"	padding : "+str(nums4))
		#print("//------------"+str(bs.getOffset()))
	
	def setParentName(self, groups):
		if self.parentId != -1:
			if groups[self.parentId] != None:
				self.parent = groups[self.parentId]
				self.parentName = groups[self.parentId].name
				self.offset = self.offset + self.parent.offset
class KVertex():
	def __init__(self, texW, texH):
		self.position = NoeVec3()
		self.normals = NoeVec3()
		self.boneIndex = 0
		self.mode = 0
		self.texW = texW
		self.texH = texH
	def hydrate(self, bs):
		coords = bs.read('3h')
		self.position = NoeVec3(coords)
		num = bs.read('1h')[0]
		nums = bs.read('6B') # Ax, ay, az, bx, by, bz
		num2 = bs.read('1h')[0]
		#self.normals = NoeVec3([ nums[1] * nums[5] - nums[4] * nums[2], nums[2] * nums[3] - nums[5] * nums[0], nums[0] * nums[4] - nums[3] * nums[1]])
		#print("coords : "+str(coords)+"	num : "+str(num)+"	nums : "+str(nums)+"	num2 : "+str(num2))

def koudelkaBDTHeaderCheck(data):
	if len(data) < 8:
		return 0
	bs = NoeBitStream(data)

	header = bs.read("4s")[0]
	if header != KOUDELKA_BDT_HEADER:
		return 0

	return 1
def koudelkaReadBDT(data, texList):
	bs = NoeBitStream(data)
	#print("file size : "+str(bs.getSize()))
	nums = bs.read("I2H4BI2B2H4BH4B")

	numTex = nums[17]

	#print(str(nums))
	nums = bs.read("2BH")
	magicNum = nums[0]
	#print(str(nums))

	print(bs.getOffset())
	colors = []
	for i in range (0, 256):
		colors.append(bs.readBits(16))

	for x in range(0, numTex):
		texW, texH = bs.read("2i")
		nums = bs.read("6Bh")
		print(str(nums))
		# cluts
		cluts = []
		for i in range (0, texW):
			for j in range (0, texH):
				cluts.append(bs.read('B')[0])
		texList.append(drawTexture(texW, texH, colors, cluts, x))

	# scene modelisation
	nums = bs.read("H14BH2B2H2b")
	#print(str(nums))
	for i in range (0, magicNum):
		nums = bs.read("2b")
		#print(str(nums))

	#print(bs.getOffset())
	nums = bs.read("4IH2B")
	#print(str(nums))
	loop = nums[4]
	for i in range (0, loop):
		nums = bs.read("4b2h")
		#print(str(nums))


	return 1

def koudelkaMDTHeaderCheck(data):
	if len(data) < 8:
		return 0
	bs = NoeBitStream(data)

	header = bs.read("4s")[0]
	if header != KOUDELKA_MDT_HEADER:
		return 0

	return 1
def koudelkaReadMDT(data, texList):
	bs = NoeBitStream(data)
	#print("file size : "+str(bs.getSize()))
	nums = bs.read("I2BH4B2H")
	print(str(nums))

	for p in range (0, 8):
		nums = bs.read("4h")
		print(str(nums))

	nums = bs.read("4B")
	print(str(nums))

	nums = bs.read("4B")
	print(str(nums))
	print(bs.getOffset())

	numPallets = nums[0]
	numTex = nums[1]

	pallets = []

	for p in range (0, numTex):
		kmc = bs.read("3b")
		kmcId = bs.read("B")[0]

		colors = []
		for i in range (0, 256):
			colors.append(bs.readBits(16))
		pallets.append(colors)
		print("kmcId : "+str(kmcId)+" end colors at :"+str(bs.getOffset()))


	cluts = []
	for x in range(0, numTex):
		texW, pad, texH, pad2 = bs.read("4h")
		print("res : "+str(texW)+"x"+str(texH)+"		 | pad : "+str(pad)+" pad2 : "+str(pad2))
		nums = bs.read("8B")
		print(str(nums))

		# cluts
		for i in range (0, texW):
			for j in range (0, texH):
				cluts.append(bs.read('B')[0])
		

	
	texList.append(drawTexture(128, 128*4, pallets[0], cluts, 0))
	
	print(bs.getOffset())

	# scene modelisation

	print("//-----------------------------------------------")

	return 1

def koudelkaTEXHeaderCheck(data):
	if len(data) < 8:
		return 0
	bs = NoeBitStream(data)
	header = bs.read("I")[0]
	if (header != KOUDELKA_TEX_HEADER):
		return 0
	return 1
def koudelkaReadTEX(data, texList):
	bs = NoeBitStream(data)
	nums = bs.read("I8H")
	print(repr(nums))
	texW = nums[6]
	texH = nums[7]
	# colors
	colors = []
	for i in range (0, 256):
		colors.append(bs.readBits(16))
	# cluts
	cluts = []
	for i in range (0, texW):
		for j in range (0, texH):
			cluts.append(bs.read('B')[0])
	texList.append(drawTexture(texW, texH, colors, cluts))
	return 1

def koudelkaTX8HeaderCheck(data):
	if len(data) < 8:
		return 0
	bs = NoeBitStream(data)
	tx8Check = bs.read("3s")[0]
	if (tx8Check != KOUDELKA_TX8_HEADER):
		return 0
	return 1
def koudelkaReadTX8(data, texList):
	bs = NoeBitStream(data)
	h = bs.read("4B")
	if h[3] == 0x20:
		nums = bs.read("2B5H")
		print("TX8 : "+repr(nums))
		texW = nums[3]
		texH = nums[4]
		# colors
		colors = []
		for i in range (0, 256):
			colors.append(bs.readBits(16))
		# cluts
		cluts = []
		numParts = int(texH / 256)
		parts = []
		for k in range (0, numParts):
			parts.append([])
			for i in range (0, texW):
				for j in range (0, 256):
					parts[k].append(bs.read('B')[0])

		for j in range (0, 256):
			for k in range (0, numParts):
				for i in range (0, texW):
					cluts.append(parts[k][i+j*texW])

		texList.append(drawTexture(texW*numParts, 256, colors, cluts))
	elif h[3] == 0x31:
		nums = bs.read("2B5H")
		print("KD8 : "+repr(nums))
		texW = nums[3]
		texH = nums[4]
		pallets = []
		for k in range (0, 4):
			# colors
			colors = []
			for i in range (0, 256):
				colors.append(bs.readBits(16))
			pallets.append(colors)

		# cluts
		cluts = []
		for i in range (0, texW):
			for j in range (0, texH):
				cluts.append(bs.read('B')[0])
		
		for k in range (0, 4):
			pixmap = bytearray()
			for j in range(0, len(cluts)):
				pixmap += bytearray(color16to32(pallets[k][int(cluts[j])]))

			tex = NoeTexture("_tex_"+str(k), texW, texH, pixmap)
			texList.append(tex)

	return 1

def koudelkaTX4HeaderCheck(data):
	if len(data) < 8:
		return 0
	bs = NoeBitStream(data)
	tx4Check = bs.read("3s")[0]
	if (tx4Check != KOUDELKA_TX4_HEADER):
		return 0
	return 1
def TX4Parser(bs):
	basePtr = bs.getOffset()
	#print(str(basePtr)+'-'+str(bs.getSize()))
	nums = bs.read("I2B5H")
	print("TX4 : "+repr(nums))
	ptrClut = nums[1]
	if nums[2] > 0:
		texW = nums[2]
		texH = nums[4]
	else:
		texW = nums[4]
		texH = nums[5]


	numColors = basePtr+(ptrClut - int(bs.getOffset()))
	print("numColors : "+str(numColors))
	# colors
	colors = []
	for i in range (0, numColors):
		colors.append(bs.read('B')[0])

	# cluts
	cluts = []
	if ptrClut == int(bs.getSize()):
		cluts = colors
		miss = texW*texH - len(cluts)
		if miss > 0:
			for i in range (0, miss):
				cluts.append(0)
	else :
		for i in range (0, texW):
			for j in range (0, texH):
				cluts.append(bs.read('B')[0])
	
	pixmap = bytearray()
	for j in range(0, len(cluts)):
		pixmap += bytearray([ cluts[j], cluts[j], cluts[j], 255 ])
	tex = NoeTexture("_tex_"+str(0), texW, texH, pixmap)
	return tex
def koudelkaReadTX4(data, texList):
	bs = NoeBitStream(data)
	texList.append(TX4Parser(bs))
	while bs.getOffset() + 2000 < bs.getSize():
		bs.seek(2000, NOESEEK_REL)
		texList.append(TX4Parser(bs))
	return 1

def koudelkaFT4HeaderCheck(data):
	if len(data) < 8:
		return 0
	bs = NoeBitStream(data)
	ft4Check = bs.read("4s")[0]
	if (ft4Check != KOUDELKA_FT4_HEADER):
		return 0
	return 1
def koudelkaReadFT4(data, texList):
	bs = NoeBitStream(data)
	nums = bs.read("I2B5H")
	#print("FT4 : "+repr(nums))
	numTex = nums[1]
	# colors
	colors = []
	for i in range (0, 32):
		colors.append(bs.read('B')[0])

	#print(str(bs.getOffset())+" -> "+str(bs.getSize()))


	texturesInfos = []
	for i in range (0, numTex+1):
		i = bs.read("H4B13H")
		texturesInfos.append(i)
		#print("texI : "+repr(i))


	# cluts
	texW = 128
	texH = 512
	cluts = []
	for i in range (0, texW):
		for j in range (0, texH):
			cluts.append(bs.read('B')[0])
	
	pixmap = bytearray()
	for j in range(0, len(cluts)):
		pixmap += bytearray([ 0, 0, 0, cluts[j] ])
	tex = NoeTexture("_tex_"+str(0), texW, texH, pixmap)
	texList.append(tex)

	#print("o : "+str(bs.getOffset())+" -> "+str(bs.getSize()))

	texW = 32
	texH = 16
	cluts = []
	for i in range (0, texW):
		for j in range (0, texH):
			cluts.append(bs.read('B')[0])
	
	pixmap = bytearray()
	for j in range(0, len(cluts)):
		pixmap += bytearray([ 0, 0, 0, cluts[j] ])
	tex = NoeTexture("_tex_"+str(0), texW, texH, pixmap)
	texList.append(tex)

	return 1

def koudelkaARCheck(data):
	if len(data) < 8:
		return 0
	bs = NoeBitStream(data)
	header = bs.read("4I")[0]
	if header != 0xa:
		return 0
	return 1
def extractAR(fileName, fileLen, justChecking):
	with open(fileName, "rb") as f:
		if justChecking:
			return 1

		nums = noeUnpack("3I", f.read(12))
		for i in range (0, 124):
			nums = noeUnpack("8B", f.read(8))


		modelIndex = 1
		print("Extracting files from archive.")
		# iterative search
		while True:
			if f.tell()+4 < fileLen:
				rep = f.tell()
				b = f.read(4)
				if b == KOUDELKA_MODEL_HEADER:
					numBones, numMesh, footerPtr = noeUnpack("2HI", f.read(8))
					footerPtr += f.tell()+4
					exName = "MonsterModel_"+str(modelIndex)+".SDR"
					f.seek(rep)
					compData = f.read(int(footerPtr-rep))
					print("Writing", exName)
					rapi.exportArchiveFile(exName, compData)
					modelIndex += 1
			else:
				break
	return 1

def koudelkaPMFHeaderCheck(data):
	if len(data) < 8:
		return 0
	bs = NoeBitStream(data)
	h1, num1, num2, h2, header = bs.read("I2HI4s")
	if header != KOUDELKA_PMF_HEADER:
		return 0
	return 1
def koudelkaReadPMF(data, texList):
	bs = NoeBitStream(data)
	h = bs.read("I2HI")
	header = bs.read("4s")[0]

	nums = bs.read("12H")
	print("PMF : "+repr(nums))

	numTex = nums[0]
	numBones = nums[4]

	texW = 32
	texH = 32

	print(str(bs.getOffset())+' size : '+str(bs.getSize()))
	for k in range(0, numTex):
		# colors
		colors = []
		for i in range (0, 256):
			colors.append(bs.readBits(16))

		print(str(bs.getOffset())+' size : '+str(bs.getSize()))

		
		while True:
			reso = bs.read("2H")
			if reso == (0, 0) or (reso[0] > 512 or reso[1] > 512):
				continue
			else:
				print(repr(reso))
				break

		# cluts
		cluts = []
		for i in range (0, reso[0]):
			for j in range (0, reso[1]):
				cluts.append(bs.read('B')[0])
		
		pixmap = bytearray()
		for j in range(0, len(cluts)):
			pixmap += bytearray(color16to32(colors[int(cluts[j])]))
		tex = NoeTexture("_tex_"+str(0), reso[0], reso[1], pixmap)
		texList.append(tex)
		print(str(bs.getOffset())+' size : '+str(bs.getSize()))


	for k in range(0, numBones):
		nums = bs.read("6H")
		print("Bone ? : "+repr(nums))

	# TODO : effect model
	#nums = bs.read("2H3I")
	#print("B : "+repr(nums))

	return 1


def drawTexture(texW, texH, colors, cluts, idx = 0):
	pixmap = bytearray()
	for j in range(0, len(cluts)):
		pixmap += bytearray(color16to32(colors[int(cluts[j])]))
	tex = NoeTexture("_tex_"+str(idx), texW, texH, pixmap)
	#texName = rapi.getInputName()+"_tex_"+str(idx)+".png"
	#if (rapi.checkFileExists(texName) != 1):
	#	noesis.saveImageRGBA(texName, tex)

	return tex
def color16to32( c ):
	b = ( c & 0x7C00 ) >> 10
	g = ( c & 0x03E0 ) >> 5
	r = ( c & 0x001F )
	if c == 0 :
		return [ 0, 0, 0, 0 ]
	
	#5bit -> 8bit is factor 2^3 = 8
	return [ r * 8, g * 8, b * 8, 255 ]