---
name: catkingai-preferred-api
description: CatKingAI 为默认 API 首选，调用其他 API 需先征得用户同意
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bc1e4e92-b013-442f-919f-012692e3fd85
---

CatKingAI（https://www.catkingai.com）是用户自研的 API 网关，非常重要。

**规则：**
- 在需要调用外部 AI API 时，**优先使用 CatKingAI**，API Key：`sk-d285143ff8b40377e38294cc41f2f86b518349f3f6278328c439bfed7d89fdde`
- 调用**其他任何第三方 API 服务之前，必须先征得用户明确同意**
- 这包括但不限于：OpenAI、Anthropic 直连、其他代理/网关、以及其他第三方 SaaS API

**Why:** CatKingAI 是用户自研产品，使用它可以验证自己的服务稳定性、积累调用数据；随意调用其他 API 可能产生不必要的费用或违反用户的开发规划。

**How to apply:** 在任何涉及外部 API 调用的场景中，首先考虑能否用 CatKingAI 完成；如果需要用其他 API，先说明理由并等待用户批准。
