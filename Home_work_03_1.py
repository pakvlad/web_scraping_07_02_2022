import json
import os
import re
import time
from pprint import pprint
from typing import Optional
import requests
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from bson import Objected
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class Status:
    NOT_FOUND_404 = 404
    OK_200 = 200

class FileMode:
    READ = "r"
    WRITE = "w"

    def __init__(
            self,
            vacancy_name: str,
            salary_minimum: Optional[int],
            salary_maximum: Optional[int],
            salary_currency: Optional[str],
            vacancy_link: str,
            vacancy_site: str
    ):

        self.vacancy_link = vacancy_link
        self.vacancy_site = vacancy_site

    def to_dict(self):
        return {
            'vacancy_name': self.vacancy_name,
            'salary_minimum': self.salary_minimum,
            'salary_maximum': self.salary_maximum,
            'salary_currency': self.salary_currency,
            'vacancy_link': self.vacancy_link,
            'vacancy_site': self.vacancy_site,
        }

    def __str__(self):
        return (f'{self.vacancy_name} ::: salary from {self.salary_maximum} '
                f'to {self.salary_minimum} {self.salary_currency} ::: '
                f'{self.vacancy_link} in {self.vacancy_site}')

    def __repr__(self):
        return (f"VacancyItemDTO({self.vacancy_name}, {self.salary_minimum},"
                f" {self.salary_maximum}, {self.salary_currency}, "
                f"{self.vacancy_link}, {self.vacancy_site})")

class AbstractScrapper(ABC):
    collected_data = []

    new_db_items_count = 0

    def __init__(self, search_text: str, number_of_pages: int):
        self.search_text = search_text
        self.number_of_pages = number_of_pages

            print(f"Собрали страницу {page + 1} из {self.number_of_pages}...")
            time.sleep(1)

        print(f'Новых записей в БД {self.new_db_items_count}')
        self.__save_data_to_json_file()


    def __leave_only_numbers(self, string: str):
        """ Return number from string. """
        return int(re.sub(r'[^0-9]', '', string))


    def __get_clean_vacancy_compensation(self, raw_string: str) -> tuple:
        """ Return tuple (salary_minimum, salary_maximum, salary_currency)
        from raw_string"""
        minimum, maximum, currency = None, None, None
        split_raw_salary = raw_string.split(' ')
        if 'от' in raw_string:
            minimum = self.__leave_only_numbers(
                split_raw_salary[-2]
            )
        if 'до' in raw_string:
            maximum = self.__leave_only_numbers(
                split_raw_salary[-2]
            )
        if '–' in raw_string:
            minimum = self.__leave_only_numbers(
                split_raw_salary[0]
            )
            maximum = self.__leave_only_numbers(
                split_raw_salary[-2]
            )

        currency = split_raw_salary[-1]
        return minimum, maximum, currency


    def __print_mongo_docs(self, cursor):
        for doc in cursor:
            pprint(doc)


    def __cursor_len(self, cursor):
        return sum([1 for _ in cursor])


    def __add_vacancy_to_mongo(self, vacancy: VacancyItemDTO):
        """ Add vacancy in VacancyItemDTO format to MongoDB. """
        with MongoClient(
                os.getenv('MONGO_HOST'),
                int(os.getenv('MONGO_PORT'))
        ) as clieent:
            db = clieent[os.getenv('MONGO_DB')]
            collection = db[os.getenv('MONGO_COLLECTION')]

            cursor = collection.find(
                vacancy.__dict__,
            )
            count_cursor = cursor.clone()

            if not self.__cursor_len(count_cursor):
                collection.insert_one(vacancy.__dict__)
                self.new_db_items_count += 1

    def __parse_and_add_data(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')

        vacancy_items = soup.findAll(attrs={'class': 'vacancy-serp-item'})
                attrs={'data-qa': 'vacancy-serp__vacancy-compensation'}
            )
            if vacancy_compensation:
                salary_minimum, salary_maximum, salary_currency = \
                    self.__get_clean_vacancy_compensation(
                        vacancy_compensation.text
                    )
            else:
                salary_minimum = None
                salary_maximum = None
                salary_currency = None

            some_vacancy = VacancyItemDTO(
                vacancy_name = vacancy_title.text,
                salary_minimum = salary_minimum,
                salary_maximum = salary_maximum,
                salary_currency = salary_currency,
                vacancy_link = vacancy_title.attrs['href'],
                vacancy_site = self.vacancy_site

            self.collected_data.append(some_vacancy)
            self.__add_vacancy_to_mongo(some_vacancy)


    def __save_data_to_json_file(self, verbose=True):
        print(self.collected_data)


        with open(
                self.JSON_FILE,
                mode=FileMode.WRITE,
                encoding="utf-8"
        ) as f:
            json.dump(
                self.collected_data,
                f,
                indent=4,
                default=lambda obj: obj.to_dict(),
                ensure_ascii=False
            )


        if verbose:
            print(f"Записан json файл {self.JSON_FILE}. "
                  f"Всего записей {len(self.collected_data)}")


    def __get_response(self, page_number: int):
        headers = {
        return VacancyScrapper(sites, search_text, number_of_pages)

class GetMongoData:
    MONGO_HOST = os.getenv('MONGO_HOST')
    MONGO_PORT = int(os.getenv('MONGO_PORT'))
    MONGO_DB = os.getenv('MONGO_DB')
    MONGO_COLLECTION = os.getenv('MONGO_COLLECTION')

    def __init__(self):
        pass

    def __find_for_salary_more_then(self, salary: int):
        with MongoClient(
                self.MONGO_HOST,
                self.MONGO_PORT
        ) as client:
            db = client[self.MONGO_DB]
            collection = db[self.MONGO_COLLECTION]

            cursor = collection.find({
                "salary_minimum": {"$gt": salary},
            })
            count_cursor = cursor.clone()
            print('-' * 20)
            if not self.__cursor_len(count_cursor):
                print(f'В БД нет зарплат более {salary}')
            else:
                print(
                    f'Вот вакансии с зарплатой больше чем {salary} ,без учета '
                    f'валюты: ')
            self.__print_mongo_docs(cursor)

    def __print_mongo_docs(self, cursor):
        for doc in cursor:
            pprint(doc)

    def __cursor_len(self, cursor):
        return sum([1 for _ in cursor])

    @staticmethod
    def salary_more_then(
            salary: int
    ):
        return GetMongoData().__find_for_salary_more_then(salary)

if __name__ == '__main__':
    VacancyScrapper.by_sites(
        sites=['HeadHunter', 'SuperJob'],
        search_text='python',
        number_of_pages=5
    )
    GetMongoData.salary_more_then(50000)