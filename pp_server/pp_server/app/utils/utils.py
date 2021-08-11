import pickle
import numpy as np
import cv2
import torch
import re
import os

from os import getcwd
from loguru import logger
from collections import defaultdict
from shapely.geometry import Polygon

from pp_server.app.common.const import get_settings
from pp_server.app.structures.bounding_box import BoxList


settings = get_settings()


def create_boxlist(data):
    logger.debug(data["boxes"])
    texts = convert_recognition_to_text(np.array(data["rec_preds"]))
    logger.debug(texts)
    boxlist = BoxList(np.array(data["boxes"]), np.array(data["img_size"]))
    logger.info(f"texts: {texts}")
    boxlist.add_field("scores", np.array(data["scores"]))
    boxlist.add_field("texts", texts)

    if settings.PP_DEBUGGING:
        with open(f"/workspace/pp_server/assets/basic_cert_boxlist_data.pickle", "wb") as fw:
            pickle.dump(data, fw)
    return boxlist, texts


class AttnLabelConverter(object):
    """Convert between text-label and text-index"""

    def __init__(self, character, max_text_length=25):
        list_token = ["[PAD]", "[BOS]", "[EOS]", "[UNK]"]
        list_character = list(character)
        self.character = list_token + list_character
        self.remove_token_pattern = re.compile("(\[PAD\]|\[BOS\]|\[EOS\])")
        self.dict = defaultdict(lambda: self.character.index("[UNK]"))
        self.dict.update({k: v for v, k in enumerate(self.character)})
        self.max_text_length = max_text_length

    def encode(self, text):
        codes = [self.dict["[BOS]"]] + [self.dict[char] for char in text] + [self.dict["[EOS]"]]
        return torch.tensor(np.array(codes), dtype=torch.long)

    def batch_encode(self, texts=[]):
        max_text_length = self.max_text_length + 2
        batch_text = torch.LongTensor(len(texts), max_text_length).fill_(0)
        for i, text in enumerate(texts):
            batch_text[i][: len(text) + 2] = self.encode(text)
        return batch_text

    def decode(self, label_tensor):
        texts = []
        for label_arr in label_tensor:
            text = "".join([self.character[i] for i in label_arr])
            text = text[: text.find("[EOS]")]
            text = self.remove_token_pattern.sub("", text)
            texts.append(text)
        return texts


PRE_DEFINED_SET = {
    "eng_low": "abcdefghijklmnopqrstuvwxyz",
    "eng_cap": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "digits": "0123456789",
    "circle_numbers": "⓪①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯",
    "basic_symbol": "!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~₩·",
    "symbols_extended": "!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~₩·•●￦",
    "kor": "가각간갇갈갉갊감갑값갓갔강갖갗같갚갛개객갠갤갬갭갯갰갱갸갹갼걀걋걍걔걘걜거걱건걷걸걺검겁것겄겅겆겉겊겋게겐겔겜겝겟겠겡겨격겪견겯결겸겹겻겼경곁계곈곌곕곗고곡곤곧골곪곬곯곰곱곳공곶과곽관괄괆괌괍괏광괘괜괠괩괬괭괴괵괸괼굄굅굇굉교굔굘굡굣구국군굳굴굵굶굻굼굽굿궁궂궈궉권궐궜궝궤궷귀귁귄귈귐귑귓규균귤그극근귿글긁금급긋긍긔기긱긴긷길긺김깁깃깅깆깊까깍깎깐깔깖깜깝깟깠깡깥깨깩깬깰깸깹깻깼깽꺄꺅꺌꺼꺽꺾껀껄껌껍껏껐껑께껙껜껨껫껭껴껸껼꼇꼈꼍꼐꼬꼭꼰꼲꼴꼼꼽꼿꽁꽂꽃꽈꽉꽐꽜꽝꽤꽥꽹꾀꾄꾈꾐꾑꾕꾜꾸꾹꾼꿀꿇꿈꿉꿋꿍꿎꿔꿜꿨꿩꿰꿱꿴꿸뀀뀁뀄뀌뀐뀔뀜뀝뀨끄끅끈끊끌끎끓끔끕끗끙끝끼끽낀낄낌낍낏낑나낙낚난낟날낡낢남납낫났낭낮낯낱낳내낵낸낼냄냅냇냈냉냐냑냔냘냠냥너넉넋넌널넒넓넘넙넛넜넝넣네넥넨넬넴넵넷넸넹녀녁년녈념녑녔녕녘녜녠노녹논놀놂놈놉놋농높놓놔놘놜놨뇌뇐뇔뇜뇝뇟뇨뇩뇬뇰뇹뇻뇽누눅눈눋눌눔눕눗눙눠눴눼뉘뉜뉠뉨뉩뉴뉵뉼늄늅늉느늑는늘늙늚늠늡늣능늦늪늬늰늴니닉닌닐닒님닙닛닝닢다닥닦단닫달닭닮닯닳담답닷닸당닺닻닿대댁댄댈댐댑댓댔댕댜더덕덖던덛덜덞덟덤덥덧덩덫덮데덱덴델뎀뎁뎃뎄뎅뎌뎐뎔뎠뎡뎨뎬도독돈돋돌돎돐돔돕돗동돛돝돠돤돨돼됐되된될됨됩됫됴두둑둔둘둠둡둣둥둬뒀뒈뒝뒤뒨뒬뒵뒷뒹듀듄듈듐듕드득든듣들듦듬듭듯등듸디딕딘딛딜딤딥딧딨딩딪따딱딴딸땀땁땃땄땅땋때땍땐땔땜땝땟땠땡떠떡떤떨떪떫떰떱떳떴떵떻떼떽뗀뗄뗌뗍뗏뗐뗑뗘뗬또똑똔똘똥똬똴뙈뙤뙨뚜뚝뚠뚤뚫뚬뚱뛔뛰뛴뛸뜀뜁뜅뜨뜩뜬뜯뜰뜸뜹뜻띄띈띌띔띕띠띤띨띰띱띳띵라락란랄람랍랏랐랑랒랖랗래랙랜랠램랩랫랬랭랴략랸럇량러럭런럴럼럽럿렀렁렇레렉렌렐렘렙렛렝려력련렬렴렵렷렸령례롄롑롓로록론롤롬롭롯롱롸롼뢍뢨뢰뢴뢸룀룁룃룅료룐룔룝룟룡루룩룬룰룸룹룻룽뤄뤘뤠뤼뤽륀륄륌륏륑류륙륜률륨륩륫륭르륵른를름릅릇릉릊릍릎리릭린릴림립릿링마막만많맏말맑맒맘맙맛망맞맡맣매맥맨맬맴맵맷맸맹맺먀먁먈먕머먹먼멀멂멈멉멋멍멎멓메멕멘멜멤멥멧멨멩며멱면멸몃몄명몇몌모목몫몬몰몲몸몹못몽뫄뫈뫘뫙뫼묀묄묍묏묑묘묜묠묩묫무묵묶문묻물묽묾뭄뭅뭇뭉뭍뭏뭐뭔뭘뭡뭣뭬뮈뮌뮐뮤뮨뮬뮴뮷므믄믈믐믓미믹민믿밀밂밈밉밋밌밍및밑바박밖밗반받발밝밞밟밤밥밧방밭배백밴밸뱀뱁뱃뱄뱅뱉뱌뱍뱐뱝버벅번벋벌벎범법벗벙벚베벡벤벧벨벰벱벳벴벵벼벽변별볍볏볐병볕볘볜보복볶본볼봄봅봇봉봐봔봤봬뵀뵈뵉뵌뵐뵘뵙뵤뵨부북분붇불붉붊붐붑붓붕붙붚붜붤붰붸뷔뷕뷘뷜뷩뷰뷴뷸븀븃븅브븍븐블븜븝븟비빅빈빌빎빔빕빗빙빚빛빠빡빤빨빪빰빱빳빴빵빻빼빽뺀뺄뺌뺍뺏뺐뺑뺘뺙뺨뻐뻑뻔뻗뻘뻠뻣뻤뻥뻬뼁뼈뼉뼘뼙뼛뼜뼝뽀뽁뽄뽈뽐뽑뽕뾔뾰뿅뿌뿍뿐뿔뿜뿟뿡쀼쁑쁘쁜쁠쁨쁩삐삑삔삘삠삡삣삥사삭삯산삳살삵삶삼삽삿샀상샅새색샌샐샘샙샛샜생샤샥샨샬샴샵샷샹섀섄섈섐섕서석섞섟선섣설섦섧섬섭섯섰성섶세섹센셀셈셉셋셌셍셔셕션셜셤셥셧셨셩셰셴셸솅소속솎손솔솖솜솝솟송솥솨솩솬솰솽쇄쇈쇌쇔쇗쇘쇠쇤쇨쇰쇱쇳쇼쇽숀숄숌숍숏숑수숙순숟술숨숩숫숭숯숱숲숴쉈쉐쉑쉔쉘쉠쉥쉬쉭쉰쉴쉼쉽쉿슁슈슉슐슘슛슝스슥슨슬슭슴습슷승시식신싣실싫심십싯싱싶싸싹싻싼쌀쌈쌉쌌쌍쌓쌔쌕쌘쌜쌤쌥쌨쌩썅써썩썬썰썲썸썹썼썽쎄쎈쎌쏀쏘쏙쏜쏟쏠쏢쏨쏩쏭쏴쏵쏸쐈쐐쐤쐬쐰쐴쐼쐽쑈쑤쑥쑨쑬쑴쑵쑹쒀쒔쒜쒸쒼쓩쓰쓱쓴쓸쓺쓿씀씁씌씐씔씜씨씩씬씰씸씹씻씽아악안앉않알앍앎앓암압앗았앙앝앞애액앤앨앰앱앳앴앵야약얀얄얇얌얍얏양얕얗얘얜얠얩어억언얹얻얼얽얾엄업없엇었엉엊엌엎에엑엔엘엠엡엣엥여역엮연열엶엷염엽엾엿였영옅옆옇예옌옐옘옙옛옜오옥온올옭옮옰옳옴옵옷옹옻와왁완왈왐왑왓왔왕왜왝왠왬왯왱외왹왼욀욈욉욋욍요욕욘욜욤욥욧용우욱운울욹욺움웁웃웅워웍원월웜웝웠웡웨웩웬웰웸웹웽위윅윈윌윔윕윗윙유육윤율윰윱윳융윷으윽은을읊음읍읏응읒읓읔읕읖읗의읜읠읨읫이익인일읽읾잃임입잇있잉잊잎자작잔잖잗잘잚잠잡잣잤장잦재잭잰잴잼잽잿쟀쟁쟈쟉쟌쟎쟐쟘쟝쟤쟨쟬저적전절젊점접젓정젖제젝젠젤젬젭젯젱져젼졀졈졉졌졍졔조족존졸졺좀좁좃종좆좇좋좌좍좔좝좟좡좨좼좽죄죈죌죔죕죗죙죠죡죤죵주죽준줄줅줆줌줍줏중줘줬줴쥐쥑쥔쥘쥠쥡쥣쥬쥰쥴쥼즈즉즌즐즘즙즛증지직진짇질짊짐집짓징짖짙짚짜짝짠짢짤짧짬짭짯짰짱째짹짼쨀쨈쨉쨋쨌쨍쨔쨘쨩쩌쩍쩐쩔쩜쩝쩟쩠쩡쩨쩽쪄쪘쪼쪽쫀쫄쫌쫍쫏쫑쫓쫘쫙쫠쫬쫴쬈쬐쬔쬘쬠쬡쭁쭈쭉쭌쭐쭘쭙쭝쭤쭸쭹쮜쮸쯔쯤쯧쯩찌찍찐찔찜찝찡찢찧차착찬찮찰참찹찻찼창찾채책챈챌챔챕챗챘챙챠챤챦챨챰챵처척천철첨첩첫첬청체첵첸첼쳄쳅쳇쳉쳐쳔쳤쳬쳰촁초촉촌촐촘촙촛총촤촨촬촹최쵠쵤쵬쵭쵯쵱쵸춈추축춘출춤춥춧충춰췄췌췐취췬췰췸췹췻췽츄츈츌츔츙츠측츤츨츰츱츳층치칙친칟칠칡침칩칫칭카칵칸칼캄캅캇캉캐캑캔캘캠캡캣캤캥캬캭컁커컥컨컫컬컴컵컷컸컹케켁켄켈켐켑켓켕켜켠켤켬켭켯켰켱켸코콕콘콜콤콥콧콩콰콱콴콸쾀쾅쾌쾡쾨쾰쿄쿠쿡쿤쿨쿰쿱쿳쿵쿼퀀퀄퀑퀘퀭퀴퀵퀸퀼큄큅큇큉큐큔큘큠크큭큰클큼큽킁키킥킨킬킴킵킷킹타탁탄탈탉탐탑탓탔탕태택탠탤탬탭탯탰탱탸턍터턱턴털턺텀텁텃텄텅테텍텐텔템텝텟텡텨텬텼톄톈토톡톤톨톰톱톳통톺톼퇀퇘퇴퇸툇툉툐투툭툰툴툼툽툿퉁퉈퉜퉤튀튁튄튈튐튑튕튜튠튤튬튱트특튼튿틀틂틈틉틋틔틘틜틤틥티틱틴틸팀팁팃팅파팍팎판팔팖팜팝팟팠팡팥패팩팬팰팸팹팻팼팽퍄퍅퍼퍽펀펄펌펍펏펐펑페펙펜펠펨펩펫펭펴편펼폄폅폈평폐폘폡폣포폭폰폴폼폽폿퐁퐈퐝푀푄표푠푤푭푯푸푹푼푿풀풂품풉풋풍풔풩퓌퓐퓔퓜퓟퓨퓬퓰퓸퓻퓽프픈플픔픕픗피픽핀필핌핍핏핑하학한할핥함합핫항해핵핸핼햄햅햇했행햐향허헉헌헐헒험헙헛헝헤헥헨헬헴헵헷헹혀혁현혈혐협혓혔형혜혠혤혭호혹혼홀홅홈홉홋홍홑화확환활홧황홰홱홴횃횅회획횐횔횝횟횡효횬횰횹횻후훅훈훌훑훔훗훙훠훤훨훰훵훼훽휀휄휑휘휙휜휠휨휩휫휭휴휵휸휼흄흇흉흐흑흔흖흗흘흙흠흡흣흥흩희흰흴흼흽힁히힉힌힐힘힙힛힝",
    "kor_jamo": "ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎㄲㄸㅃㅆㅉㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣㅐㅒㅔㅖㅘㅙㅚㅝㅞㅟㅢ",
    "mlt_all": 'فروجنالمشىحطزأقعكضبدُّهت!سيةثئغصظَِذخ ءإْ+:.آ/٠٧٩١٣٦٨٤ؤڤڥ،"ٌ٢ًڨ#ـ-‎٥ڭ٬٫()پFlameGridChcknQut!PsLMBToSHgAqb0173954286UNKéVyDwv-xR\'ôOEIXf.pâ:YÈ+/W™zÉ%èjZJ°à?Ôç,()Âê_ـ$á;#&·"€*£Ê@[]ËŒ<>ÀÇ²ÁÎîœεûÜ‘—¥~\α、“`äößÖüÄ酒店旺潮ʒβŠṠ=δóзŸ₩한국공에디자인아트샵평천연:검은색_작은_정사각형:타로월일라쓰레기는맛있즉석떡볶이전문점료주차장항우종합글벌리더십센터총무과니다정류소나났현위치개Ø만화방오세요원겸색맥딜버까지–매콤작렬또거워건대역관엽円脂肪にも×出庫釣銭切れō月極清水港区南口・長鐸禁煙席三井のリパーク西労災各種健康保険取扱いダイコ蕾均一全品最大《》ùÃìÙúÌòˉ’члфÒ”●ĀШÑকুন্তল মঙগবারحلاãᄋū分|新年音乐会梦之声学院ɑΦƹ۸मुळार्ग스픠강남신사담배프콘택렌즈도미দিহোওপথস~&-:+®./,%@٬!،"?$*)(€<>\'¥。—=#•§·∣:검은색_작은_정사각형:×₩※♬・|▁[]ঃ।_‌\协辛庄通县节能技术推广站民事刑法律咨询。泛华金融服务集团易酷网吧运河邮政支局本地区编码中国老天津卫炸酱面逸林宣东花园岷江桥学校域馨雅幼稚农业银行北京双舟台球俱乐部康医门诊注意安全十字路口新城文化大厦宝岛眼镜海男·不要让我们的孩子只在博物馆里才见到今动榆树甲猫超市乎每件生活小一盒青山绿水夏仁者智心图说价值观友善诚信敬爱治公正平等自由和谐明主富强浙义乌吉作教建成社会深改革依从严党勤劳万如第四季神探洛克黄员同步英这世界很秘店添特色份菜盘鸡焖鱼头()酸汤肥牛36元82麻辣锅香素什锦更品,升级味欢迎尝!助点餐排队抢红包米粒粥铺扫随机立减最高免单禁止停车百苑请出示证汽堂号提醒魏村人数:4需桌货厢式发布空气重污染橙预警0日至1月I放标准、筑垃圾渣土砂石输辆上驶做好健防护吸烟专97利电马灌溉环保内宠入除年残疾儿童使用手摇轮椅外其他未经允许得进泰伟滨限.绕共有家商灯釜阳制造科鲁奖质荣获去油曲霉掌握核交管理像采租纳税寿寺族西泉三厂洼苏州街长春优选少命育基责任于消应急设备汇贤楼辅五温库周边燃炮竹钻仪铁展览丁酉肖暨雉开蓝创断铝窗塑钢锈话5光房盗彩结构肯德蔬果企愿景为可赖连锁牌顾客供与卡;游费待时按求刷前已申换但因各种殊原尚领道思位院二零六淀源闸及龙王庙府九七非谢绝参榭船箫声醉紫宫洗间危险勿靠近冰薄滑野洪闲拒“低”打认轻钮考名众届弘扬旅宜兴驰白陈云夫著营养若木然之联合圈际饮组织范矿加工过曾题词甘南湖音喷圣指定疗窝沟封闭龋齿项目牙办关场购您语洋笼回转火典赛司仙踪期福而森格淇淋乡俗户评委颁美容招募欧莎瑞丝所址旁千鹤丽热线惠继续室溪登身此谷峡忘忧宁静致远以后昏赶玉渡风叉-瀑佛返岔计约~个救援报告并候独具匠艺传统精鲜甜软糯丰皆纯食爨产豆蜂蜜料烈庆祝度处衡代曹杨驿岸洲古虹泾淞清湾酒灾梯圖請邊門窺視孔看楚訪開你處措施須知置間了钩窥视發現或濃煙時即照往遇電樓下松拥秋盈越想象装型羽绒背暖茄玛纤体变功就是女始直将幕斗園验¥先射频瘦脸详情梦层满概念靡烘培简衣络旗舰灭器箱烫伤冷临厅实承程征方向便讯飞研究测算厚奇虎—士挡聘笔试《沙拍》剧影映胶片无持票礼秩序栏常识瘾也息被褥起般扑盛盆焰泼把接烧附湿降类着切再干粉触爆张贴覆盖否则违反拨引赏鞭玩星跑确脱浸来滚熄快脚踩暂言践围鞋洁灰桶久给问攀半径寓太净航销售國際舱济别墅尊听蘭郡m拼阻塞岗检查调宾桂送拉凤祥没?跳墙媒却她睡武昌达汉导嘉当坑洞必须戴帽纵横赢模珞珈省军昆仑斯分派紧休座财首艇资浮俏现带業系跆拳折何死眠堵占珍貝禾吃慧移签启媛碰走钟塔庵训足订旺角疆厉击举害黑坊挥量监督刻章避佑宿舍械群苹學复印留取论真描条幅录泳\胜/叠翠亭阁結萬眾缘書两侧赁佳讲解怀柔螺紅殿寶雄阿弥陀左菩萨右势壁画诸祖师罗離諸熱惱恒涼岁陪勒悬崖跨坐盼望棵宴飲伴收次啟題投诉八对难震纬°C力付款多诺亚修卖妆皙鹿港镇丹棱廊卷帘焙榛巧尽享浓郁滋配饰%纺羊毛潮茶午套吞冻煎+饺吴拎住甩饭澡介妥己私冠整眉坡夜淡材谨挪相寧館麒麟献滿漢席鬼斧碑鸟纹耕荔枝互幻朋固态圆距柜流尺寸厘斤忠董嘴鼓川皇李俊永檐板砖砌漫纽绘陶盂郝志历书藏戏沃句纪瞬递鑫詹#压缆锐繁记煌鍋汁郊初晴桃样波维落顺欣尔控杂性析感综端亦卓捐赠妇益鸣都陆键陡峭炉峰岫索碧蒙倡植补充喝芙蓉隔乘吊睦撞闻烦恼妖孽均鐘响斋雕细珠串匾煤杉粗榧途属栈阶倚擦剪鸿药币速昊居档庭烤漆镁钛磨夹玻璃弯焊氩弧蓬荆受携棚摆罩扳泡亮膜稻枫叶露御草显抱碳惺摄畅极坠爬犬韩栓菲贵央玄威汀规划曝罚菱莲荷厕摘唐喜悦轩幔塘鲍朱歌几壹渔末班迈皋奥延虑表巷隧廖兰玖玥咖啡棋茗豪宅檔写拜ο缝栋错失帮宽侯祠槟余跃枉奋芯批借尾倍厨熙怡麦亨邻鹰澜扶屋顶雨誉诞朦胧诗墓铭卑鄙睛它寻找孕昨答舒婷蕨杜甫員遗茅故窄滞池銀會議舫玫瑰胡存贺察案隆召踏樟芳形习乔皮褐卵微较耐寒底遭突况莫無脑達嶺馥幸拔沁脾沐浴棍陵長杏氟疏俄>隅帆匡兄弟姊妹哈慢翻恭齐段瓶密耀鄂战略卧透巢朔泵堆迹么腾娱鲨毕翔搬钱醜裕優令鼎椒龍刀削匹普总早晚勘沪杭讨莅臻丘赐車冀史憨又晋僧講經臺為陽篆鐫係纉宗剑摩岩拙喇叭喧哗境疯侨饼假争杀根缩垂钓柱押拿钥匙莓瓜职访姐肉抓吐搭载雪荏苒刘阅夷岳君笑榜良赵護興勇雷涂宏勋兵佰郭迪孝符秀孟梅蒋束离涵适筹股议锡忍冬琼荚蒾蔷薇砧禅嚴莊官檬播执损坏滦巴脏病慎误砍柴读完偶卯悠涓涌澈冽润宋汴绪粮抗毁麓泊兔奔晓旭傅寨苗朗祜演婚谁魔剂弹状贯彻审谊遠燥架涪朝谈扩姚邦鹏乙烯別跟扁灣唱團冲屁啥挂倒奶鸦权宇赦袍巾铃弱田陷逼【辫】爸还驾拘判娘爷窃终贼乱丢蛟仗泽艳吗偷祸患溢血且瘫劫犯罪予毙炬励仓潍盾奠涡增迁韵湘兆硕链陕孵破硝囚圳希遵守媳拆妈徐债券坛些眺籍纱奎巡梨→凯硬戰揮區蒸徑夭種澳扣欠旧嶽惟於壇納亐馬陳列個哪刹蘑菇买异毅襄尼捌祭姓綦伐軍醫伙廉努述汕炖炒鸭柏涧粱赤锋剩邱积辖彰險隨磁仍胁坎碗號藍輝似錦侦拐筋效障兹坦释潜巨块炭挑竞激芝盟耻牢洱桷螃蟹鳝井骨裁瑶赴瓦履苍戒那侵腐壮稳郑辉觀雲勑据杰嵩仞東靖芦伊铣刨铸锻琴舞誓葛坝狮沿追迫觉抵恶劣策辰愉灏抽睿侠妙玲奕逻辑恐聚閣酿浦贸辽够比例辞琏晟坚懈怠訴話運輸閩荥母嫁胀桦甸樂秦徽岭授衔紀〇椴梁妍账操浩攻归决额仅哦燕緒拾陸貳欽彤華隸縣昂差兼散灵喀凌荐摊稀擎凭頭頂埔男女ハワイコナ海洋深層水日本蕓うちない園営業中セビヨク橋地下鉄1.4号線豚骨ラ一メン味噌ーともすみフをかやよレノじキくサえに青春つひがあ払ばニ二ろグでリ友福順都家美月(どんぶ漢城大入口스팀めぐズム酒路お心排肉五色燦宴無風02-8375火名ジットカドご利用ただけま。使る場合、の部分插してさ現金併必ず先れル飛弾銭箱牛銘柄失進協議会長話題店食ベロスマ原区木丁目央室町ゃ静岡県庁시즈오카현청ょ市役所駿府公げ新駅バタミ站北条東南西~曜土祝最料当時円基千万札き駐車券紛は注意社規定方法ゲ開曲り磁気携帯電・ネ)近づ庫出来切責任負せブ際緊急連絡間係員対応不明点こら株式暖房能力年在寒冷仕様霧ヶ峰ね!小江戸豆蔵ヒ珈ホ琲エアツ品ポデ山鼻動物病院朝夜ダ客へ願流元祖尊煎餅む堅焼束袋柿種王子巻白雪ゆ京角枚亀氏鮎寿司内九七築四〇テ島麺屋潤焚居伊勢丸疋製造直売SINCEヤ代々調剤薬局手惣菜弁松商パプ折チェ約kg:ウ/ュ税9満ざ極問わ立幌通番移迷惑,頂後繰返平適精算板っ確認上踏越止位置数自的昇装着遠慮事故及び盗難領収書発行枠違解除同乗者致警備ショ関給田境ぎ野緑郎僕説良ほ詰思河仁布丘ガ樽産道各ソ伸芉〔ゴ〕滅可矢印面向挿铁鐵條銀座芝浦川第浜6onratulis理容豊館天文台ぼ&ィ井取消表示額要押ケVA投割引前ボ証策済却看読以ゼ申込由受釣回創治三十髙喜化粧処国米沖縄久残波瑞泉恵佐之生オ請ふ百穂古升石敢當花黒そ標登録鹿児高軽相談世両医療人団歯科禁煙喫管菱機練馬建港曽御垚有限送承持帰専門濡扱飲放¥予詳烏魚刺身鳥特串休抜鮮湯度八清務务尻学校「JR馆旭冈东勤劳祉崎仲现情報ザ产业报场舎厅舍巴歳親神正笑華源閣村民郷総研煮観光案p荷体作戦葵半熟覇茶買求召編成弱ぺ貸付BHyh吉住綱ギャ許垣次富士岸滑閉週共吸臭抗菌ユ指教習盛席呂遺跡mec興津草薙幹·阪横待候车牧香配硬過防ピ鷹冬期季節栄養準粒卜ヅぇ貞殿曙保幡施設得宇空器少量危険記念別奉ぉ徐般障桥稻段差武停秋葉宿降視昼每毎【左加夕為》免項ぅァ洗劑頑固汚落モ琴似署張健図屯兵支營氣輪繁鶏鍋运剛庭画質技術締断ぞ費尚等託TL超低燃瞬融槽筋耐FX蓄熱賃計工】音楽演購ヵぃ※伝款守全效活常募集括経削減替才船芦游步靖歌舞伎側笹浪克博律昭和六狩貨蘭安委交賠労災圓總宮ペ潔穴織封旬頃試供嫌脱厚丈夫油重M凖刻反U簡単」短OK材×群髪堂験版刷槳滴糀甘蔦多老舗換外侵考未微状去害べ格畳密%値贈倉衣類虫効個他果P隅早広構比型栗皮賞州床完映谷炎炭援陸衛隊徳帝附属政転雨散栓紙販藤沼初鮨好巣始吃具統椎茸缶ぱ康維疫例膚被毛糖揚饅頭午改剪票旅咨询处拔佳肴幸县骏园ぷ診捨形契騒周見罰太羽較界察閏街彩展企厳選素寧墨ォ啓紡競争盟首圏星薄迫寅乃虎育終犬慶牡池腹鞄魂丹尿衡飴制延菓輔塚庄岩瀬旧祭浅循環乙歩柔整復捻挫傷達了ヴ旦汀宝階紺呉服晩酌俊林筏洲倶激旨膳課臼挽粉価途灸炙握貫碗蒸汁于穀細義職[圈]玉杉更幕關畿沢哉荔+臣森茂樹増検塗禄里誠矯貯簿速枝末修運輸優暗臨感包D照抑再煌輝柳仙命歓迎患窓渋氷宅添絨毯声接聞想寄努猛右今信遊蒲暮葛便‘犯即庵忘办桜幾胡螢鴉鴨斜輌廃棄賢志摩陰陽阿|畑筒刑郵存ぽ究赤礼雄組随ヌ<>麗"“?告足態ぬ因載酔梅変択希望ぁゾ非省主ヱ尾嘉実綜渡辺若知遣濯乾燥幅奥温泡浄液含英圧弐稿盤楕錦系続炉巨震複起歪拡償介護槍ヲ納芋尽蜜飯泊d媒列普測象結濃囲°扉埠湾搭械●異顔寺蕎麦塾根寸匠監拘私徴罪真酸―凍操秒《兒況亭ヮヘ又勝性賑快軒櫓扇舟皆宵溝黑夏審辻〈〉隣邮乐绀吴间砂祥沿冠团#样奈藏芳賀别幼稚慈惠楊需鍼时婦寢劵倍惗率脂肪助酵働查副术燒歡亍綠內乘字鋪經濟靜刊龍慣継講憶腦強扎評W触飬约压追愉长厦梦幻广罔妆鄉传马弘嗣級翌灯妝厕堤崗莓蝶塩專姓转迴轉壽傾打險產卒催均價君樣李菀雜眼镜體驗欢临鏡永邊咲紀智區樂讀俱藥卷带充电菸颜緒學佶決稅隆滕胜湿洪掘補强嵩縱縦架並岳忠张戶絵橫龜數財染症励珍斎師壱探頼礎坊侍箇誓嘘偽秘苦唸忍鵡逗喰鎌至逸丼写肌易裁判ぴ观绍问简誌芸邦球唐國荻潅干甲範聴楼ゅ損疲肩腰痛揮拾葦梓像採晶離视员晃圭圃冥庶昌己鋳鹰栽┙樫皿模査鑑件振ゎ贋拍耳咽喉裹朋碑資芥死剖拳`息漫壮墓┑鰭愛貴紳裳官孝宫導竣郊困誰何言盲呼釜竹童舘鉾觀埼獣走丫烟勾遅幣ゐ坂揉调与额鐸諸祈祷禅稲宣昧圆汽终景糸益v퍼팩트손세자장찾이감사합니다26서180뉴스유신원룸임대빌라주차금지단기및전가능방분리/베란(인직점)판매.쌀,현래먹온천름떡아간동부성수4조페커피크림맛!더위닝복음종로한국예심치료연구소:개도곤난곡蘭谷겨울에는무낙태껌탕견역칼덱안내실콘올링타듭킬모문붙머중정공민엉환어론께결하엣터뚜르드카날낀생틱오눈을生즉석군권그미핫팡클돼고향영상프루팁앙봐믈관님의침묵속물범경택파채호체격년노편홀5FSoundZer3OPEN9CL학총남교롯데나마일초콜럿입외반쓰레류재활용품필명갤러비제곳월컵봉화산잠시청충몽를버맙핑싸애람?술펀흔돈과훼죽보곽여두변빈묶희집강백悲剧테토틸싯진싱잔면디믹쥬얼욕브즈엔솔려평육창작만은행북발알망져요있통증승송막걸7-게린말골뱅김흥띰듬녹해믿풍선야닭갈운포근젠틀힌옥철건설습꿍옛본떼최폴짜늘우양념거엿광당표빙킨큰짐저므벽할hpa팜팝추함답털삭깊바층微信扫一导航优惠海购仅限首单每最多输入金额使用直减韩元暖游와코햐夏威夷科纳洋深层水맥식순불힉많까꺼으휴"갑회덮밥됩력등록번:검은색_작은_정사각형:축담출취샾궁허익억처든빨겠십렁텔KDIAUvlT염몬틴극잡꼭황색탑왔약첫때했잖엄네[]텍렌찬떻각샤죄촬넛배달웅냉히솥누룽농업메션밴널팀언센험겁힐열찻절흡병첩높폰탁탄된찌뒤헌후씨었던憲宗딸在清慶嬪顺和宫싫쉴딩젤긴급법율투악협목립되홈캠써ᄋ놓폭응락섭뿍참샴푸먼헤롤따끈납숙계규별봄맞벤짱슈왕롱너검팅쇄켜빔훙ftkb볶런랑훈련ᄒ눔빛X딘RM삼밀잉샌친ᅳ좌·JHG않적캅길꼬턱BsiY뷔믜티%량밎액켓템~엘픈박암패것키왼흐쉐묘빠힘족케랜샵쪽책똥m압톡흉블랙톤띠첼_쿨렐셀핌슨밌효룡캡슐웃셰ᅵ몸살형접훤램척닐쉬균콩붂앗륜착탐첨객움벼룩넷맟융새른믑돔뜨슴닫릴숨퓨헙풀팔또뎀혜혀들땐팬씀값째델캔항뮤측닷컴V긋굴챠쇠ᄑ幼稚園끄럼웨턴W쿠획찰독쇼폼겡줄깨앞깐돌쌩칭졸준혁엽꿈꾸릇앨츠멀큼흑컨완끗녋랍득핏셜플옆닮젊틈딨냐쾌뾰닥느끼굉벌킴\'깅없즐챗₩쿄콤랫눌귀죠“”춘특‘’논<>칠팥营业中롭윤샛겐워낸넣벨옷픗텐펫솜퀴릭햄글빵웰밤떳꼇꽃곰곱삿펴홰팟옹혈탱캐닉뗙릿=멘짬뽕픔쟁령얻숩ᄃ앰촉낮킹돟헨켈엳튀뛰챌뎅딱숭ᅡᄊ튼깔끔듀튬핸받앱쉅눠랄앤셕셔릅썸빚덧꽉홍룬딜쏟쳤팍돠좋뱃몁쉽얹쫄깃뤼뢰俊혼횹낭킁슬슽겉며켸잘젿갚멤멜몰엠럽떠몇탈쁜븥못뇌륵웹툰질걷컬y줘싼둥튝젹wc눙멕핃헐맨같샘덩`퇘듯홉샐삐륶넹픚폐뼈쿤숯겹쑤뗜뮈젬ᅥᄂ뱍ᅧ찲웍될둠닌덕렉즤녁섿텨숴몫※&쪼멋+멍뜻日本●|즌受理밝넥大꽁*빗윈롬ᄏ큐넘옵짝릉삽쉿끓쩝랩잭슼ᄉg륙븐#콕딛겅턺잊힝컘엇옴껏넨븍텀켭뿜굽볼숲돱쁘읽휘징겸씌렇꾜칙뽑붓满意改善了딥护分弹性×핀흰잇칸新찔깡헬줌댄찐빅駐車料のお支払い홋フ・쵸丹魂反越먀켄왜덴•「」쯕궈小쟝뻥푼멩넓렬턔욘ᄁ읍꼼쭈먜곁꿀욱괴펄젼졈싀탠맘났뒷멸녕횡쟘붐썹섕륨윌ᄅ밧팻춤츨걔슥셨존았뿐킈댸먯픠갱톨깋텝였뜰뮌붕셩팸쏙বাড়ীতেহইচসগুনমলরফ্ণিকশপঞজট২৫৪১-৮অযদএখূওছথউোৌভ.,ষ০য়।ঘ৭৩ঠঙ৯\'ৎংধ/ঐ৬আ()‌ৃঃড়37 ঁঝ:TM"ঔ`~*ঋৈ%905142HP6AUSINRY!?ঢঈ8৷CLৄganEODगतिरोधकपुढेआहज्ञानफटसडीओलॉवळदबंम-१शँथइठयणैईचछभ.खौड़अऊषू()ःृ\',‌10झएऋॅ२८४घऑउ५‍३०६ॐ:औ७"ढ़/ऐFamilyResturn९!|GNO',
}


def build_label_converter(max_text_length=25):
    characters = ""
    # character_sets = model_cfg.character.sets
    character_sets = ["digits", "eng_cap", "eng_low", "basic_symbol", "kor", "kor_jamo"]
    base_dir = getcwd()
    for chracter_set in character_sets:
        if chracter_set in PRE_DEFINED_SET:
            characters += PRE_DEFINED_SET[chracter_set]
            continue
        chracter_set_path = os.path.join(base_dir, chracter_set)
        if os.path.isfile(chracter_set_path):
            with open(chracter_set_path, mode="r", encoding="utf-8") as f:
                _chars = f.readlines()
                characters += "".join(_chars).replace("\n", "")
        else:
            raise ValueError
    return AttnLabelConverter(characters, max_text_length)


# characters = ELabelCatalog.get(
#     ("digits", "eng_cap", "eng_low", "basic_symbol", "kor_2350", "kor_jamo"),
#     decipher=settings.DECIPHER,
# )


converter = build_label_converter()


def convert_recognition_to_text(rec_preds):
    texts = converter.decode(rec_preds)
    return texts


def mask_to_quadrangle(mask, mask_convex_hull=False, force_rect=False, allow_polygon=False):
    assert isinstance(mask, torch.Tensor)
    assert mask.ndimension() == 2
    assert mask.dtype == torch.bool
    mask = mask.numpy().astype(np.uint8)

    contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # TODO: handle this
    # assert len(contours) > 0
    if len(contours) == 0:
        return np.zeros((4, 2), dtype=np.int32)

    if not mask_convex_hull:
        areas = np.array([cv2.contourArea(cnt) for cnt in contours])
        idx_max_area = np.argsort(areas)[-1]
        contour = contours[idx_max_area]
    else:
        contour = np.concatenate(contours, 0)
        contour = cv2.convexHull(contour, False)
        mask = cv2.fillConvexPoly(np.zeros(mask.shape), contour, 1)
        mask = np.uint8(mask)

    if force_rect:
        marect = cv2.minAreaRect(contour)
        quad = cv2.boxPoints(marect)
        return np.int32(quad)

    epsilon = 0.02 * cv2.arcLength(contour, True)
    eps_min = 0.0
    eps_max = epsilon
    eps = (eps_max + eps_min) / 2

    # find upperbound
    approx = cv2.approxPolyDP(contour, eps, True)
    cnt = 0

    if allow_polygon:
        return approx.squeeze(1)

    while len(approx) < 4 and cnt < 10:
        eps_max = (eps_max - eps_min) * 2 + eps_max
        eps_min = eps
        eps = (eps_max + eps_min) / 2
        approx = cv2.approxPolyDP(contour, eps, True)
        cnt += 1

    # find possible quadrangle approximation
    if len(approx) != 4:
        for j in range(10):
            approx = cv2.approxPolyDP(contour, eps, True)
            if len(approx) == 4:
                break
            if len(approx) < 4:  # reduce eps
                eps_max = eps
            else:  # increase eps
                eps_min = eps
            eps = (eps_max + eps_min) / 2

    # get rotatedRect
    marect = cv2.minAreaRect(contour)
    marect = cv2.boxPoints(marect)

    approx = np.squeeze(approx)
    contour = np.squeeze(contour)

    if len(approx) != 4:
        quad = marect
    else:
        poly_marect = Polygon([(x, y) for x, y in zip(marect[:, 0], marect[:, 1])])
        poly_approx = Polygon([(x, y) for x, y in zip(approx[:, 0], approx[:, 1])])
        poly_contour = Polygon([(x, y) for x, y in zip(contour[:, 0], contour[:, 1])])

        if not poly_marect.is_valid or not poly_approx.is_valid or not poly_contour.is_valid:
            quad = marect
        else:
            inter_marect = poly_marect.intersection(poly_contour).area
            inter_approx = poly_approx.intersection(poly_contour).area
            union_marect = poly_marect.union(poly_contour).area
            union_approx = poly_approx.union(poly_contour).area

            iou_marect = inter_marect / union_marect
            iou_approx = inter_approx / union_approx
            if iou_marect > iou_approx:
                quad = marect
            else:
                quad = np.squeeze(approx)

    return np.int32(quad)
