# GitHub 发布记录

最后更新：2026-07-06

## 目的

本文记录本项目首次发布到 GitHub 的过程和结果，方便后续 AI 或开发者快速理解：

- 远端仓库在哪里；
- 当前主分支提交到了什么状态；
- 哪些文件是源码，哪些是生成物；
- 后续继续开发时应该如何验证和推送。

## GitHub 仓库

仓库地址：

```text
https://github.com/pilipalaBeng/AIProgrammingLanguage
```

Git remote：

```text
origin https://github.com/pilipalaBeng/AIProgrammingLanguage.git
```

本地分支：

```text
main -> origin/main
```

## 已完成的关键提交

```text
67271e2 Add LAI v0 compiler
77ff631 Add project README
```

其中：

- `67271e2`：加入 LAI v0 编译器、示例源码、测试、项目记忆文档。
- `77ff631`：加入项目 README，说明项目目标、v0 语法、运行方式和路线图。

## 当前项目状态

当前项目已经完成 LAI v0 最小闭环：

```text
main.lai -> lai_compiler.py -> build/main.c -> clang -> build/main.exe
```

当前示例源码：

```lai
fn main() {
    print("Hello LAI")
    let name = "JD"
    print(name)
}
```

当前运行结果：

```text
Wrote build\main.c
Built build\main.exe
Hello LAI
JD
```

## 推送前验证记录

已运行单元测试：

```powershell
python -m unittest tests.test_lai_compiler -v
```

结果：5 个测试通过。

已运行端到端编译：

```powershell
python lai_compiler.py main.lai --run
```

结果：成功生成 `build\main.c` 和 `build\main.exe`，并输出 `Hello LAI` 与 `JD`。

## Git 忽略规则

已经加入 `.gitignore`，避免提交生成物和缓存：

```text
__pycache__/
*.py[cod]
build/
*.exe
```

注意：

- `build/main.c` 和 `build/main.exe` 是编译生成物，不应手动维护。
- `hello.exe` 是早期 C 编译链路验证产物，不应提交。
- Python 的 `__pycache__/` 不应提交。

## 后续 AI 接手建议

1. 先读取 `README.md`，了解项目对外说明。
2. 再读取 `docs/ai/project-brief.md` 和 `docs/ai/active-context.md`，了解当前阶段。
3. 修改编译器前先运行：

   ```powershell
   python -m unittest tests.test_lai_compiler -v
   ```

4. 每次新增语法点时，优先补充 `tests/test_lai_compiler.py`。
5. 推送前运行：

   ```powershell
   python -m unittest tests.test_lai_compiler -v
   python lai_compiler.py main.lai --run
   git status --short --branch
   ```

6. 不要提交 GitHub 密码、token、浏览器登录态或其他凭据。

## 常用 Git 命令

查看状态：

```powershell
git status --short --branch
```

提交文档或代码：

```powershell
git add <files>
git commit -m "<message>"
```

推送到 GitHub：

```powershell
git push
```

如果新环境还没有 remote：

```powershell
git remote add origin https://github.com/pilipalaBeng/AIProgrammingLanguage.git
git branch -M main
git push -u origin main
```
