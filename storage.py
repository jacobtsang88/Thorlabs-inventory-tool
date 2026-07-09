import json


class Storage:


    def save(self, data, filename):

        with open(filename,"w") as f:
            json.dump(
                data,
                f,
                indent=4
            )


    def load(self, filename):

        with open(filename) as f:
            return json.load(f)