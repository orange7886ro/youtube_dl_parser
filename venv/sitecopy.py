import urllib3
import os
import time
from HTMLParser import HTMLParser

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

#Get proxy server addr
class GetAvailableProxyServer():
  def __init__(self):
    self.currentPort = ''
    self.currentProxy = ''
    self.GetProxy = False
    self.prefix = 'http://www.cooleasy.com/?act=list&port=&type=&country=China&page='
    self.page = 1
    self.http = urllib3.PoolManager()
  #Is server alive?
  def IsProxyServerAlive(self, IP, Port):
    response = os.system("ping -c 2 "+IP+' -p '+ Port)
    if response == 0:
      print 'Trying '+IP+':'+Port+' Success'
      return True
    else:
      #print 'Trying '+IP+':'+Port+' Fail'
      return False

  def GetProxyIPandPort(self):
    self.GetProxy = False
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
        if self.IsProxyServerAlive(parser_IP.data[i], parser_port.data[i]):
          self.currentProxy = parser_IP.data[i]
          self.currentPort = parser_port.data[i]
          self.GetProxy = True
          break
      parser_IP.close()
      parser_port.close()
      if self.GetProxy:
        #print self.currentProxy+':'+self.currentProt
        break
      self.page+=1


#Download partial from sohu TV
def DownloadVideo(inputURL, IP, Port):
  #(http_proxy=http://218.60.56.95:8080 ./youtube-dl -g --get-filename http://tv.sohu.com/20140923/n404564864.shtml)
  print 'Start of getting URL : (http_proxy=http://'+IP+':'+Port+' ./youtube-dl -g --get-filename '+inputURL+') > source/source.txt'
  #os.system('(http_proxy=http://'+IP+':'+Port+' ./youtube-dl -g --get-filename '+inputURL+') > source/source.txt')
  print 'End of getting URL'
  with open('source/source.txt') as current_file:
    partial_array = current_file.readlines()
  print len(partial_array)
  for i in range(0, (len(partial_array)-1), 1):
    if i%2 == 1:
      partial_name = partial_array[i]
      print type(partial_name)
      print partial_name+'/'+partial_url
      print 'Start download '+str(i)+'/'+str(len(partial_array))+':wget -o '+str(partial_name)+' '+str(partial_url)
      #result = os.system('wget -o '+partial_name+' '+partial_url)
      print 'End of download'
    else:
      partial_url = partial_array[i]
  return result

#Main
sohuURL = []
sohuURL.append('http://tv.sohu.com/20130914/n386591920.shtml')
for j in range(0, (len(sohuURL)), 1):
  ProxyServer = GetAvailableProxyServer()
  ProxyServer.GetProxyIPandPort()
  print ProxyServer.currentProxy+':'+ProxyServer.currentPort
  if ProxyServer.currentProxy != '':
    result = DownloadVideo(sohuURL[j], ProxyServer.currentProxy, ProxyServer.currentPort)
    print result





