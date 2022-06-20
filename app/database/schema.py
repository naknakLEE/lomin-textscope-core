import datetime as dt
import yaml  # type: ignore
import typing
import io
import msoffcrypto
import openpyxl
from os import environ
from pathlib import Path, PurePath


from typing import Any, Dict, List, Optional, TypeVar, Union
from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, NUMERIC, JSON, String, func
from sqlalchemy.orm import Session, relationship
from sqlalchemy.ext.declarative import declarative_base

from passlib.context import CryptContext

from app.database.connection import Base, db
from app.utils.logging import logger
from app.common.const import get_settings
from app import hydra_cfg

settings = get_settings()
metadata = Base.metadata

ModelType = TypeVar("ModelType", bound=Base)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

exist_column_table = {
    "VWIFCD": "cmn_cd_id,cmn_cd_val",
    "VWIFEMP": "eno",
    "VWIFORGCUR": "org_id,dept_st_dt",
    
    "KeiUserInfo": "emp_eno",
    "KeiOrgInfo": "org_org_id",
    
    "UserInfo": "user_email",
    "RoleInfo": "role_index",
    "UserRole": "user_email,role_index",
    "Document": "document_id",
    "ModelInfo": "model_index",
    "InspectInfo": "inspect_id"
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
    def get_all(cls, session: Session, **kwargs: Dict[str, Any]) -> Optional[ModelType]:
        query = session.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col == val)
        return query.all()

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
            query = query.filter(col.in_(val))
        return query.all() if query else None

    @typing.no_type_check
    @classmethod
    def get_all_query(cls, session: Session, **kwargs: Dict[str, Any]) -> Optional[ModelType]:
        query = session.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col == val)
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

    alarm_index = Column(Integer, primary_key=True, comment='알람 유니크 인덱스')
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

    org_org_id = Column(String, primary_key=True, comment='조직ID')
    org_org_nm = Column(String, comment='조직명')
    org_hgh_dpcd = Column(String, comment='상위조직ID')
    org_dept_lvl = Column(String, comment='현시점의 부서트리 레벨(뎁스)')
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


class TaskInfo(Base, BaseMixin):
    __tablename__ = 'task_info'
    __table_args__ = {'comment': 'textscope 서비스 task 정보'}

    task_id = Column(String, primary_key=True, comment='테스크 아이디')
    user_email = Column(ForeignKey('user_info.user_email'), nullable=False, comment='테스크 생성자 아이디(이메일)')
    user_team = Column(String, nullable=False, comment='테스크 생성 당시 유저의 정보')
    task_content = Column(JSON, comment='테스크 내용')
    task_start_time = Column(DateTime, comment='테스크 시작 시각')
    task_end_time = Column(DateTime, comment='테스크 종료 시각')
    is_used = Column(Boolean, comment='사용 여부')


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

    class_code = Column(String, primary_key=True, comment='항목 코드')
    model_index = Column(ForeignKey('model_info.model_index'), nullable=False, comment='모델 유니크 인덱스')
    class_name_kr = Column(String, comment='항목 한글 명')
    class_name_en = Column(String, comment='항목 영문 명')
    class_use = Column(Boolean, comment='항목 사용 여부')
    is_used = Column(Boolean, comment='사용 여부')

    model_info = relationship('ModelInfo')


class DocumentInfo(Base, BaseMixin):
    __tablename__ = 'document_info'
    __table_args__ = {'comment': 'textscope 서비스 학습 또는 추론을 위해 업로드된 문서 정보'}

    document_id = Column(String, primary_key=True, comment='문서 아이디')
    user_email = Column(ForeignKey('user_info.user_email'), nullable=False, comment='문서 등록자 아이디(이메일)')
    user_team = Column(String, nullable=False, comment='문서 등록 당시 유저의 정보')
    document_path = Column(String, comment='문서 저장 경로')
    document_description = Column(String, comment='문서 설명')
    document_model_type = Column(String, comment='문서 유형(해외투자 사업 계획서, 해외투자 신고서, ...)')
    document_type = Column(String, comment='문서 타입(정형, 비정형)')
    document_upload_time = Column(DateTime, default=func.now(), comment='문서 업로드 시각')
    document_pages = Column(Integer, comment='문서 총 페이지 수')
    inspect_id = Column(String, default='None', comment='문서의 최근 검수 아이디')
    is_used = Column(Boolean, comment='사용 여부')

    user_info = relationship('UserInfo')


class KeiUserInfo(Base, BaseMixin):
    __tablename__ = 'kei_user_info'
    __table_args__ = {'comment': 'textscope 서비스에 필요한 인사 정보'}

    emp_eno = Column(String, primary_key=True, comment='(SSO)행번')
    emp_usr_emad = Column(ForeignKey('user_info.user_email'), nullable=False, comment='(SSO)사용자이메일주소')
    emp_usr_nm = Column(String, comment='(SSO)성명')
    emp_decd = Column(String, comment='(SSO)부서코드')
    emp_tecd = Column(String, comment='(SSO)팀코드')
    emp_ofps_cd = Column(String, comment='(SSO)직위코드')
    emp_pscl_cd = Column(String, comment='(SSO)직급코드')
    is_used = Column(Boolean, comment='사용 여부')

    user_info = relationship('UserInfo')


class RolePermission(Base, BaseMixin):
    __tablename__ = 'role_permission'
    __table_args__ = {'comment': 'textscope 서비스 역할 권한'}

    created_time = Column(DateTime, primary_key=True, default=func.now())
    role_index = Column(ForeignKey('role_info.role_index'), nullable=False, comment='역할 유니크 인덱스')
    permission_code = Column(ForeignKey('permission_info.permission_code'), nullable=False, comment='권한 코드')
    is_used = Column(Boolean, comment='사용 여부')

    permission_info = relationship('PermissionInfo')
    role_info = relationship('RoleInfo')



class UserRole(Base, BaseMixin):
    __tablename__ = 'user_role'
    __table_args__ = {'comment': 'textscope 서비스 유저 그룹'}

    created_time = Column(DateTime, primary_key=True, default=func.now())
    user_email = Column(ForeignKey('user_info.user_email'), nullable=False, comment='아이디(이메일)')
    role_index = Column(ForeignKey('role_info.role_index'), nullable=False, comment='역할 유니크 인덱스')
    is_used = Column(Boolean, comment='사용 여부')

    role_info = relationship('RoleInfo')
    user_info = relationship('UserInfo')


class AlarmRead(Base, BaseMixin):
    __tablename__ = 'alarm_read'
    __table_args__ = {'comment': '사용자가 읽은 알람 정보'}

    created_time = Column(DateTime, primary_key=True, default=func.now())
    user_email = Column(ForeignKey('user_info.user_email'), nullable=False, comment='아이디(이메일)')
    alarm_index = Column(ForeignKey('alarm_info.alarm_index'), nullable=False, comment='알람 유니크 인덱스')
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
    model_index = Column(Integer, nullable=False, comment='사용된 모델의 유니크 인덱스')
    inference_result = Column(JSON, comment='추론 결과')
    inference_type = Column(String, comment='추론 종류(gocr, kv)')
    inference_start_time = Column(DateTime, nullable=False, default=func.now(), comment='추론 시작 시각')
    inference_end_time = Column(DateTime, comment='추론 완료 시각')
    page_num = Column(Integer, comment='추론한 페이지 페이지')
    page_doc_type = Column(String, comment='페이지의 문서 타입')
    page_width = Column(Integer, comment='이미지 변환 후 가로 크기')
    page_height = Column(Integer, comment='이미지 변환 후 세로 크기')
    is_used = Column(Boolean, comment='사용 여부')

    document = relationship('DocumentInfo')


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
    inspect_status = Column(String, default='대기', comment='검수 상태(대기, 검수 중, 완료)')
    is_used = Column(Boolean, comment='사용 여부')

    user_info = relationship('UserInfo')
    inference = relationship('InferenceInfo')
    
    @typing.no_type_check
    @classmethod
    def get_all(cls, session: Session, **kwargs: Dict[str, Any]) -> Optional[ModelType]:
        query = session.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col.in_(val))
        return query


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


table_class_mapping = dict({
        "vw_if_cd": VWIFCD,
        "vw_if_emp": VWIFEMP,
        "vw_if_org_cur": VWIFORGCUR,
        "alarm_info": AlarmInfo,
        "kei_org_info": KeiOrgInfo,
        "model_info": ModelInfo,
        "permission_info": PermissionInfo,
        "role_info": RoleInfo,
        "task_info": TaskInfo,
        "user_info": UserInfo,
        "class_info": ClassInfo,
        "document_info": DocumentInfo,
        "kei_user_info": KeiUserInfo,
        "role_permission": RolePermission,
        "user_role": UserRole,
        "alarm_read": AlarmRead,
        "inference_info": InferenceInfo,
        "user_alarm": UserAlarm,
        "user_role": UserRole,
        "inspect_info": InspectInfo,
        "visualize_info": VisualizeInfo,
})

def create_db_table() -> None:
    try:
        session = next(db.session())
        Base.metadata.create_all(db._engine)
        
    finally:
        session.close()


def insert_initial_data() -> None:
    try:
        session = next(db.session())
        db_dir="/workspace/app/assets/database/"
        
        for file in settings.FAKE_DATA_XLSX_FILE_LIST:
            if file.get("name") in hydra_cfg.database.insert_initial_filename:
                fake_xlsx_d = io.BytesIO()
                
                with open(db_dir + file.get("name") + ".xlsx", 'rb') as xlfile:
                    fake_xlsx_e = msoffcrypto.OfficeFile(xlfile)
                    fake_xlsx_e.load_key(password=file.get("password"))
                    fake_xlsx_e.decrypt(fake_xlsx_d)
                wb = openpyxl.load_workbook(filename=fake_xlsx_d)
                
                for table_name in wb.get_sheet_names():
                    
                    ws = wb.get_sheet_by_name(table_name)
                    row_cells = list(ws.rows)
                    for row_cell in row_cells[1:]:
                        
                        fake_data = dict()
                        target_table = table_class_mapping.get(table_name.lower())
                        for column, cell in zip(row_cells[0], row_cell):
                            if cell.value is None: continue
                            
                            column_name: str = column.value.lower()
                            cell_value: str = str(cell.value)
                            
                            db_type = getattr(target_table, column_name).type
                            
                            if isinstance(db_type, Boolean):
                                if cell_value[0].upper() == "Y" or cell_value[0].upper() == "T" or cell_value[0] == "1":
                                    cell_value = True
                                else:
                                    cell_value = False
                            
                            fake_data.update(dict({column_name:cell_value}))
                        target_table.create(session, auto_commit=True, **fake_data)
        del fake_data, target_table, ws, wb, fake_xlsx_e, fake_xlsx_d, file
        
    finally:
        session.close()