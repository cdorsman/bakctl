import paramiko
from lib.logging import logger



class Client:
    "A wrapper of paramiko.SSHClient"
    TIMEOUT = 120

    def __init__(self,
                 host,
                 port,
                 username,
                 password,
                 key=None,
                 passphrase=None):
        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(
                                paramiko.AutoAddPolicy()
                                )
        # Load private key is provided.
        if key is not None:
            key = paramiko.Ed25519Key\
                            .from_private_key_file(key)

        # .from_private_key(StringIO(key),
        try:
            self.client.connect(
                            host,
                            port,
                            username=username,
                            password=password,
                            pkey=key,
                            timeout=self.TIMEOUT)

            transport = self.client.get_transport()
            transport.default_max_packet_size = 100000000
            transport.default_window_size = 100000000

            if self.client is None:
                logger.error("Cannot create SSH-connection")
                raise("No connection to %s", host)

        except SSHException as ssh_err:
            logger.error("Connection failed %s", ssh_err)
            logger.info("Exitting")
            exit(1)

    # Close SSH-connection
    def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None

    # execute command through SSH connection
    def execute(self, command, sudo=False) -> dict:
        feed_password = False
        # execute command with sudo if sudo is true
        # and user is not root and password is not empty
        if sudo and self.username != "root":
            command = "sudo -S -p '' %s" % command
            feed_password = self.password is not None\
                and len(self.password) > 0
        # Capture output, stderr and stdin.
        stdin, stdout, stderr = self.client.exec_command(command)
        # Enter password to sudo
        if feed_password:
            stdin.write(self.password + "\n")
            stdin.flush()
        # return results and return value from execution
        return {'out': stdout.readlines(),
                'err': stderr.readlines(),
                'retval': stdout.channel.recv_exit_status()}

    def put(self, filename, destination) -> None:
        if self.client is not None:
            sftp = self.client.open_sftp()
            sftp.put(filename, destination)
            self.client.close()
        else:
            logger.error("Cannot create SSH-connection")
            raise paramiko.SSHException("Not connected")
