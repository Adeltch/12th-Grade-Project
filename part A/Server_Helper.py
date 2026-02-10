__author__ = "Adel Tchernitsky"


RESPONSES_FOLDER = "Response\\"


# File Handling
class file_object:
    def __init__(self, name, file_id, file_length):
        self.name = name
        self.id = file_id
        self.length = file_length
        self.content = b""

    def append_file(self, decoded_data):
        self.content += decoded_data

    def check_if_got_all_file(self):
        return self.length is not None and len(self.content) >= self.length

    def write_file(self):
        """Write collected data to disk"""
        file_path = RESPONSES_FOLDER + self.name
        with open(file_path, "wb") as f:
            f.write(self.content)
        print(f"[+] File written: {file_path}")
