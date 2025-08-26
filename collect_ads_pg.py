import asyncio

from olx_reposter.config.project_variables import emails, password
from olx_reposter import OlxAdReposter

olx_reposter = OlxAdReposter()


async def main_pg():
    for index, email in enumerate(emails):
        await olx_reposter.write_to_db(index + 1, email, password, "postgres")
    olx_reposter.page_close()

if __name__ == '__main__':
    asyncio.run(main_pg())
