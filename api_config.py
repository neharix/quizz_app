import os

import requests

RED = "\033[31m"
BLUE = "\033[34m"
LOW_INTENSITY = "\033[2m"  # Makes the following color less intense
RESET = "\033[0m"

dark_violet = f"{LOW_INTENSITY}{RED}{BLUE}"  # Combine codes for a dark violet effect
print(dark_violet + "Developed by neharix" + RESET)


api_url = ""


def reset_console():
    os.system("cls||clear")
    print(dark_violet + "Developed by neharix" + RESET)


is_correct_protocol = False

print("API taslamaňyz haýsy protokoly goldaýar:\n1 - HTTP\n2 - HTTPS\n")

while not is_correct_protocol:
    protocol_type = input("")
    if protocol_type == "1":
        api_url += "http://"
        is_correct_protocol = True
    elif protocol_type == "2":
        api_url += "https://"
        is_correct_protocol = True
    else:
        print("Dogry warianty saýlaň!")

reset_console()

is_correct_url = False

print("API taslamanyň IP ýa-da domen salgysyny giriziň:")

while not is_correct_url:
    url = input("")
    try:
        response = requests.request("GET", api_url + url + "/echo/")
        if response.status_code == 200:
            is_correct_url = True
            api_url += url
        else:
            print(
                "Eho funksiýasy jogap berip bilmedi. Taslamanyň eho funksiýasynyň ýagdaýyny barlaň!"
            )
            input("")
            exit()
    except requests.ConnectionError:
        print(
            "Berlen salgy bilen arabaglanyşyk gurulyp bilinmedi!\nInternet ýa-da Ethernet baglanyşygyňyzy barlamagyňyzy haýyş edýäris"
        )
        input("")
        exit()

reset_console()

is_accepted = False

while not is_accepted:
    accept = input(f'Berlen "{api_url}" URL tassyklaň [H/Ý]:')
    if accept.lower() == "h":
        with open("api", "w+") as file:
            file.write(api_url)
        print(
            "URL tassyklanyldy! Programmany soňlandyrmak üçin <Enter> düwmesine basyň..."
        )
        input()
        is_accepted = True
    elif accept.lower == "ý" or accept.lower() == "y":
        print(
            "URL tassyklanylmady! Programmany soňlandyrmak üçin <Enter> düwmesine basyň..."
        )
        input()
        is_accepted = True
    else:
        print("Hawa ýa-da ýok?[H/Ý]")
