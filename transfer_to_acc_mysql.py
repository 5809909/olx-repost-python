import asyncio

from olx_reposter import OlxAdReposter, MySQLDatabaseModel
from olx_reposter.config.project_variables import emails, password

olx_reposter = OlxAdReposter()


async def main():
    data_from_transfer_db = await MySQLDatabaseModel().select_all_rows_from_transfer_db()
    for single_data in data_from_transfer_db:
        if not single_data[4]:
            await olx_reposter.transfer_ad_between_accounts(int(single_data[3]),
                                                            emails[single_data[1] - 1], password,
                                                            emails[single_data[2] - 1], password, "mysql")
        else:
            olx_reposter.page_close()


if __name__ == '__main__':
    asyncio.run(main())
