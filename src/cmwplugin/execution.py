from functools import wraps
#from litp.core.mco_commands import run_mco_command

#SSH_OPTIONS = "-o %s" % " -o ".join([
#    "ServerAliveInterval=60",
#    "ServerAliveCountMax=5",
#    "UserKnownHostsFile=/dev/null",
#    "PubkeyAuthentication=no",
#    "StrictHostKeyChecking=no"])


def patch_callback(callback_function):
    @wraps(callback_function)
    def _install(callback_api, *args, **kwargs):
        return callback_function(callback_api, *args, **kwargs)
    return _install
