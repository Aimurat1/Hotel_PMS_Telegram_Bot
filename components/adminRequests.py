class adminRequests:
    def __init__(self, request_id, user_id, booking_id, phone_number, request_type, telegram_id, **kwargs) -> None:
        self.request_id = request_id
        self.user_id = user_id
        self.booking_id = booking_id
        self.phone_number = phone_number
        self.request_type = request_type
        self.telegram_id = telegram_id
        self.requestDict = kwargs
        
    def __str__(self) -> str:
        return (f"""
{self.request_id}
{self.user_id}
{self.booking_id}
{self.phone_number}
{self.request_type}
{self.requestDict}
              """)