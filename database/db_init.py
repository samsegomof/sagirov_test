import sqlite3

class DatabaseControl:
    def __init__(self):
        self.base = sqlite3.connect('forms')
        self.cur = self.base.cursor()
    
    def connect_check(self):
        if self.base:
            print('BD is connected')
        self.base.execute('CREATE TABLE IF NOT EXISTS forms(first_name TEXT, last_name TEXT, email TEXT, phone_number TEXT, birth_date TEXT, user_id TEXT, form_time TEXT)')
        self.base.commit()

    async def sql_add_command(self, state, current_time):
        async with state.proxy() as data:
            values = list(data.values())
            values.append(current_time)
            print(values)
            self.cur.execute('INSERT INTO forms VALUES (?, ?, ?, ?, ?, ?, ?)', tuple(values, ))
            self.base.commit()


database_controller = DatabaseControl()