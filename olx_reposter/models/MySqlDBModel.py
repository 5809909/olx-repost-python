from datetime import datetime

from mysql.connector.aio import connect

from ..config import mysql_user, mysql_password, mysql_database, mysql_host


class MySQLDatabaseModel:

    @staticmethod
    async def _init_db():
        conn = await connect(
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            host=mysql_host,
        )

        cur = await conn.cursor()

        await cur.execute('''
                        CREATE TABLE IF NOT EXISTS olx (
                            id INT AUTO_INCREMENT PRIMARY KEY,
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

        await cur.execute('''
                        CREATE TABLE IF NOT EXISTS transfer_ads (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            advertising_id INT NOT NULL,
                            account_to INT NOT NULL,
                            account_from INT NOT NULL,
                            is_transferred BOOLEAN DEFAULT FALSE
                        )
                    ''')

        await conn.commit()
        await conn.close()

    async def store_ad(self, index, data, date_run_script, time_run_script):
        await self._init_db()
        for ad in data:
            ad_id = ad['id']
            ad_activated_date = ad['activatedAt']
            ad_validTo_date = ad['validTo']
            ad_title = ad['title']
            ad_price = int(ad['price'])
            ad_views = ad['stats']['views']
            ad_favorites = ad['stats']['observed']
            conn = await connect(user=mysql_user, password=mysql_password, database=mysql_database, host=mysql_host)
            cur = await conn.cursor()
            await cur.execute(
                '''INSERT INTO olx(
                    acc_id, advertising_id, title, price, views, likes,
                    start_date, end_date, end_time, date, time)
                 VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                (index, ad_id,
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
                 ))
            await conn.commit()
            await conn.close()

    async def select_all_rows_from_transfer_db(self):
        conn = await connect(user=mysql_user, password=mysql_password, database=mysql_database, host=mysql_host)
        cur = await conn.cursor()
        await cur.execute("SELECT * FROM transfer_ads")
        rows = await cur.fetchall()
        await conn.close()
        return rows if rows else []

    async def check_ad_in_db(self, ad_id):
        conn = await connect(user=mysql_user, password=mysql_password, database=mysql_database, host=mysql_host)
        cur = await conn.cursor()
        await cur.execute("SELECT * FROM olx WHERE advertising_id = %s", (ad_id,))
        row = await cur.fetchone()

        await conn.close()

        if row is None:
            raise Exception("ID IS NONE")
        else:
            return int(row[2])


    @staticmethod
    async def update_is_transferred_field_in_transfer_db(ad_id: int):
        conn = await connect(user=mysql_user, password=mysql_password, database=mysql_database, host=mysql_host)
        cur = await conn.cursor()
        await cur.execute("UPDATE transfer_ads SET is_transferred = %s WHERE advertising_id = %s", (True, ad_id))
        await conn.commit()
        await conn.close()
