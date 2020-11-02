import paramiko
from os.path import expanduser


class SSHDeskHandler:
    def __init__(self):
        pass

    def set_height(self, height):
        cmd_to_execute = "curl localhost:9987/" + str(height)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            "raspberrypi.local",
            username="pi",
            key_filename=expanduser("~") + "/.ssh/id_rsa.pub",
        )
        client.exec_command(cmd_to_execute)

    def toggle(self):
        self.set_height("toggle")

    def up(self):
        self.set_height("up")

    def down(self):
        self.set_height("down")
