from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools
import random
import nltk
from nltk.metrics import distance as dist

class FormGenerator:
    SCOPES = "https://www.googleapis.com/auth/forms.body"
    DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

    def __init__(self, title):
        self.title = title
        self.times_to_check = 50
        self.correct_words = []
        self.correct_sentences = []
        self.change_words = []
        self.remove_words = []
        self.add_words = []
        self.old_i = 0
        self.alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'w', 'y']
        self.store = file.Storage("token.json")
        self.creds = None
        self.pdf = False

    def insert_letter(self, char, string, index):
        return string[:index] + char + string[index:]

    def set_variables(self, Word, Sentence, i):
        self.correct_words.insert(i, Word)
        self.correct_sentences.insert(i, Sentence)

    def add_word(self):
        new_word_add = []
        stat_add = []
        for i in range(self.times_to_check):
            new_word = self.insert_letter(
                self.alphabet[random.randint(0, len(self.correct_words[self.old_i]) - 1)],
                self.correct_words[self.old_i],
                random.randint(0, len(self.correct_words[self.old_i]) - 1)
            )
            new_word_add.insert(i, new_word)
            stat_add.insert(i, dist.jaro_winkler_similarity(self.correct_words[self.old_i], new_word) + dist.jaro_similarity(self.correct_words[self.old_i], new_word))
        best_stat_add = max(stat_add)
        self.add_words.insert(self.old_i, new_word_add[stat_add.index(best_stat_add)])
        print(self.add_words[self.old_i] + " " + str(best_stat_add))

    def sub_word(self):
        new_word_sub = []
        stat_sub = []
        for i in range(self.times_to_check):
            new_word = list(self.correct_words[self.old_i])
            new_word[random.randint(0, len(self.correct_words[self.old_i]) - 1)] = ""
            new_word_sub.insert(i, ''.join(new_word))
            stat_sub.insert(i, dist.jaro_winkler_similarity(self.correct_words[self.old_i], new_word_sub[i]) + dist.jaro_similarity(self.correct_words[self.old_i], new_word_sub[i]))
        best_stat_sub = max(stat_sub)
        self.remove_words.insert(self.old_i, new_word_sub[stat_sub.index(best_stat_sub)])
        print(self.remove_words[self.old_i] + " " + str(best_stat_sub))

    def change_word(self):
        string_list = list(self.correct_words[self.old_i])
        new_word_change = []
        stat_list_change = []
        for i in range(self.times_to_check):
            first_num = random.randint(0, len(string_list) - 1)
            second_num = random.randint(0, len(string_list) - 1)
            if first_num == second_num:
                first_num = random.randint(0, len(string_list) - 1)
                second_num = random.randint(0, len(string_list) - 1)
            string_list[first_num], string_list[second_num] = string_list[second_num], string_list[first_num]
            new_word_change.insert(i, ''.join(string_list))
            stat_list_change.insert(i, dist.jaro_winkler_similarity(self.correct_words[self.old_i], new_word_change[i]) + dist.jaro_similarity(self.correct_words[self.old_i], new_word_change[i]))
        best_stat_change = max(stat_list_change)
        self.change_words.insert(self.old_i, new_word_change[stat_list_change.index(best_stat_change)])
        print(self.change_words[self.old_i] + " " + str(best_stat_change))

    def generate_form(self):
        if not self.creds or self.creds.invalid:
            flow = client.flow_from_clientsecrets("client_secrets.json", self.SCOPES)
            self.creds = tools.run_flow(flow, self.store)

        form_service = discovery.build(
            "forms", "v1", http=self.creds.authorize(Http()), discoveryServiceUrl=self.DISCOVERY_DOC, static_discovery=False
        )

        new_form = {
            "info": {
                "title": self.title,
                "documentTitle": self.title
            },
        }

        result = form_service.forms().create(body=new_form).execute()

        settings = {
            "requests": [
                {
                    "updateSettings": {
                        "settings": {
                            "quizSettings": {
                                "isQuiz": True
                            }
                        },
                        "updateMask": "quizSettings.isQuiz"
                    }
                }
            ]
        }

        form_service.forms().batchUpdate(formId=result["formId"], body=settings).execute()

        for i in range(len(self.correct_words)):
            self.old_i = i
            self.add_word()
            self.sub_word()
            self.change_word()

            while self.add_words[i] == self.correct_words[i]:
                self.add_word()

            while self.remove_words[i] == self.correct_words[i]:
                self.sub_word()

            while self.change_words[i] == self.correct_words[i]:
                self.change_word()

            title = str(self.correct_sentences[i]).replace(self.correct_words[i], "______")
            points = 1 if i >= 20 else 5

            new_question = {
                "requests": [
                    {
                        "createItem": {
                            "item": {
                                "title": title,
                                "questionItem": {
                                    "question": {
                                        "required": True,
                                        "grading": {
                                            "pointValue": points,
                                            "correctAnswers": {
                                                "answers": [{"value": self.correct_words[i]}]
                                            },
                                        },
                                        "choiceQuestion": {
                                            "type": "RADIO",
                                            "options": [
                                                {"value": self.correct_words[i]},
                                                {"value": self.remove_words[i]},
                                                {"value": self.add_words[i]},
                                                {"value": self.change_words[i]},
                                            ],
                                            "shuffle": True,
                                        },
                                    }
                                },
                            },
                            "location": {"index": i},
                        }
                    }
                ]
            }

            form_service.forms().batchUpdate(formId=result["formId"], body=new_question).execute()

        get_result = form_service.forms().get(formId=result["formId"]).execute()
        print(get_result)



