import asyncio
import datetime
import random
from typing import List

import flet as ft
import requests
import settings


class Answer:
    def __init__(self, answer: dict) -> None:
        self.pk = answer.get("pk")
        self.answer = answer.get("answer")
        self.question = answer.get("question")
        self.image = answer.get("image")
        self.is_image = answer.get("is_image")

    def __str__(self):
        return "{\n" + f"\t'pk':'{self.pk}',\n\t'answer':'{self.answer}'," + "\n}\n"


class Question:
    def __init__(self, question: dict) -> None:
        self.pk = question.get("pk")
        self.question = question.get("question")
        self.image = question.get("image")
        self.is_image = question.get("is_image")
        self.is_answered = False
        self.answers = []

        for answer in question.get("answers"):
            self.answers.append(Answer(answer))

        random.shuffle(self.answers)


class NavigationItem(ft.Container):
    def __init__(self, question: Question, index, data, on_click):
        super().__init__()
        self.question = question
        self.ink = True
        self.padding = ft.padding.only(left=5, top=5, bottom=5, right=15)
        self.border_radius = 5
        self.data = data
        self.icon = ft.Icon(
            name=ft.icons.QUESTION_MARK,
            color=ft.colors.PRIMARY,
            size=18,
        )
        self.text = ft.Text(f"Sorag №{index}")
        self.content = ft.Row(
            controls=[
                self.icon,
                self.text,
            ],
            expand=True,
        )
        self.on_click = on_click


class QuestionsMenu(ft.Column):
    def __init__(self, questions: list, on_click) -> None:
        super().__init__()
        self.expand = 4
        self.spacing = 5
        self.selected_index = 0
        self.controls: List[NavigationItem] = []
        for index in range(len(questions)):
            self.controls.append(
                NavigationItem(questions[index], index + 1, index, on_click)
            )
        self.scroll = ft.ScrollMode.ALWAYS

    def before_update(self):
        super().before_update()
        self.update_selected_item()

    def update_selected_item(self):
        for item in self.controls:
            if item.question.is_answered:
                item.disabled = True
                item.bgcolor = ft.colors.GREY_200
                item.content.controls[0].color = ft.colors.GREY_400
                item.content.controls[1].color = ft.colors.GREY_400
            else:
                item.bgcolor = None
                item.content.controls[1].color = None
            item.shadow = None
        self.controls[self.selected_index].bgcolor = ft.colors.SECONDARY_CONTAINER
        self.controls[self.selected_index].content.controls[1].color = ft.colors.PRIMARY
        self.controls[self.selected_index].shadow = ft.BoxShadow(
            1, 10, ft.colors.BLUE_100
        )


class CountDownText(ft.Text):
    def __init__(self, minutes, user_id, challenge_pk, token):
        super().__init__()
        self.seconds = minutes * 60
        self.__user_id = user_id
        self.__token = token
        self.__challenge_pk = challenge_pk

    def did_mount(self):
        self.running = True
        self.page.run_task(self.update_timer)

    def will_unmount(self):
        self.running = False

    def __build_dialog(self, dialog_title, dialog_message):
        def close_dlg(e):
            dlg_modal.open = False
            self.page.update()

        def dismiss_dlg(e):
            requests.post(
                url=f"{settings.API_URL}/api/v1/timeout/",
                headers={"Authorization": self.__token},
                data={
                    "challenge": self.__challenge_pk,
                },
            )
            requests.post(
                url=f"{settings.API_URL}/api/v1/test-session-update/",
                headers={"Authorization": self.__token},
                data={
                    "challenge": self.__challenge_pk,
                    "user": self.__user_id,
                    "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            )
            self.page.go("/results")

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text(dialog_title),
            content=ft.Text(dialog_message),
            actions=[
                ft.TextButton("OK", on_click=close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        dlg_modal.on_dismiss = dismiss_dlg

        return dlg_modal

    async def update_timer(self):
        while self.seconds and self.running:
            mins, secs = divmod(self.seconds, 60)
            hours, mins = divmod(mins, 60)
            if hours > 0:
                self.value = "{:02d}:{:02d}:{:02d}     ".format(hours, mins, secs)
            else:
                self.value = "{:02d}:{:02d}     ".format(mins, secs)
            self.update()
            await asyncio.sleep(1)
            self.seconds -= 1
            if self.seconds == 0:
                self.value = "00:00     "
                close_modal = self.__build_dialog(
                    "Wagt doldy!",
                    "Test üçin berlen wagtyňyz doldy! Çykyşyňyzy tassyklaň!",
                )
                close_modal.open = True
                self.page.overlay.append(close_modal)
                self.page.update()


class QuizzPanel(ft.Container):
    quizz_column = ft.Column()
    question_container = ft.Container(bgcolor=ft.colors.PRIMARY_CONTAINER)
    data = quizz_column

    def __init__(self):
        super().__init__()


class RequestsQuene:
    __quene: List[dict] = []

    def __init__(self, api_url: str, headers: dict) -> None:
        self.__api_url = api_url
        self.__headers = headers

    def __check_echo(self):
        try:
            requests.request("GET", f"{self.__api_url}/api/v1/")
            success = True
        except:
            success = False
        return success

    def __dequene(self):
        status = self.__check_echo()
        if status:
            for payload in self.__quene:
                requests.post(
                    url=f"{self.__api_url}/api/v1/useranswer-create/",
                    headers=self.__headers,
                    data=payload,
                )
            self.__quene.clear()
            return True
        return False

    def send(self, payload: dict):
        status = self.__check_echo()
        if status:
            requests.post(
                url=f"{self.__api_url}/api/v1/useranswer-create/",
                headers=self.__headers,
                data=payload,
            )
            if self.__quene != 0:
                self.__dequene()
        else:
            self.__quene.append(payload)
