"""配置文件 - 存储所有配置信息"""

# 紫鸟登录信息：暂时没用，用的是自动登录
ZINIAO_CONFIG = {
    "company_name": "上海数里看物科技有限公司",
    "phone": "15210519057",
    "password": "Ttianbaodao888",
}

# TEMU登录信息：暂时没用，用的是自动登录
TEMU_CONFIG = {
    "account": "ulh2154@chen-hap.shop",
    "password": "Xiao@12345678",
}

# 紫鸟店铺信息
SHOP_CONFIG = {
    "shop_id": "27561083808008",
    "api_key": "",  # 可选，如果需要API Key可以在这里填写
}

# 浏览器连接配置
BROWSER_CONFIG = {
    "port": None,  # 手动指定端口号，None表示自动扫描
    "exclude":[9222,9223,9224,9225,9226,9227,9228,9229,9230,9231,9232], # 9222,9223,9224,9225,9226,9227,9228,9229,9230
    "auto_scan": True,  # 是否自动扫描端口
    "timeout": 5000,  # CDP连接超时时间（毫秒）
}

# 常见CDP端口列表（用于快速扫描）
COMMON_CDP_PORTS = [
    60511, 60512, 60513, 65472, 65473, 9222, 9223, 9224,
    60000, 60001, 60510, 60514, 60515, 60520, 60521
]

# CDP端口扫描范围
CDP_PORT_RANGES = [
    (60500, 60600),  # 紫鸟最常见端口范围
    (65000, 66000),  # 其他常见范围
    (60000, 61000),  # 扩展范围
    (50000, 51000),  # 备用范围
    (9222, 9300),    # Chrome DevTools 默认范围
]

# 店铺标识符（用于匹配验证）
SHOP_IDENTIFIERS = [
    SHOP_CONFIG["shop_id"],  # 店铺ID
    # 可以添加其他标识符，如店铺名称等
]

# 下载路径配置（精确到国家文件夹,针对数据分析目录）
DOWNLOAD_PATHS = {
    "IT": {
        "traffic": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Trafic_vida\ROA1_IT",
        "sales": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Sales_vida\ROA1_IT_Sales",
        "reports": r"C:\Users\PC\Desktop\code\下单&回填工具\temu订单导入\ROA1_IT",
        "pricing_newproducts_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_IT\低流量",
        "pricing_trafficboost_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_IT\流量受限",
        "pricing_newproducts_pricing": r"C:\Users\PC\Desktop\code\核价\低流量\ROA1_IT",
        "product_list": r"C:\Users\PC\Desktop\code\商品表\ROA1_IT",
        "modify_inventory": r"C:\Users\PC\Desktop\code\修改库存\ROA1_IT",
        "feedback": r"C:\Users\PC\Desktop\code\下单&回填工具\生成回填模板\ROA1_IT",
        "pricing_trafficboost":r"C:\Users\PC\Desktop\code\核价\二次限流\ROA1_IT"
    },
    "DE": {
        "traffic": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Trafic_vida\ROA1_DE",
        "sales": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Sales_vida\ROA1_DE_Sales",
        "reports": r"C:\Users\PC\Desktop\code\下单&回填工具\temu订单导入\ROA1_DE",
        "pricing_newproducts_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_DE\低流量",
        "pricing_trafficboost_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_DE\流量受限",
        "pricing_newproducts_pricing": r"C:\Users\PC\Desktop\code\核价\低流量\ROA1_DE",
        "product_list": r"C:\Users\PC\Desktop\code\商品表\ROA1_DE",
        "modify_inventory": r"C:\Users\PC\Desktop\code\修改库存\ROA1_DE",
        "feedback": r"C:\Users\PC\Desktop\code\下单&回填工具\生成回填模板\ROA1_DE",
        "pricing_trafficboost":r"C:\Users\PC\Desktop\code\核价\二次限流\ROA1_DE"
    },
    "FR": {
        "traffic": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Trafic_vida\ROA1_FR",
        "sales": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Sales_vida\ROA1_FR_Sales",
        "reports": r"C:\Users\PC\Desktop\code\下单&回填工具\temu订单导入\ROA1_FR",
        "pricing_newproducts_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_FR\低流量",
        "pricing_trafficboost_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_FR\流量受限",
        "pricing_newproducts_pricing": r"C:\Users\PC\Desktop\code\核价\低流量\ROA1_FR",
        "product_list": r"C:\Users\PC\Desktop\code\商品表\ROA1_FR",
        "modify_inventory": r"C:\Users\PC\Desktop\code\修改库存\ROA1_FR",
        "feedback": r"C:\Users\PC\Desktop\code\下单&回填工具\生成回填模板\ROA1_FR",
        "pricing_trafficboost":r"C:\Users\PC\Desktop\code\核价\二次限流\ROA1_FR"
    },
    "NL": {
        "traffic": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Trafic_vida\ROA1_NL",
        "sales": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Sales_vida\ROA1_NL_Sales",
        "reports": r"C:\Users\PC\Desktop\code\下单&回填工具\temu订单导入\ROA1_NL",
        "pricing_newproducts_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_NL\低流量",
        "pricing_trafficboost_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_NL\流量受限",
        "pricing_newproducts_pricing": r"C:\Users\PC\Desktop\code\核价\低流量\ROA1_NL",
        "product_list": r"C:\Users\PC\Desktop\code\商品表\ROA1_NL",
        "modify_inventory": r"C:\Users\PC\Desktop\code\修改库存\ROA1_NL",
        "feedback": r"C:\Users\PC\Desktop\code\下单&回填工具\生成回填模板\ROA1_NL",
        "pricing_trafficboost":r"C:\Users\PC\Desktop\code\核价\二次限流\ROA1_NL"
    },
    "PL": {
        "traffic": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Trafic_vida\ROA1_PL",
        "sales": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Sales_vida\ROA1_PL_Sales",
        "reports": r"C:\Users\PC\Desktop\code\下单&回填工具\temu订单导入\ROA1_PL",
        "pricing_newproducts_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_PL\低流量",
        "pricing_trafficboost_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_PL\流量受限",
        "pricing_newproducts_pricing": r"C:\Users\PC\Desktop\code\核价\低流量\ROA1_PL",
        "product_list": r"C:\Users\PC\Desktop\code\商品表\ROA1_PL",
        "modify_inventory": r"C:\Users\PC\Desktop\code\修改库存\ROA1_PL",
        "feedback": r"C:\Users\PC\Desktop\code\下单&回填工具\生成回填模板\ROA1_PL",
        "pricing_trafficboost":r"C:\Users\PC\Desktop\code\核价\二次限流\ROA1_PL"
    },
    "RO": {
        "traffic": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Trafic_vida\ROA1_RO",
        "sales": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Sales_vida\ROA1_RO_Sales",
        "reports": r"C:\Users\PC\Desktop\code\下单&回填工具\temu订单导入\ROA1_RO",
        "pricing_newproducts_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_RO\低流量",
        "pricing_trafficboost_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_RO\流量受限",
        "pricing_newproducts_pricing": r"C:\Users\PC\Desktop\code\核价\低流量\ROA1_RO",
        "product_list": r"C:\Users\PC\Desktop\code\商品表\ROA1_RO",
        "modify_inventory": r"C:\Users\PC\Desktop\code\修改库存\ROA1_RO",
        "feedback": r"C:\Users\PC\Desktop\code\下单&回填工具\生成回填模板\ROA1_RO",
        "pricing_trafficboost":r"C:\Users\PC\Desktop\code\核价\二次限流\ROA1_RO"
    },
    "BE": {
        "traffic": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Trafic_vida\ROA1_BE",
        "sales": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Sales_vida\ROA1_BE_Sales",
        "reports": r"C:\Users\PC\Desktop\code\下单&回填工具\temu订单导入\ROA1_BE",
        "pricing_newproducts_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_BE\低流量",
        "pricing_trafficboost_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_BE\流量受限",
        "pricing_newproducts_pricing": r"C:\Users\PC\Desktop\code\核价\低流量\ROA1_BE",
        "product_list": r"C:\Users\PC\Desktop\code\商品表\ROA1_BE",
        "modify_inventory": r"C:\Users\PC\Desktop\code\修改库存\ROA1_BE",
        "feedback": r"C:\Users\PC\Desktop\code\下单&回填工具\生成回填模板\ROA1_BE",
        "pricing_trafficboost":r"C:\Users\PC\Desktop\code\核价\二次限流\ROA1_BE"
    },
    "AT": {
        "traffic": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Trafic_vida\ROA1_AT",
        "sales": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Sales_vida\ROA1_AT_Sales",
        "reports": r"C:\Users\PC\Desktop\code\下单&回填工具\temu订单导入\ROA1_AT",
        "pricing_newproducts_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_AT\低流量",
        "pricing_trafficboost_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_AT\流量受限",
        "pricing_newproducts_pricing": r"C:\Users\PC\Desktop\code\核价\低流量\ROA1_AT",
        "product_list": r"C:\Users\PC\Desktop\code\商品表\ROA1_AT",
        "modify_inventory": r"C:\Users\PC\Desktop\code\修改库存\ROA1_AT",
        "feedback": r"C:\Users\PC\Desktop\code\下单&回填工具\生成回填模板\ROA1_AT",
        "pricing_trafficboost":r"C:\Users\PC\Desktop\code\核价\二次限流\ROA1_AT"
    },
    "CZ": {
        "traffic": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Trafic_vida\ROA1_CZ",
        "sales": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Sales_vida\ROA1_CZ_Sales",
        "reports": r"C:\Users\PC\Desktop\code\下单&回填工具\temu订单导入\ROA1_CZ",
        "pricing_newproducts_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_CZ\低流量",
        "pricing_trafficboost_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_CZ\流量受限",
        "pricing_newproducts_pricing": r"C:\Users\PC\Desktop\code\核价\低流量\ROA1_CZ",
        "product_list": r"C:\Users\PC\Desktop\code\商品表\ROA1_CZ",
        "modify_inventory": r"C:\Users\PC\Desktop\code\修改库存\ROA1_CZ",
        "feedback": r"C:\Users\PC\Desktop\code\下单&回填工具\生成回填模板\ROA1_CZ",
        "pricing_trafficboost":r"C:\Users\PC\Desktop\code\核价\二次限流\ROA1_CZ"
    },
    "HU": {
        "traffic": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Trafic_vida\ROA1_HU",
        "sales": r"C:\Users\PC\Desktop\Apis\DataAnalysis\Sales_vida\ROA1_HU_Sales",
        "reports": r"C:\Users\PC\Desktop\code\下单&回填工具\temu订单导入\ROA1_HU",
        "pricing_newproducts_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_HU\低流量",
        "pricing_trafficboost_promotion": r"C:\Users\PC\Desktop\code\活动\ROA1_HU\流量受限",
        "pricing_newproducts_pricing": r"C:\Users\PC\Desktop\code\核价\低流量\ROA1_HU",
        "product_list": r"C:\Users\PC\Desktop\code\商品表\ROA1_HU",
        "modify_inventory": r"C:\Users\PC\Desktop\code\修改库存\ROA1_HU",
        "feedback": r"C:\Users\PC\Desktop\code\下单&回填工具\生成回填模板\ROA1_HU",
        "pricing_trafficboost":r"C:\Users\PC\Desktop\code\核价\二次限流\ROA1_HU"
    },
}

# 国家顺序列表（按此顺序循环处理每个国家）
COUNTRY_ORDER = [
    "NL",
    #"IT", 
    "PL",
    "DE",
    "FR",
    "RO",
    "BE", 
    "CZ",
    "AT",
    "HU",
]
# 修改库存的国家列表
MODFIY_INVENTORY = [
    "NL",
    #"IT", 
    "PL",
    "DE",
    "FR",
    "RO",
    "BE", 
    "CZ",
    "AT",
    "HU",
]

# 数据分析国家列表
DATA_ANALYSIS = [
    "NL",
    "PL",
    "DE",
    "FR",
    "RO",
    "BE",
    "CZ",
    "AT",
]