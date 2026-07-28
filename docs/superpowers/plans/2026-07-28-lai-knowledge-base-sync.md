# LAI Knowledge Base Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建兼顾 AI 检索与人工阅读的 LAI 项目知识库，更新项目同步规则，并把同名内容发布到有道云笔记的固定目录。

**Architecture:** 仓库中的六篇 Markdown 是可审查、可版本控制的内容源；有道云笔记保存同名阅读副本。知识库按索引、根目录、当前能力、架构、路线图、开发约定拆分，当前事实始终以源码和 `docs/ai` 当前文档为准。

**Tech Stack:** Markdown、PowerShell、Git、Chrome、有道云笔记网页版

## Global Constraints

- 当前发布版本是 v0.35，未来滚动队列是 v0.36-v0.44。
- 未来能力必须明确标注为规划或未实现，不能写成当前能力。
- 仓库只保存 `docs/knowledge-base/学习/开发/语言开发/灵语（LAI）/`，不提交其他领域的空目录。
- 有道云使用 `学习/开发/{Unity,Android 开发,微信小程序,语言开发}/` 分类，LAI 位于 `语言开发/灵语（LAI）/`。
- 不上传构建产物、临时日志、密钥、个人信息或未经验证的推测。
- 本次不修改编译器源码或语言行为，不以未重新执行的测试冒充本轮验证。
- 本轮不修改并行演进中的 `README.md` 和 `docs/ai`；v0.36 完成后按 `AGENTS.md` 新规则更新知识库。

---

## File Structure

**Create:**

- `docs/knowledge-base/学习/开发/语言开发/灵语（LAI）/00_LAI 知识索引.md`：总入口、阅读顺序、事实优先级和同步检查表。
- `docs/knowledge-base/学习/开发/语言开发/灵语（LAI）/01_项目根目录与模块地图.md`：根目录、核心模块、测试、示例、文档和生成物说明。
- `docs/knowledge-base/学习/开发/语言开发/灵语（LAI）/02_当前能力与运行方式.md`：v0.35 能力、C/LLVM 边界、命令和未实现项。
- `docs/knowledge-base/学习/开发/语言开发/灵语（LAI）/03_架构与编译流程.md`：编译链、模块职责和语法扩展路径。
- `docs/knowledge-base/学习/开发/语言开发/灵语（LAI）/04_未来版本规划_v0.36-v0.44.md`：九个滚动版本、待编号池和远期边界。
- `docs/knowledge-base/学习/开发/语言开发/灵语（LAI）/05_开发约定与文档入口.md`：接手、设计、验证、文档和知识库同步规则。

**Modify:**

- `AGENTS.md`：新增 LAI 知识库持续更新和有道云同步规则。
- `docs/superpowers/plans/2026-07-28-lai-knowledge-base-sync.md`：逐步勾选实际完成状态和验证证据。

## Task 1: 创建六篇本地知识库文档

**Files:**

- Create: `docs/knowledge-base/学习/开发/语言开发/灵语（LAI）/00_LAI 知识索引.md`
- Create: `docs/knowledge-base/学习/开发/语言开发/灵语（LAI）/01_项目根目录与模块地图.md`
- Create: `docs/knowledge-base/学习/开发/语言开发/灵语（LAI）/02_当前能力与运行方式.md`
- Create: `docs/knowledge-base/学习/开发/语言开发/灵语（LAI）/03_架构与编译流程.md`
- Create: `docs/knowledge-base/学习/开发/语言开发/灵语（LAI）/04_未来版本规划_v0.36-v0.44.md`
- Create: `docs/knowledge-base/学习/开发/语言开发/灵语（LAI）/05_开发约定与文档入口.md`

**Interfaces:**

- Consumes: `README.md`、`docs/ai/*.md`、当前源码/测试目录和 v0.35 设计/计划。
- Produces: 六篇可独立阅读、可按同名上传的 UTF-8 Markdown 文档。

- [x] **Step 1: 提取当前事实和历史边界**

运行：

```powershell
rg -n "^#|^##|v0\.35|v0\.36|v0\.44|当前不支持|下一步" README.md docs/ai/active-context.md docs/ai/roadmap.md docs/ai/architecture-map.md docs/ai/module-index.md docs/ai/conventions.md
```

预期：当前版本定位为 v0.35；路线图覆盖 v0.36-v0.44；旧发布记录不作为当前事实。

- [x] **Step 2: 编写索引、根目录和当前能力笔记**

`00_LAI 知识索引.md` 必须包含：当前版本、六篇职责、事实优先级、AI 快速入口、人工阅读顺序、版本完成同步检查表。

`01_项目根目录与模块地图.md` 必须包含：源码模块表、测试/示例/文档说明、生成目录和历史文件边界。

`02_当前能力与运行方式.md` 必须包含：类型/表达式/函数/控制流/比较能力、C/LLVM 对照、下列命令及未实现列表：

```powershell
python -m unittest discover -v
python lai_compiler.py main.ly --run
python lai_compiler.py examples/basic_comparisons.ly --run
python lai_compiler.py examples/unary_integer.ly --backend llvm --run
python lai_compiler.py examples/llvm_minimal.ly --backend llvm --run
python lai_compiler.py examples/llvm_arithmetic.ly --backend llvm --run
```

- [x] **Step 3: 编写架构、路线图和开发约定笔记**

`03_架构与编译流程.md` 必须包含：

```text
main.ly -> lexer -> parser -> AST -> semantic/type checker -> backend -> clang -> exe
```

并解释 `lai_compiler.py`、`lai_ast.py`、`lai_checker.py`、`lai_backend.py`、`lai_c_backend.py`、`lai_llvm_backend.py`、`lai_clang.py`、`lai_stdlib.py`、`lai_int.py` 的职责。

`04_未来版本规划_v0.36-v0.44.md` 必须逐项写明：

```text
v0.36 布尔逻辑表达式
v0.37 运行时整数安全
v0.38 通用函数早退与控制流分析
v0.39 数组核心
v0.40 数组实用操作与遍历
v0.41 循环方向与负步长
v0.42 字符串操作与最小用户标准库
v0.43 浮点数
v0.44 LLVM 变量模型与 SSA 复盘
```

`05_开发约定与文档入口.md` 必须包含：接手顺序、设计/计划路径、验证要求、生成物边界、本地/有道云知识库路径和更新流程。

- [x] **Step 4: 验证六篇文档完整性**

运行：

```powershell
$kb = 'docs/knowledge-base/学习/开发/语言开发/灵语（LAI）'
Get-ChildItem -LiteralPath $kb -File | Sort-Object Name | Select-Object Name,Length
rg -n "v0\.35|v0\.36|v0\.44|未实现|python -m unittest discover -v" $kb
```

预期：正好六篇非空 Markdown；索引/能力/路线图/约定中的版本、边界和命令均可检索。

- [x] **Step 5: 提交本地知识库**

```powershell
git add -- 'docs/knowledge-base/学习/开发/语言开发/灵语（LAI）'
git diff --cached --check
git commit -m "docs(knowledge-base): 建立 LAI 开发知识库"
```

预期：提交只包含六篇知识库文档。

## Task 2: 补全项目知识库自动同步规则

**Files:**

- Modify: `AGENTS.md`

**Interfaces:**

- Consumes: Task 1 的固定本地路径、六篇文件名和有道云目标目录。
- Produces: 后续 agent 可执行的版本完成后知识库总结与上传规则。

- [x] **Step 1: 在 `AGENTS.md` 增加知识库同步规则**

规则必须包含：

```text
每个用户可见版本或重要架构变更完成并验证后，更新
docs/knowledge-base/学习/开发/语言开发/灵语（LAI）/
中受影响的同名知识文档，并同步上传到有道云
学习/开发/语言开发/灵语（LAI）。
```

同时明确：每个版本完成后先汇总最新开发文档，再更新本地知识库并上传同名有道云笔记；只归档源码/测试已验证的稳定内容；规划标记未实现；禁止上传敏感信息和生成物；网页不可用时如实记录未同步。

- [x] **Step 2: 验证规则完整性**

运行：

```powershell
rg -n "docs/knowledge-base|学习/开发/语言开发/灵语（LAI）|有道云|最新开发文档|未实现|敏感|网页不可用" AGENTS.md
git diff --check
```

预期：`AGENTS.md` 能解析到本地/网页路径，并明确版本完成后的自动总结、上传和失败报告边界。

- [x] **Step 3: 提交项目规则更新**

```powershell
git add -- AGENTS.md
git diff --cached --check
git commit -m "docs(ai): 约定 LAI 知识库持续同步"
```

预期：提交只包含 `AGENTS.md` 中本任务新增的知识库规则；保留其中已有的并行修改。

## Task 3: 执行本地最终一致性验证

**Files:**

- Modify: `docs/superpowers/plans/2026-07-28-lai-knowledge-base-sync.md`

**Interfaces:**

- Consumes: Tasks 1-2 的六篇知识库与 `AGENTS.md` 规则。
- Produces: 可供有道云发布使用的已验证 Markdown 源，以及本轮实际验证记录。

- [x] **Step 1: 检查 Markdown、路径和未来能力措辞**

运行：

```powershell
$kb = 'docs/knowledge-base/学习/开发/语言开发/灵语（LAI）'
rg -n "TBD|TODO|已经实现.*v0\.(3[6-9]|4[0-4])|当前支持.*(数组|浮点|and|or|not)" $kb AGENTS.md
Get-ChildItem -LiteralPath $kb -File | ForEach-Object { if ($_.Length -eq 0) { throw "empty knowledge note: $($_.FullName)" } }
git diff --check
```

预期：不出现占位符或把 v0.36-v0.44 写成已实现的语句；无空文件；无空白错误。

- [x] **Step 2: 验证文档中的本地路径与命令入口**

运行：

```powershell
@('lai_compiler.py','lai_ast.py','lai_checker.py','lai_c_backend.py','lai_llvm_backend.py','main.ly','examples/basic_comparisons.ly') | ForEach-Object { if (-not (Test-Path -LiteralPath $_)) { throw "missing path: $_" } }
python lai_compiler.py --help
```

预期：路径全部存在；CLI 帮助显示 `--backend {c,llvm}`。本轮不重新运行完整单元测试和端到端构建。

- [x] **Step 3: 记录实际验证结果并提交计划状态**

在本计划末尾追加“执行记录”，写明实际命令、结果和未运行的测试，不复制旧发布测试作为本轮证据。

```powershell
git add -- 'docs/superpowers/plans/2026-07-28-lai-knowledge-base-sync.md'
git diff --cached --check
git commit -m "docs(knowledge-base): 记录本地知识库验证结果"
```

预期：计划中的本地步骤和验证状态与实际执行一致。

## Task 4: 创建并验证有道云知识库

**Files:**

- Read: `docs/knowledge-base/学习/开发/语言开发/灵语（LAI）/*.md`
- Update externally: 有道云笔记 `学习/开发/语言开发/灵语（LAI）`
- Modify: `docs/superpowers/plans/2026-07-28-lai-knowledge-base-sync.md`

**Interfaces:**

- Consumes: Task 3 验证完成的六篇本地 Markdown。
- Produces: 四类开发目录、LAI 子目录、六篇同名有道云 Markdown 笔记和网页验证记录。

- [ ] **Step 1: 创建有道云开发分类**

在 `学习` 下创建 `开发`，再创建四个同级目录：

```text
Unity
Android 开发
微信小程序
语言开发
```

在 `语言开发` 下创建 `灵语（LAI）`。

- [ ] **Step 2: 创建六篇同名 Markdown 笔记并写入完整内容**

按照本地文件名逐一创建：

```text
00_LAI 知识索引.md
01_项目根目录与模块地图.md
02_当前能力与运行方式.md
03_架构与编译流程.md
04_未来版本规划_v0.36-v0.44.md
05_开发约定与文档入口.md
```

每篇笔记正文必须与对应本地 Markdown 完整内容一致，不上传设计/计划、构建物或其他仓库文件。

- [ ] **Step 3: 验证网页保存与关键内容**

重新进入 `学习/开发/语言开发/灵语（LAI）`，确认：

```text
目录内正好存在六篇同名笔记
00_LAI 知识索引.md 包含 v0.35 和六篇职责
04_未来版本规划_v0.36-v0.44.md 包含 v0.36 与 v0.44
未来路线图明确标记为未实现规划
页面显示内容已保存
```

- [ ] **Step 4: 回写首次同步执行记录**

在本计划“执行记录”中写明网页目录、笔记数量和验证结果；不修改并行演进中的 `docs/ai`。

```powershell
git add -- 'docs/superpowers/plans/2026-07-28-lai-knowledge-base-sync.md'
git diff --cached --check
git commit -m "docs(knowledge-base): 记录有道云首次同步结果"
```

预期：提交只记录已经在网页端验证的同步结果。

- [ ] **Step 5: 推送并核对最终状态**

```powershell
git status --short --branch
git log -5 --oneline
git push origin main
git status --short --branch
```

预期：所有知识库与同步记录提交已推送到 `origin/main`，最终工作区干净并与远端同步。

## 执行记录

### 本地知识库与规则

- 2026-07-28：创建六篇本地知识库文档，提交 `a4c6d40`；任务级规格与质量审查通过，无遗留问题。
- 2026-07-28：在 `AGENTS.md` 增加版本完成后汇总最新开发文档、更新本地知识库和上传有道云的规则，提交 `cde5719`。
- 六篇文档数量和非空检查通过；v0.35、v0.36、v0.44、未实现边界和指定测试命令均可检索。
- 一致性扫描未发现占位符，也未发现把 v0.36-v0.44 写成已实现能力的表述。
- 关键源码、示例路径检查通过；`python lai_compiler.py --help` 显示 `--backend {c,llvm}` 且默认 `c`。
- `git diff --check` 通过。输出中的 CRLF 提示来自工作区已有 Windows 换行转换配置，不是空白错误。
- 本轮未重新运行完整单元测试和端到端构建；知识库引用的 v0.35 测试结果属于既有发布记录，不作为本轮新验证。

### 有道云首次同步

- 状态：待执行。
