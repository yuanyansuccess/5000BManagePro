# build/tools —— 环境安装包获取工具

## 为什么这里没有现成的安装包？

环境安装包体积很大（MySQL 5.7 约 300 MB、Python 约 25 MB、Git 约 60 MB）：

- Git 仓库**不适合存放大二进制**：会让 `clone` / `push` 变得极慢，且 GitHub 对单个文件有 **100 MB** 限制；
- 安装包属于"可随时重新获取的第三方制品"，放进仓库属于冗余；
- 因此本目录提供**一键下载脚本**，联网即可把所需安装包全部取回，断网环境下也可先在有网机器下载后拷贝到本机。

## 一键下载（推荐）

双击运行：

```
build\tools\download_installers.bat
```

会自动下载到 `build\tools\installers\`（该目录已加入 `.gitignore`，不会入库）：

| 安装包 | 版本 | 用途 |
|--------|------|------|
| python-3.9.13-amd64.exe | 3.9.13 | Python 运行环境 |
| mysql-installer-5.7.44.msi | 5.7.44 | MySQL 数据库 |
| Git-2.45.2-64-bit.exe | 2.45.2 | 代码拉取/版本管理 |

## Python 依赖离线包（内网/断网部署用）

若目标机器不能联网，先在有网的机器执行：

```
build\tools\download_offline_wheels.bat
```

会把后端依赖全部下载成 wheel 包到 `build\tools\offline_wheels\`，把该目录整体拷贝到目标机器后执行：

```
python -m pip install --no-index --find-links=build\tools\offline_wheels -r requirements.txt
```

## 手动下载（脚本失效时的备用地址）

| 软件 | 官方地址 |
|------|----------|
| Python 3.9.13 | https://www.python.org/downloads/release/python-3913/ |
| MySQL 5.7 | https://dev.mysql.com/downloads/mysql/5.7.html |
| Git | https://git-scm.com/download/win |

> 若官网改版导致脚本下载失败，按上表手动下载后，把安装文件放进 `build\tools\installers\` 即可，后续步骤不变。
