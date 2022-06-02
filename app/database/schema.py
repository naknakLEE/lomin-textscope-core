import uuid
import yaml  # type: ignore
import typing

from typing import Any, Dict, List, Optional, TypeVar
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Table, text, func
from sqlalchemy.orm import Session, relationship
from sqlalchemy.ext.declarative import declarative_base

from passlib.context import CryptContext
from pydantic.networks import EmailStr

from app.database.connection import Base, db
from app.utils.logging import logger
from app.common.const import get_settings


settings = get_settings()

Base = declarative_base()
metadata = Base.metadata

ModelType = TypeVar("ModelType", bound=Base)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

exist_column_table = {
    "UserInfo": "user_employee_num",
    "RoleInfo": "role_index",
    "UserRole": "user_employee_num,role_index",
    "Document": "document_id",
    "ModelInfo": "model_index",
}


class BaseMixin:
    def all_columns(self) -> List:
        return [
            c
            for c in self.__table__.columns  # type: ignore
            # if c.primary_key is False and c.name != "created_at"
        ]

    @typing.no_type_check
    @classmethod
    def check_raw_exists(cls, session: Session, **kwargs: Dict[str, Any]) -> str:
        check_columns = exist_column_table.get(cls.__name__)
        message = ""
        if check_columns is None:
            return message
        inputs: Dict = {}
        for check_column in check_columns.split(","):
            inputs[check_column] = kwargs.get(check_column)
        is_exist = cls.get(session, **inputs)
        if is_exist:
            message = f"This {check_columns} already exist"
            logger.warning(f"{message}\n{yaml.dump([kwargs])}")
            return message
        return message

    @typing.no_type_check
    @classmethod
    def get(cls, session: Session, **kwargs: Dict[str, Any]) -> Optional[ModelType]:
        query = session.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col == val)
        return query.first()

    @typing.no_type_check
    @classmethod
    def get_multi(
        cls, session: Session, skip: int = 0, limit: int = 100, **kwargs: Dict[str, Any]
    ) -> Optional[ModelType]:
        query = session.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col == val)
        query = query.offset(skip).limit(limit)
        return query.all() if query else None

    @typing.no_type_check
    @classmethod
    def get_all(cls, session: Session, **kwargs: Dict[str, Any]) -> Optional[ModelType]:
        query = session.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col == val)
        return query.all() if query else None

    @typing.no_type_check
    @classmethod
    def remove(cls, session: Session, **kwargs: Dict[str, Any]) -> ModelType:
        query = session.query(cls)
        for key, val in kwargs.items():
            query.filter(key == val)
        obj = query.delete()
        session.flush()
        session.commit()
        return obj

    @typing.no_type_check
    @classmethod
    def update(
        cls,
        session: Session,
        id: int,
        auto_commit: bool = True,
        **kwargs: Dict[str, Any],
    ) -> Optional[ModelType]:
        query = session.query(cls).filter(cls.id == id).first()
        for key, val in kwargs.items():
            setattr(query, key, val)
        session.flush()
        if auto_commit:
            session.commit()
        return query

    @typing.no_type_check
    @classmethod
    def create(
        cls, session: Session, auto_commit: bool = True, **kwargs: Dict[str, Any]
    ) -> Optional[ModelType]:
        check_result = cls.check_raw_exists(session, **kwargs)
        if check_result:
            return check_result
        obj = cls()
        for col in obj.all_columns():
            col_name = col.name
            if col_name in kwargs:
                setattr(obj, col_name, kwargs.get(col_name))
        session.add(obj)
        session.flush()
        if auto_commit:
            session.commit()
        return obj


class AlarmInfo(Base, BaseMixin):
    __tablename__ = 'alarm_info'
    __table_args__ = {'comment': 'textscope 서비스 알람 목록'}

    alarm_index = Column(Integer, primary_key=True, comment='알람 유니크 인덱스')
    alarm_range = Column(String, nullable=False, default='전체', comment='알람 노출 범위(전체, 팀)')
    alarm_type = Column(String, nullable=False, comment='알람 종류(문서 분류 AI 모델 학습, 구성원)')
    alarm_title = Column(String, nullable=False, comment='알람 제목')
    alarm_content = Column(String, nullable=False, default='(내용없음)', comment='알람 내용')
    alarm_created_time = Column(DateTime, nullable=False, default=func.now(), comment='알람 생성 시각')
    alarm_modified_time = Column(DateTime, nullable=False, default=func.now(), comment='알람 수정 시각')
    is_used = Column(Boolean, comment='사용 여부')


class ModelInfo(Base, BaseMixin):
    __tablename__ = 'model_info'
    __table_args__ = {'comment': 'textscope 서비스 등록된 딥러닝 모델 정보'}

    model_index = Column(Integer, primary_key=True, comment='모델 유니크 인덱스')
    model_name_kr = Column(String, comment='모델 한글 명')
    model_name_en = Column(String, comment='모델 영문 명')
    model_version = Column(String, comment='모델 버전')
    model_path = Column(String, comment='모델 저장 경로')
    model_type = Column(String, comment='모델 종류')
    model_created_time = Column(DateTime, default=func.now(), comment='모델 등록 시각')
    is_used = Column(Boolean, comment='사용 여부')


class PageInfo(Base, BaseMixin):
    __tablename__ = 'page_info'
    __table_args__ = {'comment': 'textscope 서비스 문서의 특정 페이지 정보'}

    page_id = Column(String, primary_key=True, comment='페이지 아이디')
    page_num = Column(Integer, comment='추론한 페이지 인덱스')
    page_doc_type = Column(String, comment='페이지의 문서 타입')
    page_width = Column(Integer, comment='이미지 변환 후 가로 크기')
    page_height = Column(Integer, comment='이미지 변환 후 세로 크기')


class PermissionInfo(Base, BaseMixin):
    __tablename__ = 'permission_info'
    __table_args__ = {'comment': 'textscope 서비스 권한 정보'}

    permission_code = Column(String, primary_key=True, comment='권한 코드')
    permission_name = Column(String, comment='권한 이름')
    is_used = Column(Boolean, comment='사용 여부')


class RoleInfo(Base, BaseMixin):
    __tablename__ = 'role_info'
    __table_args__ = {'comment': 'textscope 서비스 그룹 정보'}

    role_index = Column(Integer, primary_key=True, comment='역할 유니크 인덱스')
    role_name = Column(String, nullable=False, default='역할이름', comment='역할 이름')
    is_used = Column(Boolean, comment='사용 여부')


class ClassInfo(Base, BaseMixin):
    __tablename__ = 'class_info'
    __table_args__ = {'comment': 'textscope 서비스 딥러닝 모델의 항목(라벨 클래스)'}

    class_code = Column(String, primary_key=True, comment='항목 코드')
    model_index = Column(ForeignKey('model_info.model_index'), nullable=False, comment='모델 유니크 인덱스')
    class_name_kr = Column(String, comment='항목 한글 명')
    class_name_en = Column(String, comment='항목 영문 명')
    class_use = Column(Boolean, comment='항목 사용 여부')
    is_used = Column(Boolean, comment='사용 여부')

    model_info = relationship('ModelInfo')


class RolePermission(Base, BaseMixin):
    __tablename__ = 'role_permission'
    __table_args__ = {'comment': 'textscope 서비스 역할 권한'}

    created_time = Column(DateTime, primary_key=True, default=func.now())
    role_index = Column(ForeignKey('role_info.role_index'), nullable=False, comment='역할 유니크 인덱스')
    permission_code = Column(ForeignKey('permission_info.permission_code'), nullable=False, comment='권한 코드')
    is_used = Column(Boolean, comment='사용 여부')

    permission_info = relationship('PermissionInfo')
    role_info = relationship('RoleInfo')


class UserInfo(Base, BaseMixin):
    __tablename__ = 'user_info'
    __table_args__ = {'comment': '수출입은행과 주기적으로 동기화되는 정보'}

    user_employee_num = Column(Integer, primary_key=True, comment='(SSO)사원번호')
    user_email = Column(String, nullable=False, comment='(SSO)이메일')
    user_pw = Column(String, nullable=False, comment='(SSO)비밀번호')
    user_office = Column(String, comment='(SSO)지점')
    user_division = Column(String, comment='(SSO)본부')
    user_department = Column(String, comment='(SSO)부서')
    user_team = Column(String, comment='(SSO)팀')
    user_name = Column(String, comment='(SSO)사원이름')
    is_used = Column(Boolean, comment='사용 여부')


class AlarmRead(Base, BaseMixin):
    __tablename__ = 'alarm_read'
    __table_args__ = {'comment': '사용자가 읽은 알람 정보'}

    created_time = Column(DateTime, primary_key=True, default=func.now())
    employee_num = Column(ForeignKey('user_info.user_employee_num'), nullable=False, comment='(SSO)사원번호')
    alarm_index = Column(ForeignKey('alarm_info.alarm_index'), nullable=False, comment='알람 유니크 인덱스')
    is_used = Column(Boolean, comment='사용 여부')

    alarm_info = relationship('AlarmInfo')
    user_info = relationship('UserInfo')


class DocumentInfo(Base, BaseMixin):
    __tablename__ = 'document_info'
    __table_args__ = {'comment': 'textscope 서비스 학습 또는 추론을 위해 업로드된 문서 정보'}

    document_id = Column(String, primary_key=True, comment='문서 아이디')
    employee_num = Column(ForeignKey('user_info.user_employee_num'), nullable=False, comment='문서 등록자 (SSO)사원번호')
    user_personnel = Column(String, nullable=False, comment='문서 등록 당시 등록자의 인사정보(SSO)')
    document_path = Column(String, comment='문서 저장 경로')
    document_description = Column(String, comment='문서 설명')
    document_type = Column(String, comment='문서 업로드 타입')
    document_upload_time = Column(DateTime, default=func.now(), comment='문서 업로드 시각')
    document_pages = Column(Integer, comment='문서 총 페이지 수')
    is_used = Column(Boolean, comment='사용 여부')

    user_info = relationship('UserInfo')


class TaskInfo(Base, BaseMixin):
    __tablename__ = 'task_info'
    __table_args__ = {'comment': 'textscope 서비스 task 정보'}

    task_id = Column(String, primary_key=True, comment='테스크 아이디')
    employee_num = Column(ForeignKey('user_info.user_employee_num'), nullable=False, comment='(SSO)사원번호')
    user_personnel = Column(String, nullable=False, comment='테스크 생성 당시 생성자의 인사정보(SSO)')
    task_content = Column(JSON, comment='테스크 내용')
    task_start_time = Column(DateTime, comment='테스크 시작 시각')
    task_end_time = Column(DateTime, comment='테스크 종료 시각')
    is_used = Column(Boolean, comment='사용 여부')

    user_info = relationship('UserInfo')


class UserAlarm(Base, BaseMixin):
    __tablename__ = 'user_alarm'
    __table_args__ = {'comment': '사용자 알람 설정'}

    created_time = Column(DateTime, primary_key=True, default=func.now())
    employee_num = Column(ForeignKey('user_info.user_employee_num'), nullable=False, comment='(SSO)사원번호')
    alarm_type = Column(String, nullable=False, comment='알람 종류(문서 분류 AI 모델 학습, 구성원)')
    is_used = Column(Boolean, comment='사용 여부')

    user_info = relationship('UserInfo')


class UserRole(Base, BaseMixin):
    __tablename__ = 'user_role'
    __table_args__ = {'comment': 'textscope 서비스 유저 그룹'}

    created_time = Column(DateTime, primary_key=True, default=func.now())
    user_employee_num = Column(ForeignKey('user_info.user_employee_num'), nullable=False, comment='(SSO)사원번호')
    role_index = Column(ForeignKey('role_info.role_index'), nullable=False, comment='역할 유니크 인덱스')
    is_used = Column(Boolean, comment='사용 여부')

    role_info = relationship('RoleInfo')
    user_info = relationship('UserInfo')


class InferenceInfo(Base, BaseMixin):
    __tablename__ = 'inference_info'
    __table_args__ = {'comment': 'textscope 서비스 추론 정보'}

    inference_id = Column(String, primary_key=True, comment='추론 아이디')
    document_id = Column(ForeignKey('document_info.document_id'), nullable=False, comment='문서 아이디')
    employee_num = Column(Integer, comment='추론 요청한 사원의 사번')
    user_personnel = Column(String, nullable=False, comment='추론 요청 당시 요청자의 인사정보(SSO)')
    model_index = Column(Integer, nullable=False, comment='사용된 모델의 유니크 인덱스')
    inference_result = Column(JSON, comment='추론 결과')
    page_id = Column(ForeignKey('page_info.page_id'), nullable=False, comment='추론한 페이지 인덱스')
    inference_type = Column(String, comment='추론 종류(gocr, cls, kv)')
    inference_start_time = Column(DateTime, nullable=False, default=func.now(), comment='추론 시작 시각')
    inference_end_time = Column(DateTime, comment='추론 완료 시각')
    is_used = Column(Boolean, comment='사용 여부')

    document = relationship('DocumentInfo')
    page = relationship('PageInfo')


class InspectInfo(Base, BaseMixin):
    __tablename__ = 'inspect_info'
    __table_args__ = {'comment': 'textscope 서비스 검수 정보'}

    inspect_id = Column(String, primary_key=True, comment='검수 아이디')
    employee_num = Column(ForeignKey('user_info.user_employee_num'), nullable=False, comment='검수자 (SSO)사원번호')
    user_personnel = Column(String, nullable=False, comment='검수 당시 검수자의 인사정보(SSO)')
    inference_id = Column(ForeignKey('inference_info.inference_id'), nullable=False, comment='추론 아이디')
    inspect_start_time = Column(DateTime, nullable=False, default=func.now(), comment='검수 시작 시각')
    inspect_end_time = Column(DateTime, comment='검수 종료 시각')
    inspect_result = Column(JSON, comment='검수 결과')
    inspect_accuracy = Column(Float(53), comment='검수 결과 정확도')
    inspect_status = Column(String, nullable=False, default='-', comment='검수 상태(검수 중, 검수 완료)')
    is_used = Column(Boolean, comment='사용 여부')
    group_index = Column(Integer)

    user_info = relationship('UserInfo')
    inference = relationship('InferenceInfo')


class VisualizeInfo(Base, BaseMixin):
    __tablename__ = 'visualize_info'
    __table_args__ = {'comment': 'textscope 서비스 추론결과 시각화 이미지 정보'}

    visualize_id = Column(Integer, primary_key=True, comment='시각화 유니크 인덱스')
    inference_id = Column(ForeignKey('inference_info.inference_id'), nullable=False, comment='추론 아이디')
    visualize_type = Column(String, comment='시각화 종류(gocr, kv)')
    visualize_method = Column(String, comment='시각화 인식결과 표시 방법(overay, split)')
    visualize_img_path = Column(String, comment='시각화 이미지 저장 겨로')
    visualize_created_time = Column(DateTime, default=func.now(), comment='시각화 저장 시각')
    is_used = Column(Boolean, comment='사용 여부')

    inference = relationship('InferenceInfo')


def create_db_table() -> None:
    try:
        session = next(db.session())
        Base.metadata.create_all(db._engine)
        
    finally:
        session.close()


def insert_initial_data() -> None:
    try:
        session = next(db.session())
        
        for fake_role in settings.FAKE_ROLE_INFORMATION_LIST:
            RoleInfo.create(session, auto_commit=True, **fake_role)
        
        for fake_user in settings.FAKE_USER_INFORMATION_LIST:
            UserInfo.create(session, auto_commit=True, **fake_user)
        
        for fake_role_user in settings.FAKE_ROLE_USER_INFORMATION_LIST:
            UserRole.create(session, auto_commit=True, **fake_role_user)
        
        for fake_model in settings.FAKE_MODEL_INFORMATION_LIST:
            ModelInfo.create(session, auto_commit=True, **fake_model)
        
    finally:
        session.close()