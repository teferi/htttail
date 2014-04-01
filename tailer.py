import os.path
import select

__all__ = ['Tailer']

has_inotify, has_kqueue = True, True

try:
    from pyinotify import WatchManager, Notifier, ProcessEvent, IN_MODIFY
except ImportError:
    has_inotify = False

try:
    from select import kqueue, kevent
except ImportError:
    has_kqueue = False

if not any([has_inotify, has_kqueue]):
    raise ImportError("This module needs either inotyfy or kqueue support")


class DoesNotExist(Exception):
    pass


class BaseTailer(object):
    def __init__(self, f, callback=None, timeout=None):
        self.file = f
        self.callback = callback
        self.timeout = timeout

    def __iter__(self):
        return self.check_forever()

    def check_forever(self):
        while True:
            yield self.check_once()

    def check_once(self):
        """
        Should be implemented in a subclass
        """
        raise NotImplemented


class InoTailer(BaseTailer):
    def __init__(self, file, should_read=True, callback=None, timeout=None):
        super(InoTailer, self).__init__(file, callback, timeout)
        if self.timeout:
            self.timeout *= 1000

        self._should_read_myself = should_read
        if not hasattr(self.file, 'fileno') and self._should_read_myself:
            if not os.path.exists(self.file):
                raise DoesNotExist("Can't find %s. It does not seem to exist" % self.file)
            self.file = open(self.file)

        class Watcher(ProcessEvent):
            pass
        if callable(self.callback):
            setattr(Watcher, 'process_IN_MODIFY', self.callback)
        mask = IN_MODIFY
        self.wm = WatchManager()
        self.notifier = Notifier(self.wm, Watcher())
        self.wm.add_watch(self.file.name, mask,)

        self._initial_lines = None
        if not self.at_end():
            if self._should_read_myself:
                self._initial_lines = self.file.read().rstrip('\n').split('\n')
            else:
                self._initial_lines = True

    def at_end(self):
        return self.file.tell() == os.path.getsize(self.file.name)

    def check_once(self):
        if self._initial_lines:
            self._initial_lines, result = None, self._initial_lines
            return result
        self.notifier.process_events()
        if self.notifier.check_events(self.timeout):
            self.notifier.read_events()
            if self._should_read_myself:
                result = self.file.read().rstrip('\n').split('\n')
                return result
            return True
        return None

    def wait(self, with_timeout=False):
        timeout = None
        if with_timeout:
            timeout = self.timeout
        self.notifier.check_events(timeout)


class KQTailer(BaseTailer):

    def __init__(self, file, callback=None, timeout=None):
        super(KQTailer, self).__init__(file, callback, timeout)

        self._should_read_myself = False
        if not hasattr(self.file, 'fileno'):
            self._should_read_myself = True
            if not os.path.exists(self.file):
                raise DoesNotExist("Can't find %s. It does not seem to exist" % self.file)
            self.file = open(self.file)
        self.kq = kqueue()
        self.ke = kevent(self.file, filter=select.KQ_FILTER_READ,
                         flags=select.KQ_EV_ADD)

    def check_once(self):
        klist = self.kq.control((self.ke,), 1, self.timeout)
        if klist:
            if self._should_read_myself:
                result = self.file.read().rstrip('\n').split('\n')
                if callable(self.callback):
                    map(self.callback, result)
                return result
            return True
        return None

    def wait(self, with_timeout=False):
        timeout = None
        if with_timeout:
            timeout = self.timeout
        self.kq.control((self.ke,), 1, timeout)

if has_inotify:
    Tailer = InoTailer
elif has_kqueue:
    Tailer = KQTailer
