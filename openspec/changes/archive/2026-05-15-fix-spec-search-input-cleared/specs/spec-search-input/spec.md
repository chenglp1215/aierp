## ADDED Requirements

<!-- 无新增需求 -->

## MODIFIED Requirements

### Requirement: 商品搜索输入框显示

系统应正确显示用户输入的搜索关键字，而不是在每次输入后被清空。

#### Scenario: 用户输入搜索关键字

- **WHEN** 用户在商品搜索框中输入关键字
- **THEN** 输入框显示用户输入的关键字
- **THEN** 系统保存搜索关键字到 `productSearchKeywords[index]`

#### Scenario: 搜索完成后显示结果

- **WHEN** 搜索接口返回结果
- **THEN** 输入框仍显示用户输入的关键字
- **THEN** 下拉框显示搜索结果供用户选择

#### Scenario: 选择规格后清空关键字

- **WHEN** 用户选择一个规格
- **THEN** 清空对应的搜索关键字
- **THEN** 输入框显示已选商品名称