import json, texttable as tt
from collections import OrderedDict
from functools import partial



class LifePathBuilder:

    lifepaths = OrderedDict()
    born_life_paths = {}
    chosen_life_paths = []
    life_path_names = []
    current_setting = ''

    def required_n_lifepaths(self, required_lifepaths):
        if len(self.chosen_life_paths) >= required_lifepaths:
            return True
        else:
            return False

    def __init__(self):
        lifepath_rule_engine = {'+has_n_lifepaths_or_more': self.required_n_lifepaths,
                                }
        self.load_man_lifepaths()

        paths = []
        for dic in [y for x, y in self.lifepaths.items()]:
            for k, v in dic.items():
                if 'requires' in v:
                    paths.append(v['requires'])

        lset = set(paths)
        paths = (list(lset))
        for path in paths:
            print(path)

        print(len(paths))


    def load_man_lifepaths(self, filepath = 'resources/mannishlifepaths.json'):
        with open(filepath) as json_file:
            self.lifepaths = json.load(json_file)

        for k in self.lifepaths:
            for x in self.lifepaths[k]:
                self.lifepaths[k][x]['setting'] = k
                if "Born" in x:
                    self.born_life_paths[x] = self.lifepaths[k][x]

    def add_lifepath(self, lifepath_name, lifepath):
        self.chosen_life_paths.append(lifepath)
        self.life_path_names.append((lifepath_name))

    def calculate_stats(self):
        return None

    def build_valid_options(self):
        if len(self.chosen_life_paths) == 0:
            return self.born_life_paths

        last_lifepath = self.chosen_life_paths[-1]
        valid_lifepaths = {}
        for k, v in self.lifepaths.items():
            if k == last_lifepath['setting'] or k in last_lifepath['key_leads']:
                return
        # if 'Born' not in k:

        return valid_lifepaths





lifep = LifePathBuilder()