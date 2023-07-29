import requests 
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable
from itertools import count


def get_headhunter_salary(vacancies):
    total_salary = 0
    vacancies_count = 0
    for vacancy in vacancies:  
        payment = vacancy.get("salary")
        if payment:
            salary_from = payment['from']
            salary_to = payment['to']
            salary = predict_rub_salary(salary_from, salary_to)
            if salary:
                total_salary += salary
                vacancies_count += 1
    average_salary = 0
    if vacancies_count:
        average_salary = total_salary / vacancies_count
    return vacancies_count, average_salary


def get_superjob_payment(vacancies):
    total_salary = 0
    vacancies_count = 0
    for vacancy in vacancies:
        salary_from = vacancy.get("payment_from")
        salary_to = vacancy.get("payment_to")
        salary = predict_rub_salary(salary_from, salary_to)
        if salary:
            total_salary += salary
            vacancies_count += 1
    average_salary = 0
    if vacancies_count:
        average_salary = total_salary / vacancies_count
    return vacancies_count, average_salary


def predict_rub_salary(payment_from, payment_to):
    if payment_from and payment_to:
        salary = (payment_from + payment_to)/2
    elif payment_from :
        salary = payment_from * 1.2
    elif payment_to:
        salary = payment_to * 0.8
    else:
        salary =  None
    return salary


def get_vacancies_superjob(superjob_secret_key, language):
    superjob_url = f"https://api.superjob.ru/2.0/vacancies"
    headers = {
        "X-Api-App-Id" : superjob_secret_key
    }
    params = {
        "keyword" : f"Программист {language}",
        "town" : "Москва",
    }
    vacancies_sj = []
    for page in count(0):
        params['page'] = page
        response = requests.get(superjob_url, headers=headers, params=params)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            if response.status_code == 400:
                print(f"Bad request occurred. Exiting pagination loop.")
                break
            else:
                raise ex
        response = response.json()
        vacancies_sj.extend(response.get('objects'))
        if not response.get('more'):
            break
    return vacancies_sj


def get_vacancies_headhunter(language):
    hh_url = "https://api.hh.ru/vacancies"
    vacancies_hh = []
    params = {
        "text" : f"Программист {language}",
        "area" : "1",
        "cuurency" : "RUR"
    }
    for page in count(0):
        try:
            response = requests.get(hh_url, params=params)
            params["page"] = page
            response.raise_for_status()
            response = response.json()
            vacancies_hh.extend(response.get("items", []))
            if page >= response['pages']:
                break
        except requests.exceptions.HTTPError:
            continue
    return vacancies_hh
        

def make_table(languages, languages_rate, table_name):
    full_table = [["Язык программирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"]]
    for language in languages:
        table_params = [
            language, languages_rate[language]["vacancies_found"], languages_rate[language]["vacancies_processed"], languages_rate[language]["average_salary"]
        ]
        full_table.append(table_params)
    table = AsciiTable(full_table, table_name)
    return table


def make_superjob_languages_rate(superjob_secret_key, languages):
    languages_rate_sj = {}
    for language in languages:   
        vacancies_sj = get_vacancies_superjob(superjob_secret_key, language)
        try:
            vacancies_count, average_salary = get_superjob_payment(vacancies_sj)
            languages_rate_sj[language] = {
                "vacancies_found" : len(vacancies_sj),
                "vacancies_processed" : vacancies_count,
                "average_salary" : int(average_salary)
            }       
        except TimeoutError:
            ("Прошло слишком много времени на обработку информации, переходим к следующей вакансии")
            continue
    return languages_rate_sj


def make_headhunter_languages_rate(languages):
    languages_rate_hh = {}   
    for language in languages:
        vacancies_hh = get_vacancies_headhunter(language)
        try:
            vacancies_count, average_salary = get_headhunter_salary(vacancies_hh)
            languages_rate_hh[language] = {
                "vacancies_found" : len(vacancies_hh),
                "vacancies_processed" : vacancies_count,
                "average_salary" : int(average_salary)
            }
        except TimeoutError:
            ("Прошло слишком много времени на обработку информации, переходим к следующей вакансии")
            continue
    return languages_rate_hh


def main():
    load_dotenv()
    superjob_secret_key = os.environ["SUPERJOB_SECRET_KEY"]    
    languages = ["JavaScript", "Java", "Python", "PHP", "C++", "C#", "C", "Go"]
    languages_rate_sj = make_superjob_languages_rate(superjob_secret_key, languages)
    languages_rate_hh = make_headhunter_languages_rate(languages)
    table_sj = make_table(languages, languages_rate_sj, "SuperJob Moscow")
    table_hh = make_table(languages, languages_rate_hh, "HeadHunter Moscow")
    print(table_sj.table, table_hh.table)


if __name__ == "__main__":
    main()
