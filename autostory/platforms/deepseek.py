import os


class DeepSeekApi:
    def get_key(self):
        api_key=os.environ['DEEP_SEEK_API_KEY'] # DEEP_SEEK_API_KEY=sk-e9d9c2f2f9a04b3fa2f25188e81e62e1
        return api_key
