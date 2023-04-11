from database_manage import DataBase
from data_values import tree_tables, values


db = DataBase()


def set_values_tree_tables(tree_tables, values, quantity=''):
    previous = ''
    for tree_table in tree_tables:
        tree_table_verbose = db.get_verbose_name(tree_table)
        if len(values[tree_table_verbose][0]) > 1:
            previous = f', fk_{previous}'
        if len(values[tree_table_verbose][0]) > 2:
            quantity = ', quantity'
        db.insert_tree_data(tree_table, values[tree_table_verbose], previous, quantity)
        previous = tree_table
    db.insert_client_data(tree_tables, 'client', values['clients'])
    db.insert_client_data(tree_tables, 'order', values['orders'])


def set_tree_table_and_trigger(table_list):
    previous = None
    for tree_tabel in table_list:
        db.create_tree_table(tree_tabel, previous)
        if previous:
            db.create_tree_trigger(tree_tabel, previous)
        previous = tree_tabel


if __name__ == '__main__':
    db.connection_open()
    set_tree_table_and_trigger(tree_tables)
    db.create_client_table()
    db.create_order_table(tree_tables)
    set_values_tree_tables(tree_tables, values)
    db.connection_close()
