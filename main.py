import random

import flet as ft
import requests

import components
import views

api_url = ""
token = ""


def main(page: ft.Page):

    # Параметры страницы
    login_page = views.LoginPage()
    challenges_page = None
    challenge_page = None
    results_page = None

    def route_change(e):
        global challenges_page, challenge_page, results_page
        page.views.clear()
        page.views.append(login_page)
        if page.route == "/challenges":
            challenges_page = views.ChallengesPage(login_page.get_token())
            page.views.append(challenges_page)
        if page.route == "/challenge":
            challenge_page = views.ChallengePage(
                challenges_page.get_selected_challenge(), login_page.get_token()
            )
            page.views.append(challenge_page)
        if page.route == "/results":
            results_page = views.ResultsPage(
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


ft.app(target=main, assets_dir="assets", view=ft.WEB_BROWSER)
