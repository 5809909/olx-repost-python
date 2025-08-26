import asyncio

from olx_reposter.config.project_variables import emails, password
from olx_reposter import OlxAdReposter

olx_reposter = OlxAdReposter()


# MYSQL
async def main_mysql():
    for index, email in enumerate(emails):
        await olx_reposter.write_to_db(index + 1, email, password, "mysql")
    olx_reposter.page_close()


if __name__ == '__main__':
    asyncio.run(main_mysql())
