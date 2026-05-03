import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('backend/data/phones.db')
cursor = conn.cursor()

# 处理器映射
processor_map = {
    # 华为
    'HUAWEI Mate 70 Pro(12GB/512GB)': '麒麟9020',
    'HUAWEI Mate 70 Pro+(16GB/512GB)': '麒麟9020',
    'HUAWEI Mate 70(12GB/512GB)': '麒麟9010',
    'HUAWEI Mate 80(12GB/256GB)': '麒麟9020',
    'HUAWEI Pura 70 Pro(12GB/256GB)': '麒麟9010',
    'HUAWEI Pura 70(12GB/1TB)': '麒麟9000S1',
    'HUAWEI Pura X(12GB/256GB)': '麒麟9020',
    'HUAWEI Pura X(12GB/512GB)': '麒麟9020',
    '华为 Pura 90 Pro': '麒麟9030S',
    '华为 Pura 90 Pro Max': '麒麟9030S',
    '华为 Pura X Max': '麒麟9030 Pro',
    '华为 畅享90 Pro Max 128GB': '麒麟8000',
    '华为Mate X5 （12GB/256GB）': '麒麟9000S',
    '华为Pura 80 Pro(12GB/256GB)': '麒麟9020',
    '华为Pura 80 Ultra（16GB/512GB）': '麒麟9020',
    '华为Pura 80(12GB/256GB)': '麒麟9010S',
    '华为Pura 90 Pro Max(16GB/512GB)': '麒麟9030S',
    '华为Pura X Max(16GB/512GB/典藏版)': '麒麟9030 Pro',
    '华为nova 14 Pro（256GB）': '麒麟8020',
    '华为nova 14 Ultra（256GB）': '麒麟8020',
    '华为nova 14（256GB）': '麒麟8000',
    '华为novaFlip': '麒麟8000',
    '华为畅享 70X(128GB)': '麒麟8000A',
    '华为畅享 80（128GB）': '麒麟710A',
    '华为畅享90 Pro Max 128GB': '麒麟8000',
    '魅族Note 16(12GB/256GB)6600mAh超耐久电池，泰坦护盾合金架构，IP65 防水泼溅': '第三代骁龙7s',
    '魅族Note 16(8GB/128GB)6600mAh超耐久电池，泰坦护盾合金架构，IP65 防水泼溅': '紫光展锐T8200',
    '三星Galaxy Z Flip7 FE（8GB/256GB）Al大视野智能外屏，5000万像素超清相机，多模态Galaxy AI': 'Exynos 2500',

    # 联想
    'Moto S50(12GB/256GB)天玑 7300，68W 快充，6.36英寸OLED屏幕': '天玑7300',
    'Moto X70 Air Pro(16GB/512GB)轻薄最强AI影像，双8K AI云台影像，清晰防抖新标准': '骁龙8至尊版',
    'Moto X70 Air(12GB/512GB)超轻薄直屏，多面耐摔，强力抗水': '第四代骁龙7',
    'Moto edge 60 Pro（12GB/512GB）索尼5000万影像系统，悬浮四曲机身，全生态直觉交互': '天玑8350',
    'Moto g100 Pro(12GB/512GB)6720mAh大电池强续航，杜比双扬1.5K高刷超清屏，湿手触控防水防污': '天玑7300',
    'Moto g100 Pro(8GB/256GB)6720mAh大电池强续航，杜比双扬1.5K高刷超清屏，湿手触控防水防污': '天玑7300',
    'Moto g100s(8GB/128GB)千元小钢炮，护眼强续航，多功能NFC': '骁龙6s Gen4',
    'Moto g100s(8GB/256GB)千元小钢炮，护眼强续航，多功能NFC': '骁龙6s Gen4',
    'Moto g54（8GB/128GB）5000万AI影像，5000mAh， 120Hz': '天玑7020',
    'Moto g75(8GB/256GB)护眼大屏，抗冻耐摔，第三代骁龙6': '骁龙6 Gen3',
    'Moto razr 50 Ultra(12GB/512GB)无界AI大屏，潘通色彩定制，新五代星轨转轴': '骁龙8s Gen3',
    'Moto razr 60 12GB+512GB60万次折叠认证，康宁防护，湿手触控': '天玑7400X',
    'Moto razr 60 8GB+256GB60万次折叠认证，康宁防护，湿手触控': '天玑7400X',
    'Moto razr 60 Ultra(16GB/256GB)4英寸大外屏，第六代折叠屏，30W无线充': '骁龙8至尊版',
    'moto S50 Neo(8GB/256GB)潘通色彩定制，应用六开，AI夜景大师': '骁龙6s Gen3',
    '小米 17 Ultra': '骁龙8至尊版',

    # 真我
    '真我15 Pro（12GB+256GB）': '第四代骁龙7',
    '真我15T（8GB+128GB）前后5000万超清拍照，7000mAh泰坦电池，4000nits阳光屏': '天玑6400 Max',
    '真我GT Neo2（8GB/256GB/全网通/5G版）': '骁龙870',
    '真我GT Neo5 150W（8GB/256GB）': '骁龙8+ Gen1',
    '真我GT Neo5 SE（8GB/256GB）': '第二代骁龙7+',
    '真我GT Neo6 SE(8GB/256GB)': '第三代骁龙7+',
    '真我GT 大师探索版（12GB/256GB/全网通/5G版）': '骁龙870',
    '真我GT5 150W （12GB/256GB）': '骁龙8 Gen2',
    '真我GT5 Pro(12GB/256GB)': '骁龙8 Gen3',
    '真我GT7 Pro(12GB/256GB)': '骁龙8至尊版',
    '真我GT8 Pro（12GB/256GB）': '第五代骁龙8至尊版',
    '真我GT8 Pro（12GB/512GB）': '第五代骁龙8至尊版',
    '真我Neo7 SE(8GB/256GB)': '天玑8400-MAX',
    '真我Neo7 Turbo(12GB/256GB)': '天玑9400e',
    '真我Neo7 Turbo(12GB/512GB)': '天玑9400e',

    # 三星
    'ROG 游戏手机6（8GB/128GB）矩阵式液冷散热6.0，165Hz三星电竞屏，2x3Plus肩键': '骁龙8+ Gen1',
    '三星Galaxy A54（8GB/128GB）光学防抖，IP67等级，5000毫安大电池': 'Exynos 1380',
    '三星Galaxy A56(8GB/256GB)5000万像素，5000mAh大电池，7.4mm机身': 'Exynos 1580',
    '三星Galaxy Note 20 Ultra（12GB/256GB/全网通/5G版）S Pen，三星笔记，120Hz自适应屏幕，专业视频拍摄': '骁龙865 Plus',
    '三星Galaxy S20（12GB/128GB/全网通）6400万后置主摄，LPDDR5内存，AI一键多拍': '骁龙865',
    '三星Galaxy S24 Ultra(12GB/256GB)Al智享生活办公，四长焦系统，SPen': '骁龙8 Gen3',
    '三星Galaxy S24(8GB/256GB)装甲铝边框，超视觉引擎，Galaxy AI': '骁龙8 Gen3',
    '三星Galaxy S25 Ultra': '骁龙8至尊版',
    '三星Galaxy Z Flip7（12GB/256GB）多模态Galaxy Al，超大视野智能外屏，5000万超清主摄': 'Exynos 2500',
    '三星Galaxy Z Fold5（12GB/512GB）闭合折叠，轻薄手感，PC般强大生产力': '骁龙8 Gen2',
    '三星Galaxy Z Fold7(12GB/256GB)': '骁龙8至尊版',
    '三星Galaxy Z TriFold（16GB/512GB）多功能大屏幕，Galaxy Al，2亿像素广角摄像头': '骁龙8至尊版',

    # 小米
    'Redmi  Note 14 Pro(8GB/128GB)IP68防尘防水，固态电解质电池，高光护眼屏': '天玑7300-Ultra',
    'Redmi  Note 14(6GB/128GB)': '天玑7025-Ultra',
    'Redmi  Note 15(6GB/128GB)第三代骁龙6，5800mAh大电量，IP66防尘防水': '骁龙6 Gen3',
    'Redmi K70(12GB/256GB)第二代晓龙8，光影猎人，120W充电': '骁龙8 Gen2',
    'Redmi K90 Pro Max(12GB/256GB)': '第五代骁龙8至尊版',
    'Redmi Note 15 Pro+(12GB/256GB)真抗摔，真防水，长续航': '第四代骁龙7s',
    'Redmi Turbo 4 Pro(12GB/256GB)第四代骁龙 8s，双环路3D冰封散热，6.83英寸极窄边大屏': '骁龙8s Gen3',
    'Redmi Turbo 4天玑 8400-Ultra，6550mAh大电池，小米澎湃OS2': '天玑8400-Ultra',
    'Redmi Turbo 5 MAX(12GB/256GB)': '天玑9500s',
    'Redmi（红米）Turbo 4 12GB+512GB天玑 8400-Ultra，6550mAh大电池，小米澎湃OS2': '天玑8400-Ultra',
    '小米MIX FOLD 4(12GB/256GB)': '骁龙8 Gen3',

    # 魅族
    '魅族17 Pro（8GB/128GB/全网通/5G版）6400W专业影像系统，27W无线超充，mSmart 5G，mEngine 3.0': '骁龙865',
    '魅族17（8GB/128GB/全网通/5G版）超线性扬声器，mSmart 5G，mEngine 3.0，全场景影像系统': '骁龙865',
    '魅族20 INFINITY 无界版（12GB/256GB）2.48mm 四等极边，91% 极致屏占,惊艳视觉感官，挑战行业极限': '骁龙8 Gen2',
    '魅族21 Pro(12GB+256GB)Flyme AI，2k+ 单手臻彩屏，mTouch Max 广域超声波指纹识别': '骁龙8 Gen3',
    '魅族21 Pro(16GB+512GB)Flyme AI，2k+ 单手臻彩屏，mTouch Max 广域超声波指纹识别': '骁龙8 Gen3',
    '魅族Lucky 08(12GB/512GB)无界天线系统，星轨科技美学，AI按键': '第二代骁龙7s',
    '魅族Lucky 08(8GB/256GB)无界天线系统，星轨科技美学，AI按键': '第二代骁龙7s',
    '魅族Note 16 (8GB/256GB)超级信号战神，五年持久流畅认证，三防品质认证': '紫光展锐T8200',
    '魅族Note 16 Pro(12GB/512GB)超级信号战神，五年持久流畅认证，三防品质认证': '第三代骁龙7s',
    '魅族Note 16 Pro(16GB/512GB)超级信号战神，五年持久流畅认证，三防品质认证': '第三代骁龙7s',

    # 一加
    '一加13T(12GB/256GB)性能超强小直屏，骁龙 8 至尊版，冰川电池': '骁龙8至尊版',
    '一加13T(12GB/512GB)性能超强小直屏，骁龙 8 至尊版，冰川电池': '骁龙8至尊版',
    '一加15T(12GB/256GB)': '第五代骁龙8至尊版',
    '一加15（12GB/256GB）': '第五代骁龙8至尊版',
    '一加Ace 3 Pro（12GB/256GB）第三代骁龙 8，冰川电池，1.5K东方屏': '骁龙8 Gen3',
    '一加Ace 5 至尊版(12GB/256GB)': '天玑9400+',
    '一加Ace 5(12GB/256GB)第三代骁龙 8，冰川电池，电竞护眼屏': '骁龙8 Gen3',
    '一加Ace 6 至尊版(12GB/256GB)': '天玑9500',

    # vivo
    'iQOO Neo8（12GB/256GB）自研芯片 V1+，120W 超快闪充，VC立体散热系统': '骁龙8+ Gen1',
    'iQOO Neo9(12GB/256GB)第二代骁龙 8，自研电竞芯片 Q1，MX920 索尼大底主摄': '骁龙8 Gen2',
    'iQOO Z11 Turbo(12GB/256GB)': '第五代骁龙8',
    'vivo X300 Ultra(12GB/256GB)': '第五代骁龙8至尊版',
    'vivo Y600 Pro（8GB/256GB）': '天玑7300e',

    # 努比亚
    '努比亚Flip 2(12GB/512GB)5000万后置双摄，全视角悬停摄影，轻薄抗摔': '天玑7300X',
    '努比亚Flip 2(8GB/256GB)5000万后置双摄，全视角悬停摄影，轻薄抗摔': '天玑7300X',
    '努比亚Z50 Ultra（8GB/256GB）真全面屏，第四代屏下摄像，黄金双焦段定制光学': '骁龙8 Gen2',
    '努比亚小牛(6GB/256GB)Neovision泰山AI影像，双玻璃机身，5000mAh大电池': '紫光展锐T760',
    '努比亚红魔8 PRO（8GB/128GB）UDC全面屏4.0，ICE11.0魔冷散热系统，80w快充': '骁龙8 Gen2',

    # ROG
    'ROG 游戏手机9 Pro(16GB/512GB)光显矩阵屏，185Hz高刷，SoC中置架构': '骁龙8至尊版',
    'ROG 游戏手机9 Pro(24GB/1TB)光显矩阵屏，185Hz高刷，SoC中置架构': '骁龙8至尊版',
    'ROG 游戏手机9(12GB/256GB)光显矩阵屏，185Hz高刷，SoC中置架构': '骁龙8至尊版',
    'ROG 游戏手机9(12GB/512GB)光显矩阵屏，185Hz高刷，SoC中置架构': '骁龙8至尊版',

    # 索尼
    '索尼移动Xperia 1 VII（12GB/256GB）': '骁龙8至尊版',
    '索尼移动Xperia 1 VII（16GB/512GB）': '骁龙8至尊版',
    '索尼移动Xperia 5 V(8GB/256GB)': '骁龙8 Gen2',
    '红米note14': '天玑7025-Ultra',

    # 苹果
    'Apple（苹果）iPhone Air 256GB': 'A19 Pro',
    '苹果 iPhone 17': 'A19',
    '苹果 iPhone 17 Pro Max': 'A19 Pro',
    '苹果iPhone 17 Pro Max（256GB）': 'A19 Pro',

    # OPPO
    'OPPO Find X9 Pro(12GB/256GB)': '天玑9500',
    'OPPO Find X9 Ultra(12GB/256GB)': '第五代骁龙8至尊版',
    'OPPO Find X9s Pro(16GB/512GB)': '天玑9500',

    # 荣耀
    '荣耀 500 Pro': '骁龙8至尊版',
}

# 更新数据库
updated = 0
not_found = []

cursor.execute('SELECT id, model FROM phones WHERE processor IS NULL OR processor = ""')
rows = cursor.fetchall()

for id, model in rows:
    if model in processor_map:
        cursor.execute('UPDATE phones SET processor = ? WHERE id = ?', (processor_map[model], id))
        updated += 1
    else:
        not_found.append(model)

conn.commit()

print(f'已更新: {updated}条')
print(f'未匹配: {len(not_found)}条')

if not_found:
    print('\n未匹配的型号:')
    for m in not_found:
        print(f'  {m}')

# 验证
cursor.execute('SELECT COUNT(*) FROM phones WHERE processor IS NOT NULL AND processor != ""')
processor_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM phones')
total = cursor.fetchone()[0]

print(f'\nProcessor完整率: {processor_count}/{total} ({processor_count/total*100:.1f}%)')

conn.close()