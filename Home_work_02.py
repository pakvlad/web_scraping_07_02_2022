# 2. Зарегистрироваться на https://openweathermap.org/api и написать функцию, которая получает погоду в данный момент для города,
# название которого получается через input. https://openweathermap.org/current
import time
import json
import requests

def get_data(service, appid, city):
    while True:
        time.sleep(1)
        url = f'{service}?q={city}&appid={appid}'
        response = requests.get(url)
        if response.status_code == 200:
            print(url)
            break
    return response.json()

appid = '58d09533756a1c09b57c6dbebb66865a'
service = 'http://api.openweathermap.org/data/2.5/weather'
city = input('Введите название города: ')
response = get_data(service, appid, city)

print('Получен результат')
print(response)

with open('1_2_weather.json', 'w') as f:
    json_repo = json.dump(response, f)
