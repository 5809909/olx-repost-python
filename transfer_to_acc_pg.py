import asyncio

from olx_reposter import PostgresDatabaseModel, OlxAdReposter
from olx_reposter.config.project_variables import emails, password

olx_reposter = OlxAdReposter()


async def main():
    data_from_transfer_db = await PostgresDatabaseModel().select_all_rows_from_transfer_db()
    for single_data in data_from_transfer_db:
        if not single_data['is_transferred']:
            await olx_reposter.transfer_ad_between_accounts(int(single_data['advertising_id']),
                                                            emails[single_data['account_from'] - 1], password,
                                                            emails[single_data['account_to'] - 1], password, "postgres")
        else:
            olx_reposter.page_close()


if __name__ == '__main__':
    asyncio.run(main())
