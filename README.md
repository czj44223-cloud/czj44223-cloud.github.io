# litterburger 的开发笔记

中文个人开发博客。网址：https://czj44223-cloud.github.io/

## 结构与维护

- `content/posts/`：Markdown 文章。
- `assets/style.css`：响应式样式。
- `site.json`：站点标题、GitHub 链接、可选的公开联系方式。
- `scripts/build.py`：仅依赖 Python 3 标准库的静态构建器。
- `scripts/check.py`：内部链接、页面标记、安全转义和移动端样式检查。
- `docs/`：提交到 GitHub Pages 的构建产物，不能只修改这里。

## 发一篇文章

1. 在 `content/posts/` 新建 `YYYY-MM-DD-slug.md`，slug 使用小写英文字母、数字、连字符。
2. 参考现有文章，填写如下元信息，再写正文：

```markdown
---
title: 新文章标题
date: 2026-11-08
summary: 一句话简介。
---
# 新文章标题

正文。
```

3. 在仓库根目录执行：

```sh
python3 scripts/build.py
python3 scripts/check.py
# 可选：本地预览，然后打开终端显示的地址
python3 -m http.server 8000 --directory docs --bind 127.0.0.1
```

4. 检查无误后，提交源码与 `docs/` 一起推送到 `main`。Pages 从 `main /docs` 自动发布；不需要 Actions token 或额外部署服务。

```sh
git add content docs
git commit -m "Add a new note"
git push origin main
```

当前 Markdown 子集支持标题、段落、有序/无序列表、链接、行内代码、围栏代码块；不支持嵌套列表、图片、表格和加粗。原始 HTML 被转义，不执行。所有文章均会发布，不支持私密草稿或定时发布。请不要将草稿、密钥、真实配置或私人数据放进本仓库。

## 可选公开联系方式

`site.json` 中 `contacts.emails` 为公开邮箱列表，`contacts.youtube` 为公开频道链接。仅在本人确认准确内容并同意公开后修改，再重新构建。邮箱会以明文显示且可能被抓取；不放占位邮箱或推测频道。

## 发布和回退

在 GitHub 仓库 Settings → Pages 中，Source 选择 Deploy from a branch，分支 `main`、目录 `/docs`。如果更新未生效，查看 Pages build 状态。需要撤回内容时使用正常的修正提交，不强推、不删除历史。

## 检查范围

自动检查包括全部内部链接和资源、中文语言标记、移动端 viewport、单列 CSS 断点、键盘焦点、减少动态效果偏好、Markdown HTML 转义。并不替代真实浏览器的视觉和多设备测试。

## 许可

站点代码、构建器及样式采用 MIT，见 LICENSE。文章内容不自动适用 MIT；未另行标注时保留作者权利。「寻源」是独立软件，适用其自定义许可，不是 MIT，也不是 OSI 开源。
