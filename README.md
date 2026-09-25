# 骰池精确概率（Svelte + Flask + Docker Compose）

桌面骰池的**精确**概率计算器：不做蒙特卡洛模拟，全部概率以约分分数返回，
低概率尾部每次计算都完全相同、可复算。

## 规则

输入：原骰数 `n`（1~6）、面数 `faces`（2~8）、保留颗数 `keep`（1~n）、
重掷面集合 `reroll`、阈值 `threshold`。每颗骰独立结算：

1. 先掷一次（1..faces 均匀）；
2. 命中重掷面集合则**恰好重掷一次**，以第二次结果为准（不再重掷）；
3. 最终面为最大面 `faces` 时，追加掷一颗附加骰并相加；
   附加骰不再重掷、也不再触发追加；
4. 全部骰子结算后，从 `n` 个总点数中**保留最高的 `keep` 颗求和**。

服务返回每个总分的精确概率（约分分数）、期望、以及 `P(总分 ≥ threshold)`；
所有概率之和恒为 1（响应中 `total_probability` 固定为 `"1/1"`）。

## 架构

```
浏览器 ──HTTP──> ui 容器（nginx：静态页面 + /api 反代）──HTTP──> odds 容器（Flask/gunicorn）
```

- `odds/`：Flask 服务。`dice.py` 用 `fractions.Fraction` 精确计算
  （单骰分布 → 多重集枚举 + 多项式系数 → 最高 K 颗求和的分布）。
- `ui/`：Svelte 单页应用，编辑规则并绘制概率柱图（柱上标注约分分数，
  ≥ 阈值的柱子高亮），附原始 JSON 响应面板。

## 运行（Docker Compose）

```bash
docker compose up --build
# 打开 http://localhost:8080
# odds 服务直接暴露在 http://localhost:5000
```

## API

`POST /api/distribution`

```json
{ "n": 3, "faces": 6, "keep": 2, "reroll": [1], "threshold": 12 }
```

响应（节选）：

```json
{
  "params": { "n": 3, "faces": 6, "keep": 2, "reroll": [1], "threshold": 12 },
  "distribution": [
    { "total": 2, "num": "1", "den": "46656", "decimal": 2.143347050754458e-05 }
  ],
  "expectation": { "num": "12454385", "den": "1119744", "decimal": 11.1225… },
  "at_least": { "threshold": 12, "num": "9779", "den": "23328", "decimal": 0.4191… },
  "total_probability": "1/1"
}
```

`num`/`den` 为最简分数的分子/分母；`decimal` 仅供绘图参考。
参数非法时返回 400 与错误信息。`GET /health` 用于健康检查。

## 测试

### 精确性对拍（pytest）

`odds/tests/test_dice.py` 用**独立实现的暴力枚举**（逐路径展开
首掷 × 重掷 × 附加骰，再枚举 n 颗骰的全部结果元组）与生产算法对拍：

- 单骰：面数 2~8 × 重掷面全部子集；
- 骰池：面数 2~4 × n 1~4 × keep 1~n × 重掷面全部子集；
- 期望、尾部概率、分数已约分、概率和为 1。

```bash
cd odds
pip install -r requirements.txt pytest
python -m pytest tests/ -q
```

### 浏览器主流程（Playwright）

`ui/e2e/chart.spec.js`：编辑规则 → 点击计算 → 核对每根柱子的分数标签
与页面上的原始 JSON 响应一致，并与直接调用 API 的响应一致（三方一致）。

```bash
cd ui
npm install
npm run build && npx vite preview &      # 本地联调（默认 baseURL :4173）
npx playwright install chromium
npx playwright test
# 或对 Docker Compose 起的服务跑：
UI_BASE_URL=http://localhost:8080 npx playwright test
```

## 本地开发

```bash
# 终端 1：精确概率服务
cd odds && pip install -r requirements.txt && python app.py

# 终端 2：前端（/api 自动代理到 localhost:5000）
cd ui && npm install && npm run dev
```
