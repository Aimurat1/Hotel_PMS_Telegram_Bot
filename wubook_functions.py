import xmlrpc.client
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db, firestore, get_app, delete_app
# import google.cloud.firestore_v1 as google_cloud
import datetime
import json
import pytz
# import firebase_with_api as firebase


server = xmlrpc.client.Server('https://wired.wubook.net/xrws/')
token = "Wired API token"
lcode = 1111111


roomsID = {"double": 591608, "shared": 591614, "twins": 591613, "deluxe": 591612}
rooms_id_name = {591608: "double", 591614: "shared", 591613: "twins", 591612: "deluxe"}
rooms_id_arr = [591608, 591614, 591613, 591612]

channels_id = {0: "WooDoo", 2: "Booking", 43: "Airbnb"}


def get_availability_for_all(dfrom: datetime.datetime, dto: datetime.datetime):
    dto = dto - datetime.timedelta(days=1)
    
    dfrom = dfrom.strftime("%d/%m/%Y")
    dto = dto.strftime("%d/%m/%Y")
    
    # print(dfrom, dto)
    res, avail = server.fetch_rooms_values(token, lcode, dfrom, dto, rooms_id_arr)
    availability_per_room = {}
    for room in avail:
        avail_arr = []
        for avail_num in avail[str(room)]:
            avail_arr.append(avail_num['avail'])
        # avail_num = avail[str(room)][0]['avail']
        name = rooms_id_name[int(room)]
        availability_per_room[name] = avail_arr
        
    return availability_per_room

def get_availability_for_single(room_type: str, dfrom: datetime.datetime, dto: datetime.datetime):
    dto = dto - datetime.timedelta(days=1)
   
    dfrom = dfrom.strftime("%d/%m/%Y")
    dto = dto.strftime("%d/%m/%Y")
    room_id = roomsID[str(room_type)]
    res, avail = server.fetch_rooms_values(token, lcode, dfrom, dto, room_id)
    avail_arr = []
    for avail_num in avail[str(room_id)]:
        avail_arr.append(avail_num['avail'])
    return avail_arr

def price_for_room(room_type: str):
    room_id = roomsID[str(room_type)]
    
    today = datetime.datetime.now(tz=pytz.timezone("Asia/Almaty"))
    tomorrow = today + datetime.timedelta(days=1)
    
    today_str = today.strftime("%d/%m/%Y")
    tomorrow_str = tomorrow.strftime("%d/%m/%Y")
    
    pricing_plans = {
        "booking": 216197,
        "woodoo": 216198,
        "airbnb": 216199
    }
    
    res, prices = server.fetch_plan_prices(token, lcode, pricing_plans['woodoo'], today_str, tomorrow_str)
    return prices[str(room_id)][0]

def new_booking(booking_details: dict):
    
    room_id = roomsID[str(booking_details['room_type'])]
    
    rooms = {str(room_id): [1, "nb"]}
    customer = {'fname': booking_details['name'], 'lname': booking_details['surname'], 'email': booking_details['email'], "city": "--", "street": "--", "country": "--", "lang": "--", "phone": booking_details['phonenumber']}
    guests = {'men': int(booking_details['number_of_people']), 'children': 0}
    
    dfrom = booking_details["dfrom"].strftime("%d/%m/%Y")
    dto = booking_details["dto"].strftime("%d/%m/%Y")
    
    res1, room = server.fetch_single_room(token, lcode, str(room_id), 0)
    price = room[0]['price']
    
    delta = booking_details["dto"] - booking_details["dfrom"]
    number_of_nights = delta.days
    
    total_price = number_of_nights*price
    
    res, new_booking = server.new_reservation(token, lcode, dfrom, dto, rooms, customer, str(total_price), "Bot booking", 0, 0, guests, 0, 1, 1)
    
    if(res == 0):
        return True
    else:
        return False
    
def cancel_booking(rcode: str):
    res, cancel = server.cancel_reservation(token, lcode, rcode, "Отменено гостем", 1)
    
    if res == 0:
        return True
    else:
        return False
    
def change_room(booking_details: dict):
    
    cancel_booking(booking_details['rcode'])
    
    room_id = roomsID[str(booking_details['room_type'])]
    
    rooms = {str(room_id): [int(booking_details['room_amount']), "nb"]}
    customer = {'fname': booking_details['name'], 'lname': booking_details['surname'], 'email': booking_details['email'], "city": "--", "street": "--", "country": "--", "lang": "--", "phone": booking_details['phonenumber']}
    guests = {'men': int(booking_details['number_of_people']), 'children': 0}
    
    dfrom = booking_details["dfrom"].strftime("%d/%m/%Y")
    dto = booking_details["dto"].strftime("%d/%m/%Y")
    
    res1, room = server.fetch_single_room(token, lcode, str(room_id), 0)
    price = room[0]['price']
    
    delta = booking_details["dto"] - booking_details["dfrom"]
    number_of_nights = delta.days
    
    total_price = number_of_nights*price*int(booking_details['room_amount'])
    
    res, new_booking = server.new_reservation(token, lcode, dfrom, dto, rooms, customer, str(total_price), "Bot booking", 0, 0, guests, 0, 1, 1)
    
    if(res == 0):
        return True
    else:
        return False
    
def make_no_show_guest(rcode: int, with_penalty:bool):
    res, status = server.bcom_notify_noshow(token, lcode, rcode, with_penalty)
    
    return res, status

def make_no_ota_for_day(date: datetime.datetime, value: bool):
    
    date_str = date.strftime("%d/%m/%Y")
    
    roomdays = []
    
    if value == True:
        no_ota = 1
    else: no_ota = 0
    
    for room in roomsID:
        roomdays.append({
            "id": roomsID[room],
            "days": [{"no_ota": no_ota}]
        })
        
    print(date_str)
    print(roomdays)
    
    res = server.update_avail(token, lcode, date_str, roomdays)
    
    return True if res[0] == 0 else False

def main():
    
    pass

if __name__ == "__main__":
    main()