<h1 align="center">Agentic Coding - Project Template</h1>

<p align="center">
  <a href="https://github.com/The-Pocket/PocketFlow" target="_blank">
    <img 
      src="./assets/banner.png" width="600"
    />
  </a>
</p>

This is a project template for Agentic Coding with [Pocket Flow](https://github.com/The-Pocket/PocketFlow), a 100-line LLM framework, and your editor of choice.

- We have included the [.cursorrules](.cursorrules), [.clinerules](.clinerules), and [.windsurfrules](.windsurfrules) files to let Cursor AI (also Cline, or Windsurf) help you build LLM projects.
- Want to learn how to build LLM projects with Agentic Coding?

  - Check out the [Agentic Coding Guidance](https://the-pocket.github.io/PocketFlow/guide.html)
  - Check out the [YouTube Tutorial](https://www.youtube.com/@ZacharyLLM?sub_confirmation=1)

## 資料庫初始化

每次你有 model/schema 變動時，請先執行：

```sh
python scripts/init_db.py
```

這會自動建立（或更新）所有 SQLite 資料表，確保資料庫結構正確。
