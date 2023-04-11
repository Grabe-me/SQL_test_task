import psycopg2
import re
from database_config import *
import logging
from data_values import client, order, sequency_start

logging.basicConfig(
    format=u'%(filename)s [ LINE:%(lineno)+3s ]#%(levelname)+8s [%(asctime)s]  %(message)s',
    level=logging.INFO,
)


class DataBase:

    connection = None

    def connection_open(self):
        try:
            self.connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                dbname=dbname,
                port=port
            )

            self.connection.autocommit = True

            logging.info("PostgreSQL connection opened")

        except Exception as exc:
            logging.critical(f"Error while working with PostgreSQL: {exc}")

    def connection_close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            logging.info("PostgreSQL connection closed")

    def check_connection(self):
        if self.connection:
            return None
        else:
            logging.critical('Lost connection with PostgreSQL')
            raise Exception

    def create_client_table(self, table: str = 'client'):
        table_verbose = self.get_verbose_name(table)
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""CREATE TABLE IF NOT EXISTS {table_verbose} (
                        {table} SERIAL PRIMARY KEY,
                        name VARCHAR(50) NOT NULL,
                        surname VARCHAR(50) NOT NULL,
                        address text NOT NULL
                    );
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_{table}
                    ON {table_verbose} (name, surname, address);
                    SELECT setval('clients_client_seq', {sequency_start});"""
            )
        logging.info(f'Created new table "{table_verbose}"')

    def create_order_table(self, tree_tables: list, table: str = 'order', client: str = 'client'):
        table_verbose = self.get_verbose_name(table)
        client_verbose = self.get_verbose_name(client)
        to_buy = tree_tables[-1]
        to_buy_verbose = self.get_verbose_name(to_buy)
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""CREATE TABLE IF NOT EXISTS {table_verbose} (
                        fk_{client} INTEGER REFERENCES {client_verbose}({client}),
                        fk_{to_buy} VARCHAR(50) REFERENCES {to_buy_verbose}({to_buy}),
                        {table}_number SERIAL NOT NULL UNIQUE
                    );"""
            )
        logging.info(f'Created new table "{table_verbose}"')

    def create_tree_table(self, table: str, parent_table: str = None):
        table_verbose = self.get_verbose_name(table)
        string = ''
        if parent_table:
            logging.debug('parent_table is TRUE')
            parent_table_verbose = self.get_verbose_name(parent_table)
            string = f", fk_{parent_table} VARCHAR(50) REFERENCES {parent_table_verbose}({parent_table})"
        self.check_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""CREATE TABLE IF NOT EXISTS {table_verbose} (
                    {table} VARCHAR(50) PRIMARY KEY,
                    quantity INTEGER
                    {string}
                )"""
            )
        logging.info(f'Created new tree_table "{table_verbose}"')

    def get_verbose_name(self, name):
        verbose_name = f'{name}s'
        if name == 'category':
            verbose_name = 'categories'
        return verbose_name

    def insert_tree_data(self, table: str, data: tuple, parent_table='', quantity=''):
        self.check_connection()
        table_verbose = self.get_verbose_name(table)
        data = self.check_for_characters(data)
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""INSERT INTO {table_verbose}({table}{parent_table}{quantity}) VALUES {data}"""
            )
        logging.info(f'Insert new data into table "{table_verbose}"')

    def insert_client_data(self, tree_tables: list, table: str, data: tuple):
        self.check_connection()
        table_verbose = self.get_verbose_name(table)
        data = self.check_for_characters(data)
        if table == client:
            info = 'name, surname, address'
        elif table == order:
            info = f'fk_{client}, fk_{tree_tables[-1]}'
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""INSERT INTO {table_verbose}({info}) VALUES {data}"""
            )
        logging.info(f'Insert new data into table "{table_verbose}"')


    def check_for_characters(self, string):
        string = str(string)
        string = re.sub(r",\s*\)", ")", string)
        string = re.sub(r"\(\(", "(", string)
        string = re.sub(r"\)\)", ")", string)
        return string

    def create_tree_trigger(self, table: str, parent_table: str):
        self.check_connection()
        table_verbose = self.get_verbose_name(table)
        parent_table_verbose = self.get_verbose_name(parent_table)
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""CREATE OR REPLACE FUNCTION update_{parent_table}_quantity()
                    RETURNS TRIGGER AS $$
                    BEGIN
                      UPDATE {parent_table_verbose}
                      SET quantity = (SELECT COUNT(*) FROM {table_verbose} 
                      WHERE fk_{parent_table} = NEW.fk_{parent_table})
                      WHERE {parent_table} = NEW.fk_{parent_table};
                      RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;

                    CREATE TRIGGER update_{parent_table}_quantity_trigger
                    AFTER INSERT OR UPDATE OR DELETE ON {table_verbose}
                    FOR EACH ROW
                    EXECUTE FUNCTION update_{parent_table}_quantity();"""
            )
        logging.info(f'Created new trigger on table "{table_verbose}"')
