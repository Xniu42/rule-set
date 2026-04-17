# GeoSite 到 Egern Rule Set 同步方案

## 1. 概览

本文档定义本仓库后续实现与维护时的单一事实来源（Single Source of Truth，SSO）。

本项目用于定时拉取 `MetaCubeX/meta-rules-dat` 的指定 `GeoSite` 源文件，将其转换为符合 Egern 语法的 `rule set` 文件，并保存到当前仓库，供 Egern 作为本地或远程规则集引用。

## 2. 边界

### 2.1 处理范围

- 仅处理 `MetaCubeX/meta-rules-dat` 的 `GeoSite` 数据。
- 仅转换已在本仓库配置文件中显式声明的目标集合。
- 仅生成 Egern 可直接使用的域名类 `rule set` 文件。
- 支持本地补丁层，用于增补或剔除少量域名项。
- 支持定时同步与手动触发同步。

### 2.2 非处理范围

- 不转换 `GeoIP`。
- 不拉取全部 `GeoSite` 集合。
- 不手工维护自动生成文件。
- 不修改 `claude.yaml` 与 `custom.yaml` 的内容。
- 不依赖 Egern 内置 `geosite` 功能；本项目目标即为规避该限制。

## 3. 前置条件

### 3.1 上游数据来源

- 上游仓库：`MetaCubeX/meta-rules-dat`
- 上游分支：`meta`
- 上游目录：`geo/geosite`
- 上游单文件路径格式：`geo/geosite/<source>.yaml`

### 3.2 当前目标语法

Egern 支持 5 种域名类规则集字段：

- `domain_set`
- `domain_suffix_set`
- `domain_keyword_set`
- `domain_regex_set`
- `domain_wildcard_set`

当前上游 `GeoSite` YAML 的 `payload` 经复核，仅包含以下两类项：

- 普通域名，例如 `openaiapi-site.azureedge.net`
- 以 `+.` 开头的后缀域名，例如 `+.openai.com`

因此，第一阶段仅需要生成以下两类字段：

- 普通域名 -> `domain_set`
- `+.` 后缀域名 -> `domain_suffix_set`

其余 3 种域名类字段当前不使用。若上游未来出现新语法，转换任务必须失败并保留旧文件，不允许静默忽略或猜测性转换。

### 3.3 执行环境

- 本地执行环境：可运行 Python 3
- 自动执行环境：GitHub Actions
- GitHub 仓库建议为公开仓库；公开仓库使用标准 GitHub Hosted Runner 时，定时同步通常可免费执行

## 4. 目标目录结构

```text
rule-set/
├── Egern/
│   ├── claude.yaml
│   ├── custom.yaml
│   └── generated/
│       ├── openai.yaml
│       ├── scholar-non-cn.yaml
│       └── ...
├── config/
│   └── geosite.yaml
├── overrides/
│   ├── openai.include.txt
│   ├── openai.exclude.txt
│   └── ...
├── scripts/
│   └── build_geosite.py
├── tests/
│   └── test_build_geosite.py
├── docs/
│   └── geosite-sync-sso.md
└── .github/
    └── workflows/
        └── sync-geosite.yml
```

## 5. 目录职责

### 5.1 `Egern/`

- `Egern/claude.yaml`：手工维护，永久保留
- `Egern/custom.yaml`：手工维护，永久保留
- `Egern/generated/`：自动生成目录，仅允许同步脚本写入

### 5.2 `config/`

- `config/geosite.yaml`：唯一配置入口
- 所有需要同步的目标集合均在此声明
- 后续新增、停用、修改同步目标时，仅修改此文件

### 5.3 `overrides/`

- 用于少量本地补丁
- `*.include.txt`：在上游结果基础上追加规则项
- `*.exclude.txt`：在上游结果基础上剔除规则项
- 补丁文件仅用于处理上游未覆盖或本地不需要的少量差异

### 5.4 `scripts/`

- 放置转换脚本
- 负责拉取、解析、转换、合并补丁、校验、输出

### 5.5 `tests/`

- 放置最小必要测试
- 用于校验转换逻辑、异常阻断逻辑与输出稳定性

## 6. 配置模型

`config/geosite.yaml` 采用声明式结构。每个目标集合必须显式定义本地稳定标识与上游源名称。

示例：

```yaml
upstream:
  repo: MetaCubeX/meta-rules-dat
  branch: meta
  path: geo/geosite

targets:
  - id: openai
    enabled: true
    sources:
      - openai

  - id: scholar-non-cn
    enabled: true
    sources:
      - category-scholar-!cn

  - id: steam-cn
    enabled: false
    sources:
      - steam@cn
    include: overrides/steam-cn.include.txt
    exclude: overrides/steam-cn.exclude.txt
```

字段说明：

- `id`：本地稳定标识，同时作为输出文件名主体；仅允许使用 `a-z`、`0-9`、`-`
- `enabled`：是否参与本次同步
- `sources`：上游 `GeoSite` 名称列表，允许一个本地目标合并多个上游源
- `include`：可选；追加补丁文件路径
- `exclude`：可选；剔除补丁文件路径

设计约束：

- `id` 与 `source` 必须分离
- 不允许直接以 `category-scholar-!cn`、`steam@cn` 等上游名称作为本地文件名
- 特殊字符源名由 `sources` 保存，本地文件名统一由 `id` 决定

## 7. 补丁文件规范

补丁文件每行一条规则项，仅允许以下两种写法：

- `example.com`：精确域名
- `+.example.com`：域名后缀

其他规则：

- 允许空行
- 允许以 `#` 开头的注释行
- 不允许使用正则、通配符、关键字等其他语法

示例：

```text
# 精确域名
api.example.com

# 后缀域名
+.example.org
```

补丁处理顺序：

1. 拉取并合并所有 `sources`
2. 解析并分类为 `domain_set` 与 `domain_suffix_set`
3. 应用 `include`
4. 应用 `exclude`
5. 去重
6. 排序
7. 输出

## 8. 转换规则

### 8.1 输入规则

上游文件格式：

```yaml
payload:
  - openaiapi-site.azureedge.net
  - +.openai.com
```

### 8.2 输出规则

生成文件格式：

```yaml
domain_set:
  - openaiapi-site.azureedge.net

domain_suffix_set:
  - openai.com
```

### 8.3 语法映射

- `example.com` -> `domain_set`
- `+.example.com` -> `domain_suffix_set`，输出时移除 `+.`

### 8.4 输出约束

- 自动去重
- 自动按字典序排序
- 空字段不输出
- 自动删除 `Egern/generated/` 中已不再由当前配置生成的旧 `.yaml` 文件
- 文件编码为 UTF-8
- 行尾统一为 LF
- 生成文件可重复执行并保持稳定 diff

### 8.5 失败保护

出现以下情况时，任务必须失败：

- 上游文件不存在
- 上游文件无法下载
- 上游 YAML 无法解析
- `payload` 缺失
- `payload` 中出现非受支持语法
- 生成结果为空且配置未显式允许空集

失败时的处理要求：

- 不覆盖已有生成文件
- 工作流返回失败状态
- 日志输出具体失败目标与原因

## 9. 生成文件规范

每个自动生成文件放置于 `Egern/generated/<id>.yaml`。

文件头建议包含注释，记录以下信息：

- 生成来源仓库
- 生成来源分支
- 生成来源集合名
- 不写入生成时间；生成时间会导致无意义 diff，并使定时任务在源数据未变化时仍产生提交

示例：

```yaml
# source_repo: MetaCubeX/meta-rules-dat
# source_branch: meta
# source_names: openai
domain_set:
  - openaiapi-site.azureedge.net

domain_suffix_set:
  - chat.com
  - openai.com
```

## 10. 自动同步流程

### 10.1 触发方式

- `schedule`：定时执行，建议每天 1 次
- `workflow_dispatch`：手动触发

### 10.2 执行阶段

1. 检出当前仓库
2. 准备运行环境
3. 读取 `config/geosite.yaml`
4. 下载每个已启用目标对应的上游 YAML
5. 执行转换与补丁合并
6. 执行语法校验与结果校验
7. 仅在输出变更时提交更新

### 10.3 提交原则

- 仅提交自动生成目录与必要配置文件
- 不改动手工维护文件
- 无变更时不提交空提交
- 变更检测必须覆盖新增文件、修改文件与删除文件

## 11. 验证与验收

### 11.1 成功标准

- 每个启用目标均成功生成 `Egern/generated/<id>.yaml`
- 生成文件仅包含 `domain_set` 与 `domain_suffix_set`
- 生成文件可被 YAML 解析
- 同一输入重复执行两次，输出内容完全一致
- `Egern/claude.yaml` 与 `Egern/custom.yaml` 未被修改

### 11.2 检查方式

配置检查：

- 检查 `config/geosite.yaml` 中 `id` 是否唯一
- 检查 `id` 是否满足命名约束

输出检查：

- 检查生成文件是否存在
- 检查生成文件是否仅包含受支持字段
- 检查条目是否已去重并排序

流程检查：

- 模拟上游 404，确认任务失败且不覆盖旧文件
- 模拟非法 `payload`，确认任务失败且输出明确错误

## 12. 最小测试范围

至少覆盖以下场景：

- `openai`：普通单源转换
- `category-scholar-!cn`：带 `!` 的源名称
- `steam@cn`：带 `@` 的源名称
- 多 `sources` 合并
- `include` 生效
- `exclude` 生效
- 非法 `payload` 阻断
- 空结果阻断

## 13. 常见问题与处理

### 13.1 症状：工作流成功执行，但 Egern 实际未命中规则

原因：

- 使用了上游原始 `payload` 文件而非转换结果
- Egern 引用的路径不是 `Egern/generated/*.yaml`
- 主配置引用了旧文件名

定位：

- 检查仓库内生成文件是否为 `domain_set` 与 `domain_suffix_set` 结构
- 检查 Egern 使用的 URL 或本地路径是否指向正确文件

修复：

- 改为引用本仓库生成文件
- 校对目标 `id` 与引用路径

复验：

- 重新加载 Egern 配置并验证规则命中

### 13.2 症状：某个目标突然生成失败

原因：

- 上游文件路径变更
- 上游新增了当前未支持的语法
- 上游文件暂时不可访问

定位：

- 查看工作流日志中的失败目标与原始内容摘要

修复：

- 确认上游路径
- 扩展转换器语法支持，或临时停用该目标

复验：

- 手动触发工作流并确认恢复成功

### 13.3 症状：生成文件内容与预期不一致

原因：

- `include` 或 `exclude` 补丁配置错误
- 多 `sources` 合并后出现覆盖认知偏差

定位：

- 检查对应 `overrides` 文件
- 对比源集合拉取结果与生成结果

修复：

- 修正补丁内容
- 必要时拆分目标集合

复验：

- 重新生成并比对输出

## 14. 后续执行原则

- 先落地目录与配置文件，再实现转换脚本
- 先实现本地可重复执行，再接入 GitHub Actions
- 先覆盖最小测试范围，再启用定时同步
- 未更新本文档前，不得擅自改变目录职责、配置格式与转换规则

## 15. 参考

- MetaCubeX 仓库：<https://github.com/MetaCubeX/meta-rules-dat>
- MetaCubeX `meta` 分支 `GeoSite` 目录：<https://github.com/MetaCubeX/meta-rules-dat/tree/meta/geo/geosite>
- Egern Rules 文档：<https://egernapp.com/docs/configuration/rules/>
