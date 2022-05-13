from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master # render the UI
		self.master.protocol("WM_DELETE_WINDOW", self.handler) # handler for user hitting the "X" button
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0 
		self.sessionId = 0 # assign to the Client when connect to a server
		self.requestSent = -1
		self.teardownAcked = 0 #flag to indicate disconnection to server and close the socket 
		self.connectToServer()
		self.frameNbr = 0	# detect loss in packet and maybe reordering packet
		self.packetLost = 0 # number of packets lost

		self.RtpPortOpen = False # check if the rtp port is open or not

		
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
	
	def setupMovie(self):
		"""Setup button handler."""
		if(self.state == self.INIT):
			self.sendRtspRequest(self.SETUP)
			# self.state = self.READY
	#TODO
	
	def exitClient(self):
		"""Teardown button handler."""
		self.sendRtspRequest(self.TEARDOWN)
		try:
			os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT) #Delete the cache image from video
		except:
			print("Video was not loaded.")
	#TODO

	def pauseMovie(self):
		"""Pause button handler."""
		if(self.state == self.PLAYING):
			self.sendRtspRequest(self.PAUSE)
			# self.state = self.READY
	#TODO
	
	def playMovie(self):
		"""Play button handler."""
		if(self.state == self.READY):
			self.sendRtspRequest(self.PLAY)

			# self.state = self.PLAYING

	#TODO
	
	def listenRtp(self):		
		"""Listen for RTP packets."""
		while True:
			try:
				data = self.rtpSocket.recv(11540)
				if data:
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)
					
					recvFrameNbr = rtpPacket.seqNum()
					print("Receive Packet, Seq Num: " + str(recvFrameNbr))

					try:
						# print(self.frameNbr +1,'--',rtpPacket.seqNum())
						if self.frameNbr + 1 != rtpPacket.seqNum():
							self.packetLost += 1 #flag khi mất gói tin
							print('X' * 50 + "\n + 'LOST PACKET' + n" + 'X' * 50)
					# version = rtpPacket.version()
					except:
						# print("seqNum() Loi \n")
						# traceback.print_exc(file=sys.stdout)
						# print("\n")
						pass
					if recvFrameNbr > self.frameNbr: # Discard the late packet
						self.frameNbr = recvFrameNbr
						self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
			except:
				pass
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file = open(cachename, "wb") # open to write to the cache
		file.write(data)
		file.close()
		return cachename
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		currFrame = ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image = currFrame, height=288) 
		self.label.image = currFrame
		
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create TCP socket
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			print ("Could not connect to Server")
	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		requestMess =''
		if(requestCode == self.SETUP):
			threading.Thread(target=self.recvRtspReply).start()
			# Update RTSP sequence number.
			self.rtspSeq = self.rtspSeq + 1

			requestMess = "SETUP %s RTSP/1.0\nCSeq: %d\nTRANSPORT: RTP/UDP; client_port= %d" % (self.fileName, self.rtspSeq, self.rtpPort)

			# Keep track of the sent request.
			# self.requestSent = ...
			self.requestSent = self.SETUP
		elif(requestCode == self.PLAY):
			# Update RTSP sequence number.
			self.rtspSeq = self.rtspSeq + 1

			requestMess = "PLAY %s RTSP/1.0\nCSeq: %d\nTRANSPORT: RTP/UDP; client_port= %d" % (self.fileName, self.rtspSeq, self.rtpPort)

			# Keep track of the sent request.
			# self.requestSent = ...
			self.requestSent = self.PLAY
		elif(requestCode == self.PAUSE):
			# Update RTSP sequence number.
			self.rtspSeq = self.rtspSeq + 1

			requestMess = "PAUSE %s RTSP/1.0\nCSeq: %d\nTRANSPORT: RTP/UDP; client_port= %d" % (self.fileName, self.rtspSeq, self.rtpPort)

			# Keep track of the sent request.
			# self.requestSent = ...
			self.requestSent = self.PAUSE
		elif(requestCode == self.TEARDOWN):
			# Update RTSP sequence number.
			self.rtspSeq = self.rtspSeq + 1

			requestMess = "TEARDOWN %s RTSP/1.0\nCSeq: %d\nTRANSPORT: RTP/UDP; client_port= %d" % (self.fileName, self.rtspSeq, self.rtpPort)

			# Keep track of the sent request.
			# self.requestSent = ...
			self.requestSent = self.TEARDOWN

		print('Sending request: ' + requestMess)
		self.rtspSocket.send(requestMess.encode())

		
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		while True:
			reply = self.rtspSocket.recv(1024) # 1024 bytes
			
			if reply: 
				self.parseRtspReply(reply.decode("utf-8"))
			
			# Close the RTSP socket upon requesting Teardown
			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		lines = data.split('\n') # lines là list chứa các string trả về từ server
		seqNum = int(lines[1].split(' ')[1])
		
		# Process only if the server reply's sequence number is the same as the request's
		if seqNum == self.rtspSeq:
			session = int(lines[2].split(' ')[1])
			# New RTSP session ID
			if self.sessionId == 0:
				self.sessionId = session
			
			# Process only if the session ID is the same
			if self.sessionId == session:
				if int(lines[0].split(' ')[1]) == 200: 
					if self.requestSent == self.SETUP:
						self.state = self.READY
						# Open RTP port.
						if not self.RtpPortOpen: self.openRtpPort() 
					elif self.requestSent == self.PLAY:
						self.state = self.PLAYING
						self.playEvent = threading.Event() # tạo ra một kênh kết nối chờ đợi 1 event giữa các thread
						self.playEvent.clear()
						threading.Thread(target=self.listenRtp).start()
					elif self.requestSent == self.PAUSE:
						self.state=self.READY
						# The play thread exits. A new thread is created on resume.
						self.playEvent.set() # tạm dừng thread lại

					elif self.requestSent == self.TEARDOWN:
						self.state = self.INIT
						# Flag the teardownAcked to close the socket.
						self.teardownAcked = 1
						self.rtpSocket.shutdown(socket.SHUT_RDWR)
						self.rtpSocket.close()
						self.playEvent.set()

						for i in os.listdir():
							if i.find(CACHE_FILE_NAME) == 0:
								os.remove(i)
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		
		# Set the timeout value of the socket to 0.5sec
		# ...
		self.RtpPortOpen = True
		self.rtpSocket.settimeout(0.5)
		self.rtpSocket.bind(('', self.rtpPort))

		

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		#TODO
		self.pauseMovie()
		if self.state != self.TEARDOWN: self.sendRtspRequest(self.TEARDOWN)
		# if(self.checkSocketIsOpen):
		# 	self.rtpSocket.shutdown(socket.SHUT_RDWR)
		# 	self.rtpSocket.close()
		self.master.destroy()  # Close the gui window
		sys.exit(0)
