import rumps
import time
import copy

try:
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve

rumps.debug_mode(True)


def timez():
    return time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime())


class TimerApp(object):
    def __init__(self, timer_interval=1):
        self.timer = rumps.Timer(self.on_tick, 1)
        self.timer.stop()  # timer running when initialized
        self.timer.count = 0
        self.app = rumps.App("Timebox", "🥊")
        self.start_pause_button = rumps.MenuItem(title='Start timer',
                                                 callback=lambda _: self.start_timer(_, self.interval))
        self.stop_button = rumps.MenuItem(title='Stop timer',
                                          callback=None)
        self.buttons = {}
        self.buttons_callback = {}
        for i in [5, 10, 15, 20, 25]:
            title = str(i) + ' Minutes'
            callback = lambda _, j=i: self.set_mins(_, j)
            self.buttons["btn_" + str(i)] = rumps.MenuItem(title=title, callback=callback)
            self.buttons_callback[title] = callback
        self.buttons["btn_5"].state = True
        self.interval = 5*60
        self.app.menu = [
            self.start_pause_button,
            None,
            *self.buttons.values(),
            None,
            self.stop_button]

    def run(self):
        self.app.run()

    def set_mins(self, sender, interval):
        for key, btn in self.buttons.items():
            if sender.title == btn.title:
                self.interval = interval*60
                btn.state = True
            elif sender.title != btn.title:
                btn.state = False

    def start_timer(self, sender, interval):
        for key, btn in self.buttons.items():
            btn.set_callback(None)

        if sender.title.lower().startswith(("start", "continue")):

            if sender.title == 'Start timer':
                # reset timer & set stop time
                self.timer.count = 0
                self.timer.end = interval

            # change title of MenuItem from 'Start timer' to 'Pause timer'
            sender.title = 'Pause timer'

            # lift off! start the timer
            self.timer.start()
        else:  # 'Pause Timer'
            sender.title = 'Continue timer'
            self.timer.stop()

    def on_tick(self, sender):
        time_left = sender.end - sender.count
        mins = time_left // 60 if time_left >= 0 else time_left // 60 + 1
        secs = time_left % 60 if time_left >= 0 else (-1 * time_left) % 60
        if mins == 0 and time_left < 0:
            rumps.notification(title='Timebox',
                               subtitle='Time is up! Take a break :)',
                               message='')
            self.stop_timer(sender)
            self.stop_button.set_callback(None)
        else:
            self.stop_button.set_callback(self.stop_timer)
            self.app.title = '{:2d}:{:02d}'.format(mins, secs)
        sender.count += 1

    def stop_timer(self, sender=None):
        self.timer.stop()
        self.timer.count = 0
        self.app.title = "🥊"
        self.stop_button.set_callback(None)

        for key, btn in self.buttons.items():
            btn.set_callback(self.buttons_callback[btn.title])

        self.start_pause_button.title = 'Start timer'


if __name__ == '__main__':
    app = TimerApp(timer_interval=1)
    app.run()
