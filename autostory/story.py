from deepseek import DeepSeekApi


class Story:
    def __init__(self, api):
        self.llm_api=api
    def generate(self):
        pass





if __name__ == '__main__':
    story =Story(DeepSeekApi())
