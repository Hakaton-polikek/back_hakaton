from django.db import models

class Test(models.Model):
    name = models.SlugField()

class Question(models.Model):
    question = models.TextField()
    test = models.ForeignKey("Test", models.CASCADE)

class Answer(models.Model):
    question = models.ForeignKey("Question", models.CASCADE)
    speciality = models.ForeignKey("Speciality", models.CASCADE)
