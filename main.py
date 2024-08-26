import asyncio
import datetime
import random
from typing import List

import flet as ft
import requests

with open("api", "r") as file:
    API_URL: str = file.read()

token = ""


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
                url=f"{API_URL}/api/v1/timeout/",
                headers={"Authorization": self.__token},
                data={
                    "challenge": self.__challenge_pk,
                },
            )
            requests.post(
                url=f"{API_URL}/api/v1/test-session-update/",
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


class LoginPage(ft.View):

    def __init__(self):
        super().__init__()
        self.route = "/"

        self.__name_field = ft.TextField(
            label="Ady",
            border_color=ft.colors.WHITE,
            focused_color=ft.colors.BLACK87,
            hover_color=ft.colors.WHITE24,
            fill_color=ft.colors.WHITE24,
        )
        self.__surname_field = ft.TextField(
            label="Familiýasy",
            border_color=ft.colors.WHITE,
            focused_color=ft.colors.BLACK87,
            hover_color=ft.colors.WHITE24,
            fill_color=ft.colors.WHITE24,
        )
        self.__about_field = ft.TextField(
            label="Edarasy",
            border_color=ft.colors.WHITE,
            focused_color=ft.colors.BLACK87,
            hover_color=ft.colors.WHITE24,
            selection_color=ft.colors.WHITE12,
            fill_color=ft.colors.WHITE24,
        )
        self.__submit_btn = ft.ElevatedButton(
            "Tassyklamak", on_click=lambda e: self.__submit()
        )
        self.__column = ft.Column(
            [
                ft.Row([self.__name_field], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([self.__surname_field], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([self.__about_field], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([self.__submit_btn], alignment=ft.MainAxisAlignment.END),
            ],
            spacing=20,
        )
        self.__appbar = ft.AppBar(
            title=ft.Text("Giriş"),
            center_title=True,
            bgcolor=ft.colors.SURFACE_VARIANT,
        )

        self.__login_container = ft.Container(
            ft.Container(
                self.__column,
                bgcolor=ft.colors.INVERSE_PRIMARY,
                width=400,
                padding=ft.padding.all(40),
                border_radius=10,
                margin=ft.margin.only(top=150, bottom=150),
                shadow=ft.BoxShadow(1, 10, "#bdbdbd"),
            ),
            alignment=ft.alignment.center,
        )
        self.controls = [self.__appbar, self.__login_container]
        self.__about_field_focused = False

    def __build_dialog(self, dialog_title, dialog_message):
        def close_dlg(e):
            dlg_modal.open = False
            self.page.update()

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text(dialog_title),
            content=ft.Text(dialog_message),
            actions=[
                ft.TextButton("OK", on_click=close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        return dlg_modal

    def __submit(self):

        name = self.__name_field.value
        surname = self.__surname_field.value
        about = self.__about_field.value

        cyrillic = "ёйцукенгшщзхъфывапролджэячсмитьбю"
        symbols = ".,/\\`'[]()!@#$%^&*№:;{}<>?+=-_" + '"'
        filling_error = False
        for char in name.lower() + surname.lower() + about.lower():
            if char in symbols or char in cyrillic:
                filling_error = True
                break

        if filling_error:
            dialog_title = "Kabul edilmeýän simwollar"
            dialog_message = "Girizen maglumatlaryňyzda kabul edilmeýän simwollar ulanylypdyr! Täzeden synanyşmagyňyzy haýyş edýäris!"
            dlg_modal = self.__build_dialog(dialog_title, dialog_message)
            self.page.overlay.append(dlg_modal)
            dlg_modal.open = True
            self.page.update()
        elif name == "" or surname == "":
            dialog_title = "Doly giriziň!"
            if name == "" and surname == "":
                dialog_message = "Adyňyzy we familiýaňyzy girizmegiňizi haýyş edýäris!"
            elif name == "" and not surname == "":
                dialog_message = "Adyňyzy girizmegiňizi haýyş edýäris!"
            elif surname == "" and not name == "":
                dialog_message = "Familiýaňyzy girizmegiňizi haýyş edýäris!"
            dlg_modal = self.__build_dialog(dialog_title, dialog_message)
            self.page.overlay.append(dlg_modal)
            dlg_modal.open = True
            self.page.update()
        else:
            enable_chars = ("qwertyuiopasdfghjklzxcvbnm", "1234567890")
            password = ""
            username = (
                (name + surname)
                .lower()
                .replace("ý", "y")
                .replace("ž", "zh")
                .replace("ä", "a")
                .replace("ç", "ch")
                .replace("ş", "sh")
                .replace("ň", "n")
                .replace("ö", "o")
                .replace("ü", "u")
            )
            for i in range(random.randint(8, 12)):
                in_choice = random.randint(0, 1)
                if in_choice == 0:
                    letter_id = random.randint(0, 25)
                    password += random.choice(
                        (
                            enable_chars[0][letter_id].upper(),
                            enable_chars[0][letter_id].lower(),
                        )
                    )
                else:
                    password += enable_chars[1][random.randint(0, 9)]
            try:
                user_url = f"{API_URL}/api/v1/auth/users/"
                journal_url = f"{API_URL}/api/v1/auth-journal/create"
                login_url = f"{API_URL}/api/v1/auth/token/login"

                payload = {
                    "first_name": name,
                    "last_name": surname,
                    "username": username,
                    "password": password,
                    "email": "stub@email.com",
                }
                payload_dub = {
                    "name": name,
                    "surname": surname,
                    "username": username,
                    "password": password,
                }

                files = []
                headers = {}

                user_response = requests.request(
                    "POST", user_url, headers=headers, data=payload, files=files
                ).json()

                if (
                    user_response["username"][0]
                    == "A user with that username already exists."
                    or user_response["username"][0]
                    == "Пользователь с таким именем уже существует."
                ):
                    url = f"{API_URL}/api/v1/auth-journal/" + username
                    response = requests.request(
                        "GET", url, headers=headers, files=files
                    ).json()
                    login_payload = {
                        "username": response[0]["username"],
                        "password": response[0]["password"],
                    }
                else:

                    profile_payload = {
                        "about": about if about != "" else "Default",
                        "user": user_response["id"],
                    }

                    profile_response = requests.request(
                        "POST",
                        f"{API_URL}/api/v1/create_profile/",
                        headers={},
                        data=profile_payload,
                    ).json()

                    response = requests.request(
                        "POST",
                        journal_url,
                        headers=headers,
                        data=payload_dub,
                        files=files,
                    ).json()
                    login_payload = {
                        "username": response["username"],
                        "password": response["password"],
                    }

                login_response = requests.request(
                    "POST", login_url, headers=headers, data=login_payload, files=files
                ).json()
                self.__token = "Token " + login_response["auth_token"]
                self.page.go("/challenges")
            except requests.exceptions.ConnectionError:
                dialog_title = "Baglanyşyk näsazlygy"
                dialog_message = "Serwer bilen baglanyşyk prosesinde näsazlyk döredi. Internet/Ethernet baglanyşygyňyzy barlaň!"
                dlg_modal = self.__build_dialog(dialog_title, dialog_message)
                self.page.overlay.append(dlg_modal)
                dlg_modal.open = True
                self.page.update()

    def get_token(self):
        return self.__token

    def focus(self, e: ft.KeyboardEvent):

        if e.key == "Enter":
            fields = (self.__name_field, self.__surname_field) if self.__about_field_focused else (self.__name_field, self.__surname_field, self.__about_field)
            blank_filled = True
            for field in fields:
                if field.value == "":
                    self.__about_field_focused = True if fields.index(field) == 2 else False
                    blank_filled = False
                    field.focus()
                    break
            if blank_filled:
                self.__submit()


        self.page.update()

class ChallengesPage(ft.View):
    def __init__(self, token: str):
        super().__init__()
        self.__token = token
        self.__challenges_list = requests.request(
            "GET", f"{API_URL}/api/v1/challengelist/", headers={"Authorization": self.__token}
        ).json()

        self.__appbar = ft.AppBar(
            title=ft.Text("Testler"),
            bgcolor=ft.colors.SURFACE_VARIANT,
            center_title=True,
        )

        self.__grid = ft.GridView(
            expand=1,
            runs_count=5,
            max_extent=300,
            child_aspect_ratio=3,
            spacing=10,
            run_spacing=10,
        )

        containers = []

        for challenge in self.__challenges_list:
            if challenge["is_participated"]:
                containers.append(
                    ft.Container(
                        bgcolor=ft.colors.GREY_200,
                        border_radius=5,
                        padding=15,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.START,
                            controls=[
                                ft.Icon(name=ft.icons.QUIZ_OUTLINED, color=ft.colors.GREY_400),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            challenge["name"],
                                            weight=ft.FontWeight.W_500,
                                            size=20,
                                            color=ft.colors.GREY_400,
                                        ),
                                        ft.Text(f"Sorag sany: {
                                                challenge['question_count']}", color=ft.colors.GREY_400),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                            ],
                        ),
                    )
                )
            else:
                containers.append(
                    ft.Container(
                        on_click=lambda e: self.__run_challenge(pk=e.control.data),
                        data=challenge["pk"],
                        bgcolor=ft.colors.SECONDARY_CONTAINER,
                        border_radius=5,
                        padding=15,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.START,
                            controls=[
                                ft.Icon(name=ft.icons.QUIZ_OUTLINED),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            challenge["name"],
                                            weight=ft.FontWeight.W_500,
                                            size=20,
                                        ),
                                        ft.Text(f"Sorag sany: {
                                                challenge['question_count']}"),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                            ],
                        ),
                    )
                )

        for container in containers:
            self.__grid.controls.append(container)

        self.controls = [
            self.__appbar,
            self.__grid,
        ]


    def __run_challenge(self, pk: int):

        self.__selected_challenge = pk

        self.page.go("/challenge")

    def get_selected_challenge(self):
        return self.__selected_challenge

class ChallengePage(ft.View):
    def __init__(self, pk: int, token: str):
        super().__init__()
        self.__token = token
        self.__challenge_pk = pk
        self.__user_data = requests.request(
            "GET",
            f"{API_URL}/api/v1/auth/users/",
            headers={"Authorization": self.__token},
        ).json()
        self.__challenge_data = requests.request(
            "GET", f"{API_URL}/api/v1/challenge/{self.__challenge_pk}/", headers={"Authorization": self.__token}
        ).json()
        self.__session = requests.request(
            "POST",
            url=f"{API_URL}/api/v1/test-session-create/",
            headers={"Authorization": self.__token},
            data={"challenge": self.__challenge_pk, "user": int(self.__user_data[0]["id"])},
        ).json()

        questions_data = requests.request(
            "GET", f"{API_URL}/api/v1/challenge-data/{self.__challenge_pk}/", headers={"Authorization": self.__token}
        ).json()
        random.shuffle(questions_data)
        self.__questions_menu: QuestionsMenu = QuestionsMenu(
            [Question(question) for question in questions_data], self.__question_menu_item_clicked,
        )

        self.__requests_quene = RequestsQuene(API_URL, {"Authorization": self.__token})

        self.route = "/challenge"

        self.__quizz_panel = ft.Column(scroll=ft.ScrollMode.AUTO)

        self.floating_action_button = ft.FloatingActionButton(icon=ft.icons.ARROW_FORWARD, scale=1.1, width=110, height=45, on_click=self.__accept, bgcolor=ft.colors.PRIMARY, foreground_color=ft.colors.WHITE)

        self.__current_question_index = 0
        question: Question = self.__questions_menu.controls[self.__current_question_index].question

        if question.is_image:
            row = ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                expand=True,
                controls=[
                    ft.Text("Suraty görmek üçin basyň", weight=ft.FontWeight.BOLD),
                    ft.IconButton(icon=ft.icons.ARROW_FORWARD_IOS, data=question.image, on_click=self.__show_image_dialog),
                ],
                spacing=10,
            )
        else:
            row = ft.Row(
                alignment=ft.MainAxisAlignment.START,
                controls=[
                    ft.Text(question.question),
                ],
                scroll=ft.ScrollMode.AUTO,
            )

        self.__question_row = ft.Row(
            controls=[
                ft.Container(
                    bgcolor=ft.colors.INVERSE_PRIMARY, 
                    content=row,
                    expand=True,
                    margin=ft.margin.only(10, 20, 10, 25),
                    padding=ft.padding.only(20, 15, 20, 15),
                    shadow=ft.BoxShadow(1, 10, "#bdbdbd"),
                    border_radius=30,
                ),
            ],
        )
        
        self.__answers_grid = ft.GridView(auto_scroll=True, runs_count=2, padding=10, height=295, child_aspect_ratio=5)
        
        self.__answer_containers = self.__build_answer_containers(self.__questions_menu.controls[0].question.answers)
        self.__selected_answer = None
        self.__current_question = question.pk
        self.__answered_questions_count = 0
        self.__progress_ring = ft.ProgressRing(value=1)
        self.__answered_questions_count_text = ft.Text(f"{self.__answered_questions_count}/{self.__challenge_data["question_count"]}   ")

        self.__answers_grid.controls = self.__answer_containers
        
        self.__quizz_panel.controls = [
            ft.Row(controls=[ft.Text("Sorag:", size=18)], alignment=ft.MainAxisAlignment.CENTER),
            self.__question_row, 
            ft.Row(controls=[ft.Text("Jogaplar:", size=18)], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(
                content=self.__answers_grid,
                margin=ft.margin.only(top=25)
            )
        ]

        self.controls = [
            ft.AppBar(
                title=ft.Text(self.__challenge_data["name"]),
                bgcolor=ft.colors.SURFACE_VARIANT,
                center_title=True,
                actions=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.icons.TIMER_SHARP),
                            CountDownText(
                                self.__challenge_data["time_for_event"], self.__user_data[0]["id"], self.__challenge_data["pk"], self.__token),
                        ],
                    ),
                    ft.Row(
                        controls=[
                            self.__progress_ring,
                            self.__answered_questions_count_text,
                        ],
                    )
                ],
            ),
            ft.Row(
                controls=[
                    ft.Container(content=self.__questions_menu, alignment=ft.alignment.top_center),
                    ft.VerticalDivider(),
                    ft.Container(content=self.__quizz_panel, expand=True, alignment=ft.alignment.top_center),
                ],    
                expand=True,
                spacing=10,
                alignment=ft.alignment.top_center,
            )
        ]

    
    def __build_image_dialog(self, image_url: str):
        def close_dlg(e):
            dlg_modal.open = False
            self.page.update()

        column = ft.Column(
            controls=[
                ft.Image(
                    src=f"{API_URL}{image_url}",
                    expand=True,
                ),
            ]
        )

        container = ft.Container(content=column, height=600)

        dlg_modal = ft.AlertDialog(
            modal=True,
            content=container,
            actions=[
                ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.START,
        )
        return dlg_modal

    def __show_image_dialog(self, e: ft.ControlEvent):
        dlg = self.__build_image_dialog(e.control.data)
        dlg.open = True
        self.page.overlay.append(dlg)
        self.page.update()


    def __build_answer_containers(self, answers: List[Answer]):
        containers = []

        for answer in answers:
            if answer.is_image:
                row = ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    expand=True,
                    controls=[
                        ft.Text("Suraty görmek üçin basyň", weight=ft.FontWeight.BOLD, color=ft.colors.PRIMARY),
                        ft.IconButton(icon=ft.icons.ARROW_FORWARD_IOS, data=answer.image, on_click=self.__show_image_dialog),
                    ],
                    spacing=10,
                )
            else:
                row = ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    controls=[
                        ft.Text(answer.answer, color=ft.colors.PRIMARY),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                )
            containers.append(
                ft.Container(
                    on_click=self.__select,
                    bgcolor=ft.colors.SECONDARY_CONTAINER,
                    border_radius=30,
                    padding=15,
                    data=answer,
                    content=row,
                    shadow=ft.BoxShadow(1, 7.5, "#e2e2e2"),
                    animate=ft.animation.Animation(150, ft.AnimationCurve.EASE_IN)
                )
            )
        return containers

    def __select(self, e: ft.ControlEvent):
        for answer_container in self.__answer_containers:
        
            if answer_container.data != e.control.data:
                answer_container.bgcolor = ft.colors.SECONDARY_CONTAINER
            else:
                if self.__selected_answer == e.control.data:
                    self.__selected_answer = None
                    answer_container.bgcolor = ft.colors.SECONDARY_CONTAINER
                else:
                    self.__selected_answer = answer_container.data
                    answer_container.bgcolor = ft.colors.INVERSE_PRIMARY
        self.page.update()

    def __accept(self, e: ft.ControlEvent):
        if self.__selected_answer == None and e.control.data != "modal_accept":
            self.__dlg_empty_answer_modal = self.__build_empty_answer_dialog("Jogap meýdançasy boş!", "Dowam eden ýagdaýyňyzda soragy bilmedigiňizi tassyklarsyňyz.")
            self.page.overlay.append(self.__dlg_empty_answer_modal)
            self.__dlg_empty_answer_modal.open = True
            self.page.update()
        else:
            if e.control.data == "modal_accept":
                self.__dlg_empty_answer_modal.open = False
            self.__questions_menu.controls[self.__current_question_index].question.is_answered = True
            try:
                index = self.__current_question_index + 1
                if not self.__questions_menu.controls[index].question.is_answered:
                    self.__current_question_index += 1
                else:
                    # не бейте палками. лень новое исключение создавать
                    raise IndexError
            except IndexError:
                for item in self.__questions_menu.controls:
                    if not item.question.is_answered:
                        self.__current_question_index = self.__questions_menu.controls.index(item)
                        break
                else:
                    requests.post(
                        url=f"{API_URL}/api/v1/test-session-update/",
                        headers={"Authorization": self.__token},
                        data={
                            "challenge": self.__challenge_data["pk"],
                            "user": self.__user_data[0]["id"],
                            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        },
                    )
                    self.page.go("/results")
            payload = {
                "answer": None if self.__selected_answer == None else self.__selected_answer.pk,
                "question": self.__current_question,
                "challenge": self.__challenge_data["pk"],
                "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            self.__questions_menu.selected_index = self.__current_question_index
            self.__questions_menu.update_selected_item()
            self.__answered_questions_count += 1
            self.__progress_ring.value = 1 - (self.__answered_questions_count / self.__challenge_data["question_count"])
            self.__answered_questions_count_text.value = f"{self.__answered_questions_count}/{self.__challenge_data["question_count"]}   "
            self.__update_page()
            self.__requests_quene.send(payload)
            self.__selected_answer = None

    def __question_menu_item_clicked(self, e):
        self.__current_question_index = e.control.data
        self.__questions_menu.selected_index = e.control.data
        self.__questions_menu.update_selected_item()
        self.__update_page()
        self.__selected_answer = None

    def __update_page(self):
        question: Question = self.__questions_menu.controls[self.__current_question_index].question
        self.__current_question = question.pk
        if question.is_image:
            row = ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                expand=True,
                controls=[
                    ft.Text("Suraty görmek üçin basyň", weight=ft.FontWeight.BOLD),
                    ft.IconButton(icon=ft.icons.ARROW_FORWARD_IOS, data=question.image, on_click=self.__show_image_dialog),
                ],
                spacing=10,
            )
        else:
            row = ft.Row(
                alignment=ft.MainAxisAlignment.START,
                controls=[
                    ft.Text(question.question),
                ],
                scroll=ft.ScrollMode.AUTO,
            )

        self.__question_row = ft.Row(
            controls=[
                ft.Container(
                    bgcolor=ft.colors.INVERSE_PRIMARY, 
                    content=row,
                    expand=True,
                    margin=ft.margin.only(10, 20, 10, 25),
                    padding=ft.padding.only(20, 15, 20, 15),
                    shadow=ft.BoxShadow(1, 10, "#bdbdbd"),
                    border_radius=30,
                ),
            ],
        )
        self.__quizz_panel.controls[1] = self.__question_row
        self.__answer_containers = self.__build_answer_containers(self.__questions_menu.controls[self.__current_question_index].question.answers)
        self.__answers_grid.controls = self.__answer_containers
        self.page.update()

    def __build_empty_answer_dialog(self, dialog_title, dialog_message):
        def close_dlg(e):
            dlg_modal.open = False
            self.page.update()

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text(dialog_title),
            content=ft.Text(dialog_message),
            actions=[
                ft.IconButton(icon=ft.icons.HIGHLIGHT_OFF, on_click=close_dlg),
                ft.IconButton(icon=ft.icons.CHECK_CIRCLE_OUTLINE, on_click=self.__accept, data="modal_accept"),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        return dlg_modal

    def get_challenge_data(self):
        return self.__challenge_data

class ResultsPage(ft.View):
    def __init__(self, challenge_data, token):
        super().__init__()
        self.__challenge_data = challenge_data
        self.__token = token

    def did_mount(self):
        self.running = True
        self.page.run_task(self.__build_chart)

    def will_unmount(self):
        self.running = False

    async def __build_chart(self):
        await asyncio.sleep(1)
        headers = {"Authorization": self.__token}

        response = requests.request("GET", f"{API_URL}/api/v1/useranswers/{self.__challenge_data['pk']}/", headers=headers).json()

        self.normal_radius = 100
        self.hover_radius = 110
        self.normal_title_style = ft.TextStyle(
            size=12, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD
        )
        self.hover_title_style = ft.TextStyle(
            size=16,
            color=ft.colors.WHITE,
            weight=ft.FontWeight.BOLD,
            shadow=ft.BoxShadow(blur_radius=2, color=ft.colors.BLACK54),
        )
        self.normal_badge_size = 40
        self.hover_badge_size = 50

        self.__true_answer, self.__false_answer, self.__empty_answer = 0, 0, 0

        for answer in response:
            if answer["is_true"]:
                self.__true_answer += 1
            else:
                if answer["is_empty"]:
                    self.__empty_answer += 1
                else:
                    self.__false_answer += 1

        sections, legends = [], []
        if not self.__true_answer == 0:
            percent = (self.__true_answer / self.__challenge_data["question_count"]) * 100 
            sections.append(
                ft.PieChartSection(
                    percent,
                    title=f"{percent:.2f}%",
                    title_style=self.normal_title_style,
                    color=ft.colors.GREEN,
                    radius=self.normal_radius,
                    badge=self.badge(ft.icons.CHECK_CIRCLE_OUTLINE, self.normal_badge_size),
                    badge_position=0.98,
                )
            )
            legends.append(
                ft.Container(
                    padding=ft.padding.only(left=5, top=5, bottom=5, right=15),
                    content=ft.Row(
                        controls=[ft.Icon(name=ft.icons.CHECK_CIRCLE_OUTLINE), ft.Text(f"Dogry jogap: {self.__true_answer}"),],
                        expand=True
                    )
                ),
            )
        if not self.__false_answer == 0:
            percent = (self.__false_answer / self.__challenge_data["question_count"]) * 100 
            sections.append(
                ft.PieChartSection(
                    percent,
                    title=f"{percent:.2f}%",
                    title_style=self.normal_title_style,
                    color=ft.colors.RED,
                    radius=self.normal_radius,
                    badge=self.badge(ft.icons.HIGHLIGHT_OFF, self.normal_badge_size),
                    badge_position=0.98,
                )
            )
            legends.append(
                ft.Container(
                    padding=ft.padding.only(left=5, top=5, bottom=5, right=15),
                    content=ft.Row(
                        controls=[ft.Icon(name=ft.icons.HIGHLIGHT_OFF), ft.Text(f"Ýalňyş jogap: {self.__false_answer}"),],
                        expand=True
                    )
                ),
            )
        if not self.__empty_answer == 0:
            percent = (self.__empty_answer / self.__challenge_data["question_count"]) * 100
            sections.append(
                ft.PieChartSection(
                    percent,
                    title=f"{percent:.2f}%",
                    title_style=self.normal_title_style,
                    color=ft.colors.GREY,
                    radius=self.normal_radius,
                    badge=self.badge(ft.icons.DND_FORWARDSLASH, self.normal_badge_size),
                    badge_position=0.98,
                )
            )
            legends.append(
                ft.Container(
                    padding=ft.padding.only(left=5, top=5, bottom=5, right=15),
                    content=ft.Row(
                        controls=[ft.Icon(name=ft.icons.DND_FORWARDSLASH), ft.Text(f"Jogapsyz: {self.__empty_answer}"),],
                        expand=True
                    )
                ),
            )

        self.chart = ft.PieChart(
            sections=sections,
            sections_space=0,
            center_space_radius=0,
            on_chart_event=self.on_chart_event,
            expand=True,
        )

        self.controls = [
            ft.AppBar(
                title=ft.Text("Netije"),
                bgcolor=ft.colors.SURFACE_VARIANT,
                center_title=True,
            ),
            ft.Row(controls=[self.chart]),
            ft.Row(controls=[ft.Column(controls=legends)], alignment=ft.MainAxisAlignment.CENTER),
        ]
        self.page.update()

    def badge(self, icon, size):
        return ft.Container(
            ft.Icon(icon),
            width=size,
            height=size,
            border=ft.border.all(1, ft.colors.BROWN),
            border_radius=size / 2,
            bgcolor=ft.colors.WHITE,
        )

    async def on_chart_event(self, e: ft.PieChartEvent):
        for idx, section in enumerate(self.chart.sections):
            if idx == e.section_index:
                section.radius = self.hover_radius
                section.title_style = self.hover_title_style
            else:
                section.radius = self.normal_radius
                section.title_style = self.normal_title_style
        await self.chart.update_async()


def main(page: ft.Page):

    # Параметры страницы
    login_page = LoginPage()
    challenges_page = None
    challenge_page = None
    results_page = None

    def route_change(e):
        global challenges_page, challenge_page, results_page
        page.views.clear()
        page.views.append(login_page)
        if page.route == "/challenges":
            challenges_page = ChallengesPage(login_page.get_token())
            page.views.append(challenges_page)
        if page.route == "/challenge":
            challenge_page = ChallengePage(
                challenges_page.get_selected_challenge(), login_page.get_token()
            )
            page.views.append(challenge_page)
        if page.route == "/results":
            results_page = ResultsPage(
                challenge_page.get_challenge_data(), login_page.get_token()
            )
            page.views.append(results_page)

        if page.route == "/":
            page.on_keyboard_event = login_page.focus
        else:
            page.on_keyboard_event = lambda e: None
        page.update()

    def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)
        page.update()

    page.title = "IT Meydança Quizz"
    page.scroll = ft.ScrollMode.AUTO
    page.window.maximized = True
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.MainAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.on_error = lambda e: print(f"{type(e.control)}: {e.data}")
    page.go(page.route)
    page.update()


ft.app(target=main)
