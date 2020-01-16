import rumps
import time
import subprocess
import shlex
import csv
import sqlite3
import os

try:
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve

rumps.debug_mode(True)

SEC_TO_MIN = 1


def timez():
    return time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime())


def get_things_min(index=0, complete_task=False):
    try:
        conn = sqlite3.connect(os.path.expanduser('~/Library/Containers/com.culturedcode.ThingsMac/Data/Library/Application Support/Cultured Code/Things/Things.sqlite3'))
        sql = ("SELECT\n"
               "            TAG.title,\n"
               "            TASK.title,\n"
               "            \"things:///show?id=\" || TASK.uuid\n"
               "            FROM TMTask as TASK\n"
               "            LEFT JOIN TMTaskTag TAGS ON TAGS.tasks = TASK.uuid\n"
               "            LEFT JOIN TMTag TAG ON TAGS.tags = TAG.uuid\n"
               "            LEFT OUTER JOIN TMTask PROJECT ON TASK.project = PROJECT.uuid\n"
               "            LEFT OUTER JOIN TMArea AREA ON TASK.area = AREA.uuid\n"
               "            LEFT OUTER JOIN TMTask HEADING ON TASK.actionGroup = HEADING.uuid\n"
               "            WHERE TASK.trashed = 0 AND TASK.status = 0 AND TASK.type = 0 AND TAG.title IS NOT NULL\n"
               "            AND TASK.start = 1\n"
               "            AND TASK.startdate is NOT NULL\n"
               "            ORDER BY TASK.todayIndex\n"
               "            LIMIT 100")
        tasks = []
        for row in conn.execute(sql):
            tasks.append([*row])
        conn.close()
        task = tasks[index]
        if not complete_task:
            if task[0]:
                return int(task[0].replace("min", ""))*SEC_TO_MIN
        else:
            if task[2]:
                # print("open the following url: ", task[2])
                subprocess.call(shlex.split('open '+task[2]))
    except:
        return 60


class TimerApp(object):
    def __init__(self, timer_interval=1):
        self.timer = rumps.Timer(self.on_tick, 1)
        self.timer.stop()  # timer running when initialized
        self.timer.count = 0
        self.app = rumps.App("Timebox", "🥊")
        self.start_pause_button = rumps.MenuItem(title='Start Timer',
                                                 callback=lambda _: self.start_timer(_, self.interval))
        self.stop_button = rumps.MenuItem(title='Stop Timer',
                                          callback=None)
        self.buttons = {}
        self.buttons_callback = {}
        for i in [5, 10, 15, 20, 25]:
            title = str(i) + ' Minutes'
            callback = lambda _, j=i: self.set_mins(_, j)
            self.buttons["btn_" + str(i)] = rumps.MenuItem(title=title, callback=callback)
            self.buttons_callback[title] = callback
        self.interval = get_things_min()
        self.button_things = rumps.MenuItem(title="Things Interval ("+str(round(self.interval/SEC_TO_MIN))+"min)", callback=lambda _: self.set_things_mins(_, self.interval))
        self.button_things.state = True
        self.app.menu = [
            self.start_pause_button,
            None,
            self.button_things,
            None,
            *self.buttons.values(),
            None,
            self.stop_button]

    def run(self):
        self.app.run()

    def set_things_mins(self, sender, interval):
        self.interval = get_things_min()
        print("self interval is now", self.interval)
        self.button_things.title = "Things Interval (" + str(round(self.interval / SEC_TO_MIN)) + "min)"
        self.set_mins(sender, self.interval)

    def set_mins(self, sender, interval):
        for btn in [self.button_things, *self.buttons.values()]:
            if sender.title == btn.title:
                self.interval = interval*SEC_TO_MIN
                btn.state = True
            elif sender.title != btn.title:
                btn.state = False

    def start_timer(self, sender, interval):
        for btn in [self.button_things, *self.buttons.values()]:
            btn.set_callback(None)

        if sender.title.lower().startswith(("start", "continue")):

            if sender.title == 'Start Timer':
                # reset timer & set stop time
                self.timer.count = 0
                self.timer.end = interval

            # change title of MenuItem from 'Start timer' to 'Pause timer'
            sender.title = 'Pause Timer'

            # lift off! start the timer
            self.timer.start()
        else:  # 'Pause Timer'
            sender.title = 'Continue Timer'
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
        self.button_things.set_callback(lambda _: self.set_things_mins(_, get_things_min()))

        if self.button_things.state:
            self.interval = get_things_min(1)
            self.button_things.title = "Things Interval ("+str(round(self.interval/SEC_TO_MIN))+"min)"
            get_things_min(0, True)

        self.start_pause_button.title = 'Start Timer'


if __name__ == '__main__':
    app = TimerApp(timer_interval=1)
    app.run()
