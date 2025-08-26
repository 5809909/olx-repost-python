from datetime import datetime

import asyncpg

from ..config import pg_user, pg_password, pg_database, pg_host


class PostgresDatabaseModel:

    @staticmethod
    async def _init_db():
        conn = await asyncpg.connect(user=pg_user, password=pg_password, database=pg_database, host=pg_host)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS olx(
                id SERIAL PRIMARY KEY,
                acc_id INT NOT NULL,
                advertising_id INT NOT NULL,
                title TEXT NOT NULL,
                price INT NOT NULL,
                views INT NOT NULL,
                likes INT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                end_time TIME NOT NULL,
                date DATE NOT NULL,
                time TIME NOT NULL
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS transfer_ads(
                id SERIAL PRIMARY KEY,
                advertising_id INT NOT NULL,
                acc_from INT NOT NULL,
                acc_to INT NOT NULL,
                is_transferred BOOLEAN DEFAULT FALSE
            )
        ''')
        await conn.close()

    async def store_ad(self, index, data, date_run_script, time_run_script):
        await self._init_db()
        for ad in data:
            ad_id = ad['id']
            ad_activated_date = ad['activatedAt']
            ad_validTo_date = str(ad['validTo'])
            ad_title = ad['title']
            ad_price = int(ad['price'])
            ad_views = int(ad['stats']['views'])
            ad_favorites = int(ad['stats']['observed'])
            conn = await asyncpg.connect(user=pg_user, password=pg_password, database=pg_database, host=pg_host)
            row = await conn.execute(
                '''INSERT INTO olx(
                    acc_id, advertising_id, title, price, views, likes,
                    start_date, end_date, end_time, date, time
                ) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)''',
                index,
                ad_id,
                ad_title,
                ad_price,
                ad_views,
                ad_favorites,
                datetime.fromisoformat(ad_activated_date).replace(tzinfo=None).date(),
                datetime.fromisoformat(ad_validTo_date).replace(tzinfo=None).date(),
                datetime.fromisoformat(ad_validTo_date).replace(tzinfo=None).time(),
                date_run_script,
                time_run_script
            )
            await conn.close()

    async def select_all_rows_from_transfer_db(self):
        conn = await asyncpg.connect(user=pg_user, password=pg_password, database=pg_database, host=pg_host)
        row = await conn.fetch("SELECT * FROM transfer_ads")
        await conn.close()
        if row is None:
            return None
        else:
            return row

    async def check_ad_in_db(self, ad_id):
        conn = await asyncpg.connect(user=pg_user, password=pg_password, database=pg_database, host=pg_host)
        row = await conn.fetchrow("SELECT * FROM olx WHERE advertising_id = $1", ad_id)
        await conn.close()

        if row is None:
            raise Exception("ID IS NONE")
        else:
            return int(row['advertising_id'])

    @staticmethod
    async def update_is_transferred_field_in_transfer_db(ad_id: int):
        conn = await asyncpg.connect(user=pg_user, password=pg_password, database=pg_database, host=pg_host)
        row = await conn.execute("UPDATE transfer_ads SET is_transferred = $1 WHERE advertising_id = $2", True, ad_id)
        await conn.close()
