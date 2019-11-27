import json
from collections import OrderedDict

import dice

shades = {'B': 4, 'G': 3, 'W': 2}
shadeNames = {'B': 'Black', 'G': 'Grey', 'W': 'White'}


def find_difficulty(dice_count, ob):
    if ob > dice_count:
        return "Challenging"
    if ob == dice_count:
        return "Difficult"
    if ob == dice_count - 1:
        if dice_count <= 3:
            return "Routine"
        else:
            return "Difficult"
    if ob == dice_count - 2:
        if dice_count <= 6:
            return "Routine"
        else:
            return "Difficult"
    if ob <= dice_count - 3:
        return "Routine"
    return "Error"


def get_result(successes, ob):
    result = successes - ob
    if result == 0:
        return "Success - Obstacle met"
    if result > 0:
        return "Success - Margin of Success: {}".format(result)
    if result < 0:
        return "Failure - Margin of Failure: {}".format(result * -1)
    return "Error getting result string"


class Ability:
    name = ''
    shade = ''
    exponent = 0

    def __init__(self, name, shade, exponent):
        self.name = name
        self.exponent = int(exponent)
        if shade in ['B', 'G', 'W']:
            self.shade = shade
        else:
            raise ValueError("Invalid Input")

    def roll(self, explode):
        try:
            ob = int(input("What is the Obstacle for this {} test? ".format(self.name)))

        except:
            print("Please enter an integer")
            self.roll()

        helping_dice = int(input("Enter any helping dice and FORKs: ") or 0)
        artha_dice = int(input("Enter in bonus dice from Persona: ") or 0)

        roll = dice.roll("{}d6{}".format(self.exponent + helping_dice + artha_dice, 'x' if explode is True else ''))
        print("Initial Roll: {}".format(roll))
        if 6 in roll:
            if explode == False:
                fate_reroll = yes_no_prompt("Use fate to explode 6s? (y/N): ")
                if fate_reroll:
                    roll_2 = dice.roll('{}d6x'.format(len([d for d in roll if d == 6])))
                    print("New Roll: {}".format(roll_2))
                    roll = roll + roll_2
            if explode == True:
                if len([d for d in roll if d < shades[self.shade]]) > 0:
                    fate_reroll = yes_no_prompt("Use fate to reroll 1 failed die? (y/N) ")
                    if fate_reroll:
                        roll_2 = dice.roll('1d6x')
                        print("New Roll: {}".format(roll_2))
                        if roll_2[0] > min(roll):
                            print("New Roll replaces the lowest value in the initial roll")
                            roll[roll.index(min(roll))] = roll_2[0]
                            if len(roll_2) > 1:
                                print("Oh wow, 6s. Yeah 6s explode so we'll add those results I guess")
                            roll = roll + roll_2[1:]
                        else:
                            print("New Roll not higher than lowest value in initial roll, so nothing has changed")
        difficulty = find_difficulty(helping_dice + self.exponent, ob)
        successes = len([d for d in roll if d >= shades[self.shade]])
        print("Final Result for {} Test: {}".format(self.name, roll))
        print("{} Successes with {} Shade Against Ob {}".format(successes, shadeNames[self.shade], ob))
        print(get_result(successes, ob))
        print("Ob {} with {} dice makes this test {}".format(ob, self.exponent + helping_dice, difficulty))
        return successes - ob


class Skill(Ability):

    def roll(self):
        explode = yes_no_prompt("Is {} a skill where 6s are open-ended? (y/N): ".format(self.name))
        Ability.roll(self, explode)


class Stat(Ability):

    def roll(self):
        explode = True if self.name == "Steel" or self.name == "Faith" or self.name == "Hatred" else False
        Ability.roll(self, explode)


class Character:
    stats = OrderedDict()
    skills = OrderedDict()
    name = ''
    gender = ''
    stock = ''
    lifepaths = []
    traits = []
    property = []
    reputations = []
    affiliations = []

    def load_character(self, filepath):
        with open(filepath) as json_file:
            data = json.load(json_file, object_pairs_hook=OrderedDict)

            self.name = data['name']
            self.gender = data['gender']
            self.stock = data['stock']
            self.lifepaths = [lifepath[1] for lifepath in data['lifepaths']]

            self.load_stats(data['stats'])
            self.calculate_hesitation()
            self.calculate_steel()
            self.load_skills(data['skills']['lifepath'])
            self.load_skills(data['skills']['general'])
            self.print_character()
            print()
            alter_ability = yes_no_prompt("Does any skill shade need to be changed? (y/N): ".format(self.name))
            if alter_ability:
                self.alter_skill_shade()

    def load_stats(self, file_stats):
        for stat in file_stats:
            self.stats[stat['name']] = Stat(stat['name'], stat['shade'],
                                            stat['mentalPoints'] + stat['physicalPoints'] + stat['eitherPoints'])

    def load_skills(self, file_skills):
        for skill in file_skills:
            self.skills[skill['name'].title()] = Skill(skill['name'], "B",
                                               skill['lifepathPoints'] + skill['generalPoints'])

    def calculate_health(self, data):
        health_exponent = (self.stats['Will'] + self.stats['Forte']) / 2
        if self.stock.lower() in ['dwarf', 'elf', 'orc']:
            health_exponent = health_exponent + 1

        detrimental_questions = ['Does the character live in squalor and filth?',
                                 'Is the character frail or sickly?',
                                 'Was the character severely wounded in the past?',
                                 'Has the character been tortured and enslaved?']
        advantageous_questions = ['Is the character athletic and active?',
                                  'Does the character live in a really clean and happy place,'
                                  ' like the hills in the Sound of Music?']

        for question in data['attr_mod_questions']['Health']:
            if question['question'] in detrimental_questions and question['answer']:
                health_exponent = health_exponent - 1
            if question['question'] in advantageous_questions and question['answer']:
                health_exponent = health_exponent + 1

        health_shade = 'B'

        self.stats['Health'] = Stat('Health', health_shade, health_exponent)



    def calculate_hesitation(self):
        self.stats['Hesitation'] = Stat('Hesitation', self.stats['Will'].shade, 10 - self.stats['Will'].exponent)

    def calculate_steel(self):
        steel_shade = 'B'
        steel_exponent = 3
        while True:
            try:
                steel_shade = input("Enter Steel Shade: (B, G, W)").upper()
                if steel_shade not in ['B', 'G', 'W']:
                    raise ValueError
            except ValueError:
                print("Invalid Shade, shades are: B, G, W")
                continue
            else:
                break
        while True:
            try:
                steel_exponent = int(input('Enter final Steel value (1 - 10): '))
                if steel_exponent < 1 or steel_exponent > 10:
                    raise ValueError
            except ValueError:
                print("Value must be integer between 1 and 10")
                self.stats['Steel'] = input('Enter final Steel value: ')
                continue
            else:
                break
        self.stats['Steel'] = Stat('Steel', steel_shade, steel_exponent)



    def print_character(self):
        print("Name: {}".format(self.name))
        print("Gender: {}".format(self.gender))
        print("Stock: {}".format(self.stock))
        print("--- Stats ---")
        for stat_name, stat in self.stats.items():
            print("{}: {} {}".format(stat.name, stat.shade, stat.exponent))
        print("--- Skills ---")
        for skill_name, skill in self.skills.items():
            print("{}: {} {}".format(skill.name, skill.shade, skill.exponent))

    def alter_stat_shade(self):
        self.alter_ability_shade(self.stats)

    def alter_skill_shade(self):
        self.alter_ability_shade(self.skills)

    def alter_ability_shade(self, ability_list):
        valid_name = False
        valid_shade = False
        while not valid_name:
            ability_name = input("Ability Name: ").title()
            if ability_name not in ability_list:
                print("{} not found in list of skills.".format(ability_name))
                print("--- Skills: ---")
                for ability_name, skill in ability_list.items():
                    print(ability_name)
            else:
                valid_name = True
        while not valid_shade:
            new_shade = input("New Shade (B, G, W): ").upper()
            if new_shade not in ['B', 'G', 'W']:
                print('Invalid Shade. Valid Shades = B, G, W')
            else:
                valid_shade = True

        ability_list[ability_name].shade = new_shade


def yes_no_prompt(prompt):
    prompt_answer = input(prompt)
    if prompt_answer.lower() == 'y' or prompt_answer.lower() == 'yes':
        return True
    return False


def test():
    skill3 = Skill("Sword", "B", 3)
    skill3.roll()

    skill4 = Skill("Sorcery", "G", 5)
    skill4.roll()

    stat = Stat("Will", "B", 4)
    stat.roll()

    stat2 = Stat("Steel", "B", 4)
    stat2.roll()
