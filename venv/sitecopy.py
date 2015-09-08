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

#multi-thread
class Job:
     def __init__(self, threadname, server, username, password, sourcefile):
             self.name = threadname
             self.server =  server
             self.username = username
             self.password = password
             self.sourcefile = sourcefile
     def do(self):
             #time.sleep(2)

             print("\t[Info] Job({0}) is done!".format(self.name))

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
    except urllib3.HTTPError, e:
        print 'Error code: ', e.code
        return e.code
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
        if parser_IP.data[i] in self.FailProxys:
          continue
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
    #sleep(initial_wait)
    for i in range(2):
      try:
        self.ssh.connect(ServerIP, username=User, password=PassWord)
        break
      except (BadHostKeyException, AuthenticationException,
              SSHException, socket.error) as e:
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
  def DownloadVideotest(self, inputURL, IP, Port):
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
    for i in range(0, (len(partial_array)-1), 1):
      if i%2 == 1:
        partial_element = partial_array[i].split('-')
        partial_name = GetVideoName.filename+partial_element[1]
        partial_name = partial_name.replace('\n', '')
        cmd_to_execute = 'wget -O Downloads/'+GetVideoName.filename+'/'+partial_name+' '+partial_url+' --proxy=on -c -e "http_proxy=http://'+IP+':'+Port+'"'
        #cmd_to_execute = 'curl -O Downloads/'+GetVideoName.filename+'/'+partial_name+' '+partial_url+' -c -e "http_proxy=http://'+IP+':'+Port+'"'
        print cmd_to_execute
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd_to_execute)
        print ssh_stdout.read()
        print ssh_stderr.read()
      else:
        partial_url = partial_array[i].replace('\n', '')
    print 'End download'
    #Combine video
    #require: sudo apt-get install mencoder
    #mencoder -ovc copy -oac mp3lame -idx -o out.mp4 *.mp4
    cmd_to_execute = 'mkdir Downloads/Finish'
    ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd_to_execute)
    partial_element = partial_name.split('.')
    cmd_to_execute = 'mencoder -ovc copy -oac mp3lame -idx -o Downloads/Finish/'+GetVideoName.filename+'.'+partial_element[(len(partial_element)-1)]+' Downloads/'+GetVideoName.filename+'/'+GetVideoName.filename+'*.'+partial_element[(len(partial_element)-1)]
    #print cmd_to_execute
    ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd_to_execute)
    time.sleep(30)
    cmd_to_execute = 'rm Downloads/'+GetVideoName.filename+' -rf'
    ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd_to_execute)
    cmd_to_execute = 'source/'+partial_element[1]+'.txt'
    ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd_to_execute)
    time.sleep(3)
    return False

#Main
reload(sys)
sys.setdefaultencoding('utf8')
with open('source/sohuURL.txt') as current_file:
      sohuURL = current_file.readlines()
#sohuURL = []
#sohuURL.append('http://tv.sohu.com/20141022/n405361376.shtml')
#sohuURL.append('http://tv.sohu.com/20140620/n401112867.shtml')
ServerList = []
UserNameList = []
PassWordList = []
#ServerList.append('192.168.0.246')
#UserNameList.append('SherylHsu')
#PassWordList.append('Vm6vm0qo47886')
ServerList.append('192.168.0.108')
UserNameList.append('alex')
PassWordList.append('vuot9442')
DownloadLimit = 30
proxyOK = False
ssh=DownloadVideoViaSSH(ServerList[0], UserNameList[0], PassWordList[0])
ProxyServer = GetAvailableProxyServer()
for j in range(0, (len(sohuURL)-1), 1):
  sohuURL[j] = sohuURL[j].replace('\n', '')
  retry = True
  while retry:
    if proxyOK == False:
      ProxyServer.GetProxyIPandPort(sohuURL[j])
    print ProxyServer.currentProxy+':'+ProxyServer.currentPort
    if ProxyServer.currentProxy != '':
      retry = ssh.DownloadVideotest(sohuURL[j], ProxyServer.currentProxy, ProxyServer.currentPort)
      if retry == False:
        proxyOK = True
      else:
        proxyOK = False





