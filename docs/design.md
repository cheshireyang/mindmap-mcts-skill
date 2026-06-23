# MindMap-MCTS Codex Skill 设计规格

## 1. 目标

第一版目标是把现有的 MindMap-MCTS 方案落成一个可在 Codex 本地工作流中稳定使用的工具链：

- 用 Codex skill 约束 Agent 在复杂任务中的探索流程。
- 用本地 CLI 维护思维树真相源，避免模型手算 UCB 或手改 markdown。
- 用 JSON 保存状态，用 markdown 渲染可读视图。
- 保留 Claude Code 兼容空间，但不把它作为第一版硬目标。

这个版本的重点是先形成最小可用闭环：初始化树、扩展节点、评估节点、选择前沿、回传价值、渲染视图，并让 Agent 能按固定循环使用它。

## 2. 适用场景

启用 MindMap-MCTS 的场景：

- 复杂调试：多个可疑原因并存，需要系统排查。
- 架构或方案选择：多个候选路径需要比较。
- 需求拆解：目标不清晰，需要逐层分解和收敛。
- Agent 出现反复试错、绕圈、沉没成本明显的迹象。

不启用的场景：

- 单步命令或明确事实查询。
- 一眼能确定实现路径的小改动。
- 用户明确要求直接执行，不希望增加探索流程。

## 3. 非目标

第一版不做以下内容：

- 不做完整 Web app。
- 不做 SQLite 后端。
- 不做多用户协作。
- 不做自动生成最终代码改动。
- 不把 markmap 或浏览器可视化作为必需依赖。

这些能力可以在核心循环稳定后作为增强版本加入。

## 4. 总体形态

推荐形态是三层结构：

1. Codex skill
   - 定义何时触发、每轮怎么执行、如何记录证据、何时收敛。
   - Agent 必须通过 CLI 操作树，不直接编辑渲染后的 markdown。

2. Python CLI 树引擎
   - 负责 JSON 真相源、原子操作、UCB 选择、价值回传、markdown 渲染。
   - 提供稳定命令接口，供 Codex skill 调用。

3. 可读 markdown 视图
   - 从 JSON 渲染生成。
   - 供用户和 Agent 快速查看当前搜索状态。
   - 后续可接入 markmap、TUI 或轻量 Web 可视化。

## 5. 文件布局

建议第一版落地为一个本地工具目录：

```text
mindmap/
  mindmap-mcts-skill-design.md
  2026-06-23-mindmap-mcts-codex-skill-design.md
  tool/
    mindmap_mcts/
      __init__.py
      cli.py
      engine.py
      model.py
      render.py
    tests/
      test_engine.py
      test_cli.py
  skills/
    mindmap-mcts/
      SKILL.md
  examples/
    login-timeout.tree.json
    login-timeout.tree.md
```

如果后续要安装为正式 Codex skill，可以把 `skills/mindmap-mcts/SKILL.md` 复制或同步到 Codex skills 目录。

## 6. 数据模型

树状态保存为 JSON。根对象包含元信息、参数、节点列表和快照信息。

```json
{
  "version": 1,
  "title": "修复登录偶发超时",
  "root_id": "n1",
  "params": {
    "exploration_c": 0.7,
    "max_depth": 6,
    "max_iterations": 8,
    "branch_width": 3
  },
  "nodes": [
    {
      "id": "n1",
      "parent": null,
      "content": "修复登录偶发超时",
      "type": "goal",
      "state": "exploring",
      "V": 0.5,
      "N": 0,
      "evidence": "初始目标",
      "created_at": "2026-06-23T00:00:00-07:00",
      "updated_at": "2026-06-23T00:00:00-07:00"
    }
  ]
}
```

节点字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 稳定唯一标识，默认 `n1`、`n2` 递增 |
| `parent` | string/null | 父节点 id，根节点为 null |
| `content` | string | 想法、假设、方案或验证动作 |
| `type` | enum | `goal`、`hypothesis`、`option`、`probe`、`decision` |
| `state` | enum | `frontier`、`exploring`、`verified`、`pruned`、`selected` |
| `V` | number | 价值估计，范围 `[0, 1]` |
| `N` | integer | 访问次数 |
| `evidence` | string | 支撑当前价值的简短证据 |
| `created_at` | string | ISO 时间 |
| `updated_at` | string | ISO 时间 |

## 7. CLI 命令

第一版提供以下命令：

```bash
mindmap init --title "修复登录偶发超时" --out task.tree.json
mindmap add task.tree.json --parent n1 --type hypothesis --content "DB 连接池耗尽"
mindmap eval task.tree.json --id n2 --value 0.8 --evidence "日志出现 pool timeout"
mindmap prune task.tree.json --id n3 --evidence "grep 无重试逻辑，排除"
mindmap select task.tree.json
mindmap backprop task.tree.json --from n2
mindmap render task.tree.json --out task.tree.md
mindmap show task.tree.json
```

命令行为：

- `init` 创建根节点和默认参数。
- `add` 只添加一个节点，批量扩展由 Agent 多次调用完成。
- `eval` 写入 `V`、`evidence`，并把节点状态设为 `verified` 或 `exploring`。
- `prune` 把节点状态设为 `pruned`，价值置为 `0`。
- `select` 根据 UCB 从根向下选择最值得探索的前沿节点。
- `backprop` 从指定节点向根回传访问次数和价值。
- `render` 从 JSON 生成 markdown 大纲。
- `show` 输出当前最佳路径、前沿节点和预算状态摘要。

## 8. 搜索规则

选择阶段由代码执行：

```text
score = V + c * sqrt(ln(N_parent + 1) / N_child)
```

规则细节：

- `N_child = 0` 时，该子节点分数视为无限大，保证新分支至少被探索一次。
- 已剪枝节点不参与选择。
- 如果某一层没有可选子节点，当前节点就是本轮前沿。
- 默认 `c = 0.7`。

回传阶段由代码执行：

- 选择路径上的祖先节点 `N += 1`。
- 父节点 `V` 默认更新为未剪枝子节点中的最大 `V`。
- 若父节点所有子节点都已剪枝，父节点可被自动降为低价值，但不自动剪枝。

## 9. Codex Skill 行为

Skill 的职责是约束 Agent 的使用流程，不负责实现算法。

启动流程：

1. 判断任务是否适合启用 MindMap-MCTS。
2. 若适合，创建或打开当前任务的 `.tree.json`。
3. 渲染 `.tree.md`，向用户展示当前思维树。
4. 调用 `mindmap select` 选择本轮前沿节点。

每轮循环：

1. 读取前沿节点。
2. 生成 2 到 3 个互斥、具体、可验证的子节点。
3. 对每个子节点执行最低成本真实探针，例如读代码、grep、跑单测、查日志。
4. 用 `mindmap eval` 或 `mindmap prune` 写回价值和证据。
5. 调用 `mindmap backprop` 回传价值。
6. 调用 `mindmap render` 更新 markdown 视图。
7. 判断是否收敛或需要用户决策。

终止条件：

- 存在一条价值不低于 `0.85` 且关键节点有真实证据支持的路径。
- 达到迭代预算。
- 多条路径价值接近，且没有廉价探针能继续区分，需要用户选择。

收敛后，Agent 应把选定路径转成执行计划，再进入具体实现。

## 10. Markdown 渲染

渲染输出示例：

```markdown
# 修复登录偶发超时

- [n1] (V=0.85 N=5 exploring) 修复登录偶发超时
  - [n2] (V=0.90 N=3 verified) 假设：DB 连接池耗尽 -- 日志见 pool timeout
    - [n5] (V=0.95 N=1 selected) 方案：max 5 到 20 + 超时回收 -- 压测下超时消失
  - [n3] (V=0.00 N=1 pruned) 假设：前端重试风暴 -- grep 无重试逻辑，排除
```

第一版使用英文状态名，避免终端或测试环境中的符号兼容问题。后续可以增加 emoji 渲染选项。

## 11. 人在环中

用户可以牵引探索方向，但不直接编辑渲染文件作为真相源。

第一版支持两种牵引方式：

- 通过 CLI 添加节点、剪枝节点、重评估节点。
- 直接编辑 JSON，但 Agent 下一轮必须先运行 `mindmap show` 或 `mindmap render` 重新读取状态。

Skill 应在关键分叉时停下并展示：

- 当前最佳路径。
- 价值接近的替代路径。
- 每条路径的关键证据。
- 建议的下一步探针或用户决策点。

## 12. 错误处理

CLI 需要处理以下错误：

- JSON 文件不存在或格式错误：输出明确错误，不创建隐式新树。
- 节点 id 不存在：列出可用相近 id 或提示运行 `show`。
- `V` 超出 `[0, 1]`：拒绝写入。
- 尝试给剪枝节点添加子节点：默认拒绝，除非显式传入 `--force`。
- 检测到环或孤儿节点：`show` 和 `render` 应失败并指出问题节点。
- 多个命令同时写文件：第一版采用原子写入临时文件再替换，降低损坏风险。

## 13. 测试策略

核心测试集中在树引擎和 CLI：

- 初始化树会创建合法根节点和默认参数。
- 添加节点会生成稳定 id，并正确挂到父节点下。
- UCB 选择会优先访问 `N = 0` 的节点。
- 剪枝节点不会被 `select` 选中。
- 回传会更新祖先 `N` 和 `V`。
- 渲染输出保留父子层级、状态、价值和证据。
- 非法 JSON、非法节点 id、非法价值会返回非零退出码。

Skill 文档通过人工检查验证：

- 是否明确规定 Agent 不直接改 markdown。
- 是否明确要求真实探针优先。
- 是否明确规定收敛和用户决策条件。

## 14. 分阶段交付

第一阶段：核心闭环

- Python 包结构。
- JSON 模型和文件读写。
- `init`、`add`、`eval`、`prune`、`select`、`backprop`、`render`、`show`。
- 单元测试。
- Codex skill 初版。

第二阶段：使用体验

- 示例任务。
- 更清晰的 `show` 摘要。
- markmap 兼容渲染选项。
- 预算状态提示。

第三阶段：可视化和回放

- 文件监听。
- 浏览器或 TUI 可视化。
- 每轮快照。
- 探索过程回放。

## 15. 第一版完成标准

第一版完成时，应满足：

- 用户能用 CLI 创建一棵树并完成至少一轮 MCTS 循环。
- Codex skill 能指导 Agent 按树循环做复杂任务探索。
- markdown 视图能清楚展示节点、价值、访问次数、状态和证据。
- 测试覆盖核心算法和主要 CLI 错误路径。
- 在一个示例任务中能跑出“选择前沿、扩展、评估、回传、收敛或暴露分叉”的完整记录。
