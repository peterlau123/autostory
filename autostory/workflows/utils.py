'''
Workflow utils

'''

import logging

class PromptReader:
    def __init__(self,prompt_file):
        self.prompt_file = prompt_file

    def read(self):
        logging.info("Reading Prompt File {}".format(self.prompt_file))
        with open(self.prompt_file) as f:
            return f.read()
