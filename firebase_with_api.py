import firebase_admin
from firebase_admin import credentials
from firebase_admin import db, firestore, storage
import google.cloud.firestore_v1 as google_cloud
import datetime
import json
import pytz
import copy
import os, re
from utils.random_symbols import random_symbols
import utils.currency_converter as converter

import time

cred = credentials.Certificate("firebase_test.json")


firebase_admin.initialize_app(cred, {'storageBucket': ''})


db = firestore.client()

    
def isGuestByPhoneNumber(phone_number):
    docs = db.collection('guests').where('phone_number', '==', '+77087254390').stream()
    return docs is not None

def getGuestIdByPhoneNumber(phone_number):
    docs = db.collection('guests').where('phone_number', '==', phone_number).stream()
    for doc in docs:
        return doc.id
    
    
def isBookingByPhoneNumber(phone_number):
    id = getGuestIdByPhoneNumber(phone_number)
    collection = db.collection('guests').document(id).collection('booking')

    return collection.stream() is not None


def getBookingByPhoneNumber(phone_number):
    id = getGuestIdByPhoneNumber(phone_number)
    
    if id is None:
        return None
    
    collection = db.collection('guests').document(id).collection('booking').where('checked_out', '==', False)
    bookings = []
    for doc in collection.stream():
        booking = doc.to_dict()
        if(booking['status'] != 1):
            continue
        booking['user_id'] = id
        booking['id'] = doc.id
        booking['checkin_date'] = datetime.datetime.strptime(booking['checkin_date'], "%Y-%m-%d")
        booking['checkout_date'] = datetime.datetime.strptime(booking['checkout_date'], "%Y-%m-%d")
        if booking['room_number'] is None or booking['room_number'] == "" or (type(booking['room_number']) == list and len(booking['room_number']) == 0):
            booking['room_number'] = booking['room_type']
        bookings.append(booking)
    
    return bookings

def getBookingByRcode(rcode):

    collection = db.collection_group('booking').where("reservation_code", "==", int(rcode)).where('checked_out', '==', False)
    
    bookings = []
    for doc in collection.stream():
        booking = doc.to_dict()
        if(booking['status'] != 1):
            continue
        booking['id'] = doc.id
        booking['checkin_date'] = datetime.datetime.strptime(booking['checkin_date'], "%Y-%m-%d")
        booking['checkout_date'] = datetime.datetime.strptime(booking['checkout_date'], "%Y-%m-%d")
        if booking['room_number'] is None or booking['room_number'] == "" or (type(booking['room_number']) == list and len(booking['room_number']) == 0):
            booking['room_number'] = booking['room_type']
        bookings.append(booking)
    
    return bookings
    
def getUserByPhoneNumber(phone_number):
    docs = db.collection('guests').where('phone_number', '==', phone_number).stream()
    for doc in docs:
        user = doc.to_dict()
        user['id'] = doc.id
        return user
    
def addCancelBookingRequest(phone_number, booking):
    user_id = getGuestIdByPhoneNumber(phone_number)
    booking_id = booking["id"]
    collection_query = db.collection('admin_requests')
    docs = collection_query.where('user_id', '==', user_id).get()
    
    if len(docs) == 0:

        added_doc = collection_query.document()
        added_doc.set({
            'user_id': user_id
        })
        collection_query.document(added_doc.id).collection('cancel_booking').add({
                'booking_id': booking_id,
                'approved': False
        })
    else:
        for doc in docs:
            cancels = collection_query.document(doc.id).collection('cancel_booking').where("booking_id", "==", booking_id).get()
            if len(cancels) == 0:
                collection_query.document(doc.id).collection('cancel_booking').add({
                    'booking_id': booking_id,
                    'approved': False
                })
        
def approveBookingRequest(phone_number, booking_id, type):
    user_id = getGuestIdByPhoneNumber(phone_number)

    update_data = {'approved' : True}
    
    collection_query = db.collection('admin_requests')
    docs = collection_query.where('user_id', '==', user_id).get()
    
    for doc in docs:
        sub_docs = collection_query.document(doc.id).collection(type).where('booking_id', '==', booking_id).get()
        for sub_doc in sub_docs:
            collection_query.document(doc.id).collection(type).document(sub_doc.id).update(update_data)

def addEditDatesBookingRequest(phone_number, booking, new_dates):
    user_id = getGuestIdByPhoneNumber(phone_number)
    booking_id = booking["id"]
    collection_query = db.collection('admin_requests')
    docs = collection_query.where('user_id', '==', user_id).get()
    
    if len(docs) == 0:
        added_doc = collection_query.document()
        added_doc.set({
            'user_id': user_id
        })
        collection_query.document(added_doc.id).collection('edit_dates').add({
                'booking_id': booking_id,
                'new_checkin_date': new_dates['checkin_date'],
                'new_checkout_date': new_dates['checkout_date'],
                'approved': False
        })
    else:
        for doc in docs:
            edit_dates = collection_query.document(doc.id).collection('edit_dates').where("booking_id", "==", booking_id).get()
            if len(edit_dates) == 0:
                collection_query.document(doc.id).collection('edit_dates').add({
                    'booking_id': booking_id,
                    'new_checkin_date': new_dates['checkin_date'],
                    'new_checkout_date': new_dates['checkout_date'],
                    'approved': False
                })
            else:
                for edit_date in edit_dates:
                    collection_query.document(doc.id).collection('edit_dates').document(edit_date.id).update({
                        'approved': False,
                        'new_checkin_date': new_dates['checkin_date'],
                        'new_checkout_date': new_dates['checkout_date']
                    })
                
                
def addEditRoomBookingRequest(phone_number, booking, new_room_type):
    user_id = getGuestIdByPhoneNumber(phone_number)
    booking_id = booking["id"]
    collection_query = db.collection('admin_requests')
    docs = collection_query.where('user_id', '==', user_id).get()
    
    if len(docs) == 0:
        added_doc = collection_query.document()
        added_doc.set({
            'user_id': user_id
        })
        collection_query.document(added_doc.id).collection('edit_room').add({
                'booking_id': booking_id,
                'new_room_type': new_room_type,
                'approved': False
        })
    else:
        for doc in docs:
            edit_rooms = collection_query.document(doc.id).collection('edit_room').where("booking_id", "==", booking_id).get()
            if len(edit_rooms) == 0:
                collection_query.document(doc.id).collection('edit_room').add({
                    'booking_id': booking_id,
                    'new_room_type': new_room_type,
                    'approved': False
                })
            else:
                for edit_room in edit_rooms:
                    collection_query.document(doc.id).collection('edit_room').document(edit_room.id).update({
                        'approved': False,
                        'new_room_type': new_room_type
                    })
                  
def getBookingRequests(phone_number, booking_id, type: str):
    user_id = getGuestIdByPhoneNumber(phone_number)
    collection_query = db.collection('admin_requests')
    docs = collection_query.where('user_id', '==', user_id).get()
    
    cancel_bookings = []
    for doc in docs:
        sub_docs = collection_query.document(doc.id).collection(type).where('booking_id', '==', booking_id).get()
        for sub_doc in sub_docs:
            cancel_bookings.append(sub_doc.to_dict())
    
    # print(cancel_bookings)
    return cancel_bookings        
    
def updateBookingDetails(phone_number, booking_id, dict_to_update):
    user_id = getGuestIdByPhoneNumber(phone_number)
    collection_query = db.collection('guests')
    
    collection_query.document(user_id).collection('booking').document(booking_id).update(dict_to_update)
    doc = collection_query.document(user_id).collection('booking').document(booking_id).get()
    
    booking = doc.to_dict()
    booking['id'] = doc.id
    booking['checkin_date'] = datetime.datetime.strptime(booking['checkin_date'], "%Y-%m-%d")
    booking['checkout_date'] = datetime.datetime.strptime(booking['checkout_date'], "%Y-%m-%d")
    return booking

def getRequestsByType(request_type, approved):
    requestArr = []
    collection_query = db.collection('admin_requests')
    docs = collection_query.stream()
    for doc in docs:
        requests = collection_query.document(str(doc.id)).collection(str(request_type)).stream()
        # print(requests)
        for request in requests:
            requestDict = request.to_dict()
            if(requestDict['approved'] == approved):
                print(requestDict)
                requestDoc = doc.to_dict()
                requestDict['request_id'] = doc.id
                requestDict['user_id'] = requestDoc['user_id']
                requestArr.append(requestDict)
            
    return requestArr

def getBookingById(user_id, booking_id):
    user = {}
    us = db.collection('guests').document(user_id).get()

    user = us.to_dict()
    
    booking = db.collection('guests').document(user_id).collection('booking').document(booking_id).get()

    user['booking'] = booking.to_dict()
    
    user['booking']['id'] = booking_id
    user['booking']['user_id'] = user_id
    
    user['booking']['checkin_date'] = datetime.datetime.strptime(user['booking']['checkin_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
    user['booking']['checkout_date'] = datetime.datetime.strptime(user['booking']['checkout_date'], "%Y-%m-%d").strftime("%d-%m-%Y")
        
    return user
    
def getBookingForRooms(indate):

    if type(indate) == str:
        indate = datetime.datetime.strptime(indate, "%Y-%m-%d")
    
    indate = indate.replace(tzinfo=pytz.timezone("Asia/Almaty"))
    
    indate_timestamp = int(indate.timestamp())
    print(indate_timestamp)
    
    rooms_occupation = {
        '1': None,
        '2': None,
        '3': None,
        '4': None,
        '5.1': None,
        '5.2': None,
        '5.3': None,
        '5.4': None,
        '5.5': None,
        '5.6': None,
        '6': None,
    }
    
    rooms = db.collection("room_occupation").stream()
    
    for room in rooms:
        room_dict = room.to_dict()
        rooms_occupation[str(room.id)] = room_dict
     
    return rooms_occupation   
    

rooms_id_name = {591608: "standard", 591614: "hostel", 591613: "twins", 591612: "lux"}
roomsID = {"standard": 591608, "hostel": 591614, "twins": 591613, "lux": 591612}

def getBookingForRoomTypes(indate):
    
    print(indate)

    if type(indate) == str:
        indate = datetime.datetime.strptime(indate, "%Y-%m-%d")
    
    indate = indate.replace(tzinfo=pytz.timezone("Asia/Almaty"))
    
    indate_timestamp = int(indate.timestamp())
    
    print(indate_timestamp)
    
    rooms_occupation = {
        'hostel': [],
        'standard': [],
        'twins': [],
        'lux': [],
    }
    
    print("Works!")
    
    
    for room_name in rooms_occupation:
        bookings = db.collection_group('booking').where("checkin_date_timestamp", "<=", indate_timestamp)\
                                            .where('room_type_id', 'array_contains', f'{roomsID[room_name]}').where("checked_out", "==", False)\
                                                .where("status", "==", 1).stream()
        
        
        for booking in bookings:
            booking_dict = booking.to_dict()
            user = getBookingById(booking_dict["user_id"], booking.id)    
            
            if(booking_dict['checkout_date_timestamp'] > indate_timestamp):
                user['checkout_today'] = False
                user['booking']['booking_id'] = booking.id
                rooms_occupation[f'{room_name}'].append(user)
            if(booking_dict['checkout_date_timestamp'] == int(indate_timestamp)):
                user['checkout_today'] = True
                user['booking']['booking_id'] = booking.id
                rooms_occupation[f'{room_name}'].append(user)
                
            if(booking_dict['checkin_date_timestamp'] == int(indate_timestamp)):
                user['checkin_today'] = True
            else:
                user['checkin_today'] = False

    
    print("Done")
    
    return rooms_occupation
    
def getBookingForDay(date = None, only_checkin: bool = None):
    if date is None : date = datetime.datetime.now(tz=pytz.timezone("Asia/Almaty")).strftime("%Y-%m-%d")
    
    if type(date) == str:
        date = datetime.datetime.strptime(date, "%Y-%m-%d")
    
    date = date.replace(tzinfo=pytz.timezone("Asia/Almaty"))
    
    indate_timestamp = date.timestamp()
    # print(indate_timestamp)
    
    bookings_for_day_dict = {
        "checkin": [],
        "checkout": []
    }
    
    checkin_bookings = db.collection_group('booking').where("checkin_date_timestamp", "==", indate_timestamp).stream()
                                        # .where("checked_out", "==", False).stream()
                                        
    for checkin_booking in checkin_bookings:
        booking_dict = checkin_booking.to_dict()
        if(booking_dict['status'] != 1):
            continue
        user = getBookingById(booking_dict["user_id"], checkin_booking.id)
        user['user_id'] = booking_dict["user_id"]
        user['booking']['booking_id'] = checkin_booking.id
        
        bookings_for_day_dict['checkin'].append(user)
        
    if(only_checkin is not None and only_checkin == True):
        return bookings_for_day_dict
        
    checkout_bookings = db.collection_group('booking').where("checkout_date_timestamp", "==", indate_timestamp).stream()
                                        # .where("checked_out", "==", False)\
                                        
                                        
    for checkout_booking in checkout_bookings:
        booking_dict = checkout_booking.to_dict()
        if(booking_dict['status'] != 1):
            continue
        user = getBookingById(booking_dict["user_id"], checkout_booking.id)
        user['user_id'] = booking_dict["user_id"]
        user['booking']['booking_id'] = checkout_booking.id
        bookings_for_day_dict['checkout'].append(user)
   
    return bookings_for_day_dict

#Найти бронь
    
def getBookingByFullName(fullname: str):
    nameArr = fullname.split(" ")
    name = nameArr[0]
    surname = nameArr[1]
    guestsArr = []
    
    guests = db.collection("guests").where("name", "==", name).where("lastname", "==", surname).stream()
    for guest in guests:
        guestDict = {}
        guestDict = guest.to_dict()
        guestDict['user_id'] = guest.id
        guestDict['booking'] = []
        bookings = db.collection("guests").document(guest.id).collection("booking").stream()
        for booking in bookings:
            bookingDict = booking.to_dict()
            bookingDict['booking_id'] = booking.id
            if(bookingDict['checked_out'] == False and bookingDict['status'] == 1):
                guestDict['booking'].append(bookingDict)
            
        guestsArr.append(guestDict)
    
    return guestsArr

def searchBookingByPhoneNumber(phone_number: str):
    phoneArr = [c for c in phone_number]
    # print(arr)
    if phoneArr[0] != "+":
        phone_number = '+'+phone_number
        
    guestsArr = []
    
    guests = db.collection("guests").where("phone_number", "==", phone_number).stream()
    for guest in guests:
        guestDict = {}
        guestDict = guest.to_dict()
        guestDict['user_id'] = guest.id
        guestDict['booking'] = []
        bookings = db.collection("guests").document(guest.id).collection("booking").stream()
        for booking in bookings:
            bookingDict = booking.to_dict()
            bookingDict['booking_id'] = booking.id
            if(bookingDict['checked_out'] == False and bookingDict['status'] == 1):
                guestDict['booking'].append(bookingDict)
            
        guestsArr.append(guestDict)
    
    return guestsArr

def getBookingByEmail(email: str):
    guestsArr = []
    
    guests = db.collection("guests").where("email", "==", email).stream()
    for guest in guests:
        guestDict = {}
        guestDict = guest.to_dict()
        guestDict['user_id'] = guest.id
        guestDict['booking'] = []
        bookings = db.collection("guests").document(guest.id).collection("booking").stream()
        for booking in bookings:
            bookingDict = booking.to_dict()
            bookingDict['booking_id'] = booking.id
            if(bookingDict['checked_out'] == False and bookingDict['status'] == 1):
                guestDict['booking'].append(bookingDict)
            
        guestsArr.append(guestDict)
    
    return guestsArr

def getStatusFromGuestBookingID(user_id: str, booking_id: str):
    statusDict = {}
    statuses = db.collection('guests').document(user_id).collection('booking').document(booking_id).collection('status').get()
    for status in statuses:
        return status.to_dict()
    
def approveStatusFromGuestBookingID(user_id: str, booking_id: str, status: str, value: bool = None):
    statuses = db.collection('guests').document(user_id).collection('booking').document(booking_id).collection('status').stream()
    for st in statuses:
        statusDict = st.to_dict()
        if value is None: value = not statusDict[str(status)]
        db.collection('guests').document(user_id).collection('booking').document(booking_id).collection('status')\
            .document(st.id).update({str(status): value})

def addCollectionToBooking():
    guests = db.collection('guests').stream()
    for guest in guests:
        bookings = db.collection('guests').document(guest.id).collection('booking').stream()
        for booking in bookings:
            statuses = db.collection('guests').document(guest.id).collection('booking').document(booking.id)\
                    .collection('status').stream()
            for status in statuses:
                db.collection('guests').document(guest.id).collection('booking').document(booking.id)\
                    .collection('status').document(status.id).update({
                        'user_id': guest.id,
                        'booking_id': booking.id,
                    })

def flatten(lst):
    flat_list = []
    for sublist in lst:
        for item in sublist:
            flat_list.append(item)
    return flat_list

def getCheckedInGuests() -> list: 
     
  

    statuses = db.collection_group("status").where("checked_in", "==", True).stream()
    
    guests = {}
    
    for status in statuses:
        status_dict = status.to_dict()
        try:
            user = getBookingById(status_dict['user_id'], status_dict['booking_id'])
        except:
            # print("Error")
            # print(status_dict)
            pass
        checkin = int(user['booking']['checkin_date_timestamp'])
        if checkin not in guests.keys():
            guests[checkin] = []
        guests[checkin].append(user)
    
    guests = dict(sorted(guests.items(),reverse=True)) 
    return flatten(list(guests.values()))
    return guests

def getBookingByStatus_1(status: str, value: bool) -> list:      
    statuses = db.collection_group("status").where("checked_out", "==", False).where(str(status), "==", bool(value)).stream()
    
    guests = []
    
    for status in statuses:
        status_dict = status.to_dict()
        try:
            user = getBookingById(status_dict['user_id'], status_dict['booking_id'])
        except:
            # print("Error")
            # print(status_dict)
            pass
        guests.append(user)
        
    return guests
     
def getBookingByStatus(status: str, value: bool) -> list:

    bookings = db.collection_group("booking").where("checked_out", "==", False).where("status", "==", 1).stream()
    
    guests = []
    
    for booking in bookings:
        booking_dict = booking.to_dict()
        status_dict = db.collection("guests").document(booking_dict['user_id']).collection("booking").document(booking.id).collection("status").get()[0].to_dict()
        
        if status_dict[str(status)] == value:
            user = getBookingById(booking_dict['user_id'], booking.id)

            
            guests.append(user)
            
    return guests
        
    


def setTelegramDetailsToUser(phonenumber: str, username: str, telegram_id: str):
    firebase_id = getGuestIdByPhoneNumber(phonenumber)
    dict_to_update = {
        'telegram_id': telegram_id,
        'telegram_username': username if username is not None else None
    }
    db.collection("guests").document(str(firebase_id)).update(dict_to_update)
    
def setTelegramDetailsToUserByID(user_id, username: str, telegram_id: str):
    dict_to_update = {
        'telegram_id': telegram_id,
        'telegram_username': username if username is not None else None
    }
    db.collection("guests").document(str(user_id)).update(dict_to_update)

def upload_photo_to_cloud_storage(filename):
    bucket = storage.bucket()
    blob = bucket.blob(f"passport/{filename}")
    blob.upload_from_filename(f"./media/passports/{filename}")
    
    os.remove(f"./media/passports/{filename}")
    
    blob.make_public()
    
    url = blob.public_url
    url += f"?id={random_symbols()}"
    
    return url
    # print(f"File {filename} uploaded to passport/{filename}.")
    
def get_links_from_storage():
    files = storage.Client(credentials=credentials).list_blobs(firebase_admin.storage.bucket().name) # fetch all the files in the bucket
    for i in files: print('The public url is ', i.public_url)
    
def put_link_passport_to_booking(user_id: str, booking_id: str, link_to_passport: str):
    db.collection('guests').document(user_id).collection('booking').document(booking_id).update({"passport_link": link_to_passport})
    
def updateBookingWithId(user_id: str, booking_id: str, dict_to_update: dict):
    for key in dict_to_update:
        if dict_to_update[key] == "DELETE_FIELD":
            dict_to_update[key] = firestore.DELETE_FIELD
            
    db.collection("guests").document(str(user_id)).collection('booking').document(str(booking_id)).update(dict_to_update)

def updateBookingWithId_array(user_id: str, booking_id: str, field: str, value_to_append: str):
    
    booking = db.collection("guests").document(str(user_id)).collection('booking').document(str(booking_id)).get()
    
    booking_dict:dict = booking.to_dict()
    
    if str(field) in booking_dict.keys() and type(booking_dict[str(field)]) is list:
        booking_array:list = booking_dict[str(field)]
    else:
        booking_array:list = []
    
    booking_array.append(value_to_append)
    
    db.collection("guests").document(str(user_id)).collection('booking').document(str(booking_id)).update({str(field): booking_array})
    
    


def updateRoomOccupancy(guest, room):
    
    rooms = {
            "5.1": "hostel",
            "5.2": "hostel", 
            "5.3": "hostel", 
            "5.4": "hostel", 
            "5.5": "hostel", 
            "5.6": "hostel", 
            "1": "standard",
            "2": "standard",
            "3": "standard",
            "4": "twins",
            "6": "lux"
    }
        
    if guest is None:
        db.collection('room_occupation').document(str(room)).set({
            'available': True,
            'type': rooms[str(room)]

        })
    else:
        newGuest = []
        
        for g in guest:
            newGuest.append({'checkout_today': g['checkout_today'], 'checkin_today': g['guest']['checkin_today'], 'guest': {'user_id': g['guest']['booking']['user_id'], 'booking_id': g['guest']['booking']['booking_id'], 'rcode': g['guest']['booking']['reservation_code']}})
        
        if len(guest) == 1 and guest[0]['checkout_today'] == True:
            db.collection('room_occupation').document(str(room)).set({
            'available': True,
            'guests': newGuest,
            'type': rooms[str(room)]
            })
        else:
            db.collection('room_occupation').document(str(room)).set({
                'available': False,
                'guests': newGuest,
                'type': rooms[str(room)]

            })

def updateRoomOccupancyTest(guest, room):
    
    rooms = {
            "5.1": "hostel",
            "5.2": "hostel", 
            "5.3": "hostel", 
            "5.4": "hostel", 
            "5.5": "hostel", 
            "5.6": "hostel", 
            "1": "standard",
            "2": "standard",
            "3": "standard",
            "4": "twins",
            "6": "lux"
    }
        
    if guest is None:
        db.collection('room_occupation_test').document(str(room)).set({
            'available': True,
            'type': rooms[str(room)]

        })
    else:
        newGuest = []
        
        for g in guest:
            newGuest.append({'checkout_today': g['checkout_today'], 'checkin_today': g['guest']['checkin_today'], 'guest': {'user_id': g['guest']['booking']['user_id'], 'booking_id': g['guest']['booking']['booking_id'], 'rcode': g['guest']['booking']['reservation_code']}})
        
        if len(guest) == 1 and guest[0]['checkout_today'] == True:
            db.collection('room_occupation_test').document(str(room)).set({
            'available': True,
            'guests': newGuest,
            'type': rooms[str(room)]
            })
        else:
            db.collection('room_occupation_test').document(str(room)).set({
                'available': False,
                'guests': newGuest,
                'type': rooms[str(room)]

            })
         
def assignGuestToRoomTest(guest, room_type_id):
    
    # dailyRoomOccupancyCheck()
    
    rooms_id_name = {591608: "standard", 591614: "hostel", 591613: "twins", 591612: "lux"}
    roomsID = {"standard": 591608, "hostel": 591614, "twins": 591613, "lux": 591612}
    
    rooms = db.collection('room_occupation_test').where("type", "==", rooms_id_name[int(room_type_id)]).where("available", "==", True).stream()
    
    today = datetime.datetime.now(tz=pytz.timezone("Asia/Almaty")).date()
    
    today = datetime.datetime.combine(today, datetime.time.min)
    
    # today = datetime.datetime(2023, 5, 7)
    
    guest_checkin_date = datetime.datetime.strptime(guest['checkin_date'], "%d-%m-%Y")
    guest_checkout_date = datetime.datetime.strptime(guest['checkout_date'], "%d-%m-%Y")

    
    print("Assign works")
    for room in rooms:
        print(room.id)
        print(room.to_dict())
        room_dict = room.to_dict()

        if "guests" not in room_dict.keys() or ("guests" in room_dict.keys() and len(room_dict['guests']) == 0):
            guests = []
            
            if guest_checkout_date == today:
                guests.append({'checkout_today': True, 'checkin_today': False, 'guest': {'booking_id': guest['id'], 'user_id': guest['user_id'], 'rcode': guest['reservation_code']}})
            else:
                guests.append({'checkout_today': False, 'checkin_today': True, 'guest': {'booking_id': guest['id'], 'user_id': guest['user_id'], 'rcode': guest['reservation_code']}})
            
            room_dict['available'] = False
            room_dict['guests'] = guests
            
                
            db.collection('room_occupation_test').document(room.id).update(room_dict)
            
            updateBookingWithId_array(user_id=guest['user_id'], booking_id=guest['id'], field="room_number", value_to_append=str(room.id))
            approveStatusFromGuestBookingID(user_id = guest['user_id'], booking_id = guest['id'], status = "checked_in", value = True)
            return room.id
            break
        
        elif len(room_dict['guests']) == 1 and room_dict['guests'][0]['checkout_today'] == True:
            
            if guest_checkin_date < today:
                print("Late checkin")
                continue

            guests = room_dict['guests']
            
            if guest_checkout_date == today:
                guests.append({'checkout_today': True, 'checkin_today': False, 'guest': {'booking_id': guest['id'], 'user_id': guest['user_id'], 'rcode': guest['reservation_code']}})
            else:
                guests.append({'checkout_today': False, 'checkin_today': True, 'guest': {'booking_id': guest['id'], 'user_id': guest['user_id'], 'rcode': guest['reservation_code']}})
            
            room_dict['available'] = False
            room_dict['guests'] = guests

            db.collection('room_occupation_test').document(room.id).update(room_dict)
            updateBookingWithId_array(user_id=guest['user_id'], booking_id=guest['id'], field="room_number",value_to_append=str(room.id))
            approveStatusFromGuestBookingID(user_id = guest['user_id'], booking_id = guest['id'], status = "checked_in", value = True)
            return room.id
            break
        
    return None


def assignGuestToRoom(guest, room_type_id):
    
    dailyRoomOccupancyCheck()
    
    rooms_id_name = {591608: "standard", 591614: "hostel", 591613: "twins", 591612: "lux"}
    roomsID = {"standard": 591608, "hostel": 591614, "twins": 591613, "lux": 591612}
    
    rooms = db.collection('room_occupation').where("type", "==", rooms_id_name[int(room_type_id)]).where("available", "==", True).stream()
    
    today = datetime.datetime.now(tz=pytz.timezone("Asia/Almaty")).date()
    
    today = datetime.datetime.combine(today, datetime.time.min)
    
    # today = datetime.datetime(2023, 5, 7)
    
    guest_checkin_date = datetime.datetime.strptime(guest['checkin_date'], "%d-%m-%Y")
    guest_checkout_date = datetime.datetime.strptime(guest['checkout_date'], "%d-%m-%Y")

    
    print("Assign works")
    for room in rooms:
        print(room.id)
        print(room.to_dict())
        room_dict = room.to_dict()
        if "guests" not in room_dict.keys() or ("guests" in room_dict.keys() and len(room_dict['guests']) == 0):
            guests = []
            
            if guest_checkout_date == today:
                guests.append({'checkout_today': True, 'checkin_today': False, 'guest': {'booking_id': guest['id'], 'user_id': guest['user_id'], 'rcode': guest['reservation_code']}})
            else:
                guests.append({'checkout_today': False, 'checkin_today': True, 'guest': {'booking_id': guest['id'], 'user_id': guest['user_id'], 'rcode': guest['reservation_code']}})

            room_dict['available'] = False
            room_dict['guests'] = guests
            
                
            db.collection('room_occupation').document(room.id).update(room_dict)
            
            updateBookingWithId_array(user_id=guest['user_id'], booking_id=guest['id'], field="room_number", value_to_append=str(room.id))
            approveStatusFromGuestBookingID(user_id = guest['user_id'], booking_id = guest['id'], status = "checked_in", value = True)
            return room.id
            break
        
        elif len(room_dict['guests']) == 1 and room_dict['guests'][0]['checkout_today'] == True:
            
            if guest_checkin_date < today:
                print("Late checkin")
                continue
            
            guests = room_dict['guests']
            
            if guest_checkout_date == today:
                guests.append({'checkout_today': True, 'checkin_today': False, 'guest': {'booking_id': guest['id'], 'user_id': guest['user_id'], 'rcode': guest['reservation_code']}})
            else:
                guests.append({'checkout_today': False, 'checkin_today': True, 'guest': {'booking_id': guest['id'], 'user_id': guest['user_id'], 'rcode': guest['reservation_code']}})
            
            room_dict['available'] = False
            room_dict['guests'] = guests

            db.collection('room_occupation').document(room.id).update(room_dict)
            updateBookingWithId_array(user_id=guest['user_id'], booking_id=guest['id'], field="room_number",value_to_append=str(room.id))
            approveStatusFromGuestBookingID(user_id = guest['user_id'], booking_id = guest['id'], status = "checked_in", value = True)
            return room.id
            break
        
    return None

def dailyRoomOccupancyCheck(room_number = None):
    today = datetime.datetime.now(tz=pytz.timezone("Asia/Almaty")).date()
    
    today = datetime.datetime.combine(today, datetime.time.min)
    
    print(today)
    # today = datetime.datetime(2023, 5, 5)
    
    today_timestamp = today.replace(tzinfo=pytz.timezone("Asia/Almaty")).timestamp()
    
    print(today_timestamp)
    if room_number is not None:
        room_dict = db.collection("room_occupation").document(str(room_number)).get().to_dict()
            
        if "guests" in room_dict.keys():
        
            guestsArr:list = []
            
            for i, guest in enumerate(room_dict['guests']):
                guest_dict = guest
                
                user_id = guest['guest']['user_id']
                booking_id = guest['guest']['booking_id']
                
                guestBooking = getBookingById(user_id, booking_id)
                
                if guestBooking['booking']['checkout_date_timestamp'] < today_timestamp:
                    # guestsArr.pop(i)
                    continue
                
                if guestBooking['booking']['checkin_date_timestamp'] == today_timestamp:
                    guest_dict['checkin_today'] = True
                else:
                    guest_dict['checkin_today'] = False
                    
                if guestBooking['booking']['checkout_date_timestamp'] == today_timestamp:
                    guest_dict['checkout_today'] = True
                else:
                    guest_dict['checkout_today'] = False
                    
                guestsArr.append(guest_dict)
                
            if len(guestsArr) == 0 or (len(guestsArr) == 1 and guestsArr[0]['checkout_today'] == True and guestsArr[0]['checkin_today'] == False):
                room_dict['available'] = True    
            
            room_dict['guests'] = guestsArr
            
        db.collection('room_occupation').document(str(room_number)).update(room_dict)

    else:
        rooms = db.collection('room_occupation').stream()
        
        roomsDict = {}
        
        for room in rooms:
            room_dict = room.to_dict()
            
            if "guests" in room_dict.keys():
            
                guestsArr:list = []
                
                for i, guest in enumerate(room_dict['guests']):
                    guest_dict = guest
                    
                    user_id = guest['guest']['user_id']
                    booking_id = guest['guest']['booking_id']
                    
                    guestBooking = getBookingById(user_id, booking_id)
                    
                    if guestBooking['booking']['checkout_date_timestamp'] < today_timestamp:
                        # guestsArr.pop(i)
                        continue
                    
                    if guestBooking['booking']['checkin_date_timestamp'] == today_timestamp:
                        guest_dict['checkin_today'] = True
                    else:
                        guest_dict['checkin_today'] = False
                        
                    if guestBooking['booking']['checkout_date_timestamp'] == today_timestamp:
                        guest_dict['checkout_today'] = True
                    else:
                        guest_dict['checkout_today'] = False
                        
                    guestsArr.append(guest_dict)
                    
                if len(guestsArr) == 0 or (len(guestsArr) == 1 and guestsArr[0]['checkout_today'] == True and guestsArr[0]['checkin_today'] == False):
                    room_dict['available'] = True    
                
                room_dict['guests'] = guestsArr
                
            db.collection('room_occupation').document(str(room.id)).update(room_dict)
            roomsDict[str(room.id)] = room_dict
        
        # print(json.dumps(roomsDict, indent=4))
        
        
def check_room_occupancy_if_delete(user_id, booking_id, rcode: int):
    booking = db.collection("guests").document(user_id).collection("booking").document(booking_id).get()
    booking_dict = booking.to_dict()
    
    if "room_number" in booking_dict.keys() and type(booking_dict["room_number"]) is list:
        for room_number in booking_dict['room_number']:
            room = db.collection("room_occupation").document(room_number).get().to_dict()
            
            room_guests:list = room['guests']
            
            for i, guest in enumerate(room_guests):
                if guest['guest']['rcode'] == rcode:
                    room_guests.pop(i)
            
            db.collection("room_occupation").document(room_number).update({"guests": room_guests})

            dailyRoomOccupancyCheck(str(room_number))
            
            approveStatusFromGuestBookingID(user_id, booking_id, "checked_in", False)               

def delete_room_number_from_booking(user_id, booking_id, room_number):
    print("Start")
    booking = db.collection("guests").document(user_id).collection('booking').document(booking_id).get().to_dict()
    
    room_number_list:list = booking['room_number']
    
    try:
        i = room_number_list.index(str(room_number)) # Find the index of '32'
        room_number_list.pop(i) # Remove it by index
    except ValueError:
        pass
    
    db.collection("guests").document(user_id).collection('booking').document(booking_id).update({"room_number":room_number_list})

    print("END")

def check_room_occupancy_if_delete_test(user_id, booking_id, rcode: int):
    booking = db.collection("guests").document(user_id).collection("booking").document(booking_id).get()
    booking_dict = booking.to_dict()
    
    if "room_number" in booking_dict.keys() and type(booking_dict["room_number"]) is list:
        for room_number in booking_dict['room_number']:
            room = db.collection("room_occupation_test").document(room_number).get().to_dict()
            
            room_guests:list = room['guests']
            
            for i, guest in enumerate(room_guests):
                if guest['guest']['rcode'] == rcode:
                    room_guests.pop(i)
            
            db.collection("room_occupation_test").document(room_number).update({"guests": room_guests})

            # dailyRoomOccupancyCheck(str(room_number))
            
            approveStatusFromGuestBookingID(user_id, booking_id, "checked_in", False)               

def delete_room_number_from_booking_test(user_id, booking_id, room_number):
    print("Start")
    booking = db.collection("guests").document(user_id).collection('booking').document(booking_id).get().to_dict()
    
    room_number_list:list = booking['room_number']
    
    try:
        i = room_number_list.index(str(room_number)) # Find the index of '32'
        room_number_list.pop(i) # Remove it by index
    except ValueError:
        pass
    
    db.collection("guests").document(user_id).collection('booking').document(booking_id).update({"room_number":room_number_list})

    print("END")


def get_not_checked_in_guests(date:datetime.datetime = None):
    if date is None:
        today = datetime.datetime.now(tz=pytz.timezone("Asia/Almaty")).date()
        today = datetime.datetime.combine(today, datetime.time.min)
    else:
        today = date
        
    # today = datetime.datetime(2023, 5, 5)
    
    today_timestamp = today.replace(tzinfo=pytz.timezone("Asia/Almaty")).timestamp()

    checkin_bookings = db.collection_group('booking').where("checkin_date_timestamp", "==", today_timestamp)\
                                .where("checked_out", "==", False).where("status", "==", 1).stream()

    not_checked_in_guests = []
    
    for checkin_booking in checkin_bookings:
        booking_dict = checkin_booking.to_dict()
        user = getBookingById(booking_dict["user_id"], checkin_booking.id)
        user['user_id'] = booking_dict["user_id"]
        user['booking']['booking_id'] = checkin_booking.id
        
        status = getStatusFromGuestBookingID(booking_dict["user_id"], checkin_booking.id)

        if(status['checked_in'] == False):
            not_checked_in_guests.append(user)
            
    return not_checked_in_guests

#Housekeeping

def get_maid(name_surname = None):
    if name_surname is None:
        maids = db.collection("housekeeping").stream()
        maids_arr = []
        for maid in maids:
            maid_dict = maid.to_dict()
            maid_dict[id] = maid.id
            maids_arr.append(maid_dict)
        return maids_arr

def add_maid(name, surname):
    newmaid = db.collection('housekeeping').document()
    newmaid.set({'name': name, 'surname': surname})
    
    return newmaid.get().id

def add_maid_details(firestore_id, update_dict):
    db.collection("housekeeping").document(str(firestore_id)).update(update_dict)


def change_rooms(user1: dict, user2: dict):
    query = db.collection("room_occupation_test")
    user1_room_dict = query.document(str(user1['room_number'])).get().to_dict()
    
    guests_user1 = user1_room_dict['guests']
    
    # print(guests_user1)
    
    user2_room_dict = query.document(str(user2['room_number'])).get().to_dict()
    
    guests_user2 = user2_room_dict['guests']
    
    # print(guests_user2)
    
    query.document(str(user1['room_number'])).update({"guests": guests_user2})
    query.document(str(user2['room_number'])).update({"guests": guests_user1})
    
    
    for guest in guests_user1:
        db.collection("guests").document(guest['guest']['user_id']).collection("booking").document(guest['guest']['booking_id']).update({'room_number': [user2['room_number']]})
    
    print("Done")
    
#automatic convert currency
def auto_convert_currency_for_guests(date: datetime.datetime = None):
    if date is None:
        checkin_checkout_dict = getBookingForDay()
    else:
        checkin_checkout_dict = getBookingForDay(date=date)
    
    print("CHECKIN")
    for checkin in checkin_checkout_dict['checkin']:
        price = checkin['booking']['price']
        currency = checkin['booking']['currency']
        
        currency_dict = {
            "price_in_KGS": converter.convert_currency(currency, "KGS", price),
            "price_in_USD": converter.convert_currency(currency, "USD", price),
            "price_in_RUB": converter.convert_currency(currency, "RUB", price),
        }
        user_id, booking_id = checkin['user_id'], checkin['booking']['booking_id']
        updateBookingWithId(user_id, booking_id, currency_dict)
        

    print("CHECKOUT")
    for checkout in checkin_checkout_dict['checkout']:
        price = checkout['booking']['price']
        currency = checkout['booking']['currency']
        
        currency_dict = {
            "price_in_KGS": converter.convert_currency(currency, "KGS", price),
            "price_in_USD": converter.convert_currency(currency, "USD", price),
            "price_in_RUB": converter.convert_currency(currency, "RUB", price),
        }
        user_id, booking_id = checkout['user_id'], checkout['booking']['booking_id']
        updateBookingWithId(user_id, booking_id, currency_dict)
        

def main():
    
    
    date = datetime.datetime(2023, 6, 14)
    auto_convert_currency_for_guests(date)

if __name__ == "__main__":
    main()
