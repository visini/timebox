import rumps
import time
import subprocess
import shlex
import sqlite3
import os

from ssh_desk_handler import SSHDeskHandler

SEC_TO_MIN = 60

def timez():
    return time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime())


def get_things_today_tasks(index=0, complete_task=False):
    conn = sqlite3.connect(
        os.path.expanduser(
            "~/Library/Group Containers/JLMPQHK86H.com.culturedcode.ThingsMac/Things Database.thingsdatabase/main.sqlite"
        )
    )
    sql = (
        "SELECT\n"
        "            TAG.title,\n"
        "            TASK.title,\n"
        '            "things:///show?id=" || TASK.uuid\n'
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
        "            LIMIT 100"
    )
    tasks = []
    try:
        for row in conn.execute(sql):
            tasks.append(row)
    except:
        pass
    conn.close()
    return tasks


def process_tasks(list_of_tasks):
    processed_tasks = {}

    for task_tuple in list_of_tasks:
        if task_tuple[0][-3:] == "min":
            processed_tasks[task_tuple[1]] = (
                int(task_tuple[0][:-3]),
                task_tuple[2],
            )

    return processed_tasks


def hour_formatter(minutes):
    if minutes // 60 > 0:
        if spare_min := minutes % 60:
            return f"{minutes // 60}h and {spare_min}min of work today!"
        else:
            return f"{minutes // 60}h of work today!"
    else:
        return f"{minutes}min of work today!"


class TimerApp(object):
    def toggle_button(self, sender):
        sender.state = not sender.state

    def __init__(self, timer_interval=1):
        self.timer = rumps.Timer(self.on_tick, 1)
        self.timer.stop()  # timer running when initialized
        self.timer.count = 0
        self.app = rumps.App("Timebox", "🥊")
        self.desk_handler = SSHDeskHandler()
        self.interval = SEC_TO_MIN
        self.current_things_task_url = None
        self.start_pause_button = rumps.MenuItem(
            title="Start Timer",
            callback=lambda _: self.start_timer(_, self.interval),
            key="s",
        )
        self.toggle_sit_stand_button = rumps.MenuItem(
            title="Toggle Sit/Stand",
            callback=lambda sender: self.toggle_button(sender),
            key="t",
        )
        self.toggle_sit_stand_button.state = True
        self.stop_button = rumps.MenuItem(title="Stop Timer", callback=None)
        self.buttons = {}
        self.buttons_callback = {}
        for i in [5, 10, 15, 20, 25]:
            title = str(i) + " Minutes"
            callback = lambda _, j=i: self.set_mins(_, j, None)
            self.buttons["btn_" + str(i)] = rumps.MenuItem(
                title=title, callback=callback
            )
            self.buttons_callback[title] = callback

        self.sync_button = rumps.MenuItem(
            title="Sync", callback=lambda _: self.sync_data(), key="r"
        )

        self.sum_menu_item = rumps.MenuItem(
            title="sum_total_time", callback=None
        )

        self.app.menu = [
            self.start_pause_button,
            self.sync_button,
            self.toggle_sit_stand_button,
            None,
            self.sum_menu_item,
            # *self.things_buttons.values(),
            None,
            *self.buttons.values(),
            None,
            self.stop_button,
        ]

        self.sync_data()

    def sync_data(self):

        for key, btn in self.buttons.items():
            btn.set_callback(self.buttons_callback[btn.title])

        self.things_tasks = get_things_today_tasks()

        self.things_processed_tasks = process_tasks(self.things_tasks)

        self.sum_of_tasks_scheduled = sum(
            [x[0] for x in self.things_processed_tasks.values()]
        )

        self.app.menu[
            "sum_total_time"
        ].title = f"{hour_formatter(self.sum_of_tasks_scheduled)}"

        if hasattr(self, "things_buttons"):
            prev_things_buttons = self.things_buttons
            for title in prev_things_buttons.keys():
                del self.app.menu[prev_things_buttons[title].title]

        self.things_buttons = {
            f"{title} → {time}min": rumps.MenuItem(
                title=f"{title} → {time}min",
                callback=lambda _, j=time, k=task_url: self.set_mins(_, j, k),
            )
            for title, (time, task_url) in self.things_processed_tasks.items()
        }

        for title, menu_item in reversed(self.things_buttons.items()):
            self.app.menu.insert_after("sum_total_time", menu_item)

    def run(self):
        self.app.menu[
            "sum_total_time"
        ].title = f"{hour_formatter(self.sum_of_tasks_scheduled)}"
        self.app.run()

    def set_mins(self, sender, interval, task_url):
        for btn in [*self.things_buttons.values(), *self.buttons.values()]:
            if sender.title == btn.title:
                self.interval = interval * SEC_TO_MIN
                cleaned_title = " ".join(sender.title.split()[:-2])
                if task_url is not None:
                    self.menu_title = " → " + cleaned_title
                    self.current_things_task_url = task_url
                else:
                    self.menu_title = ""
                btn.state = True
            elif sender.title != btn.title:
                btn.state = False

    def start_timer(self, sender, interval):
        for btn in [*self.things_buttons.values(), *self.buttons.values()]:
            btn.set_callback(None)

        if sender.title.lower().startswith(("start", "continue")):

            if sender.title == "Start Timer":
                # reset timer & set stop time
                self.timer.count = 0
                self.timer.end = interval

            # change title of MenuItem from 'Start timer' to 'Pause timer'
            sender.title = "Pause Timer"

            # lift off! start the timer
            self.timer.start()
        else:  # 'Pause Timer'
            sender.title = "Continue Timer"
            self.timer.stop()

    def on_tick(self, sender):
        time_left = sender.end - sender.count
        mins = time_left // 60 if time_left >= 0 else time_left // 60 + 1
        secs = time_left % 60 if time_left >= 0 else (-1 * time_left) % 60
        if mins == 0 and time_left < 0:
            rumps.notification(
                title="Timebox",
                subtitle="Time is up! Take a break :)",
                message="",
            )
            if self.current_things_task_url is not None:
                # print("opening url", self.current_things_task_url)
                subprocess.call(
                    shlex.split("open '" + self.current_things_task_url + "'")
                )
                self.current_things_task_url = None
            if self.toggle_sit_stand_button.state == True:
                self.desk_handler.toggle()            
            self.stop_timer(sender)
            self.stop_button.set_callback(None)
            self.sync_data()
        else:
            self.stop_button.set_callback(self.stop_timer)
            self.app.title = "{:2d}:{:02d} {}".format(
                mins, secs, getattr(self, "menu_title", "")
            )
        sender.count += 1

    def stop_timer(self, sender=None):
        self.timer.stop()
        self.timer.count = 0
        self.app.title = "🥊"
        self.stop_button.set_callback(None)

        for key, btn in self.buttons.items():
            btn.set_callback(self.buttons_callback[btn.title])

        for (title, btn) in self.things_buttons.items():
            btn.set_callback(
                lambda _: self.set_mins(
                    _, self.things_processed_tasks[title], None
                )
            )

        self.start_pause_button.title = "Start Timer"
        self.sync_data()


if __name__ == "__main__":
    app = TimerApp(timer_interval=1)
    app.run()
