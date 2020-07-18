"""
Used for managing code execution by one user on the behalf of another
For example: root creating a file in Jared's home directory but Jared is still the sole owner of the file
We probably should instantiate a global sudo_execute instead of re running it everytime in each function it's used in
^ This is going to be put inside the SiteConfig and BuildConfig later so it can be referenced for unit testing
"""

"""
MessageException from Kevin Wortman
"""

import subprocess
import types
import pwd
from functools import partial
import os

class MessageException(Exception):
    def __init__(self, message):
        if not (isinstance(message, str)):
            raise ValueError
        self.message = message

# issue reported when sudo_execute class cannot find a given user
# use for internal API

class UnknownUserException(MessageException):
    def __init__(self, message):
        super().__init__(message)

# issue reported when root code execution is invoked by non privilaged user
# use for internal API

class PrivilageExecutionException(MessageException):
    def __init__(self, message):
        super().__init__(message)

class sudo_execute():
    def __init__(self):
        self.main_user = ""

    def current_user(self) -> str:
        return subprocess.check_output(["whoami"], encoding="utf-8").strip()

    def currently_logged_in(self) -> list:
        return [user for user in subprocess.check_output(["users"], encoding="utf-8").split('\n') if user]

    def set_user(self) -> str:
        logged_in = self.currently_logged_in()
        if(len(logged_in) > 1):
            whoami = None
            while(whoami is None):
                selection = {}
                for index, user in enumerate(logged_in):
                    selection[index] =  user
                    print("[{}] {}".format(index, user))
                whoami = input("Select who you are: ")
                try:
                    whoami = self.main_user = selection[int(whoami)]
                    return whoami
                except KeyError:
                    whoami = None
                    os.system("clear")
                    print(colored("[INFO] Invalid selection, please try again", 'red'))
        self.main_user = logged_in[0]
        return logged_in[0]

    def chuser(self, user_id: int, user_gid: int):
        """
        GOAL: permanently change the user in the context of the running program
        """

        os.setgid(user_gid)
        os.setuid(user_id)

    def check_user(self, user: str):
        try:
            pwd.getpwnam(user)
            return True
        except KeyError:
            return False

    def swap_user(self, user: str):
        if(self.check_user(user)):
            du_records = pwd.getpwnam(user)
        else:
            raise UnknownUserException("Unknown user: {}".format(user))

        du_id, du_gid = du_records.pw_uid, du_records.pw_gid
        self.chuser(du_id, du_gid)

    def run_permanent(self, func: types.FunctionType, current_user: str, desired_user: str):
        """
        GOAL: run commands/functions as another user but permanently changing to that user
        Cannot be run twice in a row if script is originated with sudo
        Only root can set UID and GID back to itself, ultimately making it redundant
        Used primarliy for descalation of privilages, handing back to userspace
        """

        self.swap_user(desired_user)
        try:

            """
            We want to return console output
            """
            return func()

            # return func() if isinstance(func, partial) else func()

        except PermissionError:
            raise PrivilageExecutionException("{} does not have permission to run the command {} as the user {}".format(
                            current_user,
                            command,
                            desired_user
            ))
    

    def run_shell_process_permanent(self, command: str):
        return subprocess.Popen(command.split(), 
                            close_fds=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            encoding="utf-8").communicate()

    def run_soft(self, command: str, desired_user: str):
        command = "sudo -H -u {} bash -c '{}'".format(desired_user, command)
        try:
            out =  subprocess.check_output(command, 
                                            shell=True, 
                                            executable='/bin/bash',
                                            encoding="utf-8").split("\n")

            out = [line for line in out if line]
        except subprocess.CalledProcessError as e:
            if(e.returncode != 129):
                return ""
            raise Exception("Segmentation fault")

        return out
