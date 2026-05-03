-- 华为品牌缺失数据补充SQL脚本
-- 数据库路径: D:\my project\phone-pick-assistant\backend\data\phones.db
-- 执行方式: sqlite3 phones.db < update_huawei.sql

-- ========== Mate 系列 (旗舰商务) ==========
-- 支持50W/80W无线充电, XMAGE影像品牌, 66W/88W/100W有线充电

UPDATE phones SET charging_wireless = 80, image_brand = 'XMAGE', charging_wired = 100, camera_main = 50
WHERE brand = '华为' AND model = 'Mate 70 Pro+' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL OR camera_main IS NULL);

UPDATE phones SET charging_wireless = 80, image_brand = 'XMAGE', charging_wired = 100, camera_main = 50
WHERE brand = '华为' AND model = 'Mate 70 Pro' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL OR camera_main IS NULL);

UPDATE phones SET charging_wireless = 50, image_brand = 'XMAGE', charging_wired = 88, camera_main = 48
WHERE brand = '华为' AND model = 'Mate 60 Pro+' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL OR camera_main IS NULL);

-- ========== Pura 系列 (影像旗舰) ==========
-- 支持80W无线充电, XMAGE影像品牌, 100W有线充电

UPDATE phones SET charging_wireless = 80, image_brand = 'XMAGE', charging_wired = 100, camera_main = 50
WHERE brand = '华为' AND model = 'Pura 70 Ultra' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL OR camera_main IS NULL);

-- ========== P 系列 (旧命名) ==========
-- 支持50W无线充电, XMAGE影像品牌, 88W有线充电

UPDATE phones SET charging_wireless = 50, image_brand = 'XMAGE', charging_wired = 88, camera_main = 48
WHERE brand = '华为' AND model = 'P60 Pro' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL OR camera_main IS NULL);

-- ========== 折叠屏系列 ==========
-- Mate X5: 50W无线充电, XMAGE影像品牌, 66W有线充电

UPDATE phones SET charging_wireless = 50, image_brand = 'XMAGE', charging_wired = 66, camera_main = 50
WHERE brand = '华为' AND model = 'Mate X5' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL OR camera_main IS NULL);

-- Pocket 2: 40W无线充电, XMAGE影像品牌, 66W有线充电

UPDATE phones SET charging_wireless = 40, image_brand = 'XMAGE', charging_wired = 66, camera_main = 50
WHERE brand = '华为' AND model = 'Pocket 2' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL OR camera_main IS NULL);

-- ========== nova 系列 (时尚年轻) ==========
-- 部分支持无线充电, 无影像联名, 66W/100W有线充电

-- nova 12 Ultra: 支持50W无线充电
UPDATE phones SET charging_wireless = 50, image_brand = NULL, charging_wired = 100, camera_main = 50
WHERE brand = '华为' AND model = 'nova 12 Ultra' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL OR camera_main IS NULL);

-- nova 12 Pro: 支持50W无线充电
UPDATE phones SET charging_wireless = 50, image_brand = NULL, charging_wired = 100, camera_main = 50
WHERE brand = '华为' AND model = 'nova 12 Pro' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL OR camera_main IS NULL);

-- nova 12: 不支持无线充电
UPDATE phones SET charging_wireless = 0, image_brand = NULL, charging_wired = 66, camera_main = 50
WHERE brand = '华为' AND model = 'nova 12' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL OR camera_main IS NULL);

-- nova 11 Ultra: 支持50W无线充电
UPDATE phones SET charging_wireless = 50, image_brand = NULL, charging_wired = 100, camera_main = 50
WHERE brand = '华为' AND model = 'nova 11 Ultra' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL OR camera_main IS NULL);

-- nova 11 Pro/11: 不支持无线充电
UPDATE phones SET charging_wireless = 0, image_brand = NULL, charging_wired = 66, camera_main = 50
WHERE brand = '华为' AND model IN ('nova 11 Pro', 'nova 11') AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL OR camera_main IS NULL);

-- ========== 畅享系列 (入门级) ==========
-- 不支持无线充电(标记为0), 无影像联名, 22.5W/40W有线充电

-- 畅享 70 Pro: 40W有线充电
UPDATE phones SET charging_wireless = 0, image_brand = NULL, charging_wired = 40, camera_main = 108
WHERE brand = '华为' AND model = '畅享 70 Pro' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL OR camera_main IS NULL);

-- 畅享 70: 22.5W有线充电
UPDATE phones SET charging_wireless = 0, image_brand = NULL, charging_wired = 22.5, camera_main = 50
WHERE brand = '华为' AND model = '畅享 70' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL OR camera_main IS NULL);

-- 畅享 60 Pro: 40W有线充电
UPDATE phones SET charging_wireless = 0, image_brand = NULL, charging_wired = 40, camera_main = 48
WHERE brand = '华为' AND model = '畅享 60 Pro' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL OR camera_main IS NULL);

-- 畅享 60: 22.5W有线充电
UPDATE phones SET charging_wireless = 0, image_brand = NULL, charging_wired = 22.5, camera_main = 48
WHERE brand = '华为' AND model = '畅享 60' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL OR camera_main IS NULL);

-- 畅享 50 Pro: 40W有线充电
UPDATE phones SET charging_wireless = 0, image_brand = NULL, charging_wired = 40, camera_main = 50
WHERE brand = '华为' AND model = '畅享 50 Pro' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL OR camera_main IS NULL);

-- 畅享 50: 22.5W有线充电
UPDATE phones SET charging_wireless = 0, image_brand = NULL, charging_wired = 22.5, camera_main = 13
WHERE brand = '华为' AND model = '畅享 50' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL OR camera_main IS NULL);

-- ========== 通用规则 (兜底) ==========
-- Mate系列默认: 支持50W无线充电, XMAGE影像品牌, 66W有线充电
UPDATE phones SET charging_wireless = COALESCE(charging_wireless, 50), image_brand = COALESCE(image_brand, 'XMAGE'), charging_wired = COALESCE(charging_wired, 66)
WHERE brand = '华为' AND model LIKE 'Mate%' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL);

-- Pura系列默认: 支持50W无线充电, XMAGE影像品牌, 66W有线充电
UPDATE phones SET charging_wireless = COALESCE(charging_wireless, 50), image_brand = COALESCE(image_brand, 'XMAGE'), charging_wired = COALESCE(charging_wired, 66)
WHERE brand = '华为' AND model LIKE 'Pura%' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL);

-- P系列默认: 支持50W无线充电, XMAGE影像品牌, 66W有线充电
UPDATE phones SET charging_wireless = COALESCE(charging_wireless, 50), image_brand = COALESCE(image_brand, 'XMAGE'), charging_wired = COALESCE(charging_wired, 66)
WHERE brand = '华为' AND model LIKE 'P%' AND model NOT LIKE 'Pura%' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL);

-- nova系列默认: 不支持无线充电, 无影像联名, 66W有线充电
UPDATE phones SET charging_wireless = COALESCE(charging_wireless, 0), image_brand = COALESCE(image_brand, NULL), charging_wired = COALESCE(charging_wired, 66)
WHERE brand = '华为' AND model LIKE 'nova%' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL);

-- 畅享系列默认: 不支持无线充电(标记为0), 无影像联名, 22.5W有线充电
UPDATE phones SET charging_wireless = COALESCE(charging_wireless, 0), image_brand = COALESCE(image_brand, NULL), charging_wired = COALESCE(charging_wired, 22.5)
WHERE brand = '华为' AND model LIKE '畅享%' AND (charging_wireless IS NULL OR image_brand IS NULL OR charging_wired IS NULL);

-- 查看更新结果
SELECT brand, model, charging_wireless, image_brand, charging_wired, camera_main
FROM phones
WHERE brand = '华为';
