# rule-set

[![Sync GeoSite Rule Sets](https://github.com/Xniu42/rule-set/actions/workflows/sync-geosite.yml/badge.svg)](https://github.com/Xniu42/rule-set/actions/workflows/sync-geosite.yml)

[English](./README.md) | 简体中文

本仓库提供基于 [MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat) 中部分 GeoSite 定义转换而来的、适用于 Egern 的非官方 rule-set 文件。

## 概览

Egern 不能直接使用 MetaCubeX 的 `geosite` YAML 文件。本仓库从 MetaCubeX `meta` 分支拉取选定的 GeoSite 源文件，将其转换为 Egern 的 rule-set 语法，并将生成结果存放在 [`Egern/generated/`](./Egern/generated)。

本仓库是面向 Egern 使用场景的兼容性项目，与 MetaCubeX 或 Egern 没有隶属关系，也未获得其背书。

当前范围：

- 仅处理 GeoSite
- 仅转换选定目标
- 仅生成 Egern 域名类 rule set
- 通过 GitHub Actions 自动同步

## 项目目的

MetaCubeX GeoSite 数据在 sing-box 与 Clash/Mihomo 中可通过 `geosite:xxx` 直接复用，但 Egern 需要显式的 `domain_set`、`domain_suffix_set` 等规则集文件。

本仓库用于补足这一兼容层：

- 复用选定的上游 GeoSite 定义，避免手工维护大量域名列表
- 仅转换实际需要的目标集合
- 保持生成文件稳定，便于远程引用
- 将手工维护文件与自动生成文件分离

生成结果可能与上游源文件不同，原因包括：

- Egern 需要不同的 rule-set 格式
- 本仓库只选取上游目录中的部分集合
- 本仓库可选地应用本地 include/exclude 补丁

## 仓库结构

- [`Egern/generated/`](./Egern/generated)：自动生成的 Egern rule-set 文件
- [`Egern/claude.yaml`](./Egern/claude.yaml)：手工维护文件
- [`Egern/custom.yaml`](./Egern/custom.yaml)：手工维护文件
- [`Egern/iherb.yaml`](./Egern/iherb.yaml)：手工维护文件
- [`config/geosite.yaml`](./config/geosite.yaml)：上游 GeoSite 选择配置
- [`overrides/`](./overrides)：可选的本地 include/exclude 补丁
- [`scripts/build_geosite.py`](./scripts/build_geosite.py)：转换脚本
- [`tests/test_build_geosite.py`](./tests/test_build_geosite.py)：单元测试
- [`docs/geosite-sync-architecture.md`](./docs/geosite-sync-architecture.md)：架构与维护说明
- [`NOTICE.md`](./NOTICE.md)：上游归属与复用说明

## 在 Egern 中使用

应使用生成文件的原始文件链接，不应使用 GitHub 页面中的 `blob` 链接。

示例：

- Raw GitHub：
  - `https://raw.githubusercontent.com/Xniu42/rule-set/main/Egern/generated/openai.yaml`
- jsDelivr：
  - `https://cdn.jsdelivr.net/gh/Xniu42/rule-set@main/Egern/generated/openai.yaml`

示例文件内容：

```yaml
domain_set:
  - openaiapi-site.azureedge.net

domain_suffix_set:
  - openai.com
  - chatgpt.com
```

## 自动同步

GitHub Actions workflow 定义在 [`sync-geosite.yml`](./.github/workflows/sync-geosite.yml)。

当前行为：

- 支持 `workflow_dispatch` 手动触发
- 支持定时执行
- 安装依赖
- 运行单元测试
- 根据 [`config/geosite.yaml`](./config/geosite.yaml) 全量重建已启用目标
- 仅在 `Egern/generated/` 中存在实际变更时提交并推送

当前定时频率为每天一次，执行时间为 `03:17 UTC`。

## 本地开发

### 依赖

- Python 3
- `PyYAML`

### 运行测试

```bash
uv run --with PyYAML python3 -m unittest discover -s tests -p "test_*.py"
```

### 生成规则文件

```bash
uv run --with PyYAML python3 scripts/build_geosite.py
```

## 新增或调整目标

1. 修改 [`config/geosite.yaml`](./config/geosite.yaml)
2. 如有必要，在 [`overrides/`](./overrides) 中增加补丁文件
3. 运行测试
4. 执行生成脚本
5. 提交更新后的生成文件

## 归属说明

- 主要上游来源：[MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat)
- 本仓库使用的上游路径：`meta/geo/geosite`
- 本仓库生成文件基于选定的上游开源数据转换而来，目标是输出 Egern 可直接使用的语法
- 上游项目的作者、维护历史与原始数据归属仍属于上游项目及其贡献者

更多说明见 [`NOTICE.md`](./NOTICE.md)。

## 免责声明

本仓库是面向 Egern 使用场景的非官方兼容性项目。

生成文件按 “as is” 方式提供，不附带任何形式的保证，也不承诺技术支持、兼容性或持续可用性。

本仓库与 MetaCubeX 或 Egern 没有隶属关系，也未获得其背书。

## 说明

- 当前仅转换上游中的精确域名与 `+.` 后缀域名
- 若上游未来引入当前不支持的语法，构建会直接失败，而不是猜测性转换
- 从配置中移除的目标，会在下一次生成时自动从 `Egern/generated/` 中清理

## 许可证

本仓库按 [GPL-3.0](./LICENSE) 分发。

使用或再分发前，请同时阅读 [`NOTICE.md`](./NOTICE.md) 中的上游归属与复用说明。
