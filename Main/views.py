from dataclasses import fields

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import action, authentication_classes
from rest_framework.request import Request
from rest_framework.viewsets import GenericViewSet

from Main.models import Question, Answer, Test
from Main.serializers import TestSerializer
from Users.models import Speciality
from Users.utils import OrgAdminAuthentication, UserAuthentication

class TestsViewSet(GenericViewSet):
    authentication_classes = [OrgAdminAuthentication]
    serializer_class = TestSerializer
    queryset = Test.objects.all()

    @action(methods=["GET"], detail=False, url_path="get-all")
    def get_all(self, request):
        return Response(status=200, data={"message": "ОК!",
                                          "tests": [test.name for test in Test.objects.all()]})

    @extend_schema(request=inline_serializer("TestCreate", fields={
        "name": serializers.CharField()
    }))
    @action(methods=["POST"], detail=False, url_path="create")
    def add(self, request: Request):
        test_serializer = self.serializer_class(data=request.data)
        test_serializer.is_valid(raise_exception=True)
        test_serializer.save()
        return Response(status=200, data={"message": "Тест создан!"})


    @extend_schema(request=inline_serializer("TestAddQuestion", fields={
        "text": serializers.CharField(),
        "test_id": serializers.IntegerField()
    }))
    @action(methods=["POST"], detail=False, url_path="add-question")
    def add_question(self, request: Request):
        try:
            question = Question(text=request.data.get("text"),
                                test_id=request.data.get("test_id"))
            question.save()
        except:
            return Response(status=400, data={"message": "Невалидные данные!"})
        return Response(status=200, data={"message": "Вопрос создан!"})

    @extend_schema(request=inline_serializer("TestAddAnswer", fields={
        "text": serializers.CharField(),
        "answer_number": serializers.IntegerField(),
        "question_id": serializers.IntegerField(),
        "speciality_id": serializers.IntegerField()
    }))
    @action(methods=["POST"], detail=False, url_path="add-answer")
    def add_answer(self, request: Request):
        try:
            answer = Answer(text=request.data.get("text"),
                            question_id=request.data.get("question_id"),
                            answer_number=request.data.get("answer_number"),
                            speciality_id=request.data.get("speciality_id"))
            answer.save()
        except Exception as e:
            print(e)
            return Response(status=400, data={"message": "Невалидные данные!"})
        return Response(status=200, data={"message": "Ответ добавлен!"})

    @extend_schema(parameters=[inline_serializer("TestGetQuestion", fields={
        "test_id": serializers.IntegerField()
    })])
    @action(methods=["GET"], detail=True, url_path="get-question", authentication_classes=[UserAuthentication])
    def get_question(self, request: Request, **kwargs):
        try:
            question = Question.objects.filter(test_id=request.query_params.get("test_id"))[int(kwargs.get("pk"))-1]
        except Exception as e:
            print(e)
            return Response(status=404, data={"message": "Такого вопроса не существует!"})
        return Response(status=200, data=question.to_dict())

    @extend_schema(request=inline_serializer("TestAnswer", fields={
        "test_id": serializers.IntegerField(),
        "answer_id": serializers.IntegerField(),
    }))
    @action(methods=["POST"], detail=True, url_path="answer", authentication_classes=[UserAuthentication])
    def answer(self, request: Request, **kwargs):
        try:
            question = Question.objects.filter(test_id=request.data.get("test_id"))[int(kwargs.get("pk"))-1]
            answers = Answer.objects.filter(question=question)
            answers_count = len(answers)
            answer = answers[int(request.data.get("answer_id"))-1]
            user_spec_scores = request.user.scores.get(answer.speciality.pk)
            if not user_spec_scores:
                user_spec_scores = 0
            request.user.scores[answer.speciality.pk] = user_spec_scores
            request.user.save()
        except Exception as e:
            print(e)
            return Response(status=400, data={"message": "Невалидные данные!"})
        print(int(request.data.get("answer_id")), answers_count)
        if int(request.data.get("answer_id"))-1 == answers_count:
            speciality_id = max(request.user.scores)
            speciality = Speciality.objects.get(id=speciality_id)
            return Response(status=200, data={
                "message": "Тест пройден!",
                "text": f"По результатам теста вы прирождённый {speciality.name}!",
                "finally": True
            })
        return Response(status=200, data={"message": "ОК!", "finally": False})