import toml

class Config(dict):

    def __init__(self, *arg, filename=None):
        super().__init__(*arg)
        if filename is not None:
            self.load(filename)

    def load(self, filename):
        with open(filename, 'r') as f:
             data = toml.load(f)
        self.update(data)

    def print(self):
        print(toml.dumps(self))

    def from_dict(self,d):
        self.update(d)

    def to_dict(self):
        return dict(self)







