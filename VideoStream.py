class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			self.file = open(filename, 'rb')
		except:
			raise IOError
		self.frameNum = int(0)		
		self.dataFrame = []
		self.totalFrameNum = self.totalFrame()
		
	def nextFrame(self):
		"""Get next frame."""
		data = ''
		if self.frameNum <= self.totalFrameNum:
			data = self.dataFrame[self.frameNum]
			self.frameNum  += 1
		return data

	def setFrame(self, num):
		self.frameNum = int(num)
	
	def totalFrame(self):
		"""Count total frame."""
		try:
			tempFile = open(self.filename, 'rb')
		except:
			print ("Cannot open file for calculating totalFrame.")
		totalframeNum = 0

		dataTemp = tempFile.read(5) # Get the framelength from the first 5 bits
		while dataTemp: 
			tempFramelength = int(dataTemp)

			# Read the current frame
			dataTempContent = tempFile.read(tempFramelength)
			self.dataFrame.append(dataTempContent)
			if dataTempContent:
				totalframeNum += 1
			dataTemp = tempFile.read(5)
		return int(totalframeNum)
		
	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum