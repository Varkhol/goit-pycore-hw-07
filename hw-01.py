from collections import UserDict
from datetime import datetime, timedelta

class FieldValidationError(ValueError):
    pass


class PhoneNotFoundError(ValueError):
    pass


class RecordNotFoundError(KeyError):
    pass


class Field:
    def __init__(self, value):
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        if not value or not value.strip():
            raise FieldValidationError("Name is required")
        super().__init__(value)

class Phone(Field):
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if not (isinstance(new_value, str) and new_value.isdigit() and len(new_value) == 10):
            raise FieldValidationError(
                f"Phone number must contain exactly 10 digits. You wrote: {new_value}"
            )
        self._value = new_value

class Birthday(Field):
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        try:
            self._value = datetime.strptime(new_value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_birthday(self, date):
        self.birthday = Birthday(date)

    def add_phone(self, phone_value):
        self.phones.append(Phone(phone_value))

    def remove_phone(self, phone_value):
        phone = self.find_phone(phone_value)
        if phone:
            self.phones.remove(phone)
        else:
            raise PhoneNotFoundError(f"Phone {phone_value} not found")

    def edit_phone(self, old_phone, new_phone):
        phone = self.find_phone(old_phone)
        if phone:
            phone.value = new_phone  # setter гарантує валідацію
        else:
            raise PhoneNotFoundError(f"Phone {old_phone} not found")

    def find_phone(self, phone_value):
        for phone in self.phones:
            if phone.value == phone_value:
                return phone
        return None

    def __str__(self):
        return (
            f"Contact name: {self.name.value}, "
            f"phones: {'; '.join(p.value for p in self.phones)}"
        )


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        record = self.data.get(name)
        if record is None:
            raise RecordNotFoundError(f"Contact {name} not found")
        return record

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise RecordNotFoundError(f"Record {name} not found")

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        greeting_list = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            birthday_date = record.birthday.value.date()

            try:
                birthday_this_year = birthday_date.replace(year=today.year)
            except ValueError:
                birthday_this_year = birthday_date.replace(year=today.year, day=28)

            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)

            days_until_birthday = (birthday_this_year - today).days

            if 0 <= days_until_birthday <= 7:

                if birthday_this_year.weekday() == 5:
                    greeting_date = birthday_this_year + timedelta(days=2)
                elif birthday_this_year.weekday() == 6:
                    greeting_date = birthday_this_year + timedelta(days=1)
                else:
                    greeting_date = birthday_this_year

                greeting_list.append({
                    "name": record.name.value,
                    "congratulation_date": greeting_date.strftime("%Y.%m.%d")
                })

        return greeting_list
    
def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            if str(e):
                return str(e)
            return "Give me name and phone please."
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Enter the argument for the command."
    return inner

def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

@input_error
def add_contact(args, book):
    name = args[0]
    phone = args[1] if len(args) > 1 else None
    try:
        record = book.find(name)
        message = "Contact updated."
    except RecordNotFoundError:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args, book):
    name, new_phone = args
    record = book.find(name)
    if record.phones:
        record.phones[0].value = new_phone
    else:
        record.add_phone(new_phone)
    return "Contact updated."

@input_error
def show_phone(args, book):
    name = args[0]
    record = book.find(name)
    if not record.phones:
        return f"{name}:  No phones found"
    phones = ", ".join(p.value for p in record.phones)
    return f"Please see contact for {name}: {phones}"

@input_error
def show_all(book):
    if not book.data:
        return "No contacts found."

    result = []

    for record in book.data.values():
        phones = ", ".join(p.value for p in record.phones) if record.phones else "No phones"
        birthday = record.birthday.value.strftime("%d.%m.%Y") if record.birthday else "No birthday"
        result.append(f"{record.name.value}: {phones}; Birthday: {birthday}")
    return "\n".join(result)

@input_error
def add_birthday(args, book):
    if len(args) != 2:
        raise ValueError("Please use as: add-birthday name DD.MM.YYYY")
    name, birthday = args
    record = book.find(name)
    record.add_birthday(birthday)
    return f"Birthday for {name} added."

@input_error
def show_birthday(args, book):
    if len(args) != 1:
        raise ValueError("Please use as: show-birthday name")
    name = args[0]
    record = book.find(name)
    if record.birthday is None:
        return f"{name}'s birthday not found."
    return record.birthday.value.strftime("%d.%m.%Y")

@input_error
def birthdays(args, book):
    if args:
        raise ValueError("Please use as: birthdays")
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next week."
    return "\n".join(f"{item['name']}: {item['congratulation_date']}" for item in upcoming)

COMMANDS = {
    "add": add_contact,
    "change": change_contact,
    "phone": show_phone,
    "all": show_all,
    "add-birthday": add_birthday,
    "show-birthday": show_birthday,
    "birthdays": birthdays,
    "hello": lambda args, book: "How can I help you?",
}

def main():
    book = AddressBook()
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("").strip()
        if not user_input:
            continue

        if user_input.lower() in ("close", "exit"):
            print("Good bye!")
            break

        try:
            command, *args = parse_input(user_input)
        except ValueError:
            print("Enter a command.")
            continue

        if command in COMMANDS:
            print(COMMANDS[command](args, book))
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()
