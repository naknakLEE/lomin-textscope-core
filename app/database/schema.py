import json
import datetime as dt
import yaml  # type: ignore
import typing
import io
import msoffcrypto
import openpyxl


from fastapi.encoders import jsonable_encoder
from typing import Any, Dict, List, Optional, TypeVar
from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, NUMERIC, JSON, String, func, ARRAY
from sqlalchemy.sql import text
from sqlalchemy.orm import Session, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.orm.attributes import flag_modified

from passlib.context import CryptContext

from app.database.connection import Base, db
from app.utils.logging import logger
from app.common.const import get_settings
from app import hydra_cfg

settings = get_settings()
metadata = Base.metadata

ModelType = TypeVar("ModelType", bound=Base)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 테이블 추가 시, 테이블 클래스 명 : primary_key 추가
primary_column_table = {
    "VWIFCD": "cmn_cd_id,cmn_cd_val",
    "VWIFEMP": "eno",
    "VWIFORGCUR": "org_id,dept_st_dt",
    
    "CompanyUserInfo": "emp_eno",
    "KeiOrgInfo": "org_org_id",
    
    "ClsGroupInfo": "cls_idx",
    "DocTypeInfo": "doc_type_idx",
    "KvClassInfo": "kv_class_code",
    "ModelInfo": "model_idx",
    "ClassInfo": "class_code",
    "DocTypeKvClass": "doc_type_idx,kv_class_code",
    "DocTypeModel": "doc_type_idx,model_idx",
    "ClsGroupModel": "cls_idx,model_idx",
    "DocTypeClsGroup": "cls_idx,doc_type_idx",
    
    "CompanyInfo": "company_code",
    
    "UserInfo": "user_email",
    "GroupInfo": "group_code",
    "UserGroup": "user_email,group_code",
    "PolicyInfo": "policy_code",
    "GroupPolicy": "group_code,policy_code",
    
    "DocumentInfo": "document_idx,document_id",
    "InspectInfo": "inspect_id",
    
    "InferenceInfo": "inference_id",
    "VisualizeInfo": "visualize_id",
    
    "AlarmInfo": "alarm_idx",
    "AlarmRead": "created_time",
    "UserAlarm": "created_time",
    
    "RpaFormInfo": "rpa_idx",
    
    "LogInfo": "log_id",
    "LogDbLink": "log_idx"
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
        check_columns = primary_column_table.get(cls.__name__)
        message = ""
        if check_columns is None:
            return message
        inputs: Dict = {}
        for check_column in check_columns.split(","):
            inputs[check_column] = kwargs.get(check_column)
        is_exist = cls.get(session, **inputs)
        if is_exist:
            message = f"This {check_columns} already exist"
            # logger.warning(f"{message}\n{kwargs}")
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
    
    # 특정 컬럼이 특정 값인 row들을 조회
    # where id = 'value'
    @typing.no_type_check
    @classmethod
    def get_all(cls, session: Session, **kwargs: Dict[str, Any]) -> Optional[ModelType]:
        query = session.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col == val)
        return query.all() if query else None

    #특정 컬럼이 특정 값들인 row들을 조회
    # where id in ('value1', 'value2')
    @typing.no_type_check
    @classmethod
    def get_all_multi(cls, session: Session, **kwargs: Dict[str, Any]) -> Optional[ModelType]:
        query = session.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col.in_(val))
        return query.all() if query else None

    # 특정 컬럼이 특정 값인 query 반환
    # where id = 'value'
    @typing.no_type_check
    @classmethod
    def get_all_query(cls, session: Session, **kwargs: Dict[str, Any]) -> Optional[ModelType]:
        query = session.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col == val)
        return query

    #특정 컬럼이 특정 값들인 query 반환
    # where id in ('value1', 'value2')
    @typing.no_type_check
    @classmethod
    def get_all_query_multi(cls, session: Session, **kwargs: Dict[str, Any]) -> Optional[ModelType]:
        query = session.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col.in_(val))
        return query

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

    # 특정 컬럼(p_key)를 특정 값(p_value)로 업데이트
    # update '테이블명' set 'p_key' = 'p_value' where **kwargs
    @typing.no_type_check
    @classmethod
    def update(
        cls,
        session: Session,
        p_key: str,
        p_value: Any,
        auto_commit: bool = True,
        **kwargs: Dict[str, Any],
    ) -> Optional[ModelType]:
        query = session.query(cls).filter(getattr(cls, p_key) == p_value).first()
        for key, val in kwargs.items():
            flag_modified(query, key)
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


class VWIFCD(Base, BaseMixin):
    __tablename__ = 'VW_IF_CD'

    cmn_cd_id = Column(String, primary_key=True, nullable=False)
    cmn_cd_nm = Column(String)
    cmn_cd_val = Column(String, primary_key=True, nullable=False)
    cmn_cd_val_nm = Column(String)
    cmn_cd_val_eng_nm = Column(String)
    cmn_cd_val_abbr_nm = Column(String)
    cmn_cd_val_ord = Column(String)
    st_dt = Column(Date)
    end_dt = Column(Date)
    use_yn = Column(String)
    cnd_cd1 = Column(String)
    cnd_cd1_nm = Column(String)
    cnd_cd2 = Column(String)
    cnd_cd2_nm = Column(String)
    cnd_cd3 = Column(String)
    cnd_cd3_nm = Column(String)
    cnd_cd4 = Column(String)
    cnd_cd4_nm = Column(String)
    cnd_cd5 = Column(String)
    cnd_cd5_nm = Column(String)
    fst_rgst_eno = Column(String)
    lst_chg_enoi = Column(String)
    fst_rgst_dttm = Column(Date)
    lst_chg_dttm = Column(Date)
    bf_cmn_cd_id = Column(String)

class VWIFEMP(Base, BaseMixin):
    __tablename__ = 'VW_IF_EMP'

    eno = Column(String, primary_key=True)
    usr_nm = Column(String)
    usr_chin_nm = Column(String)
    usr_eng_nm = Column(String)
    dpcd = Column(String)
    dept_nm = Column(String)
    tmcd = Column(String)
    team_nm = Column(String)
    ofps_cd = Column(String)
    ofps_nm = Column(String)
    ofps_eng_nm = Column(String)
    pscl_cd = Column(String)
    pscl_nm = Column(String)
    ocpt_cd = Column(String)
    ocpt_nm = Column(String)
    evdg_cd = Column(String)
    evdg_nm = Column(String)
    usr_emad = Column(String)
    usr_mpno = Column(String)
    inbk_tno = Column(String)
    wplc_dvcd = Column(String)
    wplc_dv_nm = Column(String)
    inco_dt = Column(Date)
    rtrm_dt = Column(Date)
    brdt = Column(Date)
    usr_kncd = Column(String)
    bfc_sts = Column(String)
    bfc_sts_nm = Column(String)
    bfc_sts_bf = Column(String)
    bfc_sts_bf_nm = Column(String)
    rspb_bz = Column(String)
    mrrg_date = Column(String)
    obst_yn = Column(String)
    bkcl_inq_ord = Column(NUMERIC)
    sex = Column(String)
    ooh_tel = Column(String)
    zpcd = Column(String)
    adr = Column(String)
    dept_st_dt = Column(Date)
    dept_key = Column(String)
    fax_no = Column(String)
    indv_eml = Column(String)
    lva_st_dt = Column(Date)
    lva_ed_dt = Column(Date)
    lva_prr_dt = Column(Date)
    kid_3age_yn = Column(String)
    evl_eno = Column(String)
    evl_nm = Column(String)
    cfr_eno = Column(String)
    cfr_nm = Column(String)
    prmt_dt = Column(Date)
    elvt_dt = Column(Date)
    lst_chg_eno = Column(String)
    lst_chg_dttm = Column(Date)
    fst_rgst_eno = Column(String)
    fst_rgst_dttm = Column(Date)
    vct_yn = Column(String)
    rgno_enc = Column(String)
    work_h_cnt = Column(NUMERIC)
    title = Column(String)
    title_type = Column(String)
    cm_use_h_cnt = Column(NUMERIC)
    cm_rm_h_cnt = Column(NUMERIC)
    yy_dgr_use_h_cnt = Column(NUMERIC)
    yy_dgr_rm_h_cnt = Column(NUMERIC)
    etc_use_h_cnt = Column(NUMERIC)
    etc_rm_h_cnt = Column(NUMERIC)
    enter_std_ymd = Column(String)
    ci_id = Column(String)

class VWIFORGCUR(Base, BaseMixin):
    __tablename__ = 'VW_IF_ORG_CUR'

    org_id = Column(String, primary_key=True, nullable=False)
    org_nm = Column(String)
    dpcd = Column(String)
    dept_krn_nm = Column(String)
    dept_eng_nm = Column(String)
    tmcd = Column(String)
    team_nm = Column(String)
    team_eng_nm = Column(String)
    hgh_dpcd = Column(String)
    dept_ord = Column(NUMERIC)
    team_ord = Column(NUMERIC)
    wplc_dvcd = Column(String)
    dept_st_dt = Column(Date, primary_key=True, nullable=False)
    dept_ed_dt = Column(Date)
    rep_dpcd = Column(String)
    drhq_eno = Column(String)
    drhq_nm = Column(String)
    drhq_ofps_cd = Column(String)
    dldr_eno = Column(String)
    dldr_nm = Column(String)
    dldr_ofps_cd = Column(String)
    tmgr_eno = Column(String)
    tmgr_nm = Column(String)
    tmgr_ofps_cd = Column(String)
    dept_lvl_val = Column(String)
    dept_lvl = Column(String)
    crcd = Column(String)
    dept_zpcd = Column(String)
    dept_adr = Column(String)
    dept_eng_adr = Column(String)
    dept_emad = Column(String)
    dept_tno = Column(String)
    dept_kncd = Column(String)
    dept_fxno = Column(String)
    lcr_fund_dept_yn = Column(String)
    ed_fund_dept_yn = Column(String)
    dnf_dvcd = Column(String)
    rule_dept_yn = Column(String)
    dnl_dept_yn = Column(String)
    fi_net_br_cd = Column(String)
    sn_fund_dept_yn = Column(String)
    sn_dept_yn = Column(String)
    bg_dept_knd_cd = Column(String)
    crln_dept_yn = Column(String)
    bg_dept_yn = Column(String)
    bg_exec_dept_yn = Column(String)
    exeq_dept_yn = Column(String)
    dily_adt_obj_yn = Column(String)
    fd_dept_yn = Column(String)
    asts_dept_yn = Column(String)
    lwst_yn = Column(String)
    spct_wplc_yn = Column(String)
    ac_rspb_eno = Column(String)
    ac_dept_yn = Column(String)
    ac_duty_eno = Column(String)
    br_yn = Column(String)
    cnry_cd = Column(String)
    dept_sctn_cd = Column(String)
    dept_abbr_nm = Column(String)
    op_risk_org_yn = Column(String)
    use_yn = Column(String)
    bkcl_yn = Column(String)
    fst_rgst_eno = Column(String)
    fst_rgst_dttm = Column(Date)
    lst_chg_eno = Column(String)
    lst_chg_dttm = Column(Date)


class AlarmInfo(Base, BaseMixin):
    __tablename__ = 'alarm_info'
    __table_args__ = {'comment': 'textscope 서비스 알람 목록'}

    alarm_idx = Column(Integer, primary_key=True, comment='알람 유니크 인덱스')
    alarm_range = Column(String, nullable=False, default='전체', comment='알람 노출 범위(전체, 팀)')
    alarm_type = Column(String, nullable=False, comment='알람 종류(문서 분류 AI 모델 학습, 구성원)')
    alarm_title = Column(String, nullable=False, comment='알람 제목')
    alarm_content = Column(String, nullable=False, default='(내용없음)', comment='알람 내용')
    alarm_created_time = Column(DateTime, nullable=False, default=func.now(), comment='알람 생성 시각')
    alarm_modified_time = Column(DateTime, nullable=False, default=func.now(), comment='알람 수정 시각')
    is_used = Column(Boolean, comment='사용 여부')


class KeiOrgInfo(Base, BaseMixin):
    __tablename__ = 'kei_org_info'
    __table_args__ = {'comment': 'textscope 서비스에 필요한 조직 정보'}

    company_code = Column(ForeignKey('company_info.company_code'), nullable=False, comment='회사 유니크 코드')
    org_org_id = Column(String, primary_key=True, comment='조직ID')
    org_org_nm = Column(String, comment='조직명')
    org_hgh_dpcd = Column(String, comment='상위조직ID')
    org_dept_lvl_val = Column(String, comment='부서 레벨')
    org_dept_lvl = Column(String, comment='현시점의 부서트리 레벨(뎁스)')
    org_path = Column(String, comment='조직 path')
    is_used = Column(Boolean, comment='사용 여부')
    
    company_info = relationship('CompanyInfo')


class ClsGroupInfo(Base, BaseMixin):
    __tablename__ = 'cls_group_info'
    __table_args__ = {'comment': 'textscope 서비스 대분류 그룹 정보'}
    
    company_code = Column(String, comment='회사 유니크 코드')
    cls_idx = Column(Integer, primary_key=True, comment='문서 종류(대분류) 유니크 인덱스')
    cls_code = Column(String, comment='문서 종류(대분류) 표준 코드')
    cls_name_kr = Column(String, comment='문서 종류(대분류) 한글 명')
    cls_name_en = Column(String, comment='문서 종류(대분류) 영문 명')
    is_used = Column(Boolean, comment='사용 여부')


class DocTypeInfo(Base, BaseMixin):
    __tablename__ = 'doc_type_info'
    __table_args__ = {'comment': 'textscope 서비스 문서 종류(소분류) 정보'}
    
    doc_type_idx = Column(Integer, primary_key=True, comment='문서 종류(소분류) 유니크 인덱스')
    doc_type_code = Column(String, comment='문서 종류(소분류) 표준 코드')
    doc_type_code_parent = Column(String, comment='상위 문서 종류(소분류) 표준 코드')
    doc_type_name_kr = Column(String, comment='문서 종류(소분류) 한글 명')
    doc_type_name_en = Column(String, comment='문서 종류(소분류) 영문 명')
    doc_type_structed = Column(String, comment='문서 유형(정형, 비정형, 반정형)')
    is_used = Column(Boolean, comment='사용 여부')


class KvClassInfo(Base, BaseMixin):
    __tablename__ = 'kv_class_info'
    __table_args__ = {'comment': 'textscope 서비스 kv class 정보'}
    
    kv_class_code = Column(String, primary_key=True, comment='항목 서식 코드')
    kv_class_name_kr = Column(String, comment='항목 서식 한글 명')
    kv_class_name_en = Column(String, comment='항목 서식 영문 명')
    kv_class_use = Column(String, comment='항목 사용 여부')
    kv_class_type = Column(String, comment='항목 타입 (word, checkbox)')
    is_used = Column(Boolean, comment='사용 여부')


class DocTypeKvClass(Base, BaseMixin):
    __tablename__ = 'doc_type_kv_class'
    __table_args__ = {'comment': 'textscope 서비스 문서 종류(소분류)와 kv class 정보'}
    
    created_time = Column(DateTime, primary_key=True, default=func.now())
    doc_type_idx = Column(ForeignKey('doc_type_info.doc_type_idx'), nullable=False, comment='문서 종류(소분류) 유니크 인덱스')
    kv_class_code = Column(ForeignKey('kv_class_info.kv_class_code'), nullable=False, comment='항목 서식 코드')
    sequence = Column(Integer, comment='항목 표시 순서')
    is_used = Column(Boolean, comment='사용 여부')
    
    doc_type_info = relationship('DocTypeInfo')
    kv_class_info = relationship('KvClassInfo')


class ModelInfo(Base, BaseMixin):
    __tablename__ = 'model_info'
    __table_args__ = {'comment': 'textscope 서비스 등록된 딥러닝 모델 정보'}

    model_idx = Column(Integer, primary_key=True, comment='모델 유니크 인덱스')
    model_name_kr = Column(String, comment='모델 한글 명')
    model_name_en = Column(String, comment='모델 영문 명')
    model_description = Column(String, comment='모델 설명')
    model_version = Column(String, comment='모델 버전')
    model_path = Column(String, comment='모델 저장 경로')
    model_type = Column(String, comment='모델 종류')
    model_route_name = Column(String, comment='모델 route 명')
    model_artifact_name = Column(String, comment='모델 artifact 명')
    model_created_time = Column(DateTime, default=func.now(), comment='모델 등록 시각')
    is_used = Column(Boolean, comment='사용 여부')


class DocTypeClsGroup(Base, BaseMixin):
    __tablename__ = 'doc_type_cls_group'
    __table_args__ = {'comment': 'textscope 서비스 문서 종류 분류 그룹'}

    created_time = Column(DateTime, primary_key=True, default=func.now())
    cls_idx = Column(ForeignKey('cls_group_info.cls_idx'), nullable=False, comment='문서 종류(대분류) 유니크 인덱스')
    doc_type_idx = Column(ForeignKey('doc_type_info.doc_type_idx'), nullable=False, comment='문서 종류(소분류) 유니크 인덱스')
    is_used = Column(Boolean, comment='사용 여부')
    
    doc_type_info = relationship('DocTypeInfo')
    cls_group_info = relationship('ClsGroupInfo')


class DocTypeModel(Base, BaseMixin):
    __tablename__ = 'doc_type_model'
    __table_args__ = {'comment': 'textscope 서비스 문서 타입별 사용하는 모델'}

    created_time = Column(DateTime, primary_key=True, default=func.now())
    doc_type_idx = Column(ForeignKey('doc_type_info.doc_type_idx'), nullable=False, comment='문서 종류(소분류) 유니크 인덱스')
    model_idx = Column(ForeignKey('model_info.model_idx'), nullable=False, comment='모델 유니크 인덱스')
    sequence = Column(Integer, nullable=False, comment='모델 사용 순서')
    is_used = Column(Boolean, comment='사용 여부')

    doc_type_info = relationship('DocTypeInfo')
    model_info = relationship('ModelInfo')


class ClsGroupModel(Base, BaseMixin):
    __tablename__ = 'cls_group_model'
    __table_args__ = {'comment': 'textscope 서비스 대분류 그룹과 모델 관계'}

    created_time = Column(DateTime, primary_key=True, default=func.now())
    cls_idx = Column(ForeignKey('cls_group_info.cls_idx'), nullable=False, comment='문서 종류(대분류) 유니크 인덱스')
    model_idx = Column(ForeignKey('model_info.model_idx'), nullable=False, comment='문서 분류 모델 유니크 인덱스')
    is_used = Column(Boolean, comment='사용 여부')

    cls_group_info = relationship('ClsGroupInfo')
    model_info = relationship('ModelInfo')


class PolicyInfo(Base, BaseMixin):
    __tablename__ = 'policy_info'
    __table_args__ = {'comment': 'textscope 서비스 정책 정보'}

    policy_code = Column(String, primary_key=True, comment='정책 코드')
    policy_name = Column(String, comment='정책 이름')
    is_used = Column(Boolean, comment='사용 여부')


class GroupInfo(Base, BaseMixin):
    __tablename__ = 'group_info'
    __table_args__ = {'comment': 'textscope 서비스 그룹 정보'}

    group_code = Column(String, primary_key=True, comment='그룹 유니크 코드')
    group_level = Column(Integer, comment='그룹 레벨(최상=1)')
    group_name = Column(String, nullable=False, default='그룹이름', comment='그룹 이름')
    is_used = Column(Boolean, comment='사용 여부')


class LogInfo(Base, BaseMixin):
    __tablename__ = 'log_info'
    __table_args__ = {'comment': 'textscope 서비스 로그 정보'}

    log_id = Column(String, primary_key=True, comment='로그 아이디')
    log_type = Column(String, comment='로그 종류')
    created_time = Column(DateTime, default=func.now())
    user_email = Column(String, nullable=False, comment='로그 생성자 아이디(이메일)')
    user_team = Column(String, nullable=False, comment='로그 생성 당시 유저의 정보')
    log_content = Column(JSON, comment='로그 내용')
    is_used = Column(Boolean, comment='사용 여부')


class CompanyInfo(Base, BaseMixin):
    __tablename__ = 'company_info'
    __table_args__ = {'comment': 'textscope 서비스 회사 정보'}

    created_time = Column(DateTime, default=func.now())
    company_code = Column(String, primary_key=True, comment='회사 유니크 코드')
    company_name = Column(String, comment='회사 명')
    company_domain = Column(String, comment='회사 도메인')
    company_address = Column(String, comment='회사 주소')
    company_ph = Column(String, comment='회사 대표 연락처')
    company_ceo = Column(String, comment='회사 대표자 성함')


class UserInfo(Base, BaseMixin):
    __tablename__ = 'user_info'
    __table_args__ = {'comment': 'textscope 서비스 사용자 정보'}

    user_email = Column(String, primary_key=True, nullable=False, comment='아이디(이메일)')
    user_pw = Column(String, comment='비밀번호')
    user_name = Column(String, comment='이름')
    user_team = Column(String, comment='유저 정보')
    is_used = Column(Boolean, comment='사용 여부')


class ClassInfo(Base, BaseMixin):
    __tablename__ = 'class_info'
    __table_args__ = {'comment': 'textscope 서비스 딥러닝 모델의 항목(라벨 클래스)'}

    class_idx = Column(Integer, primary_key=True, comment='항목 유니크 인덱스')
    class_code = Column(String, comment='항목 코드')
    model_idx = Column(ForeignKey('model_info.model_idx'), nullable=False, comment='모델 유니크 인덱스')
    class_name_kr = Column(String, comment='항목 한글 명')
    class_name_en = Column(String, comment='항목 영문 명')
    class_use = Column(Boolean, comment='항목 사용 여부')
    is_used = Column(Boolean, comment='사용 여부')

    model_info = relationship('ModelInfo')


class DocumentInfo(Base, BaseMixin):
    __tablename__ = 'document_info'
    __table_args__ = {'comment': 'textscope 서비스 학습 또는 추론을 위해 업로드된 문서 정보'}

    document_idx = Column(BigInteger, primary_key=True, comment='문서 유니크 인덱스')
    document_id = Column(String, nullable=False, unique=True, comment='문서 아이디')
    user_email = Column(ForeignKey('user_info.user_email'), nullable=False, comment='문서 등록자 아이디(이메일)')
    user_team = Column(String, nullable=False, comment='문서 등록 당시 유저의 정보')
    document_upload_time = Column(DateTime, default=func.now(), comment='문서 업로드 시각')
    document_path = Column(String, comment='문서 저장 경로')
    document_description = Column(String, comment='문서 설명')
    document_pages = Column(Integer, comment='문서 총 페이지 수')
    cls_idx = Column(Integer, comment='문서 대분류 그룹 인덱스')
    doc_type_idxs = Column(MutableDict.as_mutable(JSON), comment='문서에 포함된 문서 소분류 인덱스 리스트')
    doc_type_idx = Column(ARRAY(Integer, zero_indexes=True), comment="")
    doc_type_code = Column(ARRAY(String, zero_indexes=True), comment="")
    doc_type_cls_match = Column(ARRAY(Boolean, zero_indexes=True), comment="")
    document_accuracy = Column(Float, comment="")
    inspect_id = Column(String, default='RUNNING_INFERENCE', comment='문서의 최근 검수 아이디')
    is_used = Column(Boolean, comment='사용 여부')

    user_info = relationship('UserInfo')


class CompanyUserInfo(Base, BaseMixin):
    __tablename__ = 'company_user_info'
    __table_args__ = {'comment': 'textscope 서비스에 필요한 인사 정보'}

    company_code = Column(ForeignKey('company_info.company_code'), nullable=False, comment='회사 유니크 코드')
    emp_eno = Column(String, primary_key=True, comment='행번')
    emp_usr_emad = Column(ForeignKey('user_info.user_email'), nullable=False, comment='사원 이메일주소')
    emp_usr_mpno = Column(String, comment='사원 휴대전화번호')
    emp_inbk_tno = Column(String, comment='사원 행내전화번호')
    emp_usr_nm = Column(String, comment='성명')
    emp_decd = Column(String, comment='부서코드')
    emp_tecd = Column(String, comment='팀코드')
    emp_org_path = Column(String, comment='조직 path')
    emp_ofps_cd = Column(String, comment='직위코드')
    emp_ofps_nm = Column(String, comment='직위명')
    emp_pscl_cd = Column(String, comment='직급코드')
    emp_fst_rgst_dttm = Column(DateTime, comment='사원 등록일')
    is_used = Column(Boolean, comment='사용 여부')

    company_info = relationship('CompanyInfo')
    user_info = relationship('UserInfo')


class GroupPolicy(Base, BaseMixin):
    __tablename__ = 'group_policy'
    __table_args__ = (UniqueConstraint('group_code', 'policy_code', name='_group_police_code'), )

    created_time = Column(DateTime, primary_key=True, default=func.now())
    group_code = Column(ForeignKey('group_info.group_code'), nullable=False, comment='그룹 유니크 코드')
    policy_code = Column(ForeignKey('policy_info.policy_code'), nullable=False, comment='정책 코드')
    policy_content = Column(MutableDict.as_mutable(JSON), comment='정책 내용')
    start_time = Column(DateTime, nullable=False, default=func.now(), comment='정책 적용 시작 시각')
    end_time = Column(DateTime, nullable=False, default=func.now(), comment='정책 적용 종료 시각')
    is_used = Column(Boolean, comment='사용 여부')

    policy_info = relationship('PolicyInfo')
    group_info = relationship('GroupInfo')



class UserGroup(Base, BaseMixin):
    __tablename__ = 'user_group'
    __table_args__ = {'comment': 'textscope 서비스 유저 그룹'}

    created_time = Column(DateTime, primary_key=True, default=func.now())
    user_email = Column(ForeignKey('user_info.user_email'), nullable=False, comment='아이디(이메일)')
    group_code = Column(ForeignKey('group_info.group_code'), nullable=False, comment='그룹 유니크 코드')
    is_used = Column(Boolean, comment='사용 여부')

    group_info = relationship('GroupInfo')
    user_info = relationship('UserInfo')


class AlarmRead(Base, BaseMixin):
    __tablename__ = 'alarm_read'
    __table_args__ = {'comment': '사용자가 읽은 알람 정보'}

    created_time = Column(DateTime, primary_key=True, default=func.now())
    user_email = Column(ForeignKey('user_info.user_email'), nullable=False, comment='아이디(이메일)')
    alarm_idx = Column(ForeignKey('alarm_info.alarm_idx'), nullable=False, comment='알람 유니크 인덱스')
    is_used = Column(Boolean, comment='사용 여부')

    alarm_info = relationship('AlarmInfo')
    user_info = relationship('UserInfo')


class InferenceInfo(Base, BaseMixin):
    __tablename__ = 'inference_info'
    __table_args__ = {'comment': 'textscope 서비스 추론 정보'}

    inference_id = Column(String, primary_key=True, comment='추론 아이디')
    document_id = Column(ForeignKey('document_info.document_id'), nullable=False, comment='문서 아이디')
    user_email = Column(String, comment='추론 요청한 유저의 아이디(이메일)')
    user_team = Column(String, nullable=False, comment='추론 요청 당시 요청자의 유저 정보')
    inference_result = Column(JSON, comment='추론 결과')
    inference_type = Column(String, comment='추론 종류(gocr, kv)')
    inference_start_time = Column(DateTime, nullable=False, default=func.now(), comment='추론 시작 시각')
    inference_end_time = Column(DateTime, comment='추론 완료 시각')
    page_num = Column(Integer, comment='추론한 페이지 페이지')
    doc_type_idx = Column(Integer, comment='페이지의 문서 종류 유니크 인덱스')
    page_width = Column(Integer, comment='이미지 변환 후 가로 크기')
    page_height = Column(Integer, comment='이미지 변환 후 세로 크기')
    is_used = Column(Boolean, comment='사용 여부')

    document_info = relationship('DocumentInfo')


class UserAlarm(Base, BaseMixin):
    __tablename__ = 'user_alarm'
    __table_args__ = {'comment': '사용자 알람 설정'}

    created_time = Column(DateTime, primary_key=True, default=func.now())
    user_email = Column(ForeignKey('user_info.user_email'), nullable=False, comment='아이디(이메일)')
    alarm_type = Column(String, nullable=False, comment='알람 종류(문서 분류 AI 모델 학습, 구성원)')
    is_used = Column(Boolean, comment='사용 여부')

    user_info = relationship('UserInfo')


class InspectInfo(Base, BaseMixin):
    __tablename__ = 'inspect_info'
    __table_args__ = {'comment': 'textscope 서비스 검수 정보'}

    inspect_id = Column(String, primary_key=True, comment='검수 아이디')
    user_email = Column(ForeignKey('user_info.user_email'), comment='검수자 아이디(이메일)')
    user_team = Column(String, comment='user_team')
    inference_id = Column(ForeignKey('inference_info.inference_id'), comment='추론 아이디')
    inspect_start_time = Column(DateTime, default=func.now(), comment='검수 시작 시각')
    inspect_end_time = Column(DateTime, comment='검수 종료 시각')
    inspect_result = Column(JSON, comment='검수 결과')
    inspect_accuracy = Column(Float(53), comment='검수 결과 정확도')
    inspect_status = Column(String, default='대기', comment='검수 상태(대기, 검수 중, 검수 완료)')
    is_used = Column(Boolean, comment='사용 여부')

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
    

class RpaFormInfo(Base, BaseMixin):
    __tablename__ = 'rpa_form_info'
    __table_args__ = {'comment': 'RPA 양식 이력'}

    rpa_idx = Column(Integer, primary_key=True, comment='rpa 양식 유니크 인텍스')
    rpa_receiver_email = Column(String, nullable=False, comment='수신자')
    rpa_title = Column(String, nullable=False, comment='rpa 양식 제목')
    rpa_body = Column(String, nullable=False, comment='rpa 양식 본문')
    rpa_nas_path = Column(String, nullable=False,comment='rpa nas 경로')
    rpa_created_time = Column(DateTime, nullable=False, default=func.now(), comment='rpa 양식 생성 시각')
    rpa_created_owner = Column(String, comment='rpa 양식 생성자(이메일)')
    rpa_modified_time = Column(DateTime, default=func.now(), comment='rpa 양식 수정 시각')
    rpa_modified_owner = Column(String, comment='rpa 양식 수정자(이메일)')
    is_used = Column(Boolean, comment='사용 여부')


class LogDbLink(Base, BaseMixin):
    __tablename__ = 'log_db_link'
    __table_args__ = {'comment': 'db link 배치이력 조회'}

    log_idx = Column(Integer, primary_key=True, comment='로그 유니크 인텍스')
    batch_type = Column(String, nullable=False, comment='배치 유형')
    batch_name = Column(String, nullable=False, comment='배치명')
    result_message = Column(String, nullable=False, comment='결과 메시지')
    db_link_start_time = Column(DateTime, comment='dblink 시작일시')
    db_link_end_time = Column(DateTime, comment='dblink 종료일시')
    created_time = Column(DateTime, nullable=False, default=func.now(), comment='dblink 생성 시각')
    created_owner = Column(String, comment='rpa 양식 수정자(이메일)')
    is_used = Column(Boolean, comment='사용 여부')



# 테이블 추가 시, 테이블 명:클래스 명 추가
table_class_mapping = dict({
    "VW_IF_CD": VWIFCD,
    "VW_IF_EMP": VWIFEMP,
    "VW_IF_ORG_CUR": VWIFORGCUR,
    "alarm_info": AlarmInfo,
    "kei_org_info": KeiOrgInfo,
    "company_user_info": CompanyUserInfo,
    "doc_type_info": DocTypeInfo,
    "model_info": ModelInfo,
    "doc_type_model": DocTypeModel,
    "kv_class_info": KvClassInfo,
    "doc_type_kv_class": DocTypeKvClass,
    "cls_group_info": ClsGroupInfo,
    "doc_type_cls_group": DocTypeClsGroup,
    "cls_group_model": ClsGroupModel,
    "policy_info": PolicyInfo,
    "group_info": GroupInfo,
    "log_info": LogInfo,
    "company_info": CompanyInfo,
    "user_info": UserInfo,
    "class_info": ClassInfo,
    "document_info": DocumentInfo,
    "group_policy": GroupPolicy,
    "user_group": UserGroup,
    "alarm_read": AlarmRead,
    "inference_info": InferenceInfo,
    "user_alarm": UserAlarm,
    "user_group": UserGroup,
    "inspect_info": InspectInfo,
    "visualize_info": VisualizeInfo,
    "rpa_form_info": RpaFormInfo,
    "log_db_link": LogDbLink,
})

# plugin 계정에 특정 테이블 권한 주기
grant_table_list = [
    "user_info",
    "user_group",
    "group_info",
    "group_policy",
    "policy_info",
    "document_info",
    "inference_info",
    "inspect_info",
    "alarm_info",
    "alarm_read",
    "user_alarm",
    "kei_org_info",
    "company_user_info",
    
    "doc_type_info",
    "doc_type_model",
    "cls_group_info",
    "doc_type_cls_group",
    "cls_group_model",
    "kv_class_info",
    "doc_type_kv_class",
    "log_db_link",
    
]

# plugin 계정에 특정 시퀀스 권한 주기
grant_sequences_list = [
    "log_db_link_log_idx_seq"
]

def create_db_table() -> None:
    try:
        session: Session = next(db.session())
        Base.metadata.create_all(db._engine)
    finally:
        session.close()

def create_extension() -> None:
    try:
        connection = db.engine.connect()
        connection.execute(text(
            "create EXTENSION IF NOT EXISTS dblink SCHEMA public"
        ))
        
    except Exception as exce:
        logger.error(exce)
    finally:
        if connection: connection.close()

def create_db_users() -> None:
    connection = None
    try:
        connection = db.engine.connect()
        sql_create_user = """CREATE USER %TS%username%TS% WITH PASSWORD '%TS%passwd%TS%'"""
        sql_grant_table = """GRANT ALL ON %TS%table%TS% TO %TS%username%TS%"""
        sql_grant_sequences = """GRANT ALL on %TS%sequences%TS% to %TS%username%TS%;"""

        
        for user in settings.POSTGRES_USERS:
            connection.execute(text(
                sql_create_user \
                .replace("%TS%username%TS%", user.get("username")) \
                .replace("%TS%passwd%TS%", user.get("passwd"))
            ))
            for table in grant_table_list:
                connection.execute(text(
                    sql_grant_table \
                    .replace("%TS%table%TS%", table) \
                    .replace("%TS%username%TS%", user.get("username"))
                ))
            for sequence in grant_sequences_list:
                connection.execute(text(
                    sql_grant_sequences \
                    .replace("%TS%sequences%TS%", sequence) \
                    .replace("%TS%username%TS%", user.get("username"))
                ))
        
    except Exception as exce:
        logger.error(exce)
    finally:
        if connection: connection.close()


def insert_initial_data() -> None:
    try:
        session = next(db.session())
        
        initial_data: InspectInfo = InspectInfo.get(session, inspect_id=settings.STATUS_RUNNING_INFERENCE)
        if initial_data is not None and initial_data.inspect_id == settings.STATUS_RUNNING_INFERENCE:
            logger.info(f'Textscope service initial data skipped')
            return
        
        db_dir="/workspace/app/assets/database/"
        
        total_row_count = 0
        insert_start = dt.datetime.now()
        
        for file_info in settings.INIT_DATA_XLSX_FILE_LIST:
            if file_info.get("name") not in hydra_cfg.database.insert_initial_filename: continue
            
            init_xlsx_d = io.BytesIO()
            with open(db_dir + file_info.get("name") + ".xlsx", 'rb') as xlfile:
                init_xlsx_e = msoffcrypto.OfficeFile(xlfile)
                init_xlsx_e.load_key(password=file_info.get("password"))
                init_xlsx_e.decrypt(init_xlsx_d)
            wb = openpyxl.load_workbook(filename=init_xlsx_d)
            
            sheets: List[str] = wb.get_sheet_names()[1:]
            for sheet_ignore in file_info.get("ignore", []):
                sheets.remove(sheet_ignore)
            
            for table_name in sheets:
                target_table = table_class_mapping.get(table_name)
                
                ws = wb.get_sheet_by_name(table_name)
                row_cells = list(ws.rows)
                
                check_columns = primary_column_table.get(table_class_mapping.get(table_name).__name__)
                check_idx_list: List[int] = list()
                for idx, column in enumerate(row_cells[0]):
                    if column.value in check_columns.split(","): check_idx_list.append(idx)
                
                for row_cell in row_cells[1:]:
                    
                    able_data = True
                    
                    for idx in check_idx_list:
                        if row_cell[idx].value is None: able_data = False
                    
                    if able_data is False:
                        continue
                    
                    init_data = dict()
                    
                    for column, cell in zip(row_cells[0], row_cell):
                        if cell.value is None: continue
                        
                        column_name = column.value.lower()
                        cell_value = str(cell.value)
                        
                        db_type = getattr(target_table, column_name).type
                        
                        if isinstance(db_type, Boolean):
                            if cell_value[0].upper() == "Y" or cell_value[0].upper() == "T" or cell_value[0] == "1":
                                cell_value = True
                            else:
                                cell_value = False
                            
                        elif isinstance(db_type, JSON):
                            cell_value: dict = json.loads(cell_value)
                        init_data.update({column_name:cell_value})
                    
                    if len(init_data) != 0:
                        result = target_table.create(session, auto_commit=True, **init_data)
                        if not isinstance(result, str): total_row_count += 1
                        del column, cell, column_name, cell_value, init_data
        del target_table, ws, wb, init_xlsx_e, init_xlsx_d, file_info
        
        logger.info(
            f'Textscope service initial data insert Total: {total_row_count} rows, {str(round((dt.datetime.now()-insert_start).total_seconds(), 3))}s'
        )
    except Exception as exce:
        logger.error(exce)
        logger.error("file: {0}, sheet: {1}, row: {2}".format(file_info.get("name"), table_name, row_cell[0].row))
    finally:
        session.close()