import urllib3
import os
import time
import sys
import paramiko
import subprocess as sub
import threading
from HTMLParser import HTMLParser
from Queue import Queue
import datetime

 

class RunCmd(threading.Thread):
    def __init__(self, cmd, timeout):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.timeout = timeout

    def run(self):
        self.p = sub.Popen(self.cmd)
        self.p.wait()

    def Run(self):
        self.start()
        self.join(self.timeout)

        if self.is_alive():
            self.p.terminate()      #use self.p.kill() if process needs a kill -9
            self.join()

#parser for video URL list
class LinksParser_VideoList(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.recording = 0
    self.data = []

  def handle_starttag(self, tag, attributes):
    if tag != 'a':
      return
    if self.recording:
      self.recording += 1
      return
    for target in attributes:
      if target == '_blank':
        break
    else:
      return
    self.recording = 1

  def handle_endtag(self, tag):
    if tag == 'a' and self.recording:
      self.recording -= 1

  def handle_data(self, data):
    if self.recording:
      self.data.append(data)

#Parser for proxy IP list
class LinksParser_IP(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.recording = 0
    self.data = []

  def handle_starttag(self, tag, attributes):
    if tag != 'td':
      return
    if self.recording:
      self.recording += 1
      return
    for name, value in attributes:
      if name == 'width' and value == '170':
        break
    else:
      return
    self.recording = 1

  def handle_endtag(self, tag):
    if tag == 'td' and self.recording:
      self.recording -= 1

  def handle_data(self, data):
    if self.recording:
      self.data.append(data)

#parser for proxy port number list
class LinksParser_port(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.recording = 0
    self.data = []

  def handle_starttag(self, tag, attributes):
    if tag != 'td':
      return
    if self.recording:
      self.recording += 1
      return
    for name, value in attributes:
      if name == 'width' and value == '70':
        break
    else:
      return
    self.recording = 1

  def handle_endtag(self, tag):
    if tag == 'td' and self.recording:
      self.recording -= 1

  def handle_data(self, data):
    if self.recording:
      self.data.append(data)

#Parser for video title
class LinksParser_VideoTitle(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.recording = 0
    self.data = []

  def handle_starttag(self, tag, attributes):
    if tag != 'h2':
      return
    if self.recording:
      self.recording += 1
      return
    #for name, value in attributes:
    #  if name == 'width' and value == '70':
    #    break
    #else:
    #  return
    self.recording = 1

  def handle_endtag(self, tag):
    if tag == 'h2' and self.recording:
      self.recording -= 1

  def handle_data(self, data):
    if self.recording:
      self.data.append(data)

class GetVideoFilename():
  def __init__(self):
    self.http = urllib3.PoolManager()
    self.filename = ''

  def GetVideoTitle(self, inputURL):
    parser_Title = LinksParser_VideoTitle()
    content = self.http.request('GET', inputURL)
    parser_Title.feed(content.data)
    self.filename = parser_Title.data[0].decode('gbk')
    self.filename = RemoveStringSpace(self.filename)

#Get proxy server addr
class GetAvailableProxyServer():
  def __init__(self):
    self.currentPort = ''
    self.currentProxy = ''
    self.GetProxy = False
    self.prefix = 'http://www.cooleasy.com/?act=list&port=&type=&country=China&page='
    self.page = 1
    self.http = urllib3.PoolManager()
    self.FailProxys = []
  #Is server alive?
  def IsProxyServerAlive(self, IP, Port, targetURL):
    #Taiwan Proxy:
    #IP='218.244.148.151'
    #Port='8080'
    Check = False
    try:
      # This returns a ProxyManager object which has the same API as other ConnectionPool objects.
      http = urllib3.proxy_from_url('http://'+IP+':'+Port)
      r = http.request('GET', targetURL)
    #except urllib3.HTTPError, e:
    #    print 'Error code: ', e.code
    #    return e.code
    except Exception, detail:
        print "ERROR:", detail
        return False
    return True
    #Check = True
    #response = os.system('env http_proxy=http://'+IP+':'+Port+' ping -c 2 '+targetURL)
    #if response != 0:
    #  return False
    #else:
    #  if Check == True:
    #    return True
    #  else:
    #   return False

  def GetProxyIPandPort(self, targetURL):
    self.GetProxy = False
    if self.currentProxy != '':
      self.FailProxys.append(self.currentProxy)
    self.currentPort = ''
    self.currentProxy = ''
    while True:
      parser_IP = LinksParser_IP()
      parser_port = LinksParser_port()
      currentURL = self.prefix+str(self.page)
      print currentURL
      content = self.http.request('GET', currentURL)
      parser_IP.feed(content.data)
      parser_port.feed(content.data)
      if len(parser_IP.data) == 0:
        break
      for i in range((len(parser_IP.data)-1), 0, -1):
        print 'tring '+parser_IP.data[i]+':'+parser_port.data[i]
        if parser_IP.data[i] in self.FailProxys:
          continue
        #print parser_IP.data[i]+':'+parser_port.data[i]
        if self.IsProxyServerAlive(parser_IP.data[i], parser_port.data[i], targetURL):
          self.currentProxy = parser_IP.data[i]
          self.currentPort = parser_port.data[i]
          self.GetProxy = True
          break
        else:
          self.FailProxys.append(parser_IP.data[i])
      parser_IP.close()
      parser_port.close()
      if self.GetProxy:
        #print self.currentProxy+':'+self.currentProt
        break
      self.page+=1

def RemoveStringSpace(inputSTR):
  items = inputSTR.strip().split(' ')
  outputSTR = ''
  for i in range(0, len(items), 1):
    outputSTR += items[i]
  return outputSTR

#class SSHConnection():
#def check_ssh(ip, user, key_file, initial_wait=0, interval=0, retries=1):

#Download partial from sohu TV and combine
class DownloadVideoViaSSH():
  def __init__(self, ServerIP, User, PassWord):
    self.ssh = paramiko.SSHClient()
    print ServerIP+','+User+','+PassWord
    self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    paramiko.util.log_to_file('paramiko.log')
    #sleep(initial_wait)
    for i in range(2):
      try:
        self.ssh.connect(ServerIP, username=User, password=PassWord)
        self.sftp = self.ssh.open_sftp()
        break
      except (paramiko.BadHostKeyException, paramiko.AuthenticationException, 
              paramiko.SSHException) as e:
        print e
        #sleep(interval)

  def DownloadVideo_local(self, inputURL, IP, Port, ServerIP, User, PassWord):
    #(http_proxy=http://218.60.56.95:8080 ./youtube-dl -g --get-filename http://tv.sohu.com/20140923/n404564864.shtml)
    print 'Start of getting URL'
    partial_element = inputURL.split('tv.sohu.com/')
    partial_element[1]=partial_element[1].replace('/', '_')
    cmd_to_execute = '(http_proxy=http://'+IP+':'+Port+' ./youtube-dl -g --get-filename '+inputURL+') > source/'+partial_element[1]+'.txt'
    os.system(cmd_to_execute)
    print 'End of getting URL'
    with open('source/'+partial_element[1]+'.txt') as current_file:
      partial_array = current_file.readlines()
    GetVideoName = GetVideoFilename()
    GetVideoName.GetVideoTitle(inputURL)
    cmd_to_execute = 'mkdir Download/'+GetVideoName.filename
    os.system(cmd_to_execute)
    if len(partial_array) == 0:
      return True
    for i in range(0, (len(partial_array)-1), 1):
      if i%2 == 1:
        partial_element = partial_array[i].split('-')
        partial_name = GetVideoName.filename+partial_element[1]
        partial_name = partial_name.replace('\n', '')
        print partial_name+'/'+partial_url
        cmd_to_execute = 'nohup wget -O Download/'+GetVideoName.filename+'/'+partial_name+' '+partial_url+' --proxy=on -c -e "http_proxy=http://'+IP+':'+Port+'" >/dev/null &'
        os.system(cmd_to_execute)
      else:
        partial_url = partial_array[i].replace('\n', '')
    #Combine video
    #require: sudo apt-get install mencoder
    #mencoder -ovc copy -oac mp3lame -idx -o out.mp4 *.mp4
    partial_element = partial_name.split('.')
    cmd_to_execute = 'nohup mencoder -ovc copy -oac mp3lame -idx -o Download/Finish/'+GetVideoName.filename+'.'+partial_element[(len(partial_element)-1)]+' Download/'+GetVideoName.filename+'/'+GetVideoName.filename+'*.'+partial_element[(len(partial_element)-1)]+' >/dev/null &'
    os.system(cmd_to_execute)
    return False

  #Download partial from sohu TV and combine (SSH download)
  #ssh = paramiko.SSHClient()
  #print ServerIP+','+User+','+PassWord
  #ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  #ssh.connect(ServerIP, username=User, password=PassWord)
  #ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd_to_execute) 
  def DownloadVideo(self, inputURL, IP, Port , videodir):
    #(http_proxy=http://218.60.56.95:8080 ./youtube-dl -g --get-filename http://tv.sohu.com/20140923/n404564864.shtml)
    print 'Start of getting URL'
    partial_element = inputURL.split('tv.sohu.com/')
    partial_element[1]=partial_element[1].replace('/', '_')
    cmd_to_execute = '(http_proxy=http://'+IP+':'+Port+' ./youtube-dl -g --get-filename '+inputURL+') > source/'+partial_element[1]+'.txt'
    os.system(cmd_to_execute) 
    print 'End of getting URL'
    with open('source/'+partial_element[1]+'.txt') as current_file:
      partial_array = current_file.readlines()
    GetVideoName = GetVideoFilename()
    GetVideoName.GetVideoTitle(inputURL)
    cmd_to_execute = 'mkdir Downloads/'+GetVideoName.filename
    ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd_to_execute) 
    if len(partial_array) == 0:
      return True
    print 'Start download'
    print len(partial_array)
    for i in range(0, (len(partial_array)-1), 1):
      if i%2 == 1:
        partial_element = partial_array[i].split('-')
        partial_name = GetVideoName.filename+partial_element[1]
        partial_name = partial_name.replace('\n', '')
        print partial_name
        videosize = 0
        retrytimer = 0
        while videosize == 0:
          try:
            retrytimer += 1
            cmd_to_execute = 'wget -O Downloads/'+GetVideoName.filename+'/'+partial_name+' '+partial_url+' --proxy=on -c -e "http_proxy=http://'+IP+':'+Port+'"'
            #cmd_to_execute = 'curl -O Downloads/'+GetVideoName.filename+'/'+partial_name+' '+partial_url+' -c -e "http_proxy=http://'+IP+':'+Port+'"'
            #print cmd_to_execute
            print cmd_to_execute
            ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd_to_execute) 
            #time.sleep(80)
            # Wait for the command to terminate
            time.sleep(1)
            while not ssh_stdout.channel.exit_status_ready():
                # Only print data if there is data to read in the channel
                if ssh_stdout.channel.recv_ready():
                    # Print data from stdout
                    print ssh_stdout.channel.recv(1024)
            #      print 'partial ok'
            #      break
            #print ssh_stdout.read()
            #print ssh_stderr.read()
            print 'Downloads/'+GetVideoName.filename+'/'+partial_name
            videoInfo = self.sftp.stat('Downloads/'+GetVideoName.filename+'/'+partial_name)
            videosize = videoInfo.st_size
            print videosize
            if videosize == 0:
              print 'Empty video, wget retrying'
            if retrytimer == 3:
              print 'Retry fail, get another proxy server'
              return True
          except Exception, detail:
            print "ERROR:", detail
            videosize = 0
            return True
      else:
        partial_url = partial_array[i].replace('\n', '')
    print 'End download'
    #Combine video
    #require: sudo apt-get install mencoder
    #mencoder -ovc copy -oac mp3lame -idx -o out.mp4 *.mp4
    cmd_to_execute = 'mkdir Downloads/Finish'
    ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd_to_execute) 
    print cmd_to_execute
    time.sleep(1)
    cmd_to_execute = 'mkdir Downloads/Finish/'+videodir
    ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd_to_execute) 
    print cmd_to_execute
    time.sleep(1)
    partial_element = partial_name.split('.')
    cmd_to_execute = 'mencoder -ovc copy -oac mp3lame -idx -o Downloads/Finish/'+videodir+'/'+GetVideoName.filename+'.'+partial_element[(len(partial_element)-1)]+' Downloads/'+GetVideoName.filename+'/'+GetVideoName.filename+'*.'+partial_element[(len(partial_element)-1)]
    #print cmd_to_execute
    ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd_to_execute) 
    #time.sleep(100)
    # Wait for the command to terminate
    time.sleep(1)
    while not ssh_stdout.channel.exit_status_ready():
      # Only print data if there is data to read in the channel
      if ssh_stdout.channel.recv_ready():
          # Print data from stdout
          print ssh_stdout.channel.recv(1024), 
    #      break
    cmd_to_execute = 'rm Downloads/'+GetVideoName.filename+' -rf'
    ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd_to_execute)
    #while not ssh_stdout.channel.exit_status_ready():
    #        if ssh_stdout.channel.recv_ready():
    #          break
    cmd_to_execute = 'rm source/'+partial_element[1]+'.txt'
    ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd_to_execute)
    #while not ssh_stdout.channel.exit_status_ready():
            # Only print data if there is data to read in the channel
    #        if ssh_stdout.channel.recv_ready():
    #          break
    time.sleep(1)
    return False


#multi-thread
class Job:    
  def __init__(self, threadname, server, username, password, sourcefile): #sourcefile=source/sohuURL.txt
    self.name = threadname    
    self.server =  server
    self.username = username
    self.password = password
    self.sourcefile = sourcefile
    self.videodir = ''
  def do(self):    
    #time.sleep(2)    
    with open(self.sourcefile) as current_file:
      sohuURL = current_file.readlines()
    ssh=DownloadVideoViaSSH(self.server, self.username, self.password)
    ProxyServer = GetAvailableProxyServer()
    proxyOK = False
    for j in range(0, (len(sohuURL)-1), 1):
      sohuURL[j] = sohuURL[j].replace('\n', '')
      if "#" not in sohuURL[j]:
        retry = True
        while retry:
          if proxyOK == False:
            print 'Start of getting proxy'
            ProxyServer.GetProxyIPandPort(sohuURL[j])
          print ProxyServer.currentProxy+':'+ProxyServer.currentPort
          print 'End of getting proxy'
          if ProxyServer.currentProxy != '':
            retry = ssh.DownloadVideo(sohuURL[j], ProxyServer.currentProxy, ProxyServer.currentPort, self.videodir)
            if retry == False:
              proxyOK = True
            else:
              proxyOK = False
      else:
        self.videodir = sohuURL[j].replace('#', '')
        print self.videodir 
        continue
    print("\t[Info] Job({0}) is done!".format(self.name)) 


#Main
reload(sys)
sys.setdefaultencoding('utf8')
#sohuURL = []
#sohuURL.append('http://tv.sohu.com/20141022/n405361376.shtml')
#sohuURL.append('http://tv.sohu.com/20140620/n401112867.shtml')
sohuURLFileList = []
sohuURLFileList.append('source/sohuURL_1.txt')
sohuURLFileList.append('source/sohuURL_2.txt')
ServerList = []
UserNameList = []
PassWordList = []
ServerList.append('192.168.0.102')
UserNameList.append('sherylhsu')
PassWordList.append('vm6vm0qo4')
ServerList.append('192.168.0.108')
UserNameList.append('alex')
PassWordList.append('vuot9442')

que = Queue()
for i in range(2):  
  que.put(Job(str(i+1), ServerList[i], UserNameList[i], PassWordList[i], sohuURLFileList[i]))
  
print("\t[Info] Queue size={0}...".format(que.qsize()))  
  
def doJob(*args):  
  queue = args[0]  
  while queue.qsize() > 0:  
    job = queue.get()  
    job.do()  
  
# Open three threads  
thd1 = threading.Thread(target=doJob, name='Thd1', args=(que,))  
thd2 = threading.Thread(target=doJob, name='Thd2', args=(que,))  
thd3 = threading.Thread(target=doJob, name='Thd3', args=(que,))  
  
# Start activity to digest queue.  
st = datetime.datetime.now()  
thd1.start()  
thd2.start()  
thd3.start()  
  
# Wait for all threads to terminate.  
while thd1.is_alive() or thd2.is_alive() or thd3.is_alive():  
  time.sleep(1)    
  
td = datetime.datetime.now() - st  
print("\t[Info] Spending time={0}!".format(td)) 





