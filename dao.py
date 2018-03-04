import mysql.connector.pooling
from registry import KINDS
import traceback

POOL_SIZE = 32


class DAO:
    def __init__(self, dsn):
        self.pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name='mypool', pool_size=POOL_SIZE, **dsn)

    def exec_query(self, query, val=None):
        # print(query, val)
        cnx = self.pool.get_connection()
        cur = cnx.cursor()
        if val:
            cur.execute(query, val)
        else:
            cur.execute(query)
        return cnx, cur

    def close(self, cnx, cur):
        cur.close()
        cnx.close()

    def sub_query_from_dic(self, from_dic, delimiter=","):
        sub_query = ""
        vlist = []
        for key in from_dic:
            fmt_str = "%s"
            append_str = "%s%s = %s" % (delimiter, key, fmt_str)
            if sub_query == "":
                append_str = append_str[len(delimiter):]
            sub_query += append_str
            vlist.append(from_dic[key])
        return sub_query, vlist

    def delete_table(self, table):
        query = "DELETE FROM %s" % table;
        cnx, cur = self.exec_query(query)
        cnx.commit()
        self.close(cnx, cur)

    def get_next_conditions(self):
        try:
            conds = []
            query = "SELECT userid, id, currency, code, val FROM conditions WHERE NOW() > next"
            cnx, cur = self.exec_query(query)
            rows = cur.fetchall()
            print("get_next_conditions",cnx,cur,rows)
            for row in rows:
                conds.append(row)
            self.close(cnx, cur)
        except Exception as e:
            # logger.error(traceback.format_exc())
            print(traceback.format_exc())
            # logger.error('get_update : ' + str(e))
            print('get_next_conditions : ' + str(e))
        return conds

    def set_member(self, member_dic):
        sub_query, vlist = self.sub_query_from_dic(member_dic)
        query = "INSERT INTO member SET %s " % sub_query
        query += "ON DUPLICATE KEY UPDATE %s" % sub_query
        vlist = vlist * 2
        cnx, cur = self.exec_query(query, vlist)
        cnx.commit()
        self.close(cnx, cur)

    def get_member(self, userid=None):
        members = []
        sub_query = ""
        if userid:
            sub_query = "WHERE userid=%s"
        query = "SELECT * FROM member %s" % sub_query
        cnx, cur = self.exec_query(query, (userid,))
        rows = cur.fetchall()
        for row in rows:
            members.append(row)
        self.close(cnx, cur)
        return members

    def insert_condition(self, cond_dic):
        query = "SELECT MAX(id) FROM conditions"
        cnx, cur = self.exec_query(query)
        rows = cur.fetchall()
        cid = 1
        if rows[0][0]:
            cid = rows[0][0] + 1
        self.close(cnx, cur)
        new_dic = {}
        for key in cond_dic:
            if key in KINDS:
                new_dic['code'] = key
                new_dic['val'] = cond_dic[key]
            else:
                new_dic[key] = cond_dic[key]
        new_dic['id'] = cid
        sub_query, vlist = self.sub_query_from_dic(new_dic)
        query = "INSERT INTO conditions SET %s" % sub_query
        cnx, cur = self.exec_query(query, vlist)
        cnx.commit()
        self.close(cnx, cur)

    def update_condition(self, set_dic, where_dic):
        set_query, set_list = self.sub_query_from_dic(set_dic)
        where_query, where_list = self.sub_query_from_dic(where_dic, " AND ")
        query = "UPDATE conditions SET %s WHERE %s" % (set_query, where_query)
        vlist = set_list+where_list
        cnx, cur = self.exec_query(query, vlist)
        cnx.commit()
        self.close(cnx, cur)

    def get_conditions(self, userid = None):
        try:
            conds = []
            where = "WHERE userid=%s" if userid else ""
            query = "SELECT userid, id, currency, code, val FROM conditions %s" % where
            arr = []
            if userid:
                arr = [userid]
            print(query, arr)
            cnx, cur = self.exec_query(query, arr)
            rows = cur.fetchall()
            for row in rows:
                conds.append(row)
            self.close(cnx, cur)
        except Exception as e:
            # logger.error(traceback.format_exc())
            print(traceback.format_exc())
            # logger.error('get_update : ' + str(e))
            print('get_conditions : ' + str(e))
        return conds

    def update_session(self, userid, set_dic):
        set_query, set_list = self.sub_query_from_dic(set_dic)
        query = "INSERT INTO member SET gap=600, %s, userid=%%s ON DUPLICATE KEY UPDATE %s, userid=%%s" % (set_query, set_query)
        vlist = set_list+[userid]+set_list+[userid]
        print(query, vlist)
        cnx, cur = self.exec_query(query, vlist)
        cnx.commit()
        self.close(cnx, cur)

    def delete_condition(self, where_dic):
        where_query, where_list = self.sub_query_from_dic(where_dic, " AND ")
        query = "DELETE FROM conditions WHERE %s" % (where_query)
        cnx, cur = self.exec_query(query, where_list)
        cnx.commit()
        self.close(cnx, cur)

if __name__ == "__main__":
    dao = DAO()
    dao.set_condition({'userid': 'test', '%': 1, 'currency': 'BTG'})
