import asyncio
from multiprocessing import Process

from telegram_part import start

from selenium_part import thread


class Main():

    def selenium_process(self):
        asyncio.run(thread.run())
    
    def telegram_process(self):
        start()

    def infinity_loop(self):
        telegram_proc = Process(target=self.telegram_process)
        selenium_proc = Process(target=self.selenium_process)
        telegram_proc.start()
        selenium_proc.start()


main = Main()
if __name__ == '__main__':
    main.infinity_loop()
