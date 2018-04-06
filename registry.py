KINDS = ('%', 'cu', 'cd')
ALLOWED_CURRENCY = (
    'BTC', 'ETH', 'DASH', 'LTC', 'ETC', 'XRP', 'BCH', 'XMR',
    'ZEC', 'QTUM', 'BTG', 'EOS', 'ICX', 'VEN', 'TRX',
)

class Registry:
    def __init__(self, id, currency='BTC', vendor=None):
        self.id = id
        self.currency = currency
        self.vendor = vendor

    def is_allowed_currency(self, currency):
        if currency in ALLOWED_CURRENCY:
            return True
        return False

    def isfloat(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def proc_cmd(self, cmd):
        user_dic = {'userid': self.id, 'gap': 600}
        cond_dic = {}
        if self.vendor is not None:
            cond_dic['vendor'] = self.vendor
        fields = cmd.split()
        kind = ""
        for i, f in enumerate(fields):
            if i == 0:
                cond_dic['userid'] = self.id
                kind = f if f in KINDS else ""
            elif i == 1:
                self.currency = f
                cond_dic['currency'] = f
            elif i == 2:
                if len(kind) == 0 or not self.isfloat(f):
                    cond_dic = {}
                else:
                    cond_dic[kind] = float(f)
        # print(user_dic, cond_dic)
        if 'currency' not in cond_dic or not self.is_allowed_currency(cond_dic['currency']):
            return user_dic, {}
        return user_dic, cond_dic

    def save_data(self, cmd, dao):
        user_dic, cond_dic = self.proc_cmd(cmd)

        # 20180127 명령어 오류시 데이터 저장하면 안됨!
        print(user_dic, cond_dic)
        if cond_dic == {}:
            msg = "%s 명령을 잘못 사용하였습니다." % cmd.split()[0]
            return False, msg

        dao.set_member(user_dic)
        is_insert, msg = dao.insert_condition(cond_dic)
        return is_insert, msg
