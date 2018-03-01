-- 회원
CREATE TABLE member (
    userid VARCHAR(20) NOT NULL,
    gap INT NOT NULL,
    sess_id VARCHAR(100) NULL,
    sess_expire DATETIME NULL,
    PRIMARY KEY (userid)
);

-- 알림조건
CREATE TABLE conditions (
    userid VARCHAR(20) NOT NULL,
    id INT NOT NULL,
    currency VARCHAR(10) NOT NULL,
    exch VARCHAR(20) NULL,
    code VARCHAR(10) NOT NULL,
    val DOUBLE NOT NULL,
    next DATETIME NULL DEFAULT '1000-01-01 00:00:00',
    PRIMARY KEY (userid, id),
    FOREIGN KEY (userid) REFERENCES member(userid)
);
