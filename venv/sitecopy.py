import urllib3
import os
import time
import sys
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
        if self.IsProxyServerAlive(parser_IP.data[i], parser_port.data[i], targetURL):
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

def RemoveStringSpace(inputSTR):
  items = inputSTR.strip().split(' ')
  outputSTR = ''
  for i in range(0, len(items), 1):
    outputSTR += items[i]
  return outputSTR

#Download partial from sohu TV
def DownloadVideo(inputURL, IP, Port):
  #(http_proxy=http://218.60.56.95:8080 ./youtube-dl -g --get-filename http://tv.sohu.com/20140923/n404564864.shtml)
  print 'Start of getting URL : (http_proxy=http://'+IP+':'+Port+' ./youtube-dl -g --get-filename '+inputURL+') > source/source.txt'
  os.system('(http_proxy=http://'+IP+':'+Port+' ./youtube-dl -g --get-filename '+inputURL+') > source/source.txt')
  print 'End of getting URL'
  with open('source/source.txt') as current_file:
    partial_array = current_file.readlines()
  GetVideoName = GetVideoFilename()
  GetVideoName.GetVideoTitle(inputURL)
  for i in range(0, (len(partial_array)-1), 1):
    if i%2 == 1:
      partial_element = partial_array[i].split('-')
      partial_name = GetVideoName.filename+partial_element[1]
      partial_name = partial_name.replace('\n', '')
      print partial_name+'/'+partial_url
      print 'wget '+str(partial_url)+' --proxy=on -P ../Download -O '+str(partial_name)+' -c -e "http_proxy=http://'+str(IP)+':'+str(Port)+'"'
      result = os.system('wget '+partial_url+' --proxy=on -P ../Download -O '+partial_name+' -c -e "http_proxy=http://'+IP+':'+Port+'"')
    else:
      partial_url = partial_array[i].replace('\n', '')
  return result

#Main
reload(sys)
sys.setdefaultencoding('utf8')
sohuURL = []
sohuURL.append('http://tv.sohu.com/20140301/n395872561.shtml')
for j in range(0, (len(sohuURL)), 1):
  ProxyServer = GetAvailableProxyServer()
  ProxyServer.GetProxyIPandPort(sohuURL[j])
  print ProxyServer.currentProxy+':'+ProxyServer.currentPort
  if ProxyServer.currentProxy != '':
    result = DownloadVideo(sohuURL[j], ProxyServer.currentProxy, ProxyServer.currentPort)
    print result
  break





