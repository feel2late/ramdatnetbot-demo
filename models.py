from sqlalchemy import BigInteger, Column, Integer, Float, String, Boolean, create_engine, DateTime
from sqlalchemy.orm import DeclarativeBase, Session

engine = create_engine("postgresql://:@localhost/")


class Base(DeclarativeBase):
    pass

with Session(autoflush=False, bind=engine) as db:
    pass

class Access(Base):
    __tablename__ = "access"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_telegram_id = Column(BigInteger)
    user_name = Column(String)
    connection_date = Column(String)
    payment_recieved = Column(String)
    shutdown_date = Column(String)
    invite_code = Column(String)
    timezone = Column(Integer, default=3)
    blocked = Column(Boolean, default=False)
    tariff = Column(String)
    postpone_payment = Column(Boolean, default=False)
    chat_with_admin = Column(Boolean, default=False)
    reminder = Column(Boolean, default=False)
    blocked_bot = Column(Boolean, default=False)
    notifications = Column(Boolean, default=True)
    web_user_id = Column(Integer)

class AccessKeys(Base):
    __tablename__ = "access_keys"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_telegram_id = Column(BigInteger)
    rdn2 = Column(String)
    rdn4 = Column(String)
    rdn5 = Column(String)
    rdn2_id = Column(String)
    rdn4_id = Column(String)
    rdn5_id = Column(String)
    ss_ned_key = Column(String)
    ss_fin_key = Column(String)
    ss_swe_key = Column(String)
    vless_ned_key = Column(String)
    vless_fin_key = Column(String)
    vless_swe_key = Column(String)
    ss_ned_port = Column(Integer)
    ss_fin_port = Column(Integer)
    ss_swe_port = Column(Integer)

class Payments(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_telegram_id = Column(BigInteger)
    amount = Column(Integer)
    type = Column(String)
    date = Column(String)
    datetime = Column(DateTime)
    month = Column(Integer)
    year = Column(Integer)

class CheckPaid(Base):
    __tablename__ = "check_paid"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id = Column(Integer)
    bill_id = Column(String)

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_telegram_id = Column(Integer)
    joining_date = Column(String)

class Invitations(Base):
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    inviter = Column(BigInteger)
    invited = Column(BigInteger)

class Banned(Base):
    __tablename__ = "banned"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_telegram_id = Column(BigInteger)
    user_name = Column(String)
    banned_at = Column(String)
    

Base.metadata.create_all(bind=engine)
