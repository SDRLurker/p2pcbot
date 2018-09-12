# 가상화폐 알림봇

## 소개

가상화폐거래소 시세를 대략 매초마다 수신하여 원하는 시세 조건에 대해 알람메세지를 보냅니다.

홈페이지 : http://p2pcbot.com:3000/

텔레그램 아이디 : [p2pcoinbot](https://telegram.me/p2pcbot)

## 웹서버

이 프로그램은 웹서버 프로그램도 같이 실행해야 합니다.

소스 저장소 : https://github.com/SDRLurker/p2pcbot2

## 사용법

* set

웹을 통해 알림메세지 조건을 설정합니다.

* ls

조건목록을 확인합니다.

* rm 번호

번호에 해당하는 조건을 삭제합니다.


* % 코인 값

코인의 등락율이 값 이상, 또는 값 이하면 알려주는 조건을 등록합니다.

* cu 코인 값

코인의 종가가 값 이상이면 알려주는 조건을 등록합니다.

* cd 코인 값

코인의 종가가 값 이하면 알려주는 조건을 등록합니다.

## 최초 DB 생성

```shell
~/p2pcbot]$ mysql -hDB주소 -uDB사용자 -p DB명 < p2pcbot.sql
```

## 설정파일 생성

```shell
~/p2pcbot]$ vi config.py
# -*- coding: utf-8 -*-
my_token = '텔레그램 토큰키'

web_host='웹서버주소'

msql = {}
msql['host'] = 'DB주소'
msql['user'] = 'DB사용자'
msql['password'] = 'DB비밀번호'
msql['db'] = 'DB명'
msql['charset'] = 'utf8'
```

## 의존성 관리

```shell
~/p2pcbot]$ pip install -r requirements.txt
```

## 프로그램 실행

```shell
~/p2pcbot]$ ./p2pcbot.py > /dev/null &
```
