from datetime import date

import requests
import yaml
from selenium import webdriver

# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

with open("./info.yml", "r") as file:
    info = yaml.safe_load(file)["services"]


def get_clients():
    with open("./clients.yml", "r") as file:
        return yaml.safe_load(file)


def initialize():
    driver = webdriver.Chrome()
    actions = ActionChains(driver)
    driver.implicitly_wait(10)
    return driver, actions


def send_text(
    message,
    to_number,
    from_number=info["openphone"]["main_number"],
    user_blame=info["openphone"]["users"]["maddy"]["id"],
):
    to_number = "+1" + to_number.strip("()- ")
    url = "https://api.openphone.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": info["openphone"]["key"],
    }
    data = {
        "content": message,
        "from": from_number,
        "to": [to_number],
        "userId": user_blame,
    }
    requests.post(url, headers=headers, json=data)


def check_q_done(driver, q_link):
    driver.implicitly_wait(10)
    url = q_link
    driver.get(url)

    complete = False

    if "mhs.com" in url:
        try:
            driver.find_element(
                By.XPATH, "//*[contains(text(), 'Thank you for completing')]"
            )
            complete = True
        except NoSuchElementException:
            complete = False
    elif "pearsonassessments.com" in url:
        try:
            driver.find_element(By.XPATH, "//*[contains(text(), 'Test Completed!')]")
            complete = True
        except NoSuchElementException:
            complete = False
    elif "wpspublish" in url:
        try:
            driver.find_element(
                By.XPATH,
                "//*[contains(text(), 'This assessment is not available at this time')]",
            )
            complete = True
        except NoSuchElementException:
            complete = False

    return complete


def check_questionnaires(driver):
    clients = get_clients()
    for id in clients:
        client = clients[id]
        for questionnaire in client["questionnaires"]:
            questionnaire["done"] = check_q_done(driver, questionnaire["link"])
    write_clients(clients)


def write_clients(clients):
    with open("./clients.yml", "w") as file:
        yaml.dump(clients, file, default_flow_style=False)


def format_appointment(client):
    appointment = client["appointment"]
    month = int(appointment[:2])
    day = int(appointment[2:4])
    year = int(appointment[4:])
    return date(year, month, day)


def check_appointment_distance(appointment: date):
    today = date.today()
    delta = appointment - today
    return delta.days


def all_questionnaires_done(client):
    return all(q["done"] for q in client["questionnaires"])


def main():
    driver, actions = initialize()
    check_questionnaires(driver)
    clients = get_clients()
    for id in clients:
        client = clients[id]
        distance = check_appointment_distance(format_appointment(client))
        done = all_questionnaires_done(client)
        if distance % 3 == 2 and not done:
            if distance >= 5:
                send_text("MESSAGE HERE", client["phone"])
            else:
                send_text(
                    f"{client['firstname']} {client['lastname']} has an appointment on {str(format_appointment(client))} and hasn't done everything, please call them.",
                    info["openphone"]["users"]["maddy"]["phone"],
                )
        if done:
            send_text(
                f"{client['firstname']} {client['lastname']} has finished their questionnares for an appointment on {str(format_appointment(client))}. Please generate.",
                info["openphone"]["users"]["maddy"]["phone"],
            )
            del clients[id]
        write_clients(clients)


main()

# TODO: Generate reports
