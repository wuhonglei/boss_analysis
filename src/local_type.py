from typing import TypedDict


class JobListQueryParams(TypedDict):
    query: str
    city: str
    page: int


class JobDetailQueryParams(TypedDict):
    securityId: str
    lid: str


class JobListItem(TypedDict):
    brandIndustry: str  # 行业
    brandLogo: str  # 公司logo
    brandName: str  # 公司名称
    brandScaleName: str  # 公司规模
    brandStageName: str  # 公司阶段(天使轮)
    city: int  # 城市id
    cityName: str  # 城市名称
    jobDegree: str  # 学历要求(本科、研究生)
    jobExperience: str  # 经验要求(应届生、1-3年、3-5年、5-10年、10年以上)
    jobLabels: list[str]  # 岗位标签 (["3-5年", "本科"])
    jobName: str  # 岗位名称
    lid: str
    salaryDesc: str  # 薪资范围
    securityId: str
    skills: list[str]  # 技能标签
    welfareList: list[str]  # 福利标签


class ZpDataInJobList(TypedDict):
    jobList: list[JobListItem]


class JobListResponse(TypedDict):
    code: int
    message: str
    zpData: ZpDataInJobList


class JobInfo(TypedDict):
    encryptId: str  # 岗位加密ID
    encryptUserId: str  # 用户加密ID
    invalidStatus: bool  # 是否无效状态
    jobName: str  # 岗位名称
    position: int  # 岗位类型ID
    positionName: str  # 岗位类型名称
    location: int  # 地点ID
    locationName: str  # 地点名称
    experienceName: str  # 经验要求
    degreeName: str  # 学历要求
    jobType: int  # 岗位类型
    proxyJob: int  # 代理岗位标识
    proxyType: int  # 代理类型
    salaryDesc: str  # 薪资描述
    payTypeDesc: str | None  # 薪资类型描述
    postDescription: str  # 岗位描述
    encryptAddressId: str  # 地址加密ID
    address: str  # 工作地址
    longitude: float  # 经度
    latitude: float  # 纬度
    staticMapUrl: str  # 静态地图URL
    pcStaticMapUrl: str  # PC端静态地图URL
    baiduStaticMapUrl: str  # 百度静态地图URL
    baiduPcStaticMapUrl: str  # 百度PC端静态地图URL
    overseasAddressList: list  # 海外地址列表
    overseasInfo: dict | None  # 海外信息
    showSkills: list[str]  # 显示技能
    anonymous: int  # 匿名标识
    jobStatusDesc: str  # 岗位状态描述


class BossInfo(TypedDict):
    name: str  # 招聘者姓名
    title: str  # 招聘者职位
    tiny: str  # 小头像URL
    large: str  # 大头像URL
    activeTimeDesc: str  # 活跃时间描述
    bossOnline: bool  # 是否在线
    brandName: str  # 品牌名称
    bossSource: int  # 招聘者来源
    certificated: bool  # 是否认证
    tagIconUrl: str | None  # 标签图标URL
    avatarStickerUrl: str | None  # 头像贴纸URL


class BrandComInfo(TypedDict):
    encryptBrandId: str  # 品牌加密ID
    brandName: str  # 品牌名称
    logo: str  # 公司logo
    stage: int  # 公司阶段ID
    stageName: str  # 公司阶段名称
    scale: int  # 公司规模ID
    scaleName: str  # 公司规模名称
    industry: int  # 行业ID
    industryName: str  # 行业名称
    introduce: str  # 公司介绍
    labels: list[str]  # 公司标签
    activeTime: int  # 活跃时间戳
    visibleBrandInfo: bool  # 是否可见品牌信息
    focusBrand: bool  # 是否关注品牌
    customerBrandName: str  # 客户品牌名称
    customerBrandStageName: str  # 客户品牌阶段名称


class JobDetailItem(TypedDict):
    pageType: int  # 页面类型
    selfAccess: bool  # 是否自主访问
    securityId: str  # 安全ID
    sessionId: str | None  # 会话ID
    lid: str  # 链接ID
    jobInfo: JobInfo  # 岗位信息
    bossInfo: BossInfo  # 招聘者信息
    brandComInfo: BrandComInfo  # 品牌公司信息


class JobDetailResponse(TypedDict):
    code: int
    message: str
    zpData: JobDetailItem


class UserInput(TypedDict):
    degree: str
    salary: str
    experience: str
