# -*- coding: utf-8 -*-
#import pyodbc


def sql_connect(record, operation):
    config_line = record.env['config.connection.line'].search(
        [(operation, '=', record.operation_id.id)])

    con_string = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:' + config_line.config_head_id.server \
                 + ';Database=' + config_line.config_head_id.database + ';UID=' \
                 + config_line.config_head_id.db_user + ';PWD=' \
                 + config_line.config_head_id.db_password + ';'

    #return pyodbc.connect(con_string)
    return


def sql_connect(self):
    config = self.env['config.connection'].search(
        [('company_id', '=', self.company_id.id)])

    con_string = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:' + config.server \
                 + ';Database=' + config.database + ';UID=' \
                 + config.db_user + ';PWD=' \
                 + config.db_password + ';'

    #return pyodbc.connect(con_string), config
    return


def test_connect(self):
    con_string = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:' + self.server \
                 + ';Database=' + self.database + ';UID=' + self.db_user \
                 + ';PWD=' + self.db_password + ';'

    #return pyodbc.connect(con_string)
    return
