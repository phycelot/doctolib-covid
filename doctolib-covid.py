import datetime
import requests
import time
import json
import webbrowser

OPEN_BROWSER = True

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

with open('centers-url.txt') as centers_url_txt:
    centers_urls = centers_url_txt.readlines()
centers_urls = [center.strip() for center in centers_urls
                if not center.startswith("#")]

try:
    print("I solemnly swear that I am up to no good.")
    print()

    old_practice_ids = []
    while True:
        for center_url in centers_urls:
            try:
                center = center_url.split("/")[5]
                raw_data = requests.get("https://www.doctolib.fr/booking/{}.json".format(center),
                                        headers=HEADERS)
                json_data = raw_data.json()
                if json_data.get("status") == 404:
                    print("Center {} not found".format(center))
                    print(json_data)
                    continue
                data = json_data["data"]

                visit_motives = [visit_motive for visit_motive in data["visit_motives"]
                                 if visit_motive["name"].startswith("1re injection") and
                                 "AstraZeneca" not in visit_motive["name"]]
                if not visit_motives:
                    continue

                places = [place for place in data["places"]]
                if not places:
                    continue

                for place in places:

                    start_date = datetime.datetime.today().date().isoformat()
                    visit_motive_ids = visit_motives[0]["id"]
                    practice_id = place["practice_ids"][0]
                    place_name = place["formal_name"]
                    place_address = place["full_address"]

                    agendas = [agenda for agenda in data["agendas"]
                               if agenda["practice_id"] == practice_id and
                               not agenda["booking_disabled"] and
                               visit_motive_ids in agenda["visit_motive_ids"]]
                    if not agendas:
                        continue

                    agenda_ids = "-".join([str(agenda["id"])
                                           for agenda in agendas])

                    response = requests.get(
                        "https://www.doctolib.fr/availabilities.json",
                        params={
                            "start_date": start_date,
                            "visit_motive_ids": visit_motive_ids,
                            "agenda_ids": agenda_ids,
                            "practice_ids": practice_id,
                            "insurance_sector": "public",
                            "destroy_temporary": "true",
                            "limit": 2
                        },
                        headers=HEADERS
                    )
                    response.raise_for_status()
                    nb_availabilities = response.json()["total"]

                    custom_center_url = center_url + \
                        "?pid=practice-"+str(practice_id)
                    result = datetime.datetime.now().strftime("%H:%M:%S") + " " + str(nb_availabilities) + \
                        " appointments are available : " + custom_center_url
                    if nb_availabilities > 0 and practice_id not in old_practice_ids:
                        old_practice_ids.append(practice_id)
                        print(result)
                        if OPEN_BROWSER:
                            webbrowser.open_new_tab(custom_center_url)
            except json.decoder.JSONDecodeError:
                print("Doctolib might be ko")
            except KeyError as e:
                print("KeyError: " + str(e))
        time.sleep(5)
except KeyboardInterrupt:
    print("Mischief managed.")
