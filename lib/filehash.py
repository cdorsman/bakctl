from lib.transfer import Client
import hashlib


class Filehash:
    """Inner class for actions around filehashes"""
    def calculate_remote_hash(
                        self,
                        host: str = "",
                        port: int = 0,
                        username: str = "",
                        priv_key: str = "",
                        filename: str = "") -> str:
        """Calculate file hash from remote file"""
        ssh = Client(host, port, username, "", priv_key)

        cmd = f'sha256sum {filename}'

        # Calculate hash of file backup on remote host
        buffer = ssh.execute(cmd)

        # Output is in a dirty dictionary. Need to
        # get string by index 0 and split on 3 spaces
        # Store result, a list, in buffer
        buffer = buffer['out'][0].split('  ')

        # List is still dirty. Need to strip the dirt
        # from it. Result is a clean list
        result = [item.strip() for item in buffer][0]

        ssh.close()
        return result

    def calculate_hash(self, filename: str = None) -> hash:
        """
        Function calculating the filehash. With the filehash it is
        possible to check and verify the integrity of a file.
        """

        # Create hash object
        hash_object: object = hashlib.sha256()

        # Open the file in binary mode
        with open(filename, 'rb') as file:
            # Read the entire file content
            file_content = file.read()

            # Update the hash object with the file content
            hash_object.update(file_content)

        # Return the hexadecimal representation of the hash
        return hash_object.hexdigest()

    def verify_hash(self,
                    filehash_src: str = "",
                    filehash_dest: str = "") -> bool:
        """
        Function for checking src and dest file hashes
        """
        if filehash_src != filehash_dest:
            return False
        return True
