from django.db import models
from requests import Request


class Test(models.Model):
    name = models.SlugField()


class Question(models.Model):
    text = models.TextField()
    test = models.ForeignKey("Test", models.CASCADE)

    def to_dict(self):
        answers = [answer.to_dict() for answer in Answer.objects.filter(question=self)]
        return dict(text=self.text, answers=answers)

class Answer(models.Model):
    question = models.ForeignKey("Question", models.CASCADE)
    speciality = models.ForeignKey("Users.Speciality", models.CASCADE)
    answer_number = models.IntegerField()
    text = models.TextField()

    def to_dict(self):
        return dict(id=self.answer_number, text=self.text)
