from twisted.application import service, strports
from twisted.internet import reactor
from twisted.internet import reactor
from twisted.web import server, resource, static
from twisted.web.server import NOT_DONE_YET

from jinja2 import Environment, FileSystemLoader, Markup

from datetime import datetime
from dateutil.parser import parse as parse_date

from threading import Thread, Lock, Event

from tailer import Tailer

import os.path
import time

class LoggerThread(Thread):
    def __init__(self, f, timeout=None):
        super(LoggerThread, self).__init__()

        self.tailer = Tailer(f, timeout)
        self.elock = Lock()
        self.rlock = Lock()

        self.go = True
        self.loglines = []
        self.event = Event()

    def run(self):
        for lines in self.tailer:
            if lines is None:
                continue
            with self.rlock:
                lines = lines[-50:]
                lines = [(parse_date(line[:30], fuzzy=True, ignoretz=True), line) for line in lines]
                self.loglines = self.loglines[len(lines):] + lines
            with self.elock:
                self.event.set()
                self.event.clear()

    def add_event(self):
        with self.elock:
            return self.event

    def lines(self):
        with self.rlock:
            lines = reversed(self.loglines)
        return lines

def _fmt_line(line):
    return line[1][:30], line[1][30:]

class Root(resource.Resource):
    isLeaf = False
    def render_GET(self, request):
        if not logger.isAlive():
            logger.start()
        lines = logger.lines()

        templ = env.get_template('index.html')
        return str(templ.render( {'items':map(_fmt_line, (logger.lines()))} ))

    def getChild(self, name, request):
        if name == '':
            return self
        return resource.Resource.getChild(self, name, request)

class UpdaterThread(Thread):
    def __init__(self, request):
        super(UpdaterThread, self).__init__()
        self.request = request

    def run(self):
        logger.add_event().wait()

        date = parse_date(self.request.args['date'][0][:30], fuzzy=True, ignoretz=True)
        lines = filter(lambda x: x[0]>date, logger.lines())

        templ = env.get_template('part.html')
        self.request.write(str(templ.render( {'items':map(_fmt_line, (reversed(lines)))} )))
        self.request.finish()

class Upd(resource.Resource):
    isLeaf = True
    def render_GET(self, request):
        u = UpdaterThread(request,)
        u.daemon = True
        u.start()
        return NOT_DONE_YET

root = Root()

root.putChild('js', static.File(os.path.abspath("js")))
root.putChild('upd', Upd())

env = Environment(loader=FileSystemLoader('templates/'))
filename = "log.log"
logger = LoggerThread(filename, 10)
logger.daemon = False
#logger.start()

site = server.Site(root)

#application = service.Application('Pansonic twister')
#server = strports.service('tcp:3000', site)
#server.setServiceParent(application)

reactor.listenTCP(3001, site)
reactor.run()
