---
name: ecommerce-kv-design
description: 把品牌规范、商品资料、核心卖点、活动价格与时间做成可直接上架的电商商品营销主视觉成图，固定交付中文版 + 英文版两张竖版 4:5 PNG。当用户要做商品主图/主视觉/活动首图/详情页头图、要求突出产品主体与营销主题、要求中英双版商品营销图，或给出商品资料要求"出图"时使用。只做视觉策划、文案规划、商品图精修或详情页长图时不使用。
metadata:
  short-description: 电商商品主视觉：中英双版 4:5 PNG 成图
---

# 电商商品营销主视觉（KV）

把商品资料变成两张能直接上架的成图：**中文版 1 张 + 英文版 1 张**，竖版 4:5，PNG。

工作方式是"画面 + 信息"分层：商品与场景由实拍、抠图或生图底图提供；标题、卖点、参数、价格、活动时间、编号标注全部由 `scripts/build_kv.py` 按 JSON 规格确定性渲染。**不要把中文、价格、日期交给生图模型**——它写不对，而且没法改。

## 交付契约（硬性）

| 项 | 要求 |
| --- | --- |
| 中文版 | `outputs/KV-CN-4x5.png` |
| 英文版 | `outputs/KV-EN-4x5.png` |
| 画布 | 竖版 4:5，默认 1200×1500，最短边 ≥1000px |
| 格式 | PNG（RGB） |
| 双版关系 | 同一底图、同一骨架、同一事实；英文版是本地化重排，不是逐字翻译 |
| 附带 | `outputs/交付说明.md`：受众、单一核心价值、卖点证据、价格与活动时间来源、待确认项 |

## 工作目录（固定约定）

```text
<项目根>/
├─ outputs/                     只放交付物
│  ├─ KV-CN-4x5.png
│  ├─ KV-EN-4x5.png
│  └─ 交付说明.md
└─ work/
   ├─ input/                    用户原始素材（实拍、logo、资质、活动截图）
   ├─ brief/kv-brief.md         结构化 brief
   ├─ spec/kv-cn.json           中文版规格（排版唯一真相源）
   ├─ spec/kv-en.json           英文版规格（同坐标，只换文案）
   ├─ base/                     底图 base-cn.png（中英共用）与可选细节图
   └─ render/                   迭代稿、对比图、report.json
```

改图 = 改 spec 后重渲染，不要直接编辑 PNG。中间产物一律留在 `work/`。

## 七步流程

1. **建档收料**：建目录，把用户素材放 `work/input/`。图片素材先看清楚内容再引用，不靠文件名猜。
2. **写 brief（Gate 1）**：按 `references/workflow-and-brief.md` 的模板产出 `work/brief/kv-brief.md`。缺价格、活动时间、认证、受众这类关键信息时一次性问清；其余按合理假设推进并标"待确认"。
3. **定受众与单一主张**：一句话写清「给谁 / 什么场景 / 解决什么 / 为什么现在买」。主标题只承载 1 个核心价值，支撑卖点 ≤3 条，价格与活动时间单独成层。这一步决定消费者能不能 3 秒看懂价值。
4. **选骨架（Gate 2）**：从 `references/visual-system.md` 的三套骨架里选一套（实景氛围 / 浅底信息 / 大主体），并说明选择理由。用户指定风格时以用户为准。
5. **定底图**：实拍优先；白底实拍就抠图合成；没有实拍就按 `references/photo-base.md` 生图；编辑纸感风用 `scripts/make_paper_base.py` 出纸纹底；编辑场景风用 `scripts/make_scene_base.py` 出呼应色渐变 + 配景；都还没有就用 `scripts/make_placeholder_base.py` 先出布局稿。中英双版共用同一张底图。
6. **写规格并渲染**：把最接近的 `assets/templates/*.json` 复制到 `work/spec/kv-cn.json` 改造，然后用 `scripts/build_kv.py` 渲染。渲染后**必须真的打开成图看**，再决定改 spec 还是收工。
7. **合规与验收（Gate 3）**：跑 `scripts/verify_kv.py`，逐条过 `references/quality-gate.md`，写交付说明。

## 硬性规则

- 文字不进生图提示词；一切文字、价格、日期由 spec 渲染。
- 一个主标题只讲一个价值；卖点 ≤3 条；信息层级 ≤4 级。
- 商品主体高度不低于画面 1/2（场景型建议 56–66%）；场景型默认把商品放在画面右 1/3（中心约 0.70），底部与画布底部留出 1/5 高度作为底部配景带，商品要落在台座上。
- 左右两列文字不得被商品轮廓压住。
- 商品主体不要压在中轴线上：靠左或靠右（约 0.66–0.72 或 0.28–0.34），且略高于视觉中线；文字列放在商品对侧。
- 底部配景带（台面/织物 + 配景）约占图高 1/5；商品底部落在配景带的顶边附近或略下方，读成"摆在上面"。
- 4:5 精确；最短边 ≥1000px；导出 PNG；放大用 `--scale` 重渲染，不拉伸位图。
- 价格、划线价、到手价条件、活动时间、认证、销量、功效：只写用户提供或可核验的事实，其余删除或标待确认（见 `references/compliance-and-claims.md`）。
- 品牌 logo 不拉伸、不重绘、不改色；无 logo 时用字标占位并在交付说明标注。
- 甲方提供内容母本（中英对照表）时，母本每一项都必须完整进入对应语言版本，用 `scripts/check_copy.py` 核对到 0 漏项。
- 英文版不得出现中文字符与全角标点；中文版不留英文占位。
- 中英双版的事实与数值必须完全一致。
- 深色/渐变背景上只用一种强调色；浅色字全走深色区，深色字全走浅色台面区，不跨区混排。
- 重要文字（主标题、价格、活动时间）优先放大；允许被商品挡住一部分，但被遮高度不超过字符高度的 1/4，且不能把一个词或一个字切断到读不出。放大后逐行核对左右两列文字的可见范围。
- 信息小字（产品名、卖点、参数、活动时间）不要用"小字排版"：1200 宽基准下正文 30–34px、标签 24–28px，字重 Bold/Medium；宁可精简文案，也不要把字号压到读不清。
- 行动语（立即选购 / Shop now）是可选图层：用户未要求、或明确要求画面不出现时，删掉文字层与下划线层，右下保持留白。
- 用户要求删减内容母本里的某一项时，不要默默省略：在母本 JSON 的 `waived` 里登记 field 与原因，`check_copy.py` 会把它单列为「豁免」而不是漏项。
- 脚本的 `[warn]` 都要处理，或在交付说明里写明原因。

## 字体

- 中文标题优先思源宋体（Noto Serif SC，可变字重 `variation` 取 `Black`/`Medium`/`Light`）。
- 拉丁标题用 `assets/fonts/PlayfairDisplay-VF.ttf`（Didone 风格高对比衬线，SIL OFL 可商用，授权文本同目录）。
- 例图上的中文大标题通常是商业授权宋体/明朝体，自由字体里最接近的是思源宋体 Heavy；用户指定字体时以用户字体为准，并把文件收进 `assets/fonts/` 保证可复现。
- spec 引用字体：复制到 `work/base/fonts/` 用相对路径，或直接写系统字体绝对路径；文件缺失时脚本告警并回退。

## 脚本用法

```bash
# 渲染（--scale 同步放大坐标与字号，保持文字锐利）
python scripts/build_kv.py --spec work/spec/kv-cn.json --out outputs/KV-CN-4x5.png
python scripts/build_kv.py --spec work/spec/kv-en.json --out outputs/KV-EN-4x5.png --scale 1.5

# 交付校验（比例、尺寸、文案是否真的渲染上去、双版是否成对）
python scripts/verify_kv.py --cn outputs/KV-CN-4x5.png --en outputs/KV-EN-4x5.png \
    --spec-cn work/spec/kv-cn.json --spec-en work/spec/kv-en.json

# 内容母本完整性核对（甲方给了中英母本表时必跑）
python scripts/check_copy.py --master work/brief/content-master.json \
    --spec-cn work/spec/kv-cn.json --spec-en work/spec/kv-en.json

# 编辑纸感风的纸纹底图
python scripts/make_paper_base.py --out work/base/base-cn.png --tone paper

# 编辑场景风的渐变 + 配景底图（与商品配色呼应）
python scripts/make_scene_base.py --out work/base/base-cn.png --palette sage --seed 20261001

# 拿到竖向场景照片时：重构成 4:5 底图，并把台面中心对到商品落点
python scripts/build_scene_from_photo.py --src work/base/scene-photo-src.jpeg \
    --dst work/base/base-cn.png --podium-px 548 --podium-py 878 --px 0.674 --py 0.80

# 商品站在水面/亮面石材上时补倒影（scene-photo-side 模板依赖它）
python scripts/make_reflection.py --src work/base/product-cutout.png \
    --out work/base/product-reflection.png

# 实拍未到位时的 4:5 占位底图
python scripts/make_placeholder_base.py --out work/base/base-cn.png --tone greige
```

脚本只依赖 Pillow；字体自动从系统字体目录解析，可用 `fonts` 字段或 `KV_FONT_DIR` 指定。

## 骨架模板

| 文件 | 骨架 | 适用 |
| --- | --- | --- |
| `assets/templates/scene-atmosphere.json` | 实景氛围型（编号标注 + 底部超大标题） | 家居、家具、灯具、大件 |
| `assets/templates/scene-atmosphere-en.json` | 上者的英文孪生版（同坐标换文案） | 中英成对交付 |
| `assets/templates/info-white.json` | 浅底信息型（参数块 + 芯片 + 细节图） | 玻璃器皿、餐具、小家电、收纳 |
| `assets/templates/hero-subject.json` | 大主体型（斜切色块 + 信息卡 + 大参数） | 母婴、宠物、3C、清洁电器 |
| `assets/templates/editorial-paper.json` | 编辑纸感型（纸纹 + 超大衬线标题 + 铜色细线体系） | 高客单、重调性、要与详情页统一气质 |
| `assets/templates/editorial-paper-en.json` | 上者的英文孪生版（同坐标换文案） | 中英成对交付 |
| `assets/templates/editorial-scene.json` | 编辑场景型（浅调渐变 + 边缘虚化枝叶 + 底部配景带 1/5 + 商品偏侧略高） | 商品颜色明确、要场景感又要调性 |
| `assets/templates/editorial-scene-en.json` | 上者的英文孪生版（同坐标换文案） | 中英成对交付 |
| `assets/templates/scene-photo-side.json` | 摄影场景·侧置主体型（商品右 1/3、底部 1/5 配景带、商品站台座） | 有棚拍静物/水台类底图，要成品级版面 |
| `assets/templates/scene-photo-side-en.json` | 上者的英文孪生版（同坐标换文案） | 中英成对交付 |

示例文案只为演示版式，交付前必须替换为真实商品信息。

## 参考文件路由

| 需要处理 | 读 |
| --- | --- |
| 目录约定、brief 模板、缺口处理、交付说明模板 | `references/workflow-and-brief.md` |
| 选骨架、网格、字号阶梯、色彩、可读性、品牌规范 | `references/visual-system.md` |
| 写或改 spec JSON、图层字段、命令行参数 | `references/spec-schema.md` |
| 底图从哪来、生图提示词结构、占位底图 | `references/photo-base.md` |
| 中英文字数预算、术语对照、本地化写法 | `references/copy-cn-en.md` |
| 极限词、价格与活动表述、类目敏感、平台差异 | `references/compliance-and-claims.md` |
| 交付前逐条验收、常见返工原因 | `references/quality-gate.md` |

## 边界

- 不发布、不上架、不改动用户平台账号；只产出文件与说明。
- 不编造资料；缺关键信息时先问，不猜价格与时间。
- 只做这一张主视觉时不要顺带做详情页长图、Listing 文案、广告投放方案，除非用户要求。
- 平台规则有时效性；涉及当前审核口径时查官方最新来源，查不到就标"未核验"。
