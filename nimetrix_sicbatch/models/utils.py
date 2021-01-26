#!/usr/bin/python3
from datetime import date, datetime
import os
import os.path
from os import path
from datetime import timedelta


def send_log(self, record, response, status):
    self.env['sicbatch.log'].create({
        'api_call': "spResultOrden",
        'script': record.production_id.id,
        'response': response,
        'create_date': date.today(),
        'status': status,
        'work_order_id': record.id,
        'production_id': record.production_id.id
    })


def file_log(self, params, sp):
    text = sp+"_"+str(params)+"_"+str(self.write_date - timedelta(hours=4))
    x_path = "/var/log/odoo/sicbatch/"
    if not path.exists(x_path):
        os.mkdir(x_path)
    filename = x_path+"sicbatch_"+str(self.write_date)+".log"
    file1 = open(filename, 'w')
    file1.write(text)
    file1.close()








