import requests
import multiprocessing
import reactivex
from reactivex.scheduler import ThreadPoolScheduler
from reactivex import operators as ops, Subject
apikey1 = "6cbf889c-9cf7-467c-8697-4618a410968b"
apikey2 = "11eae46ab12978396655f0cdc63b3777"
apikey3 = "5ae2e3f221c38a28845f05b6fee4fb8a2ef7c45e1adaf24cdc80886c"


class Data:
    lat = 0
    lng = 0
    coords = []
    locations = []
    response = None
    subject = Subject()
    optimal_thread_count = multiprocessing.cpu_count()
    pool_scheduler = ThreadPoolScheduler(optimal_thread_count)

    def parse_locations(self):
        for i in self.response['hits']:
            try:
                result_string = i['country'] + " "
                try:
                    result_string += i['state'] + " "
                except Exception:
                    pass
                try:
                    result_string += i['city'] + ""
                except Exception:
                    pass
                self.locations.append(result_string)
                self.coords.append((i['point']['lat'], i['point']['lng']))
            except Exception:
                pass

    def set_location(self, number):
        try:
            self.lat, self.lng = self.coords[int(number) - 1]
            return 0
        except Exception:
            return 1

    def get_weather(self, request):
        reactivex.of(request).pipe(
            ops.map(lambda s: get_response(s)), ops.subscribe_on(self.pool_scheduler)
        ).subscribe(
            on_next=lambda s: self.print_weather(self.parse_weather(s)),
            on_error=lambda e: print(e),
        )

    def get_place(self, request, sec_request):
        reactivex.of(request).pipe(
            ops.map(lambda s: get_response(s)), ops.subscribe_on(self.pool_scheduler)
        ).subscribe(
            on_next=lambda s: self.parse_description(self.parse_places(s, sec_request)),
            on_error=lambda e: print(e),
        )

    def parse_weather(self, response):
        try:
            return (response['weather'][0]['description'], int(response['main']['temp'] - 273.15),
                    response['main']['pressure'], response['visibility'], response['wind']['speed'])
        except Exception as e:
            print(e)

    def parse_places(self, resp, request):
        try:
            places_names = []
            places_xids = []
            for place in resp:
                if place['name'] != "":
                    places_names.append(place['name'])
                    places_xids.append(place['xid'])
            return places_names, places_xids, request
        except Exception as e:
            print(e)

    def get_description(self, text):
        try:
            return text['wikipedia_extracts']['text']
        except Exception:
            return "(Нет описания)"

    def parse_description(self, resp):
        names, xids, request = resp
        print("Места:")
        reactivex.of(*xids).pipe(
            ops.map(lambda s: (names[xids.index(s)], self.get_description(get_response(request[0] + s + request[1]))))
        ).subscribe(
            on_next=lambda s: self.print_description(s),
            on_error=lambda e: print(e),
        )
        return 1

    def print_locations(self):
        for i in range(len(self.locations)):
            print("Номер", i + 1, ":", self.locations[i], "\n----------")

    def print_weather(self, resp):
        print("Погода:", resp[0], "\nТемпература =", resp[1], "(Градусов Цельсия)\nДавление =", resp[2],
              "(гПа)\nВидимость =", resp[3], "(метров)\nСкорость ветра =", resp[4], "(м/сек)\n----------")

    def print_description(self, resp):
        name, description = resp
        print(name, "\n", description, "\n----------")


def get_response(request):
    response = requests.get(request)
    if response:
        return response.json()
    else:
        print("Ошибка запроса:")
        print(request)
        print("Http status:", response.status_code, "(", response.reason, ")")


def get_location(data):
    data.response = get_response(f'https://graphhopper.com/api/1/geocode?q={input("Введите название локации: ")}&lo'
                                 f'cale=ru&key=' + apikey1)
    data.parse_locations()
    data.print_locations()
    return data.set_location(input("Введите номер локации: "))


def get_info(data):
    response1 = f'https://api.opentripmap.com/0.1/ru/places/radius?lon={data.lng}&lat={data.lat}&form' \
                f'at=json&radius=500&apikey=' + apikey3
    response2 = f'https://api.openweathermap.org/data/2.5/weather?lat={data.lat}&lon={data.lng}&lang=ru&appi' \
                f'd=' + apikey2
    response3 = ['https://api.opentripmap.com/0.1/ru/places/xid/', '?format=json&radius=500&apikey=' + apikey3]
    data.get_weather(response2)
    data.get_place(response1, response3)


if __name__ == "__main__":
    data = Data()
    if get_location(data) == 0:
        get_info(data)
    else:
        print("Не найдено")
