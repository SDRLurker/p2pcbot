import unittest
from registry import Registry

import config
from dao import DAO
import datetime

class CmdTest(unittest.TestCase):
    def setUp(self):
        self.dsn = config.msql
        self.dsn['db'] = 'test'

    def test_rate(self):
        registry = Registry('test')
        user_json, cond_json = registry.proc_cmd("% BTG 1")
        user_dic = {'userid': 'test', 'gap': 600}
        self.assertEqual(user_json, user_dic)
        self.assertEqual(cond_json, {'userid': 'test', '%': 1, 'currency': 'BTG'})

    def test_invalid_cmd(self):
        registry = Registry('test')
        user_json, cond_json = registry.proc_cmd("invalid BTG 1")
        self.assertEqual(user_json, {'userid': 'test', 'gap': 600})
        self.assertEqual(cond_json, {})

    def test_rate_db(self):
        dao = DAO(self.dsn)

        registry = Registry('test')
        registry.save_data("% BTG 1", dao)
        self.assertEqual(dao.get_member('test'), [('test', 600, None, None)])
        self.assertEqual(dao.get_conditions(), [('test', 1, 'BTG', '%', 1.0)])

    def tearDown(self):
        dao = DAO(self.dsn)
        dao.delete_table('conditions')
        dao.delete_table('member')
