from pydoc import describe
import time
from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket
import threading
import sys
import traceback
import os

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
    DESCRIBE = 4
    describeState = False
    isDescribeSent = False
    CHANGEFRAME = 5
    CHANGESPEED = 6

    # Use for analyze
    sumOfTime = 0

    

    stop = True
    # Initiation..
    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.master = master  # render the UI
        # handler for user hitting the "X" button
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.createWidgets()
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = filename
        self.rtspSeq = 0
        self.sessionId = 0  # assign to the Client when connect to a server
        self.requestSent = -1
        self.teardownAcked = 0  # flag to indicate disconnection to server and close the socket
        self.connectToServer()
        self.frameNbr = 0  # detect loss in packet and maybe reordering packet
        self.packetLost = 0  # number of packets lost

        self.totalPacket = 0
        self.counter = 0
        self.RtpPortOpen = False  # check if the rtp port is open or not
        self.totalBytesRevc = 0

        #additional
        self.isDescribeSent = False
        self.description = ''
        self.isLost = 0
        self.isNewMovie = False
        self.totalFrame = 0
        self.isPlayed = False 
        self.isInit = False
        self.speed = float(1)

    # THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI

    def createWidgets(self):
        """Build GUI."""

        # Create Descript button
        self.start = Button(self.master, activeforeground = "#9D72FF", activebackground = "#9D72FF", fg = "#9D72FF", highlightbackground= "#9D72FF", highlightthickness= 1,
                            height=3, width=20, padx=8, pady=10)
        self.start["text"] = "Describe"
        self.start["command"] = self.describe
        self.start.grid(row=2, column=0, padx=2, pady=2)

        # Create Play button
        self.start = Button(self.master, activeforeground="#00B49D", activebackground="#00B49D", fg="#00B49D",
                            highlightbackground="#00B49D", highlightthickness=1,
                            height=3, width=20, padx=8, pady=10)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=2, column=1, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.master, activeforeground="#3CB9FC", activebackground="#3CB9FC", fg="#3CB9FC",
                            highlightbackground="#3CB9FC", highlightthickness=1,
                            height=3, width=20, padx=8, pady=10)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=2, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.master, activeforeground="#fc7400", activebackground="#fc7400", fg="#fc7400",
                               highlightbackground="#fc7400", highlightthickness=1,
                               height=3, width=20, padx=8, pady=10)
        self.teardown["text"] = "Stop"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=2, column=3, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4,
                        sticky=W+E+N+S, padx=5, pady=5)

        # Create a box to display the loss rate
        self.lossRate_box = Label(
            self.master, text='Loss rate: 0', width=15, height=1, bd=1, relief=GROOVE, anchor=E)
        self.lossRate_box.grid(
            row=3, column=0, columnspan=2, sticky=W + E, padx=1, pady=1)

        # Create a box to display the data rate
        self.dataRate_box = Label(
            self.master, text='Data rate: 0', width=15, height=1, bd=1, relief=GROOVE, anchor=E)
        self.dataRate_box.grid(
            row=3, column=2, columnspan=2, sticky=W + E, padx=1, pady=1)

        # Create desciption for GUI
        self.description_gui = Label(self.master, text = '--description--', width=28, height=8, bd = 1, relief=GROOVE)
        self.description_gui.grid(row=5, column=0, rowspan=3,columnspan=4, sticky=W + E + N + S, padx=1, pady=1)

        #########################################################
         # Create status bar for time line 
        self.status_bar = Label(self.master, text = '--/--', width=15, height=1, bd = 1, relief=GROOVE, anchor=E)
        self.status_bar.grid(row=4, column=3, sticky=W + E, padx=1, pady=1)

        # Create status bar for speed
        self.status_speed = Label(self.master, text = 'x1', width=15, height=1, bd = 1, relief=GROOVE)
        self.status_speed.grid(row=4, column=2, sticky=W + E, padx=1, pady=1)

        # Create button for slow down
        self.slowdownButton = Button(self.master, text = '<< 0.25', command=self.slowDown , width=15, height=1, bd = 1, relief=GROOVE)
        self.slowdownButton.grid(row=4, column=0, sticky=W + E, padx=1, pady=1)

        # Create button for speed up 
        self.speedupButton = Button(self.master, text = '0.25 >>', command=self.speedUp , width=15, height=1, bd = 1, relief=GROOVE)
        self.speedupButton.grid(row=4, column=1, sticky=W + E, padx=1, pady=1)

        #Create slider for video
        self.progress_slider = Scale(self.master, from_=0, to=0, length=60, bd = 5, showvalue=0, sliderlength = 25, troughcolor = '#FFBF01', orient="horizontal", command=self.seekFrame)
        self.progress_slider.grid(row=1, columnspan=4, sticky=W + E, padx=1, pady=1)

    def describe(self):
        """Setup button handler."""
        if(self.state == self.INIT): return
        self.sendRtspRequest(self.DESCRIBE)
        self.isDescribeSent = True

        # self.state = self.READY
    # TODO

    def exitClient(self):
        """Teardown button handler."""
        self.sendRtspRequest(self.TEARDOWN)
        try:
            # Delete the cache image from video
            os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
        except:
            print("Video was not loaded.")
    # TODO

    def pauseMovie(self):
        """Pause button handler."""
        if(self.state == self.PLAYING):
            self.sendRtspRequest(self.PAUSE)
            # self.state = self.READY
    # TODO

    def playMovie(self):
        """Play button handler."""
        if(self.state == self.INIT):
            self.sendRtspRequest(self.SETUP)
        if(self.state == self.READY):
            self.sendRtspRequest(self.PLAY)

            # self.state = self.PLAYING

    # TODO
    def slowDown (self):
        if self.isInit and (self.speed - 0.25) > 0: 
            self.speed = self.speed - 0.25
            self.sendRtspRequest(self.CHANGESPEED, self.speed)
            self.status_speed.config(text= 'x' + str(self.speed))

    def speedUp (self):
        if self.isInit and (self.speed + 0.25) <= 1.75: 
            self.speed = self.speed + 0.25
            self.sendRtspRequest(self.CHANGESPEED, self.speed)
            self.status_speed.config(text= 'x' + str(self.speed))

    def seekFrame(self, var):
        if self.state == self.READY:
            self.frameNbr = int(var)
            self.converted_timeInterval = time.strftime('%M:%S', time.gmtime((self.totalFrame - self.frameNbr) * self.TPF + 0.9))
            self.status_bar.config(text= '-' + self.converted_timeInterval + " / " + self.converted_timeLength)
            self.sendRtspRequest(self.CHANGEFRAME, var)
    def updateBar(self):
        self.converted_timeInterval = time.strftime('%M:%S', time.gmtime((self.totalFrame - self.frameNbr) * self.TPF + 0.9))
        if self.state != self.READY:
            self.progress_slider.set(self.frameNbr)
        self.status_bar.config(text= '-' + self.converted_timeInterval + " / " + self.converted_timeLength)
        
    def listenRtp(self):
        """Listen for RTP packets."""
        initialTime = 0
        preTime = 0
        firstPacket = False
        preSeqNum = -1
        while True:
            if(self.teardownAcked):
                self.teardownAcked = 0
                break
            try:
                data = self.rtpSocket.recv(11540)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    self.totalBytesRevc += len(data)
                    recvFrameNbr = rtpPacket.seqNum()

                    timestamp = rtpPacket.timestamp()
                    if not firstPacket:
                        initialTime = timestamp
                        preTime = timestamp
                        firstPacket = True
                    print("Receive Packet, Seq Num: " + str(recvFrameNbr))
                    if(preSeqNum == -1):
                        preSeqNum = recvFrameNbr
                    self.totalPacket += recvFrameNbr - preSeqNum
                    preSeqNum = recvFrameNbr
                    try:
                        # print(self.frameNbr +1,'--',rtpPacket.seqNum())
                        if self.frameNbr + 1 != rtpPacket.seqNum():
                            self.packetLost += 1
                            print(self.packetLost)
                            print(self.frameNbr)
                            print(rtpPacket.seqNum())

                            print('-' * 50 + "\n + 'LOST PACKET' + \n" + '-' * 50)
                    except:
                        # print("seqNum() Loi \n")
                        # traceback.print_exc(file=sys.stdout)
                        # print("\n")
                        pass
                    if (timestamp - preTime >= 1):
                        preTime = timestamp
                        lossRate = int(
                            (self.packetLost/self.totalPacket) * 100)
                        dataRate = int((self.totalBytesRevc) /
                                       ((timestamp-initialTime)*1000))
                        self.lossRate_box['text'] = "Loss rate: " + \
                            str(lossRate) + " %"
                        self.dataRate_box['text'] = "Data rate: " + \
                            str(dataRate) + " kB/s"
                    # if recvFrameNbr > self.frameNbr:  # Discard the late packet
                    self.frameNbr = rtpPacket.seqNum()
                    self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
                    self.updateBar()
            except:
                pass

    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        file = open(cachename, "wb")  # open to write to the cache
        file.write(data)
        file.close()
        return cachename

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        currFrame = ImageTk.PhotoImage(Image.open(imageFile))
        self.label.configure(image=currFrame, height=288)
        self.label.image = currFrame

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        self.rtspSocket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)  # create TCP socket
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        except:
            print("Could not connect to Server")

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""
        # -------------
        # TO COMPLETE
        # -------------
        requestMess = ''
        if(requestCode == self.SETUP):
            threading.Thread(target=self.recvRtspReply).start()
            # Update RTSP sequence number.
            self.rtspSeq = self.rtspSeq + 1

            requestMess = "SETUP %s RTSP/1.0\nCSeq: %d\nTRANSPORT: RTP/UDP; client_port= %d" % (
                self.fileName, self.rtspSeq, self.rtpPort)

            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.SETUP
        elif(requestCode == self.PLAY):
            # Update RTSP sequence number.
            self.rtspSeq = self.rtspSeq + 1

            requestMess = "PLAY %s RTSP/1.0\nCSeq: %d\nTRANSPORT: RTP/UDP; client_port= %d" % (
                self.fileName, self.rtspSeq, self.rtpPort)

            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.PLAY
        elif(requestCode == self.PAUSE):
            # Update RTSP sequence number.
            self.rtspSeq = self.rtspSeq + 1

            requestMess = "PAUSE %s RTSP/1.0\nCSeq: %d\nTRANSPORT: RTP/UDP; client_port= %d" % (
                self.fileName, self.rtspSeq, self.rtpPort)

            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.PAUSE
        elif(requestCode == self.TEARDOWN):
            # Update RTSP sequence number.
            self.rtspSeq = self.rtspSeq + 1

            requestMess = "TEARDOWN %s RTSP/1.0\nCSeq: %d\nTRANSPORT: RTP/UDP; client_port= %d" % (
                self.fileName, self.rtspSeq, self.rtpPort)

            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.TEARDOWN
        elif requestCode == self.DESCRIBE:
            self.rtspSeq += 1
            requestMess = "DESCRIBE " + str(self.fileName) + " RTSP/1.0\nCSeq: " + str(
                self.rtspSeq) + "\nSession: " + str(self.sessionId)
            self.requestSent = self.DESCRIBE

        elif requestCode == self.CHANGEFRAME:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq += 1
            requestMess = "CHANGEFRAME " + str(self.fileName) + " RTSP/1.0\nCSeq: " + str(self.rtspSeq) + "\nSession: " + str(self.sessionId) + "\nFrameNum: " + str(var)
            self.requestSent = self.CHANGEFRAME

        elif requestCode == self.CHANGESPEED:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq += 1
            requestMess = "CHANGESPEED " + str(self.fileName) + " RTSP/1.0\nCSeq: " + str(self.rtspSeq) + "\nSession: " + str(self.sessionId) + "\nSpeed: " + str(var)
            self.requestSent = self.CHANGESPEED

        print('Sending request: ' + requestMess)
        self.rtspSocket.send(requestMess.encode())

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            reply = self.rtspSocket.recv(1024)  # 1024 bytes

            if reply:
                self.parseRtspReply(reply.decode("utf-8"))

            # Close the RTSP socket upon requesting Teardown
            if self.requestSent == self.TEARDOWN:
                # self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                break

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        lines = data.split(
            '\n')  # lines là list chứa các string trả về từ server
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
                        if not self.RtpPortOpen:
                            self.openRtpPort()
                        self.sendRtspRequest(self.PLAY)
                        self.totalFrame = int(lines[3].split(' ')[1])
                        self.TPF = float(lines[4].split(' ')[1])
                        self.progress_slider['to'] = self.totalFrame
                        self.converted_timeLength = time.strftime('%M:%S', time.gmtime(self.totalFrame * self.TPF))
                        self.updateBar()
                    elif self.requestSent == self.PLAY:
                        self.state = self.PLAYING
                        # tạo ra một kênh kết nối chờ đợi 1 event giữa các thread
                        self.playEvent = threading.Event()
                        self.playEvent.clear()
                        threading.Thread(target=self.listenRtp).start()
                    elif self.requestSent == self.PAUSE:
                        self.state = self.READY
                        # The play thread exits. A new thread is created on resume.
                        self.playEvent.set()  # tạm dừng thread lại

                    elif self.requestSent == self.TEARDOWN:
                        self.state = self.INIT
                        # Flag the teardownAcked to close the socket.
                        self.teardownAcked = 1
                        self.rtpSocket.shutdown(socket.SHUT_RDWR)
                        self.rtpSocket.close()
                        self.playEvent.set()
                        self.sessionId = 0
                        self.requestSent = -1
                        self.teardownAcked = 0
                        self.frameNbr = 0
                        self.counter = 0
                        self.connectToServer()
                        self.RtpPortOpen = False
                        self.label.pack_forget()
                        self.label.image = ''
                        # self.rtspSeq = 0
                        for i in os.listdir():
                            if i.find(CACHE_FILE_NAME) == 0:
                                os.remove(i)
                                self.rtspSeq = 0

                        

                    elif (self.requestSent == self.DESCRIBE):
                        count = 5
                        self.description = lines[4]
                        while lines[count]:
                            self.description = self.description + '\n' + lines[count]
                            count = count + 1
                        self.isDescribeSent = False
                        self.describeState = False
                        self.description_gui.config(text=self.description)

    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        # -------------
        # TO COMPLETE
        # -------------
        # Create a new datagram socket to receive RTP packets from the server
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Set the timeout value of the socket to 0.5sec
        # ...
        self.RtpPortOpen = True
        self.rtpSocket.settimeout(0.5)
        self.rtpSocket.bind(('', self.rtpPort))

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        # TODO
        self.pauseMovie()
        if self.state != self.TEARDOWN:
            self.sendRtspRequest(self.TEARDOWN)
        # if(self.checkSocketIsOpen):
        # 	self.rtpSocket.shutdown(socket.SHUT_RDWR)
        # 	self.rtpSocket.close()
        self.master.destroy()  # Close the gui window
        sys.exit(0)
